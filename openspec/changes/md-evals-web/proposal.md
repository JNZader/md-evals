# Proposal: md-evals-web

> **Status**: DRAFT
> **Author**: Javier Zader
> **Date**: 2026-03-16
> **Change**: md-evals-web

---

## Intent

Crear una interfaz web completa para **md-evals** que permita a los usuarios evaluar AI skills (SKILL.md) desde el navegador sin necesidad de instalar la CLI ni configurar un entorno Python local. La web expone la misma lógica de evaluación que la CLI pero con UX visual: upload de archivos, configuración de providers, gráficos de métricas, e historial persistente.

### Motivación

1. **Barrera de entrada**: instalar Python + dependencias + configurar API keys es fricción para usuarios casuales
2. **Visualización**: las métricas de cost, context y pass rate se entienden mejor con gráficos que con tablas de terminal
3. **Historial**: poder comparar evals a lo largo del tiempo requiere persistencia (la CLI es stateless)
4. **Accesibilidad**: GitHub Models es gratis → con GitHub OAuth cualquiera puede probar md-evals sin pagar por API keys

---

## Scope

### MVP (v0.1)

| Feature | Descripción |
|---------|-------------|
| **Auth: GitHub OAuth** | Login via GitHub App → token se usa para GitHub Models (rate-limited, gratis). Fallback a PAT manual si el server no está disponible |
| **Upload & Paste** | El usuario pega texto o sube archivos (SKILL.md + eval YAML) |
| **Run Eval** | Ejecutar evaluación contra GitHub Models usando el engine existente de md-evals |
| **Results Dashboard** | Tabla de resultados + gráficos Recharts (pass rate, cost breakdown, context utilization) |
| **Provider Keys** | UI para configurar API keys de OpenAI/Anthropic/etc., encriptadas server-side (AES-256-GCM), validación antes de guardar |
| **Eval History** | Lista de evals pasadas con capacidad de ver detalle y comparar |
| **Deploy** | Frontend en GitHub Pages, Backend en Docker (Coolify/similar) |

### Post-MVP (v0.2+)

| Feature | Descripción |
|---------|-------------|
| **Diff visual** | Comparación side-by-side de dos evals (A/B testing visual) |
| **Templates de eval YAML** | Galería de evaluaciones pre-armadas para skills comunes |
| **Sharing** | URLs públicas para compartir resultados de evals |
| **Webhook triggers** | Ejecutar evals automáticamente en push a un repo |
| **Multi-user / teams** | Workspaces compartidos con roles |
| **Scheduled evals** | Cron-based re-evaluation para detectar regresiones |
| **Export** | Exportar resultados a CSV/PDF |

### Explícitamente fuera de scope (MVP)

- Mobile-specific UI (responsive sí, app nativa no)
- Admin panel / user management (single-user MVP)
- Billing / paid tiers
- Self-hosted frontend (solo GitHub Pages)
- Modificación de la lógica core de md-evals (se consume as-is)

---

## Approach

### Arquitectura General

```
┌─────────────────────────────────┐     ┌──────────────────────────────────┐
│        Frontend (SPA)           │     │         Backend (API)             │
│  React 19 + Vite + Tailwind 4  │────▶│  FastAPI (Python 3.12+)          │
│  TanStack Query + Recharts     │     │  Importa md_evals directamente   │
│  Deploy: GitHub Pages           │     │  Deploy: Docker (Coolify)        │
└─────────────────────────────────┘     └──────────┬───────────────────────┘
                                                   │
                                        ┌──────────▼───────────────────────┐
                                        │       PostgreSQL                  │
                                        │  Settings, encrypted keys,        │
                                        │  eval history + results           │
                                        └───────────────────────────────────┘
```

### Stack Técnico

| Capa | Tecnología | Justificación |
|------|-----------|---------------|
| **Frontend** | React 19 + Vite | React 19 con compiler, Vite para fast HMR |
| **Styling** | Tailwind CSS 4 | Utility-first, zero runtime, theming con CSS variables |
| **Data fetching** | TanStack Query v5 | Cache, mutations, optimistic updates, SSE streaming |
| **Charts** | Recharts | React-native charting, composable, lightweight |
| **Deploy frontend** | GitHub Pages | Gratis, CI/CD con GitHub Actions (como JNZader/ghagga) |
| **Backend** | FastAPI | Async nativo, Pydantic v2 (ya usado en md-evals), OpenAPI auto-docs |
| **ORM** | SQLAlchemy 2.0 + asyncpg | Async PostgreSQL, migrations con Alembic |
| **Auth** | GitHub OAuth (GitHub App) | Token nativo para GitHub Models, familiar para devs |
| **Encryption** | AES-256-GCM (cryptography lib) | Encrypt API keys at rest, per-user encryption key derivado |
| **DB** | PostgreSQL 16 | Relacional, JSONB para resultados flexibles, probado |
| **Deploy backend** | Docker + Coolify | Container simple, deploy automatizado |

### Flujo Principal (Happy Path)

