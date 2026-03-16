# Design: md-evals-web

**Version**: 1.0  
**Status**: Draft  
**Última actualización**: 2026-03-16  
**Spec**: [spec.md](./spec.md)  
**Proposal**: [proposal.md](./proposal.md)

---

## 1. Estructura del Monorepo

```
md-evals/
├── md_evals/                        # Core library + CLI (INTOCABLE)
│   ├── __init__.py
│   ├── cli.py                       # CLI entrypoint
│   ├── config.py                    # ConfigLoader (YAML → EvalConfig)
│   ├── engine.py                    # ExecutionEngine (run_single, run_all)
│   ├── evaluator.py                 # EvaluatorEngine (regex, exact-match, llm-judge)
│   ├── llm.py                       # LLMAdapter (litellm wrapper)
│   ├── metrics.py                   # build_usage_metrics, CostMetrics, ContextMetrics
│   ├── models.py                    # Pydantic models (EvalConfig, ExecutionResult, etc.)
│   ├── provider_registry.py         # Global provider registry
│   ├── providers/
│   │   ├── __init__.py
│   │   └── github_models.py         # GitHub Models provider
│   ├── reporter.py                  # Reporter (terminal, JSON, markdown)
│   ├── linter.py                    # SKILL.md linter
│   └── utils.py                     # Utilities
├── tests/                           # Core tests (INTOCABLE)
├── apps/
│   ├── server/                      # FastAPI backend
│   │   ├── app/
│   │   │   ├── __init__.py
│   │   │   ├── main.py              # FastAPI app factory, lifespan, startup checks
│   │   │   ├── config.py            # Pydantic Settings (env vars)
│   │   │   ├── routes/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── auth.py          # GET /auth/login, GET /auth/callback
│   │   │   │   ├── eval.py          # POST /api/eval/run, GET /api/eval/{id}, etc.
│   │   │   │   ├── providers.py     # CRUD /api/providers
│   │   │   │   └── settings.py      # GET/PUT /api/settings
│   │   │   ├── services/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── eval_service.py  # Wraps md_evals engine for web execution
│   │   │   │   ├── crypto.py        # AES-256-GCM encrypt/decrypt, HKDF derivation
│   │   │   │   └── provider_validator.py  # Validates provider API keys
│   │   │   ├── models/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── db.py            # SQLAlchemy ORM models (User, Evaluation, etc.)
│   │   │   │   └── schemas.py       # Pydantic request/response schemas
│   │   │   ├── middleware/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── auth.py          # JWT verification dependency
│   │   │   │   └── cors.py          # CORS configuration
│   │   │   └── db.py                # AsyncSession factory, engine setup
│   │   ├── alembic/
│   │   │   ├── alembic.ini
│   │   │   ├── env.py
│   │   │   └── versions/            # Migration scripts
│   │   ├── Dockerfile               # Multi-stage build
│   │   ├── pyproject.toml           # Server deps (fastapi, sqlalchemy, etc.)
│   │   └── tests/
│   │       ├── conftest.py
│   │       ├── test_auth.py
│   │       ├── test_eval.py
│   │       ├── test_crypto.py
│   │       └── test_providers.py
│   └── web/                         # React SPA
│       ├── src/
│       │   ├── App.tsx              # Router + QueryClientProvider + AuthProvider
│       │   ├── main.tsx             # ReactDOM.createRoot entrypoint
│       │   ├── pages/
│       │   │   ├── Login.tsx        # OAuth login + PAT fallback
│       │   │   ├── AuthCallback.tsx # Processes /auth/callback redirect
│       │   │   ├── Dashboard.tsx    # Eval results dashboard
│       │   │   ├── EvalRun.tsx      # Upload + paste + run eval
│       │   │   ├── History.tsx      # Eval history list + compare
│       │   │   └── Settings.tsx     # Provider keys management
│       │   ├── components/
│       │   │   ├── layout/
│       │   │   │   ├── AppShell.tsx     # Sidebar + topbar + content
│       │   │   │   ├── Sidebar.tsx      # Navigation links
│       │   │   │   └── UserMenu.tsx     # Avatar + logout
│       │   │   ├── charts/
│       │   │   │   ├── PassRateChart.tsx       # Bar chart (treatment pass rates)
│       │   │   │   ├── TokenUsageChart.tsx     # Line chart (tokens per test)
│       │   │   │   ├── ContextGauge.tsx        # Radial gauge (utilization %)
│       │   │   │   └── CostBreakdown.tsx       # Stacked bar (prompt vs completion)
│       │   │   ├── eval/
│       │   │   │   ├── EvalForm.tsx            # Textareas + drag-drop zone
│       │   │   │   ├── EvalProgress.tsx        # SSE progress with test list
│       │   │   │   ├── ResultsTable.tsx        # Test case results table
│       │   │   │   └── SummaryCard.tsx         # Pass rate, duration, counts
│       │   │   └── settings/
│       │   │       ├── ProviderKeyForm.tsx     # Add key (select provider + input)
│       │   │       └── ProviderKeyList.tsx     # List keys (masked) + delete
│       │   ├── lib/
│       │   │   ├── api.ts           # Fetch wrapper (baseURL, auth header, error handling)
│       │   │   ├── auth.tsx         # AuthContext + useAuth hook (JWT + PAT)
│       │   │   ├── types.ts         # TypeScript types matching API schemas
│       │   │   └── queryClient.ts   # TanStack QueryClient config
│       │   └── index.css            # Tailwind CSS 4 imports
│       ├── public/
│       │   └── favicon.svg
│       ├── index.html
│       ├── vite.config.ts
│       ├── tailwind.config.ts
│       ├── tsconfig.json
│       └── package.json
├── docker-compose.yml               # api + db services
├── .github/
│   └── workflows/
│       └── deploy-pages.yml         # Build + deploy frontend to GH Pages
├── openspec/                        # SDD artifacts
├── pyproject.toml                   # Core package (SIN CAMBIOS)
└── README.md
```

---

## 2. Architecture Decision Records (ADRs)

