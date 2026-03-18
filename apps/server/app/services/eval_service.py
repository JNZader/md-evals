"""Eval execution service — bridges FastAPI with md_evals engine.

Runs evaluations in background tasks, publishes SSE events via
per-eval asyncio.Queue instances, and persists results to the DB.
"""

from __future__ import annotations

import asyncio
import hashlib
import logging
import os
import tempfile
from datetime import datetime, timezone
from typing import Any

import yaml
from sqlalchemy import select, update

from app.config import settings
from app.models import Evaluation, ProviderKey, async_session_factory
from app.services.crypto import decrypt_key, derive_user_key, normalize_master_key
from app.services.session_keys import session_key_store

# md_evals imports (core library — never modified)
from md_evals.engine import ExecutionEngine
from md_evals.evaluator import EvaluatorEngine
from md_evals.llm import LLMAdapter
from md_evals.models import EvalConfig, Treatment

logger = logging.getLogger(__name__)


class EvalService:
    """Manages eval lifecycle: launch, execute, stream, persist."""

    def __init__(self) -> None:
        self._event_queues: dict[str, asyncio.Queue[dict[str, Any]]] = {}

    # ---------- Public API ----------

    async def start_eval(
        self,
        *,
        user_id: str,
        name: str,
        skill_content: str,
        eval_yaml: str,
        model: str | None = None,
        provider: str | None = None,
    ) -> dict[str, Any]:
        """Parse config, create DB record, launch background task.

        Returns a dict with ``eval_id``, ``status``, ``created_at``.
        Raises ``ValueError`` on invalid YAML / missing provider key.
        """
        # 1. Parse YAML → EvalConfig
        try:
            raw = yaml.safe_load(eval_yaml)
        except yaml.YAMLError as exc:
            raise ValueError(f"Invalid YAML: {exc}") from exc

        if not isinstance(raw, dict) or "tests" not in raw:
            raise ValueError("Eval YAML must contain a 'tests' section.")

        config = EvalConfig(**raw)

        # Override model/provider if provided explicitly
        if model:
            config.defaults.model = model
        if provider:
            config.defaults.provider = provider

        # 2. Resolve API key
        api_key = await self._resolve_api_key(user_id, config.defaults.provider)

        # 3. Create DB record
        async with async_session_factory() as session:
            evaluation = Evaluation(
                user_id=user_id,
                title=name,
                status="running",
                skill_content=skill_content,
                eval_config=config.model_dump(mode="json"),
                cost_metrics=None,
                context_metrics=None,
                error_message=None,
            )
            session.add(evaluation)
            await session.commit()
            await session.refresh(evaluation)
            eval_id = str(evaluation.id)
            created_at = evaluation.created_at

        # 5. Create event queue for SSE consumers
        self._event_queues[eval_id] = asyncio.Queue()

        # 6. Launch background execution
        asyncio.create_task(
            self._execute(
                eval_id=eval_id,
                config=config,
                skill_content=skill_content,
                api_key=api_key,
            )
        )

        return {
            "eval_id": eval_id,
            "status": "running",
            "created_at": created_at,
        }

    def get_event_queue(self, eval_id: str) -> asyncio.Queue[dict[str, Any]]:
        """Return the event queue for an eval, creating if absent."""
        if eval_id not in self._event_queues:
            self._event_queues[eval_id] = asyncio.Queue()
        return self._event_queues[eval_id]

    # ---------- Background execution ----------

    async def _execute(
        self,
        eval_id: str,
        config: EvalConfig,
        skill_content: str,
        api_key: str,
    ) -> None:
        """Run the eval in background using md_evals engine."""
        queue = self._event_queues[eval_id]
        temp_skill_path: str | None = None
        idx = 0
        total_tests = 0

        try:
            # Build adapters — pass api_key directly (no env vars).
            # GitHub Models exposes an OpenAI-compatible endpoint so we
            # remap provider to "openai" with a custom api_base.
            if config.defaults.provider == "github-models":
                adapter = LLMAdapter(
                    model=config.defaults.model,
                    provider="openai",
                    api_base="https://models.inference.ai.azure.com",
                    api_key=api_key,
                    defaults=config.defaults,
                )
            else:
                adapter = LLMAdapter(
                    model=config.defaults.model,
                    provider=config.defaults.provider,
                    api_key=api_key,
                    defaults=config.defaults,
                )
            evaluator = EvaluatorEngine(llm_adapter=adapter)
            engine = ExecutionEngine(config, adapter, evaluator)

            # Write skill content to a temp file for treatments that need it
            temp_skill_path = self._write_temp_skill(skill_content)

            # Prepare treatments — patch skill_path for non-CONTROL treatments
            treatments = self._prepare_treatments(config, temp_skill_path)

            all_tasks = config.tests
            total_tests = len(treatments) * len(all_tasks)

            # Emit eval_started
            await queue.put({
                "type": "eval_started",
                "eval_id": eval_id,
                "total_tests": total_tests,
                "model": config.defaults.model,
                "provider": config.defaults.provider,
            })

            # Run each (treatment, test) combination
            results = []
            idx = 0
            for t_name, treatment in treatments.items():
                for task in all_tasks:
                    await queue.put({
                        "type": "test_started",
                        "test_index": idx,
                        "test_name": task.name,
                        "treatment": t_name,
                    })

                    result = await asyncio.wait_for(
                        engine.run_single(treatment, task, t_name),
                        timeout=settings.EVAL_TIMEOUT_MINUTES * 60,
                    )
                    results.append(result)

                    score = max(
                        (r.score for r in result.evaluator_results),
                        default=0.0,
                    )
                    event: dict[str, Any] = {
                        "type": "test_completed",
                        "test_index": idx,
                        "test_name": task.name,
                        "treatment": t_name,
                        "passed": result.passed,
                        "score": score,
                        "duration_ms": result.response.duration_ms,
                    }
                    # Surface LLM errors so the frontend can show them
                    if result.response.content.startswith("[LLM ERROR]"):
                        event["error"] = result.response.content
                    await queue.put(event)

                    idx += 1

            # Build usage metrics
            from md_evals.metrics import build_usage_metrics

            # Temporarily enable metrics for the report
            config.output.include_usage_metrics = True
            usage_metrics = build_usage_metrics(results, config)

            # Compute summary
            total_passed = sum(1 for r in results if r.passed)
            total_duration = sum(r.response.duration_ms for r in results)

            # Serialize results for DB
            serialized_results = self._serialize_results(results)

            # Update DB
            await self._update_completed(
                eval_id=eval_id,
                results_data=serialized_results,
                usage_metrics=usage_metrics,
            )

            await queue.put({
                "type": "eval_completed",
                "eval_id": eval_id,
                "status": "completed",
                "total_passed": total_passed,
                "total_tests": len(results),
                "duration_ms": total_duration,
            })

        except asyncio.TimeoutError:
            logger.warning("Eval %s timed out", eval_id)
            await self._update_failed(eval_id, "timeout", "Eval exceeded time limit.")
            await queue.put({
                "type": "eval_timeout",
                "eval_id": eval_id,
                "completed": idx,
                "total": total_tests,
            })

        except Exception as exc:
            logger.exception("Eval %s failed: %s", eval_id, exc)
            await self._update_failed(eval_id, "failed", str(exc))
            await queue.put({
                "type": "eval_error",
                "eval_id": eval_id,
                "error": type(exc).__name__,
                "message": str(exc),
            })

        finally:
            # Clean up temp file
            if temp_skill_path and os.path.exists(temp_skill_path):
                try:
                    os.unlink(temp_skill_path)
                except OSError:
                    pass

            # Clean up env vars (safety net — keys are passed directly
            # via api_key param now, but clear just in case)
            self._clear_provider_env()

    # ---------- Helpers ----------

    async def _resolve_api_key(self, user_id: str, provider: str) -> str:
        """Resolve the API key for the given provider.

        Priority: session key (in-memory) > persistent key (DB).
        Session keys take precedence because the user explicitly chose
        to use a temporary key for this session.
        """
        # 1. Check session keys first (in-memory, higher priority)
        session_entry = await session_key_store.get_key(user_id, provider)
        if session_entry is not None:
            return session_entry.api_key

        # 2. Fall back to persistent keys in DB
        async with async_session_factory() as session:
            result = await session.execute(
                select(ProviderKey).where(
                    ProviderKey.user_id == user_id,
                    ProviderKey.provider == provider,
                )
            )
            row = result.scalar_one_or_none()

        if row is None:
            raise ValueError(
                f"No tenes una API key configurada para {provider}. "
                f"Agregala en Settings > Provider Keys."
            )

        master_key = normalize_master_key(settings.ENCRYPTION_KEY)
        user_key = derive_user_key(master_key, user_id)
        return decrypt_key(row.encrypted_api_key, user_key)

    @staticmethod
    def _set_provider_env(provider: str, api_key: str) -> None:
        """Set the environment variable that litellm expects for the provider.

        Keys are NEVER logged.
        """
        env_map: dict[str, str] = {
            "openai": "OPENAI_API_KEY",
            "anthropic": "ANTHROPIC_API_KEY",
            "google": "GOOGLE_API_KEY",
            "github-models": "GITHUB_TOKEN",
            "groq": "GROQ_API_KEY",
            "mistral": "MISTRAL_API_KEY",
            "cerebras": "CEREBRAS_API_KEY",
            "deepseek": "DEEPSEEK_API_KEY",
            "openrouter": "OPENROUTER_API_KEY",
        }
        env_var = env_map.get(provider, "OPENAI_API_KEY")
        os.environ[env_var] = api_key

    @staticmethod
    def _clear_provider_env() -> None:
        """Remove all provider env vars to avoid key leakage."""
        for var in (
            "OPENAI_API_KEY", "ANTHROPIC_API_KEY", "GOOGLE_API_KEY",
            "GITHUB_TOKEN", "GROQ_API_KEY", "MISTRAL_API_KEY",
            "CEREBRAS_API_KEY", "DEEPSEEK_API_KEY", "OPENROUTER_API_KEY",
        ):
            os.environ.pop(var, None)

    @staticmethod
    def _write_temp_skill(skill_content: str) -> str:
        """Write skill content to a named temp file and return its path."""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".md", delete=False, prefix="md_evals_skill_"
        ) as f:
            f.write(skill_content)
            return f.name

    @staticmethod
    def _prepare_treatments(
        config: EvalConfig,
        temp_skill_path: str,
    ) -> dict[str, Treatment]:
        """Build treatment dict, patching skill_path for non-CONTROL treatments."""
        treatments: dict[str, Treatment] = {}

        if not config.treatments:
            # Default: CONTROL + WITH_SKILL
            treatments["CONTROL"] = Treatment(skill_path=None)
            treatments["WITH_SKILL"] = Treatment(skill_path=temp_skill_path)
        else:
            for name, treatment in config.treatments.items():
                if treatment.skill_path is not None:
                    # Replace the original skill_path with our temp file
                    treatment.skill_path = temp_skill_path
                treatments[name] = treatment

            # Ensure CONTROL exists
            if "CONTROL" not in treatments:
                treatments["CONTROL"] = Treatment(skill_path=None)

        return treatments

    @staticmethod
    def _compute_hash(skill_content: str, eval_yaml: str, model: str) -> str:
        """SHA-256 hash for deduplication."""
        blob = f"{skill_content}\n---\n{eval_yaml}\n---\n{model}"
        return f"sha256:{hashlib.sha256(blob.encode()).hexdigest()}"

    @staticmethod
    def _serialize_results(results: list[Any]) -> dict[str, Any]:
        """Convert ExecutionResult list to JSON-serializable dict."""
        items = []
        for r in results:
            items.append({
                "treatment": r.treatment,
                "test": r.test,
                "passed": r.passed,
                "response_text": r.response.content,
                "duration_ms": r.response.duration_ms,
                "cost_metrics": {
                    "prompt_tokens": r.response.prompt_tokens,
                    "completion_tokens": r.response.completion_tokens_detail,
                    "total_tokens": r.response.total_tokens,
                },
                "evaluator_results": [
                    {
                        "evaluator_name": er.evaluator_name,
                        "passed": er.passed,
                        "score": er.score,
                        "reason": er.reason,
                    }
                    for er in r.evaluator_results
                ],
            })

        # Build summary
        total = len(results)
        passed = sum(1 for r in results if r.passed)

        # Per-treatment summary
        treatment_summary: dict[str, dict[str, Any]] = {}
        for r in results:
            if r.treatment not in treatment_summary:
                treatment_summary[r.treatment] = {"passed": 0, "total": 0}
            treatment_summary[r.treatment]["total"] += 1
            if r.passed:
                treatment_summary[r.treatment]["passed"] += 1

        for ts in treatment_summary.values():
            ts["pass_rate"] = ts["passed"] / ts["total"] if ts["total"] > 0 else 0.0

        return {
            "summary": {
                "total_tests": total,
                "total_passed": passed,
                "pass_rate": passed / total if total > 0 else 0.0,
                "duration_ms": sum(r.response.duration_ms for r in results),
                "treatments": treatment_summary,
            },
            "results": items,
        }

    async def _update_completed(
        self,
        eval_id: str,
        results_data: dict[str, Any],
        usage_metrics: dict[str, Any] | None,
    ) -> None:
        """Mark eval as completed in DB with results."""
        async with async_session_factory() as session:
            await session.execute(
                update(Evaluation)
                .where(Evaluation.id == eval_id)
                .values(
                    status="completed",
                    results=results_data,
                    cost_metrics=usage_metrics,
                    completed_at=datetime.now(timezone.utc),
                )
            )
            await session.commit()

    async def _update_failed(
        self,
        eval_id: str,
        status_val: str,
        error_message: str,
    ) -> None:
        """Mark eval as failed/timeout in DB."""
        async with async_session_factory() as session:
            await session.execute(
                update(Evaluation)
                .where(Evaluation.id == eval_id)
                .values(
                    status=status_val,
                    error_message=error_message,
                    completed_at=datetime.now(timezone.utc),
                )
            )
            await session.commit()


# Module-level singleton
eval_service = EvalService()
