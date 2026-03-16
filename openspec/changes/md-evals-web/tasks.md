# Tasks: md-evals-web

**Version**: 1.0  
**Status**: Draft  
**Última actualización**: 2026-03-16  
**Design**: [design.md](./design.md)  
**Spec**: [spec.md](./spec.md)

---

## Fases de Implementación

### Fase 1: Monorepo Scaffolding

> Crear la estructura de directorios y configuraciones base del monorepo.

| # | Task | Archivos | Dependencias | Done When | Esfuerzo |
|---|------|----------|-------------|-----------|----------|
| 1.1 | [ ] Crear estructura de directorios `apps/server/` y `apps/web/` | `apps/server/app/__init__.py`, `apps/server/app/routes/__init__.py`, `apps/server/app/services/__init__.py`, `apps/server/app/models/__init__.py`, `apps/server/app/middleware/__init__.py` | Ninguna | Directorios existen con `__init__.py` | S |
| 1.2 | [ ] Crear `apps/server/pyproject.toml` con dependencias del server | `apps/server/pyproject.toml` | 1.1 | Tiene deps: fastapi, uvicorn, sqlalchemy[asyncio], asyncpg, pyjwt, cryptography, sse-starlette, httpx, pydantic-settings, alembic, pyyaml. Dep a md-evals local (`../../`). `pip install -e .` funciona | S |
| 1.3 | [ ] Crear `apps/web/package.json` con dependencias del frontend | `apps/web/package.json` | 1.1 | Tiene deps: react, react-dom, react-router-dom, @tanstack/react-query, recharts, tailwindcss. DevDeps: vite, @vitejs/plugin-react, typescript. `pnpm install` funciona | S |
| 1.4 | [ ] Crear `apps/web/vite.config.ts` con base path para GH Pages | `apps/web/vite.config.ts` | 1.3 | `base: "/md-evals/"`, proxy para dev (`/api` → `http://localhost:8000`). `pnpm dev` arranca | S |
| 1.5 | [ ] Crear `apps/web/tsconfig.json` con strict mode | `apps/web/tsconfig.json` | 1.3 | TypeScript strict habilitado, paths configurados | S |
| 1.6 | [ ] Crear `apps/web/tailwind.config.ts` + `src/index.css` | `apps/web/tailwind.config.ts`, `apps/web/src/index.css` | 1.3 | Tailwind CSS 4 funciona en dev | S |
| 1.7 | [ ] Crear `docker-compose.yml` (api + db) | `docker-compose.yml` | 1.2 | `docker compose up db` levanta PostgreSQL con health check | S |
| 1.8 | [ ] Crear `.github/workflows/deploy-pages.yml` (placeholder) | `.github/workflows/deploy-pages.yml` | 1.3 | Workflow YAML válido (se completa en Fase 8) | S |
| 1.9 | [ ] Verificar que `md-evals` CLI sigue funcionando | — | 1.1 | `python -m md_evals --help` funciona. Tests existentes pasan (`pytest tests/`) | S |

**Gate Fase 1**: `pytest tests/` pasa (core intacto), `pip install -e apps/server/` funciona, `pnpm install` en `apps/web/` funciona.

---

### Fase 2: Backend Core

> FastAPI app factory, configuración, modelos DB, y migraciones.