### ADR-01: FastAPI importa md_evals directamente

**Contexto**: El backend necesita ejecutar evaluaciones usando la misma lógica que la CLI.

**Decisión**: FastAPI importa los módulos de `md_evals` directamente como librería Python. No usa subprocess, no wrappea la CLI, no duplica lógica.

**Imports que usa el backend**:

```python
# Parsing y configuración
from md_evals.models import EvalConfig, ExecutionResult, LLMResponse
from md_evals.config import ConfigLoader  # Solo para validación YAML

# Ejecución
from md_evals.engine import ExecutionEngine
from md_evals.llm import LLMAdapter, inject_skill, LLMError
from md_evals.evaluator import EvaluatorEngine

# Métricas
from md_evals.metrics import build_usage_metrics, CostMetrics, ContextMetrics
```

**Consecuencia**: El `pyproject.toml` del server incluye `md-evals` como dependencia local (`md-evals = {path = "../../", editable = true}`) o como paquete PyPI. En Docker, se instala desde el path del monorepo.

**Riesgo mitigado**: Si md_evals cambia su API interna, los tests del server lo detectan.

---

### ADR-02: JWT con PyJWT (HS256, 24h expiry)

**Contexto**: Necesitamos sesiones stateless sin infraestructura adicional (Redis).

**Decisión**: JWT firmado con HS256 usando `PyJWT`. Claims: `sub`, `github_user_id`, `login`, `avatar_url`, `exp`, `iat`. Expiración 24h. Sin refresh tokens en MVP.

**Librería**: `PyJWT==2.9+`

**Formato**:
```python
payload = {
    "sub": str(github_user.id),
    "github_user_id": github_user.id,
    "login": github_user.login,
    "avatar_url": github_user.avatar_url,
    "iat": int(time.time()),
    "exp": int(time.time()) + 86400,  # 24h
}
token = jwt.encode(payload, JWT_SECRET, algorithm="HS256")
```

**Frontend storage**: `localStorage` para persistir entre recargas. Se limpia en logout.

---

### ADR-03: SQLAlchemy 2.0 async + asyncpg

**Contexto**: FastAPI es async-first. Necesitamos un ORM async para PostgreSQL.

**Decisión**: SQLAlchemy 2.0 con `create_async_engine` + `asyncpg` driver. Migraciones con Alembic (modo async).

**Session management**:
```python
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

engine = create_async_engine(DATABASE_URL)
async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with async_session() as session:
        yield session
```

**Consecuencia**: Todas las queries usan `await session.execute()`. Los modelos SQLAlchemy usan `Mapped[]` type annotations (2.0 style).

---

### ADR-04: AES-256-GCM con cryptography lib

**Contexto**: Las API keys de providers se guardan en PostgreSQL y deben estar encriptadas at-rest.

**Decisión**: Esquema de encriptación:
1. **Master key**: env var `MD_EVALS_MASTER_KEY` (32 bytes hex = 256 bits)
2. **Per-user key**: derivado con `HKDF(SHA256, master_key, salt=user_id_bytes, info=b"md-evals-key-encryption")`
3. **Encryption**: `AESGCM(derived_key).encrypt(nonce, plaintext, None)`
4. **Nonce**: 12 bytes aleatorios por cada operación de encrypt
5. **Storage**: `nonce (12B) || ciphertext || tag (16B)` en columna BYTEA

**Librería**: `cryptography` (ya ampliamente usada en el ecosistema Python).

```python
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from cryptography.hazmat.primitives import hashes
import os

def derive_user_key(master_key: bytes, user_id: str) -> bytes:
    hkdf = HKDF(
        algorithm=hashes.SHA256(),
        length=32,
        salt=user_id.encode(),
        info=b"md-evals-key-encryption",
    )
    return hkdf.derive(master_key)

def encrypt_key(plaintext: str, user_key: bytes) -> bytes:
    nonce = os.urandom(12)
    aesgcm = AESGCM(user_key)
    ct = aesgcm.encrypt(nonce, plaintext.encode(), None)
    return nonce + ct  # nonce(12) || ciphertext || tag(16)

def decrypt_key(blob: bytes, user_key: bytes) -> str:
    nonce, ct = blob[:12], blob[12:]
    aesgcm = AESGCM(user_key)
    return aesgcm.decrypt(nonce, ct, None).decode()
```

---

### ADR-05: SSE con sse-starlette

**Contexto**: El frontend necesita recibir progreso de ejecución en tiempo real.

**Decisión**: Server-Sent Events (SSE) via `sse-starlette`. Unidireccional (server→client), más simple que WebSocket, compatible con TanStack Query.

**Librería**: `sse-starlette==2.1+`

**Endpoint**: `GET /api/eval/{id}/stream`

**Mecanismo interno**: El `eval_service` publica eventos en un `asyncio.Queue` por eval_id. El SSE endpoint consume de esa queue.

```python
from sse_starlette.sse import EventSourceResponse

@router.get("/api/eval/{eval_id}/stream")
async def stream_eval(eval_id: str, user=Depends(get_current_user)):
    async def event_generator():
        queue = eval_service.get_event_queue(eval_id)
        while True:
            event = await queue.get()
            yield {"event": event["type"], "data": json.dumps(event)}
            if event["type"] in ("eval_completed", "eval_error", "eval_timeout"):
                break
    return EventSourceResponse(event_generator())
```

---

### ADR-06: TanStack Query sin Zustand

**Contexto**: ¿Necesitamos Zustand para client state?

**Decisión**: **No**. TanStack Query maneja todo el server state (evals, providers, history). El auth state se gestiona con React Context (`AuthContext`). No hay suficiente client-only state en MVP para justificar otra librería.

**State map**:

| State | Dónde vive |
|-------|-----------|
| User/auth | `AuthContext` (React Context) |
| Evals, results | TanStack Query cache |
| Provider keys | TanStack Query cache |
| History | TanStack Query cache |
| Settings | TanStack Query cache |
| SSE events | Local state en `EvalProgress` component |
| Form inputs | Local state (`useState`) |