```
1. Usuario → Login con GitHub OAuth
2. GitHub → Redirect con code → Backend intercambia por token
3. Backend → Guarda token encriptado, crea sesión (JWT)
4. Usuario → Pega SKILL.md + eval YAML (o sube archivos)
5. Frontend → POST /api/evals/run con contenido
6. Backend → Parsea YAML → Instancia EvalConfig, ExecutionEngine, LLMAdapter
7. Backend → Ejecuta eval usando md_evals.engine (MISMO código que CLI)
8. Backend → Calcula métricas con md_evals.metrics
9. Backend → Guarda resultados en PostgreSQL
10. Backend → Devuelve resultados al frontend (SSE para streaming progress)
11. Frontend → Renderiza tabla + gráficos Recharts
12. Usuario → Consulta historial → Compara evals
```

### Integración con md-evals Core

El backend **importa directamente** los módulos de md-evals:

```python
from md_evals.models import EvalConfig
from md_evals.engine import ExecutionEngine
from md_evals.llm import LLMAdapter
from md_evals.evaluator import EvaluatorEngine
from md_evals.metrics import build_usage_metrics
from md_evals.reporter import Reporter  # Para exportación futura
```

**No se duplica lógica**. El backend es un adapter HTTP sobre la misma engine.

### Modelo de Datos (PostgreSQL)

```sql
-- Users (de GitHub OAuth)
users (
  id UUID PK,
  github_id BIGINT UNIQUE,
  github_login TEXT,
  github_token_enc BYTEA,       -- Token GitHub encriptado
  created_at TIMESTAMPTZ,
  updated_at TIMESTAMPTZ
)

-- API Keys de providers (encriptadas)
provider_keys (
  id UUID PK,
  user_id UUID FK → users,
  provider TEXT,                  -- 'openai', 'anthropic', etc.
  key_enc BYTEA,                 -- API key encriptada AES-256-GCM
  key_hint TEXT,                 -- Últimos 4 chars para display
  validated_at TIMESTAMPTZ,
  created_at TIMESTAMPTZ
)

-- Evaluations
evaluations (
  id UUID PK,
  user_id UUID FK → users,
  name TEXT,
  skill_content TEXT,            -- SKILL.md content
  eval_yaml TEXT,                -- eval.yaml content
  config JSONB,                  -- EvalConfig serializado
  status TEXT,                   -- 'pending', 'running', 'completed', 'failed'
  created_at TIMESTAMPTZ,
  completed_at TIMESTAMPTZ
)

-- Eval Results (un row por execution result)
eval_results (
  id UUID PK,
  evaluation_id UUID FK → evaluations,
  treatment TEXT,
  task TEXT,
  model TEXT,
  passed BOOLEAN,
  score FLOAT,
  response_text TEXT,
  cost_metrics JSONB,
  context_metrics JSONB,
  evaluator_results JSONB,
  duration_ms INTEGER,
  created_at TIMESTAMPTZ
)
```

### Estructura de Directorios

```
md-evals/
├── md_evals/          # Core (sin cambios)
├── web/
│   ├── frontend/      # React SPA
│   │   ├── src/
│   │   │   ├── components/
│   │   │   ├── pages/
│   │   │   ├── hooks/
│   │   │   ├── api/       # TanStack Query hooks
│   │   │   ├── stores/    # Zustand si necesario
│   │   │   └── lib/
│   │   ├── public/
│   │   ├── index.html
│   │   ├── vite.config.ts
│   │   ├── tailwind.config.ts
│   │   └── package.json
│   ├── backend/       # FastAPI
│   │   ├── app/
│   │   │   ├── api/       # Routers
│   │   │   ├── core/      # Config, security, encryption
│   │   │   ├── db/        # SQLAlchemy models, migrations
│   │   │   ├── services/  # Business logic (wraps md_evals)
│   │   │   └── main.py
│   │   ├── alembic/
│   │   ├── Dockerfile
│   │   └── pyproject.toml
│   └── docker-compose.yml  # Backend + PostgreSQL
├── openspec/
└── pyproject.toml     # Core package
```

### Auth Flow Detallado

```
┌──────────┐     ┌──────────┐     ┌──────────┐     ┌──────────┐
│ Frontend │     │ Backend  │     │ GitHub   │     │ GH Models│
│          │     │ (FastAPI)│     │ OAuth    │     │ API      │
└────┬─────┘     └────┬─────┘     └────┬─────┘     └────┬─────┘
     │                │                │                │
     │ Click Login    │                │                │
     ├───────────────▶│                │                │
     │                │ Redirect to    │                │
     │                │ /authorize     │                │
     │◀───────────────┤───────────────▶│                │
     │                │                │                │
     │ Redirect w/code│                │                │
     ├───────────────▶│                │                │
     │                │ Exchange code  │                │
     │                │ for token      │                │
     │                ├───────────────▶│                │
     │                │◀───────────────┤                │
     │                │                │                │
     │                │ Encrypt + save │                │
     │                │ token in DB    │                │
     │                │                │                │
     │                │ Issue JWT      │                │
     │◀───────────────┤                │                │
     │                │                │                │
     │ Run eval       │                │                │
     ├───────────────▶│                │                │
     │                │ Decrypt GH token                │
     │                │ Use as API key  ───────────────▶│
     │                │◀───────────────────────────────┤
     │◀───────────────┤                │                │
```