| # | Task | Archivos | Dependencias | Done When | Esfuerzo |
|---|------|----------|-------------|-----------|----------|
| 2.1 | [ ] Crear `app/config.py` con Pydantic Settings | `apps/server/app/config.py` | 1.2 | `Settings()` lee de env vars. Falla si falta alguna requerida (GITHUB_CLIENT_ID, JWT_SECRET, etc.). Test unitario verifica error descriptivo | S |
| 2.2 | [ ] Crear `app/db.py` con async engine + session factory | `apps/server/app/db.py` | 2.1 | `get_db()` dependency retorna AsyncSession. Se conecta a PostgreSQL del docker-compose | S |
| 2.3 | [ ] Crear modelos SQLAlchemy en `app/models/db.py` | `apps/server/app/models/db.py` | 2.2 | Tablas: users, provider_keys, evaluations, eval_results, user_settings. Mapped[] type annotations (SQLAlchemy 2.0 style) | M |
| 2.4 | [ ] Crear schemas Pydantic en `app/models/schemas.py` | `apps/server/app/models/schemas.py` | 2.3 | Request/response schemas para todos los endpoints de la spec (EvalRunRequest, EvalResponse, ProviderKeyCreate, HistoryResponse, etc.) | M |
| 2.5 | [ ] Configurar Alembic para migraciones async | `apps/server/alembic/`, `apps/server/alembic.ini`, `apps/server/alembic/env.py` | 2.3 | `alembic revision --autogenerate` genera migración inicial. `alembic upgrade head` crea las tablas en PostgreSQL | M |
| 2.6 | [ ] Crear `app/main.py` con FastAPI app factory + lifespan | `apps/server/app/main.py` | 2.1, 2.5 | App arranca con `uvicorn`, health check `/health` retorna `{"status":"ok","db":"connected"}`. Falla si env vars faltan | M |
| 2.7 | [ ] Crear CORS middleware en `app/middleware/cors.py` | `apps/server/app/middleware/cors.py` | 2.6 | CORS configurado con origins de `CORS_ORIGINS` env var. No wildcard en producción | S |

**Gate Fase 2**: `docker compose up` levanta API + DB. `GET /health` retorna 200. Alembic crea tablas. Schemas Pydantic validan correctamente.

---

### Fase 3: Auth

> OAuth flow completo, JWT, y middleware de autenticación.