---

## 3. Flujos Clave

### 3.1 OAuth Login Flow

```
┌──────────┐     ┌──────────────┐     ┌──────────────┐
│ Frontend │     │   Backend    │     │    GitHub     │
│ (React)  │     │  (FastAPI)   │     │  OAuth App   │
└────┬─────┘     └──────┬───────┘     └──────┬───────┘
     │                  │                    │
     │ 1. Click "Login" │                    │
     │─────────────────▶│                    │
     │                  │                    │
     │ 2. GET /auth/login                    │
     │  ← 302 Redirect  │                    │
     │  Location: github│.com/login/oauth/   │
     │  authorize?      │                    │
     │  client_id=X     │                    │
     │  &redirect_uri=  │                    │
     │   /auth/callback │                    │
     │  &scope=read:user│                    │
     │  &state={ts}.    │                    │
     │   {hmac}         │                    │
     │◀─────────────────│                    │
     │                  │                    │
     │ 3. User authorizes on GitHub          │
     │──────────────────────────────────────▶│
     │                  │                    │
     │ 4. GitHub redirects to callback       │
     │  GET /auth/callback?code=C&state=S    │
     │──────────────────▶                    │
     │                  │                    │
     │                  │ 5. Validate state   │
     │                  │  (HMAC + expiry)   │
     │                  │                    │
     │                  │ 6. POST /login/     │
     │                  │  oauth/access_token │
     │                  │  {client_id,        │
     │                  │   client_secret,    │
     │                  │   code}             │
     │                  │───────────────────▶│
     │                  │                    │
     │                  │ 7. ← access_token  │
     │                  │◀───────────────────│
     │                  │                    │
     │                  │ 8. GET /user        │
     │                  │  Authorization:     │
     │                  │  Bearer {token}     │
     │                  │───────────────────▶│
     │                  │                    │
     │                  │ 9. ← user profile   │
     │                  │◀───────────────────│
     │                  │                    │
     │                  │ 10. Upsert user     │
     │                  │  in PostgreSQL      │
     │                  │                    │
     │                  │ 11. Encrypt &       │
     │                  │  store GitHub token │
     │                  │                    │
     │                  │ 12. Generate JWT    │
     │                  │                    │
     │ 13. Redirect to  │                    │
     │  frontend with   │                    │
     │  JWT in query    │                    │
     │  /#/auth/callback│                    │
     │  ?token={jwt}    │                    │
     │◀─────────────────│                    │
     │                  │                    │
     │ 14. Store JWT    │                    │
     │  in localStorage │                    │
     │  + AuthContext   │                    │
     │                  │                    │
     │ 15. Redirect     │                    │
     │  to /#/dashboard │                    │
```

**State parameter**: `{base36_timestamp}.{hmac_sha256_hex}` firmado con `STATE_SECRET`. Válido por 5 minutos.

**Redirect URI**: El backend redirige al frontend con JWT como query param de la URL del SPA:
`https://{username}.github.io/md-evals/#/auth/callback?token={jwt}`

---

### 3.2 Eval Execution + SSE Streaming Flow

```
┌──────────┐     ┌──────────────┐     ┌──────────────┐     ┌──────────┐
│ Frontend │     │   Backend    │     │  md_evals    │     │ LLM API  │
│ (React)  │     │  (FastAPI)   │     │  (engine)    │     │ Provider │
└────┬─────┘     └──────┬───────┘     └──────┬───────┘     └────┬─────┘
     │                  │                    │                  │
     │ 1. POST /api/    │                    │                  │
     │  eval/run        │                    │                  │
     │  {skill_content, │                    │                  │
     │   eval_yaml,     │                    │                  │
     │   name}          │                    │                  │
     │─────────────────▶│                    │                  │
     │                  │                    │                  │
     │                  │ 2. Parse YAML      │                  │
     │                  │  → EvalConfig      │                  │
     │                  │                    │                  │
     │                  │ 3. Create eval     │                  │
     │                  │  in DB (pending)   │                  │
     │                  │                    │                  │
     │ 4. ← 202        │                    │                  │
     │  {eval_id,       │                    │                  │
     │   status:running}│                    │                  │
     │◀─────────────────│                    │                  │
     │                  │                    │                  │
     │ 5. GET /api/     │ ┌──── background ──────────────┐     │
     │  eval/{id}/stream│ │                              │     │
     │─────────────────▶│ │ 6. Build LLMAdapter          │     │
     │                  │ │  (model, provider, api_key)  │     │
     │ ← SSE stream     │ │                              │     │
     │                  │ │ 7. Build EvaluatorEngine     │     │
     │                  │ │                              │     │
     │                  │ │ 8. Build ExecutionEngine     │     │
     │                  │ │  (config, adapter, evaluator)│     │
     │                  │ │                              │     │
     │ ← eval_started   │ │ 9. Emit eval_started        │     │
     │  {total_tests}   │ │                              │     │
     │◀═════════════════│ │                              │     │
     │                  │ │ 10. For each (treatment,test):     │
     │ ← test_started   │ │  a. Emit test_started       │     │
     │  {test_index,    │ │                              │     │
     │   test_name}     │ │  b. engine.run_single()      │     │
     │◀═════════════════│ │     ├─ inject_skill()        │     │
     │                  │ │     ├─ adapter.complete() ───────▶│
     │                  │ │     │                        │  ←──│
     │                  │ │     ├─ evaluator.evaluate()  │     │
     │                  │ │     └─ → ExecutionResult     │     │
     │                  │ │                              │     │
     │ ← test_completed │ │  c. Emit test_completed     │     │
     │  {passed, score, │ │     + save result to DB      │     │
     │   duration_ms}   │ │                              │     │
     │◀═════════════════│ │                              │     │
     │                  │ │ ... repeat for all tests ... │     │
     │                  │ │                              │     │
     │                  │ │ 11. build_usage_metrics()    │     │
     │                  │ │                              │     │
     │                  │ │ 12. Update eval status       │     │
     │                  │ │  → completed                 │     │
     │                  │ │                              │     │
     │ ← eval_completed │ │ 13. Emit eval_completed     │     │
     │  {total_passed,  │ │                              │     │
     │   total_tests,   │ └──────────────────────────────┘     │
     │   duration_ms}   │                    │                  │
     │◀═════════════════│                    │                  │
     │                  │                    │                  │
     │ SSE closes       │                    │                  │
```

