"""Evaluation execution and retrieval routes."""

import json
import logging
import math
from collections.abc import AsyncGenerator
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sse_starlette.sse import EventSourceResponse

from app.middleware.auth import CurrentUser
from app.models import Evaluation, get_db
from app.models.schemas import (
    EvalDetailResponse,
    EvalHistoryItem,
    EvalHistoryResponse,
    EvalRunRequest,
    EvalRunResponse,
)
from app.services.eval_service import eval_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/eval", tags=["eval"])


# ---------- POST /api/eval/run ----------


@router.post("/run", response_model=EvalRunResponse, status_code=status.HTTP_202_ACCEPTED)
async def run_eval(
    body: EvalRunRequest,
    current_user: CurrentUser,
) -> EvalRunResponse:
    """Launch a new evaluation in the background.

    Returns 202 Accepted immediately with the eval_id. Connect to
    ``GET /api/eval/{eval_id}/stream`` for real-time SSE progress.
    """
    user_id = current_user["sub"]

    try:
        result = await eval_service.start_eval(
            user_id=user_id,
            name=body.name,
            skill_content=body.skill_content,
            eval_yaml=body.eval_yaml,
            model=body.model,
            provider=body.provider,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": "invalid_config", "message": str(exc)},
        ) from exc

    return EvalRunResponse(
        eval_id=result["eval_id"],
        status=result["status"],
        created_at=result["created_at"],
    )


# ---------- GET /api/eval/{eval_id}/stream ----------


@router.get("/{eval_id}/stream")
async def stream_eval(
    eval_id: str,
    current_user: CurrentUser,
) -> EventSourceResponse:
    """SSE stream of evaluation progress events.

    Events: ``eval_started``, ``test_started``, ``test_completed``,
    ``eval_completed``, ``eval_error``, ``eval_timeout``.
    """

    async def event_generator() -> AsyncGenerator[dict[str, str], None]:
        queue = eval_service.get_event_queue(eval_id)
        terminal_events = {"eval_completed", "eval_error", "eval_timeout"}
        while True:
            try:
                event = await queue.get()
                yield {
                    "event": event["type"],
                    "data": json.dumps(event),
                }
                if event["type"] in terminal_events:
                    break
            except Exception:
                logger.exception("SSE error for eval %s", eval_id)
                break

    return EventSourceResponse(event_generator())


# ---------- GET /api/eval/{eval_id} ----------


@router.get("/{eval_id}", response_model=EvalDetailResponse)
async def get_eval(
    eval_id: str,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
) -> EvalDetailResponse:
    """Get full results for a completed evaluation."""
    user_id = current_user["sub"]
    result = await db.execute(
        select(Evaluation).where(
            Evaluation.id == eval_id,
            Evaluation.user_id == user_id,
        )
    )
    evaluation = result.scalar_one_or_none()
    if not evaluation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": "not_found", "message": "Evaluation not found."},
        )

    return EvalDetailResponse(
        eval_id=str(evaluation.id),
        title=evaluation.title,
        status=evaluation.status,
        skill_content=evaluation.skill_content,
        eval_config=evaluation.eval_config,
        results=evaluation.results,
        cost_metrics=evaluation.cost_metrics,
        context_metrics=evaluation.context_metrics,
        error_message=evaluation.error_message,
        created_at=evaluation.created_at,
        completed_at=evaluation.completed_at,
    )


# ---------- GET /api/eval/history ----------


@router.get("/history", response_model=EvalHistoryResponse)
async def list_history(
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=20, ge=1, le=100),
    status_filter: str | None = Query(default=None, alias="status"),
    model: str | None = Query(default=None),
    date_from: datetime | None = Query(default=None),
    date_to: datetime | None = Query(default=None),
) -> EvalHistoryResponse:
    """List past evaluations with pagination and filters."""
    user_id = current_user["sub"]

    # Build base query
    base = select(Evaluation).where(Evaluation.user_id == user_id)

    if status_filter:
        base = base.where(Evaluation.status == status_filter)
    if date_from:
        base = base.where(Evaluation.created_at >= date_from)
    if date_to:
        base = base.where(Evaluation.created_at <= date_to)
    # Note: model filtering would require storing model in Evaluation or
    # querying inside eval_config JSONB. For now we filter in-memory if
    # the model column is not present — the Evaluation model stores config
    # as JSONB so we use a JSONB path query.
    if model:
        base = base.where(
            Evaluation.eval_config["defaults"]["model"].as_string() == model
        )

    # Count total
    count_q = select(func.count()).select_from(base.subquery())
    total_result = await db.execute(count_q)
    total = total_result.scalar() or 0

    # Paginate
    offset = (page - 1) * per_page
    query = (
        base.order_by(Evaluation.created_at.desc())
        .offset(offset)
        .limit(per_page)
    )
    result = await db.execute(query)
    rows = result.scalars().all()

    items = [
        EvalHistoryItem(
            eval_id=str(row.id),
            title=row.title,
            status=row.status,
            created_at=row.created_at,
            completed_at=row.completed_at,
        )
        for row in rows
    ]

    return EvalHistoryResponse(
        items=items,
        total=total,
        page=page,
        per_page=per_page,
        pages=max(1, math.ceil(total / per_page)),
    )