**Fallback sin server**: Si el backend no está disponible, el frontend muestra un campo para pegar un GitHub PAT manualmente. El PAT se envía en cada request (no se persiste en el frontend, solo en memory/session).

### Encryption Strategy (API Keys)

1. **Master key**: Variable de entorno (`MD_EVALS_MASTER_KEY`), generada una vez
2. **Per-user key derivation**: `HKDF(master_key, user_id)` → user-specific key
3. **Encryption**: AES-256-GCM con nonce aleatorio por cada key
4. **Storage**: `nonce || ciphertext || tag` en columna BYTEA
5. **Validación**: Antes de guardar, se hace un test API call al provider para verificar que la key funciona
6. **Rotation**: Si master key cambia, se necesita re-encrypt (migration script)

---

## Risks

| Risk | Probabilidad | Impacto | Mitigación |
|------|-------------|---------|------------|
| **GitHub Models rate limits** | Alta | Medio | Mostrar rate limit info en UI, sugerir usar provider propio si hay throttling |
| **GitHub OAuth token scope** | Media | Alto | Documentar scopes mínimos necesarios, solo `read:user` + lo que GitHub Models necesite |
| **CORS entre GH Pages y backend** | Media | Medio | Configurar CORS correctamente en FastAPI, usar proxy en dev |
| **md-evals breaking changes** | Baja | Alto | Backend pinta versión de md-evals, integration tests contra core |
| **Encryption key compromise** | Baja | Crítico | Master key solo en env vars, never in code/DB, auditar accesos |
| **Long-running evals** | Alta | Medio | SSE streaming para progress, timeouts configurables, background tasks con asyncio |
| **PostgreSQL en Coolify** | Baja | Medio | Docker Compose incluye PG, backups automatizados |
| **Frontend/Backend version drift** | Media | Medio | Versionado semántico, API versioning (`/api/v1/`), CI checks |

---

## Success Criteria

### MVP Launch

- [ ] Un usuario puede hacer login con GitHub OAuth y ejecutar un eval contra GitHub Models en < 2 minutos desde la primera visita
- [ ] Los resultados muestran: tabla de pass/fail + gráfico de cost + gráfico de context utilization
- [ ] Las API keys de providers se guardan encriptadas y sobreviven logout/login
- [ ] El historial muestra las últimas 50 evals con filtro por fecha
- [ ] Los resultados de la web son idénticos a los de `md-evals` CLI para el mismo input (parity test)
- [ ] El frontend carga en < 3s en conexión 3G (Lighthouse performance > 80)
- [ ] El backend responde health check en < 100ms
- [ ] Zero secrets en el frontend bundle (verificado en CI)

### Acceptance Tests

1. **E2E happy path**: Login → Upload SKILL.md + YAML → Run → Ver resultados con gráficos → Ver en historial
2. **Provider key flow**: Guardar key OpenAI → Run eval con OpenAI → Key sobrevive sesión
3. **PAT fallback**: Sin server auth → Pegar PAT → Run eval → Resultados correctos
4. **Parity**: Mismo SKILL.md + YAML → CLI output == Web output (métricas numéricas exactas)
5. **Error handling**: Key inválida → Error claro, eval timeout → Estado visible, YAML malformado → Mensaje descriptivo

---

## Open Questions

1. **¿Monorepo o repo separado?** Este proposal asume `web/` dentro de md-evals (monorepo). ¿Preferís repo separado?
2. **¿GitHub App o GitHub OAuth App?** GitHub App es más moderno y tiene scopes más granulares, pero OAuth App es más simple. Recomendación: GitHub App.
3. **¿SSE o WebSocket para streaming?** SSE es más simple y suficiente para progress unidireccional. WebSocket solo si necesitamos bidireccional.
4. **¿Session storage?** JWT stateless vs server-side sessions en Redis. Recomendación: JWT stateless para MVP, no agregar Redis.
5. **¿Zustand necesario?** TanStack Query maneja server state. ¿Hay suficiente client-only state para justificar Zustand? Probablemente no en MVP.

---

## Estimated Effort

| Componente | Esfuerzo estimado |
|-----------|-------------------|
| Backend: FastAPI scaffold + auth | 2-3 días |
| Backend: Eval execution service | 1-2 días |
| Backend: Encryption + provider keys | 1 día |
| Backend: DB models + migrations | 1 día |
| Frontend: Scaffold + routing + auth | 2 días |
| Frontend: Eval form (upload/paste) | 1-2 días |
| Frontend: Results dashboard + charts | 2-3 días |
| Frontend: History page | 1 día |
| Frontend: Settings/keys page | 1 día |
| Integration: CORS, deploy, CI | 1-2 días |
| Testing: E2E + parity tests | 2 días |
| **Total estimado** | **~15-20 días** |