**Background task mechanism**: `asyncio.create_task()` lanzado en el endpoint POST handler. El task publica eventos en un `asyncio.Queue` keyed por eval_id.

**Skill injection para web**: Dado que el SKILL.md se envía como texto (no como archivo), el backend crea un archivo temporal con el contenido del skill, o bien parchea `inject_skill` pasando el contenido directamente como `system_prompt` sin leer de disco:

```python
# En eval_service.py — inyección sin archivo
system_prompt = f"""You are a helpful AI assistant.

Below is a skill that provides guidelines for your responses:
---
{skill_content}
---

Follow the skill guidelines above when responding to the user."""

# Luego se llama adapter.complete(prompt=task_prompt, system_prompt=system_prompt)
```

Esto **no modifica** `md_evals/llm.py`. El backend llama `LLMAdapter.complete()` directamente con `system_prompt`, bypaseando `inject_skill()` que espera un path de archivo.

---

### 3.3 Provider Key Validation + Encryption Flow

```
┌──────────┐     ┌──────────────┐     ┌──────────────┐     ┌──────────┐
│ Frontend │     │   Backend    │     │   crypto     │     │ Provider │
│ Settings │     │  /providers  │     │  service     │     │   API    │
└────┬─────┘     └──────┬───────┘     └──────┬───────┘     └────┬─────┘
     │                  │                    │                  │
     │ 1. POST /api/    │                    │                  │
     │  providers       │                    │                  │
     │  {provider:      │                    │                  │
     │   "openai",      │                    │                  │
     │   key: "sk-..."}│                    │                  │
     │─────────────────▶│                    │                  │
     │                  │                    │                  │
     │                  │ 2. Validate key    │                  │
     │                  │  against provider  │                  │
     │                  │──────────────────────────────────────▶│
     │                  │                    │                  │
     │                  │ 3. Provider returns│200 OK            │
     │                  │◀─────────────────────────────────────│
     │                  │                    │                  │
     │                  │ 4. Derive user key │                  │
     │                  │  HKDF(master,      │                  │
     │                  │       user_id)     │                  │
     │                  │───────────────────▶│                  │
     │                  │                    │                  │
     │                  │ 5. Encrypt API key │                  │
     │                  │  AES-256-GCM       │                  │
     │                  │  nonce || ct || tag│                  │
     │                  │◀───────────────────│                  │
     │                  │                    │                  │
     │                  │ 6. Extract hint    │                  │
     │                  │  "sk-...{last4}"   │                  │
     │                  │                    │                  │
     │                  │ 7. Save to DB      │                  │
     │                  │  (key_enc, hint,   │                  │
     │                  │   validated_at)    │                  │
     │                  │                    │                  │
     │ 8. ← 201        │                    │                  │
     │  {provider,      │                    │                  │
     │   key_hint,      │                    │                  │
     │   validated_at}  │                    │                  │
     │◀─────────────────│                    │                  │
```

**Hint extraction**: 
```python
def extract_key_hint(key: str) -> str:
    """Extract displayable hint: prefix + last 4 chars."""
    if len(key) <= 8:
        return "****"
    prefix = key[:3]  # e.g. "sk-"
    suffix = key[-4:]
    return f"{prefix}...{suffix}"
```

---

## 4. API Contracts

### 4.1 Auth Endpoints

#### `GET /auth/login`

Redirige al usuario a GitHub OAuth.

**Response**: `302 Redirect`
```
Location: https://github.com/login/oauth/authorize
  ?client_id={GITHUB_CLIENT_ID}
  &redirect_uri={BACKEND_URL}/auth/callback
  &scope=read:user
  &state={base36_ts}.{hmac_hex}
```

---

#### `GET /auth/callback?code={code}&state={state}`

Procesa el callback de GitHub OAuth.

**Success response**: `302 Redirect`
```
Location: {FRONTEND_URL}/#/auth/callback?token={jwt}
```

**Error response**: `302 Redirect`
```
Location: {FRONTEND_URL}/#/login?error={error_code}
```

Error codes: `invalid_state`, `exchange_failed`, `access_denied`

---

### 4.2 Eval Endpoints

#### `POST /api/eval/run`

Lanza una nueva evaluación.

**Request**:
```json
{
  "name": "My Eval",
  "skill_content": "# SKILL.md\n...",
  "eval_yaml": "name: test\ntests:\n  - name: t1\n    prompt: ...",
  "model": "gpt-4o",
  "provider": "github-models"
}
```

**Response `202 Accepted`**:
```json
{
  "eval_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "running",
  "created_at": "2026-03-16T10:00:00Z"
}
```

**Errors**:
- `400 { "error": "invalid_yaml", "message": "..." }`
- `400 { "error": "missing_provider_key", "message": "..." }`
- `429 { "error": "rate_limited", "message": "...", "retry_after": 1800 }`

---

#### `GET /api/eval/{eval_id}`

Obtiene resultados de una eval completada.