| # | Task | Archivos | Dependencias | Done When | Esfuerzo |
|---|------|----------|-------------|-----------|----------|
| 3.1 | [ ] Crear `routes/auth.py` con `GET /auth/login` | `apps/server/app/routes/auth.py` | 2.6 | Redirige a `github.com/login/oauth/authorize` con client_id, redirect_uri, scope=read:user, state (HMAC-signed con STATE_SECRET). State tiene formato `{base36_ts}.{hmac_hex}` | M |
| 3.2 | [ ] Implementar `GET /auth/callback` en `routes/auth.py` | `apps/server/app/routes/auth.py` | 3.1 | Valida state (HMAC + expiry 5min). Intercambia code por access_token con GitHub. Llama GET /user. Upsert en users table. Encripta y guarda GitHub token. Genera JWT. Redirige a frontend con JWT | L |
| 3.3 | [ ] Crear JWT middleware en `app/middleware/auth.py` | `apps/server/app/middleware/auth.py` | 3.2 | Dependency `get_current_user` extrae JWT de `Authorization: Bearer`. Valida firma y expiración. Retorna user info del payload. 401 con `WWW-Authenticate: Bearer` si falla | M |
| 3.4 | [ ] Proteger todas las rutas `/api/*` con JWT | `apps/server/app/main.py`, `apps/server/app/routes/*.py` | 3.3 | Todas las rutas /api/* requieren JWT. /auth/* y /health son públicas. Request sin token → 401 `{"error":"missing_token"}`. Token expirado → 401 `{"error":"token_expired"}` | S |
| 3.5 | [ ] Tests de auth | `apps/server/tests/test_auth.py` | 3.4 | Tests: state generation/validation, JWT creation/verification, callback happy path (mock GitHub API), expired JWT, invalid signature, missing token | M |

**Gate Fase 3**: OAuth flow completo funciona contra GitHub real (con test account). JWT se genera y valida. Middleware protege /api/*.

---

### Fase 4: Provider Keys

> CRUD de API keys, encriptación, y validación contra providers reales.

| # | Task | Archivos | Dependencias | Done When | Esfuerzo |
|---|------|----------|-------------|-----------|----------|
| 4.1 | [ ] Crear `services/crypto.py` con AES-256-GCM | `apps/server/app/services/crypto.py` | 2.1 | `CryptoService`: `derive_user_key(user_id)`, `encrypt(plaintext, user_id)`, `decrypt(blob, user_id)`. Usa HKDF + AESGCM de `cryptography`. Test: encrypt → decrypt roundtrip. Test: blob sin nonce falla | M |
| 4.2 | [ ] Crear `services/provider_validator.py` | `apps/server/app/services/provider_validator.py` | 2.1 | Valida keys: OpenAI (GET /v1/models), Anthropic (POST /v1/messages), Google (GET /v1/models). Timeout 10s. Retorna `(valid: bool, error: str|None)` | M |
| 4.3 | [ ] Crear `routes/providers.py` con CRUD endpoints | `apps/server/app/routes/providers.py` | 4.1, 4.2, 3.3 | `GET /api/providers` → lista masked keys. `POST /api/providers` → valida, encripta, guarda. `DELETE /api/providers/{provider}` → elimina. `POST /api/providers/validate` → dry-run | M |
| 4.4 | [ ] Implementar hint extraction | `apps/server/app/services/crypto.py` | 4.1 | `extract_key_hint("sk-proj-abc...xyz")` → `"sk-...xyz"`. Keys cortas (≤8 chars) → `"****"` | S |
| 4.5 | [ ] Tests de crypto + providers | `apps/server/tests/test_crypto.py`, `apps/server/tests/test_providers.py` | 4.3 | Tests: encrypt/decrypt roundtrip, wrong user_id fails, hint extraction, provider validation (mocked HTTP), missing master key on startup | M |

**Gate Fase 4**: POST provider key → valida → encripta → guarda. GET retorna solo masked hints. DELETE elimina. Roundtrip crypto funciona.

---

### Fase 5: Eval Execution

> Endpoint de ejecución, integración con md_evals engine, SSE streaming.

| # | Task | Archivos | Dependencias | Done When | Esfuerzo |
|---|------|----------|-------------|-----------|----------|
| 5.1 | [ ] Crear `services/eval_service.py` con lógica de ejecución | `apps/server/app/services/eval_service.py` | 4.1, 2.3 | `EvalService.run_eval()`: parsea YAML → EvalConfig, resuelve API key, crea LLMAdapter, crea ExecutionEngine, ejecuta en background task, publica eventos en asyncio.Queue. Importa `md_evals.engine`, `md_evals.llm`, `md_evals.evaluator`, `md_evals.metrics` | L |
| 5.2 | [ ] Implementar skill injection sin archivo (tempfile) | `apps/server/app/services/eval_service.py` | 5.1 | Crea NamedTemporaryFile con skill_content, setea treatment.skill_path al path temporal. Limpia después de ejecución. No modifica md_evals/ | M |
| 5.3 | [ ] Crear `routes/eval.py` con POST /api/eval/run | `apps/server/app/routes/eval.py` | 5.1, 3.3 | POST retorna 202 con eval_id + status. Valida YAML en request. Check rate limit (10/hora). Check provider key disponible | M |
| 5.4 | [ ] Implementar GET /api/eval/{id}/stream (SSE) | `apps/server/app/routes/eval.py` | 5.1 | SSE endpoint consume de asyncio.Queue. Emite eval_started, test_started, test_completed, eval_completed/error/timeout. Stream cierra al terminar. Requiere JWT | M |
| 5.5 | [ ] Implementar GET /api/eval/{id} (resultados) | `apps/server/app/routes/eval.py` | 5.1 | Retorna eval completa con results, summary, usage_metrics. 404 si no existe o no pertenece al user | S |
| 5.6 | [ ] Implementar GET /api/eval/history con filtros | `apps/server/app/routes/eval.py` | 5.1 | Query params: page, per_page, date_from, date_to, model, status. Paginación con total/pages. Ordenado por created_at DESC | M |
| 5.7 | [ ] Implementar timeout de eval (default 10 min) | `apps/server/app/services/eval_service.py` | 5.1 | `asyncio.wait_for()` con timeout configurable. Si timeout → status="timeout", guarda resultados parciales, emite eval_timeout SSE event | M |
| 5.8 | [ ] Implementar rate limiting (10 evals/hora/usuario) | `apps/server/app/routes/eval.py` | 5.3 | Cuenta evals del usuario en última hora. Si ≥ 10, retorna 429 con Retry-After header | S |
| 5.9 | [ ] Implementar cleanup de evals huérfanas en startup | `apps/server/app/main.py` | 5.1 | En lifespan startup: marca evals con status="running" > 15 min como "failed" con error="server_restarted" | S |
| 5.10 | [ ] Tests de eval execution | `apps/server/tests/test_eval.py` | 5.8 | Tests: eval happy path (mock LLM), YAML inválido → 400, missing provider key → 400, timeout → status timeout, rate limit → 429 | L |

**Gate Fase 5**: POST /api/eval/run lanza eval, SSE stream funciona, resultados se persisten, historial con filtros funciona. md_evals engine importado y usado correctamente.

---

### Fase 6: Frontend Scaffolding

> Vite + React 19 + routing + auth context + API client.

| # | Task | Archivos | Dependencias | Done When | Esfuerzo |
|---|------|----------|-------------|-----------|----------|
| 6.1 | [ ] Crear `src/main.tsx` y `src/App.tsx` con HashRouter | `apps/web/src/main.tsx`, `apps/web/src/App.tsx`, `apps/web/index.html` | 1.3, 1.4 | React app renderiza con HashRouter. Routes definidas pero vacías (placeholder pages). `pnpm dev` muestra algo | M |
| 6.2 | [ ] Crear `src/lib/api.ts` (fetch wrapper) | `apps/web/src/lib/api.ts` | 6.1 | `apiClient` con baseURL de `VITE_API_URL`, auto-attach Authorization header, error handling (401 → redirect login), JSON parsing | M |
| 6.3 | [ ] Crear `src/lib/auth.tsx` (AuthContext + useAuth) | `apps/web/src/lib/auth.tsx` | 6.2 | `AuthProvider`: lee JWT de localStorage, decodifica payload (sin verificar firma — solo para UI), expone `user`, `login()`, `logout()`, `isAuthenticated`. `useAuth()` hook | M |
| 6.4 | [ ] Crear `src/lib/types.ts` (TypeScript types) | `apps/web/src/lib/types.ts` | — | Types: User, EvalRun, EvalResult, ProviderKey, HistoryItem, SSEEvent, PaginatedResponse. Match API contracts del design.md | M |
| 6.5 | [ ] Crear `src/lib/queryClient.ts` | `apps/web/src/lib/queryClient.ts` | 6.1 | QueryClient configurado: defaultOptions (staleTime 30s, retry 1), onError global para 401 | S |
| 6.6 | [ ] Crear `src/components/layout/AppShell.tsx` | `apps/web/src/components/layout/AppShell.tsx`, `apps/web/src/components/layout/Sidebar.tsx`, `apps/web/src/components/layout/UserMenu.tsx` | 6.3 | Layout con sidebar (nav links), topbar (user menu + avatar), content area. Auth guard: redirect a /login si no autenticado. Responsive | M |

**Gate Fase 6**: `pnpm dev` muestra app con layout, routing funciona entre páginas placeholder, auth flow redirige a GitHub, callback procesa JWT.

---

### Fase 7: Frontend Pages

> Implementación completa de todas las páginas.

| # | Task | Archivos | Dependencias | Done When | Esfuerzo |
|---|------|----------|-------------|-----------|----------|
| 7.1 | [ ] Implementar Login page | `apps/web/src/pages/Login.tsx` | 6.3 | Botón "Login with GitHub" redirige a /auth/login del backend. Campo PAT fallback visible si backend no responde (timeout 5s). Link a docs de GitHub PAT | M |
| 7.2 | [ ] Implementar AuthCallback page | `apps/web/src/pages/AuthCallback.tsx` | 6.3 | Lee `?token=` de URL, guarda en localStorage, setea AuthContext, redirige a /dashboard. Maneja `?error=` mostrando mensaje descriptivo | S |
| 7.3 | [ ] Implementar EvalRun page (upload + paste + run) | `apps/web/src/pages/EvalRun.tsx`, `apps/web/src/components/eval/EvalForm.tsx` | 6.2, 6.4 | Dos textareas (SKILL.md + eval YAML). Drag-drop zone. Validación client-side (YAML syntax, key "tests", tamaño ≤100KB/50KB). Botón "Run Eval" → POST /api/eval/run | L |
| 7.4 | [ ] Implementar SSE progress component | `apps/web/src/components/eval/EvalProgress.tsx` | 7.3 | Conecta a GET /api/eval/{id}/stream via EventSource. Muestra lista de tests con status (pending/running/pass/fail). Progress bar. Auto-navega a dashboard al completar | L |
| 7.5 | [ ] Implementar Dashboard page (results) | `apps/web/src/pages/Dashboard.tsx`, `apps/web/src/components/eval/SummaryCard.tsx`, `apps/web/src/components/eval/ResultsTable.tsx` | 6.2, 6.4 | Summary card (pass rate, counts, duration). Results table (treatment, test, pass/fail, score, duration). Carga datos de GET /api/eval/{id} | M |
| 7.6 | [ ] Implementar charts con Recharts | `apps/web/src/components/charts/PassRateChart.tsx`, `apps/web/src/components/charts/TokenUsageChart.tsx`, `apps/web/src/components/charts/ContextGauge.tsx`, `apps/web/src/components/charts/CostBreakdown.tsx` | 7.5 | Bar chart: pass rate por treatment. Line chart: tokens por test. Gauge: context utilization (green/yellow/red). Stacked bar: prompt vs completion tokens | L |
| 7.7 | [ ] Implementar History page | `apps/web/src/pages/History.tsx` | 6.2, 6.4 | Lista paginada de evals. Filtros: fecha, modelo, status. Click → navega a /eval/{id}. Selector de 2 evals para comparar side-by-side | M |
| 7.8 | [ ] Implementar comparación side-by-side | `apps/web/src/pages/History.tsx` | 7.7 | Seleccionar 2 evals → modal/page con pass rates lado a lado, delta de métricas, tabla con diff por test (improved/regressed/unchanged con colores) | L |
| 7.9 | [ ] Implementar Settings page (provider keys) | `apps/web/src/pages/Settings.tsx`, `apps/web/src/components/settings/ProviderKeyForm.tsx`, `apps/web/src/components/settings/ProviderKeyList.tsx` | 6.2, 6.4 | Lista de providers con keys masked. Form para agregar key (select provider + input). Delete con confirmación. GitHub Models muestra badge "Disponible". Optimistic updates con TanStack Query | M |

**Gate Fase 7**: Todas las páginas funcionales. Login → Run Eval → Ver Results → History → Settings. Charts renderizan con datos reales. Flujo E2E completo en browser.

---

### Fase 8: Deploy

> GitHub Pages workflow, Dockerfile final, docker-compose productivo.

| # | Task | Archivos | Dependencias | Done When | Esfuerzo |
|---|------|----------|-------------|-----------|----------|
| 8.1 | [ ] Completar `deploy-pages.yml` (GH Actions workflow) | `.github/workflows/deploy-pages.yml` | 7.* | Triggers on push to main. Steps: checkout, setup Node, pnpm install, pnpm build (con VITE_API_URL), deploy a GH Pages. Frontend accesible en `https://{user}.github.io/md-evals/` | M |
| 8.2 | [ ] Completar `Dockerfile` multi-stage | `apps/server/Dockerfile` | 5.* | Stage 1: builder (install deps + md_evals + server). Stage 2: runtime (slim, non-root user). `docker build` exitoso. Image < 200MB | M |
| 8.3 | [ ] Agregar entrypoint con Alembic auto-migrate | `apps/server/entrypoint.sh` | 8.2, 2.5 | `entrypoint.sh`: `alembic upgrade head && uvicorn ...`. Docker compose up → DB migrada automáticamente → API running | S |
| 8.4 | [ ] Configurar producción CORS y env vars | `docker-compose.yml`, `apps/server/app/config.py` | 8.2 | CORS restringido a GitHub Pages URL. Todas las env vars requeridas documentadas en docker-compose.yml como variables sin default | S |
| 8.5 | [ ] Agregar CI check: no secrets en frontend bundle | `.github/workflows/deploy-pages.yml` | 8.1 | Step en CI: `grep -r "client_secret" apps/web/dist/ && exit 1 || true`. Falla si encuentra secrets en el build | S |

**Gate Fase 8**: Frontend deployado en GH Pages. `docker compose up` levanta API + DB en producción. Health check OK. CORS restrictivo.

---

### Fase 9: Tests + Validación

> Tests unitarios, integración, y validación global.

| # | Task | Archivos | Dependencias | Done When | Esfuerzo |
|---|------|----------|-------------|-----------|----------|
| 9.1 | [ ] Tests unitarios del backend completos | `apps/server/tests/` | 5.10, 4.5, 3.5 | Coverage > 80% en services/ y routes/. Mock de GitHub API y LLM providers. Todos pasan | L |
| 9.2 | [ ] Test de parity CLI vs Web | `apps/server/tests/test_parity.py` | 5.1 | Mismo SKILL.md + eval.yaml → ejecutar via CLI (`md_evals.engine` directo) y via backend endpoint → resultados numéricos idénticos (pass/fail, scores). Mock LLM para determinismo | M |
| 9.3 | [ ] Test de backward compatibility (core intacto) | — | 1.9 | `git diff md_evals/` muestra CERO cambios. `pytest tests/` (tests del core) pasan. `python -m md_evals --help` funciona | S |
| 9.4 | [ ] Verificar `ruff check` sin errores | — | Todas | `ruff check md_evals/ apps/server/` pasa sin errores. `ruff format --check` pasa | S |
| 9.5 | [ ] Verificar frontend build sin errores | — | 7.* | `pnpm build` en apps/web/ completa sin errores TypeScript ni warnings | S |
| 9.6 | [ ] Verificar Docker build exitoso | — | 8.2 | `docker build -f apps/server/Dockerfile .` completa. Image funciona con `docker run` | S |
| 9.7 | [ ] Smoke test E2E manual | — | 8.* | Checklist manual: Login OAuth → Upload SKILL.md → Run eval (con GitHub Models) → Ver results + charts → Check history → Add provider key → Run con provider key → Delete key → Logout | M |

**Gate Fase 9**: Todos los tests pasan. Core intacto verificado. Build exitoso. Smoke test E2E superado.

---

## Validación Global (Pre-merge)

Checklist final antes de mergear a main:

```bash
# 1. Core no roto
pytest tests/                                    # Tests del core pasan
git diff md_evals/                               # CERO cambios en core
python -m md_evals --help                        # CLI funciona

# 2. Backend
cd apps/server
ruff check app/                                  # Linter clean
ruff format --check app/                         # Format clean
pytest tests/                                    # Server tests pasan

# 3. Frontend
cd apps/web
pnpm build                                       # Build sin errores
pnpm tsc --noEmit                                # TypeScript check

# 4. Docker
docker compose build                             # Builds exitosos
docker compose up -d                             # Servicios arrancan
curl http://localhost:8000/health                 # API responde OK
docker compose down

# 5. Security
grep -r "client_secret" apps/web/dist/ && exit 1 # No secrets en bundle
grep -r "MASTER_KEY" apps/web/dist/ && exit 1    # No master key en bundle
```

---

## Resumen de Esfuerzo

| Fase | Tasks | Esfuerzo total estimado |
|------|-------|------------------------|
| Fase 1: Scaffolding | 9 | ~1 día |
| Fase 2: Backend Core | 7 | ~2 días |
| Fase 3: Auth | 5 | ~2 días |
| Fase 4: Provider Keys | 5 | ~1.5 días |
| Fase 5: Eval Execution | 10 | ~3 días |
| Fase 6: Frontend Scaffolding | 6 | ~1.5 días |
| Fase 7: Frontend Pages | 9 | ~4 días |
| Fase 8: Deploy | 5 | ~1 día |
| Fase 9: Tests + Validación | 7 | ~2 días |
| **Total** | **63 tasks** | **~18 días** |

---

## Orden de Ejecución Recomendado

```
Fase 1 (Scaffolding)
  ↓
Fase 2 (Backend Core)
  ↓
┌──────────────┐     ┌──────────────┐
│ Fase 3 (Auth)│     │ Fase 6       │
│              │     │ (FE Scaffold)│
└──────┬───────┘     └──────┬───────┘
       ↓                    ↓
┌──────────────┐     ┌──────────────┐
│ Fase 4 (Keys)│     │ Fase 7       │
│              │     │ (FE Pages)   │
└──────┬───────┘     └──────┬───────┘
       ↓                    │
┌──────────────┐            │
│ Fase 5 (Eval)│            │
└──────┬───────┘            │
       ↓                    ↓
       └──────┬─────────────┘
              ↓
       Fase 8 (Deploy)
              ↓
       Fase 9 (Tests)
```

**Paralelismo posible**: Fases 3-4-5 (backend) pueden avanzar en paralelo con Fases 6-7 (frontend), ya que el frontend puede usar mocks hasta que el backend esté listo.