**Response `200 OK`**:
```json
{
  "eval_id": "550e8400-...",
  "name": "My Eval",
  "status": "completed",
  "config": { /* EvalConfig serializado */ },
  "created_at": "2026-03-16T10:00:00Z",
  "completed_at": "2026-03-16T10:02:30Z",
  "summary": {
    "total_tests": 10,
    "total_passed": 8,
    "pass_rate": 0.8,
    "duration_ms": 150000,
    "treatments": {
      "CONTROL": { "passed": 6, "total": 10, "pass_rate": 0.6 },
      "WITH_SKILL": { "passed": 8, "total": 10, "pass_rate": 0.8 }
    }
  },
  "results": [
    {
      "id": "...",
      "treatment": "CONTROL",
      "test": "test_greeting",
      "model": "gpt-4o",
      "passed": true,
      "score": 1.0,
      "response_text": "Hello! How can I help?",
      "duration_ms": 1200,
      "cost_metrics": {
        "prompt_tokens": 150,
        "completion_tokens": 25,
        "total_tokens": 175,
        "estimated_cost_usd": 0.0012,
        "data_quality": "measured"
      },
      "context_metrics": {
        "prompt_tokens_used": 150,
        "context_window_max_tokens": 128000,
        "context_utilization_pct": 0.12,
        "truncation_risk": "low",
        "data_quality": "measured"
      },
      "evaluator_results": [
        {
          "evaluator_name": "greeting_check",
          "passed": true,
          "score": 1.0,
          "reason": null
        }
      ]
    }
  ],
  "usage_metrics": { /* build_usage_metrics() output */ }
}
```

---

#### `GET /api/eval/{eval_id}/stream`

SSE stream de progreso.

**Response**: `200 OK` con `Content-Type: text/event-stream`

```
event: eval_started
data: {"eval_id":"550e8400-...","total_tests":5,"model":"gpt-4o","provider":"github-models"}

event: test_started
data: {"test_index":0,"test_name":"test_greeting","treatment":"CONTROL"}

event: test_completed
data: {"test_index":0,"test_name":"test_greeting","treatment":"CONTROL","passed":true,"score":1.0,"duration_ms":1200}

event: eval_completed
data: {"eval_id":"550e8400-...","status":"completed","total_passed":4,"total_tests":5,"duration_ms":15000}
```

---

#### `GET /api/eval/history`

Lista evals pasadas con filtros.

**Query params**: `page` (default 1), `per_page` (default 20, max 100), `date_from`, `date_to` (ISO 8601), `model`, `status`

**Response `200 OK`**:
```json
{
  "items": [
    {
      "eval_id": "...",
      "name": "My Eval",
      "status": "completed",
      "model": "gpt-4o",
      "pass_rate": 0.8,
      "total_tests": 10,
      "total_passed": 8,
      "duration_ms": 150000,
      "created_at": "2026-03-16T10:00:00Z",
      "config_hash": "sha256:abc123..."
    }
  ],
  "total": 50,
  "page": 1,
  "per_page": 20,
  "pages": 3
}
```

---

### 4.3 Provider Endpoints

#### `GET /api/providers`

Lista provider keys (masked).

**Response `200 OK`**:
```json
[
  {
    "provider": "openai",
    "key_hint": "sk-...a3Fx",
    "validated_at": "2026-03-16T09:00:00Z"
  },
  {
    "provider": "github-models",
    "key_hint": null,
    "validated_at": null,
    "status": "available",
    "note": "Usa tu token OAuth"
  }
]
```

---

#### `POST /api/providers`

Agrega una provider key.

**Request**:
```json
{
  "provider": "openai",
  "key": "sk-proj-abc123def456..."
}
```

**Response `201 Created`**:
```json
{
  "provider": "openai",
  "key_hint": "sk-...6...",
  "validated_at": "2026-03-16T10:05:00Z"
}
```

**Errors**:
- `400 { "error": "invalid_key", "message": "La API key de OpenAI es inválida o fue revocada." }`
- `400 { "error": "validation_timeout", "message": "No se pudo validar la key. El provider no respondió." }`

---

#### `DELETE /api/providers/{provider}`

Elimina una provider key.

**Response `204 No Content`**

**Error**: `404 { "error": "key_not_found", "message": "No tenés una key configurada para {provider}." }`

---

#### `POST /api/providers/validate`

Valida una key sin guardar (dry-run).

**Request**:
```json
{
  "provider": "anthropic",
  "key": "sk-ant-..."
}
```

**Response `200 OK`**:
```json
{
  "valid": true,
  "provider": "anthropic"
}
```

---

### 4.4 Settings Endpoints

#### `GET /api/settings`

**Response `200 OK`**:
```json
{
  "default_model": "gpt-4o",
  "default_provider": "github-models",
  "eval_timeout_minutes": 10,
  "max_concurrent_evals": 3
}
```

#### `PUT /api/settings`

**Request**: partial update (solo campos a cambiar)
```json
{
  "default_model": "gpt-4o-mini",
  "eval_timeout_minutes": 15
}
```

**Response `200 OK`**: settings actualizados completos.

---

### 4.5 Health Endpoint

#### `GET /health`

**Response `200 OK`**:
```json
{
  "status": "ok",
  "version": "0.1.0",
  "db": "connected"
}
```

---

## 5. Database Schema

### Entity-Relationship Diagram

```
┌────────────────────┐       ┌────────────────────────┐
│      users         │       │    provider_keys        │
├────────────────────┤       ├────────────────────────┤
│ id          UUID PK│──┐    │ id          UUID PK    │
│ github_id   BIGINT │  │    │ user_id     UUID FK ───│──┐
│  (UNIQUE)          │  │    │ provider    TEXT        │  │
│ github_login TEXT   │  │    │ key_enc     BYTEA      │  │
│ github_token_enc   │  │    │ key_hint    TEXT        │  │
│  BYTEA             │  │    │ validated_at TSTZ      │  │
│ avatar_url   TEXT  │  │    │ created_at   TSTZ      │  │
│ created_at   TSTZ  │  │    └────────────────────────┘  │
│ updated_at   TSTZ  │  │                                │
└────────────────────┘  │    ┌────────────────────────┐  │
                        │    │    evaluations          │  │
                        │    ├────────────────────────┤  │
                        ├───▶│ id          UUID PK    │  │
                        │    │ user_id     UUID FK ───│──┘
                        │    │ name        TEXT        │
                        │    │ skill_content TEXT      │
                        │    │ eval_yaml   TEXT        │
                        │    │ config      JSONB       │
                        │    │ config_hash TEXT        │
                        │    │ model       TEXT        │
                        │    │ provider    TEXT        │
                        │    │ status      TEXT        │
                        │    │ error_message TEXT      │
                        │    │ created_at   TSTZ      │
                        │    │ completed_at TSTZ      │
                        │    └──────────┬─────────────┘
                        │               │
                        │    ┌──────────▼─────────────┐
                        │    │    eval_results         │
                        │    ├────────────────────────┤
                        │    │ id          UUID PK    │
                        │    │ evaluation_id UUID FK──│─▶ evaluations.id
                        │    │ treatment    TEXT       │
                        │    │ test         TEXT       │
                        │    │ model        TEXT       │
                        │    │ passed       BOOLEAN    │
                        │    │ score        FLOAT      │
                        │    │ response_text TEXT      │
                        │    │ cost_metrics  JSONB     │
                        │    │ context_metrics JSONB   │
                        │    │ evaluator_results JSONB │
                        │    │ duration_ms  INTEGER    │
                        │    │ created_at   TSTZ      │
                        │    └────────────────────────┘
                        │
                        │    ┌────────────────────────┐
                        │    │   user_settings         │
                        │    ├────────────────────────┤
                        └───▶│ id          UUID PK    │
                             │ user_id     UUID FK    │
                             │  (UNIQUE)              │
                             │ default_model TEXT     │
                             │ default_provider TEXT  │
                             │ eval_timeout_min INT   │
                             │ max_concurrent  INT    │
                             │ updated_at   TSTZ      │
                             └────────────────────────┘
```

### SQL DDL

```sql
-- Users (GitHub OAuth)
CREATE TABLE users (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    github_id       BIGINT UNIQUE NOT NULL,
    github_login    TEXT NOT NULL,
    github_token_enc BYTEA,
    avatar_url      TEXT,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_users_github_id ON users(github_id);

-- Provider API Keys (encrypted)
CREATE TABLE provider_keys (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id         UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    provider        TEXT NOT NULL,
    key_enc         BYTEA NOT NULL,
    key_hint        TEXT NOT NULL,
    validated_at    TIMESTAMPTZ,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE(user_id, provider)
);

CREATE INDEX idx_provider_keys_user ON provider_keys(user_id);

-- Evaluations
CREATE TABLE evaluations (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id         UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    name            TEXT NOT NULL,
    skill_content   TEXT NOT NULL,
    eval_yaml       TEXT NOT NULL,
    config          JSONB,
    config_hash     TEXT,
    model           TEXT NOT NULL,
    provider        TEXT NOT NULL,
    status          TEXT NOT NULL DEFAULT 'pending'
                    CHECK (status IN ('pending', 'running', 'completed', 'failed', 'timeout')),
    error_message   TEXT,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    completed_at    TIMESTAMPTZ
);

CREATE INDEX idx_evaluations_user ON evaluations(user_id);
CREATE INDEX idx_evaluations_status ON evaluations(status);
CREATE INDEX idx_evaluations_created ON evaluations(created_at DESC);
CREATE INDEX idx_evaluations_config_hash ON evaluations(config_hash);

-- Eval Results (one row per treatment × test)
CREATE TABLE eval_results (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    evaluation_id   UUID NOT NULL REFERENCES evaluations(id) ON DELETE CASCADE,
    treatment       TEXT NOT NULL,
    test            TEXT NOT NULL,
    model           TEXT NOT NULL,
    passed          BOOLEAN NOT NULL,
    score           FLOAT NOT NULL DEFAULT 0.0,
    response_text   TEXT,
    cost_metrics    JSONB,
    context_metrics JSONB,
    evaluator_results JSONB,
    duration_ms     INTEGER NOT NULL DEFAULT 0,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_eval_results_evaluation ON eval_results(evaluation_id);

-- User Settings
CREATE TABLE user_settings (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id         UUID UNIQUE NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    default_model   TEXT NOT NULL DEFAULT 'gpt-4o',
    default_provider TEXT NOT NULL DEFAULT 'github-models',
    eval_timeout_min INTEGER NOT NULL DEFAULT 10,
    max_concurrent  INTEGER NOT NULL DEFAULT 3,
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);
```

### JSONB Schemas

**`evaluations.config`**: Serialización de `EvalConfig.model_dump(mode="json")` — contiene toda la configuración usada para la eval.

**`eval_results.cost_metrics`**:
```json
{
  "prompt_tokens": 150,
  "completion_tokens": 25,
  "total_tokens": 175,
  "estimated_cost_usd": 0.0012,
  "latency_ms": 1200,
  "data_quality": "measured"
}
```

**`eval_results.context_metrics`**:
```json
{
  "prompt_tokens_used": 150,
  "context_window_max_tokens": 128000,
  "context_utilization_pct": 0.12,
  "headroom_tokens": 127850,
  "safe_headroom_tokens": 125802,
  "max_tokens_request": 2048,
  "overflow": false,
  "overflow_tokens": 0,
  "truncation_risk": "low",
  "data_quality": "measured"
}
```

**`eval_results.evaluator_results`**:
```json
[
  {
    "evaluator_name": "greeting_check",
    "passed": true,
    "score": 1.0,
    "reason": null,
    "details": null
  }
]
```

---

## 6. Frontend Routing

### HashRouter Configuration

El frontend usa `HashRouter` de `react-router-dom` porque GitHub Pages no soporta client-side routing con HTML5 History API (returns 404 en refresh).

```tsx
// App.tsx
import { HashRouter, Routes, Route, Navigate } from "react-router-dom";
import { QueryClientProvider } from "@tanstack/react-query";
import { AuthProvider } from "./lib/auth";
import { queryClient } from "./lib/queryClient";

import Login from "./pages/Login";
import AuthCallback from "./pages/AuthCallback";
import Dashboard from "./pages/Dashboard";
import EvalRun from "./pages/EvalRun";
import History from "./pages/History";
import Settings from "./pages/Settings";
import AppShell from "./components/layout/AppShell";

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <AuthProvider>
        <HashRouter>
          <Routes>
            {/* Public routes */}
            <Route path="/login" element={<Login />} />
            <Route path="/auth/callback" element={<AuthCallback />} />

            {/* Protected routes (wrapped in AppShell) */}
            <Route element={<AppShell />}>
              <Route path="/dashboard" element={<Dashboard />} />
              <Route path="/eval/new" element={<EvalRun />} />
              <Route path="/eval/:id" element={<Dashboard />} />
              <Route path="/history" element={<History />} />
              <Route path="/settings" element={<Settings />} />
            </Route>

            {/* Redirect root to dashboard or login */}
            <Route path="/" element={<Navigate to="/dashboard" replace />} />
            <Route path="*" element={<Navigate to="/dashboard" replace />} />
          </Routes>
        </HashRouter>
      </AuthProvider>
    </QueryClientProvider>
  );
}
```

### Route Map

| Hash Route | Page Component | Auth Required | Purpose |
|------------|---------------|---------------|---------|
| `/#/login` | `Login` | No | OAuth login + PAT fallback |
| `/#/auth/callback` | `AuthCallback` | No | Process OAuth redirect, store JWT |
| `/#/dashboard` | `Dashboard` | Yes | Default landing, latest eval results |
| `/#/eval/new` | `EvalRun` | Yes | Upload + paste + run eval |
| `/#/eval/:id` | `Dashboard` | Yes | View specific eval results |
| `/#/history` | `History` | Yes | List past evals, compare |
| `/#/settings` | `Settings` | Yes | Provider keys, defaults |

### Auth Guard

```tsx
// In AppShell.tsx
function AppShell() {
  const { user, isLoading } = useAuth();

  if (isLoading) return <LoadingSpinner />;
  if (!user) return <Navigate to="/login" replace />;

  return (
    <div className="flex h-screen">
      <Sidebar />
      <main className="flex-1 overflow-auto p-6">
        <Outlet />
      </main>
    </div>
  );
}
```

---

## 7. Integración md_evals

### El EvalService como adapter

El `eval_service.py` es el puente entre el mundo HTTP y el engine de md_evals. Su responsabilidad:

1. **Parsear YAML** → `EvalConfig` (usando Pydantic directamente, no `ConfigLoader` que espera un archivo)
2. **Resolver API keys** → desencriptar la key del provider desde DB
3. **Construir LLMAdapter** → con model, provider, y api_key
4. **Construir EvaluatorEngine** → con otro LLMAdapter para llm-judge (si hay)
5. **Construir ExecutionEngine** → con config, adapter, evaluator
6. **Ejecutar** → `engine.run_all()` o iterando `engine.run_single()` para granularidad SSE
7. **Mapear resultados** → de `ExecutionResult` a modelos DB
8. **Calcular métricas** → `build_usage_metrics(results, config)`

### Flujo de datos

```python
# eval_service.py (simplified)

class EvalService:
    def __init__(self, db: AsyncSession, crypto: CryptoService):
        self.db = db
        self.crypto = crypto
        self._event_queues: dict[str, asyncio.Queue] = {}

    async def run_eval(
        self,
        user_id: str,
        skill_content: str,
        eval_yaml: str,
        name: str,
    ) -> str:
        """Launch eval in background, return eval_id."""

        # 1. Parse YAML into EvalConfig
        import yaml
        raw = yaml.safe_load(eval_yaml)
        config = EvalConfig(**raw)

        # 2. Resolve API key for the target provider
        model = config.defaults.model
        provider = config.defaults.provider
        api_key = await self._resolve_api_key(user_id, provider)

        # 3. Create DB record
        eval_id = str(uuid4())
        evaluation = Evaluation(
            id=eval_id, user_id=user_id, name=name,
            skill_content=skill_content, eval_yaml=eval_yaml,
            config=config.model_dump(mode="json"),
            config_hash=self._compute_hash(skill_content, eval_yaml, model),
            model=model, provider=provider, status="running",
        )
        self.db.add(evaluation)
        await self.db.commit()

        # 4. Create event queue for SSE
        self._event_queues[eval_id] = asyncio.Queue()

        # 5. Launch background task
        asyncio.create_task(self._execute(eval_id, config, skill_content, api_key))

        return eval_id

    async def _execute(
        self,
        eval_id: str,
        config: EvalConfig,
        skill_content: str,
        api_key: str,
    ):
        queue = self._event_queues[eval_id]
        try:
            # Build adapter
            adapter = LLMAdapter(
                model=config.defaults.model,
                provider=config.defaults.provider,
                defaults=config.defaults,
            )
            # Set API key via litellm env or api_key param
            import os
            os.environ["OPENAI_API_KEY"] = api_key  # or provider-specific

            evaluator = EvaluatorEngine(llm_adapter=adapter)
            engine = ExecutionEngine(config, adapter, evaluator)

            # Emit started
            treatments = list(config.treatments.keys())
            all_tasks = config.tests
            total = len(treatments) * len(all_tasks)
            await queue.put({
                "type": "eval_started",
                "eval_id": eval_id,
                "total_tests": total,
                "model": config.defaults.model,
                "provider": config.defaults.provider,
            })

            # Run each combination individually for SSE granularity
            results = []
            idx = 0
            for t_name in treatments:
                treatment = config.treatments.get(t_name, Treatment())
                for task in all_tasks:
                    await queue.put({
                        "type": "test_started",
                        "test_index": idx,
                        "test_name": task.name,
                        "treatment": t_name,
                    })

                    # For web: inject skill as system_prompt directly
                    # instead of using file-based inject_skill
                    result = await engine.run_single(treatment, task, t_name)
                    results.append(result)

                    await queue.put({
                        "type": "test_completed",
                        "test_index": idx,
                        "test_name": task.name,
                        "treatment": t_name,
                        "passed": result.passed,
                        "score": max(
                            (r.score for r in result.evaluator_results), default=0.0
                        ),
                        "duration_ms": result.response.duration_ms,
                    })

                    # Save individual result to DB
                    await self._save_result(eval_id, result)
                    idx += 1

            # Build usage metrics
            usage = build_usage_metrics(results, config)

            # Update evaluation status
            await self._update_status(eval_id, "completed", usage)

            total_passed = sum(1 for r in results if r.passed)
            await queue.put({
                "type": "eval_completed",
                "eval_id": eval_id,
                "status": "completed",
                "total_passed": total_passed,
                "total_tests": len(results),
                "duration_ms": sum(r.response.duration_ms for r in results),
            })

        except Exception as e:
            await self._update_status(eval_id, "failed", error=str(e))
            await queue.put({
                "type": "eval_error",
                "eval_id": eval_id,
                "error": type(e).__name__,
                "message": str(e),
            })

    def get_event_queue(self, eval_id: str) -> asyncio.Queue:
        return self._event_queues.get(eval_id, asyncio.Queue())
```

### Skill content injection sin archivo

La key insight: `engine.run_single()` calls `inject_skill(prompt, treatment.skill_path)`. Para la web, el `skill_path` es `None` (CONTROL) o un path temporal.

**Estrategia**: Crear un `NamedTemporaryFile` con el skill content, y setear `treatment.skill_path` a ese path temporal:

```python
import tempfile

# For treatments that need skill injection
with tempfile.NamedTemporaryFile(
    mode="w", suffix=".md", delete=False
) as f:
    f.write(skill_content)
    temp_skill_path = f.name

# Set skill_path on the treatment
for t_name, treatment in config.treatments.items():
    if treatment.skill_path is not None:
        treatment.skill_path = temp_skill_path

# After execution, clean up temp file
os.unlink(temp_skill_path)
```

Esto permite usar `ExecutionEngine.run_single()` sin modificar `md_evals/llm.py`.

### API Key resolution

```python
async def _resolve_api_key(self, user_id: str, provider: str) -> str:
    """Resolve API key for a provider.

    Priority:
    1. github-models → use user's GitHub OAuth token (decrypt from users table)
    2. Other providers → decrypt from provider_keys table
    """
    if provider == "github-models":
        user = await self._get_user(user_id)
        return self.crypto.decrypt(user.github_token_enc, user_id)

    key_row = await self._get_provider_key(user_id, provider)
    if not key_row:
        raise ValueError(
            f"No tenés una API key configurada para {provider}. "
            f"Agregala en Settings > Provider Keys."
        )
    return self.crypto.decrypt(key_row.key_enc, user_id)
```

---

## 8. Configuración y Environment Variables

### Backend (apps/server/app/config.py)

```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Auth
    GITHUB_CLIENT_ID: str
    GITHUB_CLIENT_SECRET: str
    JWT_SECRET: str
    STATE_SECRET: str

    # Encryption
    MD_EVALS_MASTER_KEY: str  # 64-char hex string (32 bytes)

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://user:pass@localhost:5432/md_evals"

    # CORS
    CORS_ORIGINS: str = "http://localhost:5173"  # Comma-separated

    # App
    FRONTEND_URL: str = "http://localhost:5173"
    EVAL_TIMEOUT_MINUTES: int = 10
    RATE_LIMIT_EVALS_PER_HOUR: int = 10

    class Config:
        env_file = ".env"
        case_sensitive = True
```

### Startup validation

El servidor DEBE fallar en startup si cualquier variable requerida no está seteada:

```python
# In main.py lifespan
@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = Settings()  # Raises ValidationError if missing

    # Validate master key format
    try:
        master_key_bytes = bytes.fromhex(settings.MD_EVALS_MASTER_KEY)
        assert len(master_key_bytes) == 32
    except (ValueError, AssertionError):
        raise SystemExit(
            "MD_EVALS_MASTER_KEY must be a 64-character hex string (32 bytes). "
            "Generate one with: openssl rand -hex 32"
        )

    # Test DB connection
    # Run Alembic migrations
    yield
```

---

## 9. docker-compose.yml

```yaml
version: "3.9"

services:
  api:
    build:
      context: .
      dockerfile: apps/server/Dockerfile
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql+asyncpg://md_evals:md_evals@db:5432/md_evals
      - GITHUB_CLIENT_ID=${GITHUB_CLIENT_ID}
      - GITHUB_CLIENT_SECRET=${GITHUB_CLIENT_SECRET}
      - JWT_SECRET=${JWT_SECRET}
      - STATE_SECRET=${STATE_SECRET}
      - MD_EVALS_MASTER_KEY=${MD_EVALS_MASTER_KEY}
      - CORS_ORIGINS=${CORS_ORIGINS}
      - FRONTEND_URL=${FRONTEND_URL}
    depends_on:
      db:
        condition: service_healthy
    restart: unless-stopped

  db:
    image: postgres:16-alpine
    environment:
      POSTGRES_DB: md_evals
      POSTGRES_USER: md_evals
      POSTGRES_PASSWORD: md_evals
    volumes:
      - pgdata:/var/lib/postgresql/data
    ports:
      - "5432:5432"
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U md_evals"]
      interval: 5s
      timeout: 5s
      retries: 5

volumes:
  pgdata:
```

---

## 10. Dockerfile (Backend Multi-stage)

```dockerfile
# Stage 1: Builder
FROM python:3.12-slim AS builder

WORKDIR /build

# Install build deps
RUN pip install --no-cache-dir uv

# Copy core package first (for md_evals dependency)
COPY pyproject.toml ./pyproject.toml
COPY md_evals/ ./md_evals/

# Copy server package
COPY apps/server/pyproject.toml ./apps/server/pyproject.toml

# Install dependencies
RUN cd apps/server && uv pip install --system -e "../../" && uv pip install --system -e "."

# Copy server code
COPY apps/server/ ./apps/server/

# Stage 2: Runtime
FROM python:3.12-slim AS runtime

# Create non-root user
RUN groupadd -r appuser && useradd -r -g appuser -d /app -s /sbin/nologin appuser

WORKDIR /app

# Copy installed packages and code from builder
COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin
COPY --from=builder /build/md_evals /app/md_evals
COPY --from=builder /build/apps/server /app/apps/server

USER appuser

EXPOSE 8000

CMD ["uvicorn", "apps.server.app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```
