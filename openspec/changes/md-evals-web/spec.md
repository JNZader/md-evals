# Specification: md-evals-web

**Version**: 1.0  
**Status**: Draft  
**Última actualización**: 2026-03-16  
**Proposal**: [proposal.md](./proposal.md)

---

## 1. Propósito

Agregar una interfaz web completa a md-evals que permita evaluar AI skills (SKILL.md) desde el navegador, con autenticación GitHub OAuth, gestión de API keys encriptadas, ejecución de evaluaciones con streaming de progreso, dashboard con gráficos, e historial persistente — todo consumiendo los módulos core existentes sin modificarlos.

---

## 2. Definiciones

| Término | Definición |
|---------|-----------|
| **OAuth App** | GitHub OAuth App (no GitHub App). Usa `client_id` + `client_secret` para el Web Authorization Flow. |
| **JWT** | JSON Web Token firmado por el backend. Stateless, contiene identidad del usuario. Expira en 24h. |
| **PAT** | Personal Access Token de GitHub. Fallback manual cuando el backend no está disponible. |
| **Provider Key** | API key de un LLM provider (OpenAI, Anthropic, Google, etc.). Encriptada at-rest con AES-256-GCM. |
| **SSE** | Server-Sent Events. Canal unidireccional server→client para streaming de progreso de evals. |
| **Eval** | Una ejecución completa de `md_evals.engine` contra un SKILL.md + eval YAML. |
| **Config Hash** | Hash SHA-256 del contenido de SKILL.md + eval YAML + modelo + parámetros. Identifica configuraciones idénticas. |
| **Master Key** | Clave simétrica en env var (`MD_EVALS_MASTER_KEY`) usada para derivar claves de encriptación per-user. |
| **Masked Key** | Representación parcial de una API key para display seguro (e.g. `sk-...a3Fx`). |

---

## 3. Decisiones de Arquitectura (Resueltas)

Las siguientes decisiones fueron tomadas previamente y NO están abiertas a discusión en esta spec:

| Decisión | Elección | Alternativas descartadas |
|----------|----------|--------------------------|
| Estructura de repositorio | Monorepo: `apps/` dentro de md-evals | Repo separado |
| Auth method | GitHub OAuth App (client_id + client_secret) | GitHub App (más complejo, scopes innecesarios) |
| Streaming protocol | SSE (Server-Sent Events) | WebSocket (bidireccional innecesario) |
| Session management | JWT stateless (24h expiry) | Server-side sessions + Redis |
| Client state management | TanStack Query v5 + React Context | Zustand (innecesario para MVP) |
| Frontend framework | React 19 + Vite + Tailwind CSS 4 | — |
| Backend framework | FastAPI (Python 3.12+) | — |
| Database | PostgreSQL 16 | — |
| Frontend deploy | GitHub Pages via GitHub Actions | — |
| Backend deploy | Docker multi-stage + docker-compose | — |
| Charts | Recharts | — |

---

## 4. Requirements

### REQ-AUTH: Autenticación y Autorización

#### REQ-AUTH-01: OAuth Web Flow con GitHub OAuth App

**MUST**: El backend DEBE implementar el OAuth Web Authorization Flow de GitHub usando una GitHub OAuth App (NO GitHub App).

**MUST**: El flujo DEBE seguir esta secuencia:
1. Frontend redirige a `https://github.com/login/oauth/authorize` con `client_id`, `redirect_uri`, `scope=read:user`, y `state` (CSRF protection)
2. GitHub redirige a `GET /auth/callback` con `code` y `state`
3. Backend valida `state` (HMAC-signed, expira en 5 min — patrón GHAGGA)
4. Backend intercambia `code` por `access_token` via `POST https://github.com/login/oauth/access_token` usando `client_id` + `client_secret`
5. Backend llama `GET https://api.github.com/user` con el `access_token` para obtener perfil
6. Backend genera un JWT propio y lo retorna al frontend

**MUST**: El `state` parameter DEBE usar HMAC-SHA256 con un `STATE_SECRET` del servidor, formato `{timestamp_base36}.{hmac_hex}`, validando firma y expiración (5 minutos).

**MUST**: El scope OAuth DEBE ser `read:user` como mínimo. Si GitHub Models requiere scope adicional, se agrega solo ese.

**MUST NOT**: El `client_secret` NUNCA DEBE exponerse al frontend ni incluirse en el bundle JavaScript.

##### Scenario: REQ-AUTH-01-S1 — Happy path OAuth login
```
GIVEN  el usuario no está autenticado
  AND  el backend está disponible
WHEN   el usuario hace click en "Login with GitHub"
THEN   el frontend DEBE redirigir a https://github.com/login/oauth/authorize
  AND  la URL DEBE incluir client_id, redirect_uri, scope=read:user, state
  AND  state DEBE ser un HMAC-signed token generado por el backend
```

##### Scenario: REQ-AUTH-01-S2 — Callback exitoso
```
GIVEN  GitHub redirige a /auth/callback con code y state válidos
WHEN   el backend recibe la request
THEN   DEBE validar state (HMAC + expiración < 5 min)
  AND  DEBE intercambiar code por access_token con GitHub
  AND  DEBE obtener el perfil del usuario via GET /api.github.com/user
  AND  DEBE crear o actualizar el usuario en PostgreSQL
  AND  DEBE generar un JWT con los claims especificados en REQ-AUTH-02
  AND  DEBE redirigir al frontend con el JWT (via URL fragment o query param)
```

##### Scenario: REQ-AUTH-01-S3 — State inválido
```
GIVEN  GitHub redirige a /auth/callback
  AND  el state tiene HMAC inválido o está expirado
WHEN   el backend recibe la request
THEN   DEBE redirigir al frontend con error=invalid_state
  AND  NO DEBE intercambiar el code con GitHub
```

##### Scenario: REQ-AUTH-01-S4 — GitHub deniega acceso
```
GIVEN  el usuario cancela la autorización en GitHub
WHEN   GitHub redirige a /auth/callback con error=access_denied
THEN   el backend DEBE redirigir al frontend con error=access_denied
  AND  el frontend DEBE mostrar mensaje: "Login cancelado. Necesitás autorizar la app para continuar."
```

##### Scenario: REQ-AUTH-01-S5 — Code exchange falla
```
GIVEN  state es válido pero el code ya fue usado o es inválido
WHEN   el backend intenta intercambiar con GitHub
THEN   DEBE redirigir al frontend con error=exchange_failed
  AND  DEBE loguear el error server-side
```

---

#### REQ-AUTH-02: JWT Token

**MUST**: El JWT DEBE contener los siguientes claims:

| Claim | Tipo | Fuente | Descripción |
|-------|------|--------|-------------|
| `sub` | `string` | GitHub user ID (as string) | Subject — identifica al usuario |
| `github_user_id` | `int` | `user.id` de GitHub API | ID numérico de GitHub |
| `login` | `string` | `user.login` de GitHub API | Username de GitHub |
| `avatar_url` | `string` | `user.avatar_url` de GitHub API | URL del avatar |
| `exp` | `int` | Server timestamp + 24h | Expiración (Unix timestamp) |
| `iat` | `int` | Server timestamp | Issued at (Unix timestamp) |

**MUST**: El JWT DEBE firmarse con HS256 usando un `JWT_SECRET` del servidor (env var).

**MUST**: Expiración DEBE ser 24 horas desde la emisión.

**MUST NOT**: El JWT NO DEBE contener el `access_token` de GitHub ni ningún secret.

##### Scenario: REQ-AUTH-02-S1 — JWT contiene claims correctos
```
GIVEN  el OAuth flow completó exitosamente
  AND  GitHub retornó user.id=12345, user.login="testuser", user.avatar_url="https://..."
WHEN   el backend genera el JWT
THEN   el payload DEBE contener sub="12345", github_user_id=12345, login="testuser", avatar_url="https://..."
  AND  exp DEBE ser iat + 86400 (24h en segundos)
  AND  el token DEBE ser verificable con JWT_SECRET
```

##### Scenario: REQ-AUTH-02-S2 — JWT expirado
```
GIVEN  un JWT fue emitido hace más de 24 horas
WHEN   el frontend envía una request a /api/* con ese JWT
THEN   el backend DEBE retornar 401 Unauthorized
  AND  el body DEBE incluir error="token_expired"
  AND  el frontend DEBE redirigir al login
```

##### Scenario: REQ-AUTH-02-S3 — JWT con firma inválida
```
GIVEN  un JWT con payload válido pero firmado con un secret diferente
WHEN   el frontend envía una request a /api/* con ese JWT
THEN   el backend DEBE retornar 401 Unauthorized
  AND  el body DEBE incluir error="invalid_token"
```

---

#### REQ-AUTH-03: PAT Fallback

**MUST**: Si el backend no está disponible (network error, server down), el frontend DEBE mostrar un campo de input para ingresar un GitHub Personal Access Token (PAT) manualmente.

**MUST**: El PAT ingresado DEBE validarse llamando a `GET https://api.github.com/user` directamente desde el frontend.

**MUST**: El PAT DEBE almacenarse solo en memory (React state) durante la sesión activa. NO en localStorage, NO en cookies.

**MUST**: El PAT se envía en el header `Authorization: Bearer {pat}` en cada request directa a GitHub Models.

**MUST NOT**: En modo PAT fallback, las features que requieren backend (historial, provider keys encriptadas, SSE streaming) DEBEN estar deshabilitadas con mensaje informativo.

##### Scenario: REQ-AUTH-03-S1 — Fallback a PAT
```
GIVEN  el frontend intenta conectar al backend
  AND  el backend no responde (timeout > 5s o network error)
WHEN   se renderiza la página de login
THEN   DEBE mostrarse la opción "Usar Personal Access Token"
  AND  DEBE haber un campo de input para pegar el PAT
  AND  DEBE haber un link a la documentación de GitHub para crear un PAT
```

##### Scenario: REQ-AUTH-03-S2 — PAT inválido
```
GIVEN  el usuario ingresa un PAT inválido o expirado
WHEN   el frontend valida contra GitHub API
THEN   DEBE mostrar error "Token inválido o expirado. Verificá que tenga scope read:user."
  AND  NO DEBE almacenar el PAT
```

##### Scenario: REQ-AUTH-03-S3 — Features limitadas en modo PAT
```
GIVEN  el usuario está autenticado via PAT fallback
WHEN   navega a la sección de historial o provider keys
THEN   DEBE ver un mensaje: "Esta funcionalidad requiere el backend. Conectate al servidor para usar historial y gestión de API keys."
  AND  los controles DEBEN estar visualmente deshabilitados
```

---

#### REQ-AUTH-04: Logout

**MUST**: Logout DEBE limpiar:
1. JWT del estado de la aplicación
2. `localStorage` (token y datos de usuario)
3. `sessionStorage` (redirect intents)

**MUST**: Después de logout, el usuario DEBE ser redirigido a la página de login.

**MUST NOT**: Logout NO revoca el OAuth token en GitHub (OAuth Apps no soportan revocación simple). Solo limpia el estado local.

##### Scenario: REQ-AUTH-04-S1 — Logout completo
```
GIVEN  el usuario está autenticado
WHEN   hace click en "Logout"
THEN   localStorage DEBE estar limpio de tokens y datos de usuario
  AND  sessionStorage DEBE estar limpio de redirect intents
  AND  el estado React DEBE resetearse (user=null, token=null)
  AND  DEBE redirigir a /login
```

---

#### REQ-AUTH-05: JWT Middleware

**MUST**: Todas las rutas bajo `/api/*` DEBEN requerir un JWT válido en el header `Authorization: Bearer {jwt}`.

**MUST**: Las rutas `/auth/login` y `/auth/callback` DEBEN ser públicas (sin auth).

**MUST**: El middleware DEBE extraer `github_user_id` del JWT y ponerlo disponible en el request context para todos los handlers.

**MUST**: Responses 401 DEBEN incluir `WWW-Authenticate: Bearer` header.

##### Scenario: REQ-AUTH-05-S1 — Request sin token
```
GIVEN  una request a GET /api/eval/history sin header Authorization
WHEN   el middleware procesa la request
THEN   DEBE retornar 401 con body { "error": "missing_token" }
  AND  DEBE incluir header WWW-Authenticate: Bearer
```

---

### REQ-KEYS: Gestión de API Keys de Providers

#### REQ-KEYS-01: CRUD de Provider Keys

**MUST**: El frontend DEBE proveer una UI para agregar, ver (masked) y eliminar API keys de providers LLM.

**MUST**: Providers soportados: `openai`, `anthropic`, `google`, `github-models`. Extensible a otros.

**MUST**: GitHub Models DEBE usar el OAuth token del usuario directamente — NO requiere una key separada.

**MUST**: Al agregar una key, el frontend envía la key al backend via HTTPS. El backend encripta y guarda.

**MUST**: Al listar keys, el backend DEBE retornar solo la versión masked (e.g. `sk-...a3Fx` — prefijo conocido + últimos 4 caracteres).

**MUST NOT**: El backend NUNCA DEBE retornar la key completa en ningún endpoint. Solo se desencripta internamente al ejecutar evals.

##### Scenario: REQ-KEYS-01-S1 — Agregar key de OpenAI
```
GIVEN  el usuario está autenticado
  AND  navega a Settings > Provider Keys
WHEN   selecciona provider "OpenAI" e ingresa una API key "sk-proj-abc...xyz"
  AND  hace click en "Guardar"
THEN   el frontend DEBE enviar POST /api/providers con { provider: "openai", key: "sk-proj-abc...xyz" }
  AND  el backend DEBE validar la key (REQ-KEYS-02)
  AND  si válida, DEBE encriptarla (REQ-KEYS-03) y guardar en PostgreSQL
  AND  DEBE retornar { provider: "openai", key_hint: "sk-...xyz", validated_at: "..." }
```

##### Scenario: REQ-KEYS-01-S2 — Listar keys (nunca expone completa)
```
GIVEN  el usuario tiene keys guardadas para openai y anthropic
WHEN   el frontend solicita GET /api/providers
THEN   el response DEBE ser un array con:
       [
         { provider: "openai", key_hint: "sk-...a3Fx", validated_at: "2026-03-16T..." },
         { provider: "anthropic", key_hint: "sk-...r2Dz", validated_at: "2026-03-16T..." }
       ]
  AND  NO DEBE incluir la key completa en ningún campo
```

##### Scenario: REQ-KEYS-01-S3 — Eliminar key
```
GIVEN  el usuario tiene una key guardada para openai
WHEN   hace click en "Eliminar" en la key de OpenAI
  AND  confirma en el modal de confirmación
THEN   el frontend DEBE enviar DELETE /api/providers/openai
  AND  el backend DEBE eliminar la key encriptada de PostgreSQL
  AND  la UI DEBE actualizarse inmediatamente (optimistic update)
```

##### Scenario: REQ-KEYS-01-S4 — GitHub Models no necesita key
```
GIVEN  el usuario está autenticado via OAuth
WHEN   navega a Settings > Provider Keys
THEN   "GitHub Models" DEBE aparecer con badge "Disponible" (usa tu token OAuth)
  AND  NO DEBE mostrar campo de input para key
  AND  DEBE indicar que usa el token OAuth del usuario
```

---

#### REQ-KEYS-02: Validación de Key

**MUST**: Antes de guardar una key, el backend DEBE hacer una llamada de validación real a la API del provider.

**MUST**: Validaciones por provider:

| Provider | Endpoint de validación | Criterio de éxito |
|----------|------------------------|-------------------|
| `openai` | `GET https://api.openai.com/v1/models` | Status 200 |
| `anthropic` | `POST https://api.anthropic.com/v1/messages` (con prompt trivial) | Status 200 |
| `google` | `GET https://generativelanguage.googleapis.com/v1/models` | Status 200 |

**MUST**: Si la validación falla, el backend DEBE retornar 400 con un mensaje descriptivo y NO guardar la key.

**MUST**: La validación DEBE tener timeout de 10 segundos.

##### Scenario: REQ-KEYS-02-S1 — Key válida
```
GIVEN  el usuario envía una key de OpenAI válida
WHEN   el backend la valida contra GET /v1/models
  AND  OpenAI retorna 200
THEN   la key DEBE guardarse encriptada
  AND  validated_at DEBE setearse al timestamp actual
```

##### Scenario: REQ-KEYS-02-S2 — Key inválida
```
GIVEN  el usuario envía una key de OpenAI inválida
WHEN   el backend la valida contra GET /v1/models
  AND  OpenAI retorna 401
THEN   el backend DEBE retornar 400 con { error: "invalid_key", message: "La API key de OpenAI es inválida o fue revocada." }
  AND  la key NO DEBE guardarse
```

##### Scenario: REQ-KEYS-02-S3 — Provider no responde
```
GIVEN  el usuario envía una key de Anthropic
WHEN   el backend intenta validar pero Anthropic no responde (timeout > 10s)
THEN   el backend DEBE retornar 400 con { error: "validation_timeout", message: "No se pudo validar la key. El provider no respondió. Intentá de nuevo." }
  AND  la key NO DEBE guardarse
```

---

#### REQ-KEYS-03: Encriptación de Keys

**MUST**: Todas las API keys DEBEN encriptarse con AES-256-GCM antes de guardar en PostgreSQL.

**MUST**: Esquema de encriptación:
1. Master key: env var `MD_EVALS_MASTER_KEY` (256 bits, generado una vez)
2. Per-user key: derivado via HKDF (`HKDF(master_key, salt=user_id)`)
3. Cada key se encripta con nonce aleatorio de 12 bytes
4. Storage en columna BYTEA: `nonce (12B) || ciphertext || tag (16B)`

**MUST**: La librería `cryptography` de Python DEBE usarse para la implementación.

**MUST NOT**: La master key NUNCA DEBE estar en código fuente, base de datos, ni logs.

**MUST**: Si la master key cambia, DEBE existir un migration script que re-encripte todas las keys.

##### Scenario: REQ-KEYS-03-S1 — Encriptación at-rest
```
GIVEN  el usuario guarda una API key "sk-proj-abc123"
WHEN   el backend la persiste en PostgreSQL
THEN   la columna key_enc DEBE contener bytes (nonce || ciphertext || tag)
  AND  leer key_enc directamente de la DB NO DEBE revelar la key
  AND  solo desencriptando con HKDF(master_key, user_id) se recupera la key original
```

##### Scenario: REQ-KEYS-03-S2 — Master key no configurado
```
GIVEN  MD_EVALS_MASTER_KEY no está seteado como env var
WHEN   el backend inicia
THEN   DEBE fallar con error claro: "MD_EVALS_MASTER_KEY is required. Generate one with: openssl rand -hex 32"
  AND  NO DEBE iniciar el servidor
```

---

### REQ-EVAL: Ejecución de Evaluaciones

#### REQ-EVAL-01: Upload e Input

**MUST**: El frontend DEBE aceptar input de SKILL.md y eval YAML de dos formas:
1. **Drag & drop**: Arrastrar archivos sobre una zona de drop
2. **Paste/textarea**: Pegar contenido directamente en textareas

**MUST**: El frontend DEBE validar antes de enviar:
- SKILL.md: no vacío, contenido Markdown válido (no binario)
- Eval YAML: sintaxis YAML válida, estructura mínima reconocible (`tests:` key presente)

**MUST**: Límite de tamaño: SKILL.md ≤ 100KB, eval YAML ≤ 50KB.

##### Scenario: REQ-EVAL-01-S1 — Upload via drag & drop
```
GIVEN  el usuario está en la página de nueva eval
WHEN   arrastra un archivo "SKILL.md" y un archivo "eval.yaml" a la zona de drop
THEN   el frontend DEBE detectar los archivos
  AND  DEBE llenar las textareas con su contenido
  AND  DEBE mostrar los nombres de archivo como label
```

##### Scenario: REQ-EVAL-01-S2 — YAML inválido
```
GIVEN  el usuario pega contenido YAML con sintaxis inválida (tabs mezclados con spaces, etc.)
WHEN   intenta ejecutar la eval
THEN   el frontend DEBE mostrar error inline: "YAML inválido: {detalle del error de parseo}"
  AND  DEBE resaltar la línea con el error si es posible
  AND  NO DEBE enviar la request al backend
```

##### Scenario: REQ-EVAL-01-S3 — SKILL.md > 100KB
```
GIVEN  el usuario sube un SKILL.md de 150KB
WHEN   el frontend procesa el archivo
THEN   DEBE mostrar error: "SKILL.md excede el límite de 100KB (150KB). Reducí el contenido."
  AND  NO DEBE enviar al backend
```

##### Scenario: REQ-EVAL-01-S4 — YAML sin key "tests"
```
GIVEN  el usuario pega YAML válido pero sin la key "tests"
WHEN   intenta ejecutar la eval
THEN   DEBE mostrar error: "El eval YAML debe contener una sección 'tests' con al menos un test case."
```

---

#### REQ-EVAL-02: Ejecución en Backend

**MUST**: El backend DEBE ejecutar evaluaciones importando directamente los módulos de md-evals:

```python
from md_evals.models import EvalConfig
from md_evals.engine import ExecutionEngine
from md_evals.llm import LLMAdapter
from md_evals.evaluator import EvaluatorEngine
from md_evals.metrics import build_usage_metrics
```

**MUST**: El backend es un **consumidor** de md-evals — NO DEBE modificar los módulos core.

**MUST**: La ejecución DEBE ser asíncrona (background task) para no bloquear el endpoint HTTP.

**MUST**: La eval DEBE tener timeout configurable (default: 10 minutos). Si se excede, status → `timeout`.

**MUST**: El backend DEBE manejar excepciones del engine sin crashear — status → `failed` con error message.

##### Scenario: REQ-EVAL-02-S1 — Ejecución exitosa
```
GIVEN  el usuario envía POST /api/eval/run con skill_content y eval_yaml válidos
  AND  tiene una key configurada para el provider/modelo requerido
WHEN   el backend recibe la request
THEN   DEBE crear un registro en evaluations con status="running"
  AND  DEBE retornar 202 Accepted con { eval_id: "uuid", status: "running" }
  AND  DEBE iniciar la ejecución en background
  AND  al completar, DEBE actualizar status="completed" y guardar resultados
```

##### Scenario: REQ-EVAL-02-S2 — Provider key no disponible
```
GIVEN  el eval YAML requiere modelo "gpt-4o"
  AND  el usuario no tiene key de OpenAI configurada
  AND  el modelo no está disponible en GitHub Models
WHEN   el backend intenta ejecutar
THEN   DEBE retornar 400 con { error: "missing_provider_key", message: "No tenés una API key configurada para OpenAI. Agregala en Settings > Provider Keys." }
```

##### Scenario: REQ-EVAL-02-S3 — Eval timeout
```
GIVEN  una eval está corriendo
  AND  lleva más de 10 minutos (default timeout)
WHEN   el timeout se alcanza
THEN   el backend DEBE cancelar la ejecución
  AND  status DEBE actualizarse a "timeout"
  AND  DEBE guardar resultados parciales (los test cases que completaron antes del timeout)
  AND  el SSE stream DEBE emitir evento { type: "eval_timeout", completed: N, total: M }
```

##### Scenario: REQ-EVAL-02-S4 — Engine exception
```
GIVEN  el engine de md-evals lanza una excepción inesperada durante la ejecución
WHEN   el backend captura la excepción
THEN   status DEBE actualizarse a "failed"
  AND  error_message DEBE contener el tipo de excepción y mensaje (sin stack trace en la DB)
  AND  el SSE stream DEBE emitir evento { type: "eval_error", message: "..." }
  AND  el error completo DEBE loguearse server-side
```

---

#### REQ-EVAL-03: Streaming de Progreso via SSE

**MUST**: El endpoint `GET /api/eval/{id}/stream` DEBE retornar un SSE stream con Content-Type `text/event-stream`.

**MUST**: Eventos SSE definidos:

| Event type | Payload | Cuándo |
|------------|---------|--------|
| `eval_started` | `{ eval_id, total_tests, model, provider }` | Al iniciar la eval |
| `test_started` | `{ test_index, test_name, treatment }` | Al iniciar cada test case |
| `test_completed` | `{ test_index, test_name, treatment, passed, score, duration_ms }` | Al completar cada test case |
| `eval_completed` | `{ eval_id, status, total_passed, total_tests, duration_ms }` | Al completar toda la eval |
| `eval_error` | `{ eval_id, error, message }` | Si la eval falla |
| `eval_timeout` | `{ eval_id, completed, total }` | Si la eval excede el timeout |

**MUST**: El stream DEBE cerrarse automáticamente después de `eval_completed`, `eval_error`, o `eval_timeout`.

**MUST**: El SSE endpoint DEBE requerir JWT (misma auth que otros endpoints /api/*).

**MUST**: Si el cliente se desconecta, el backend DEBE continuar la eval (no cancelar).

##### Scenario: REQ-EVAL-03-S1 — Streaming happy path
```
GIVEN  el usuario lanzó una eval con 5 test cases
WHEN   el frontend se conecta a GET /api/eval/{id}/stream
THEN   DEBE recibir eventos en orden:
       1. eval_started { total_tests: 5 }
       2. test_started { test_index: 0, test_name: "test_1" }
       3. test_completed { test_index: 0, passed: true }
       ...repite para cada test...
       N. eval_completed { total_passed: 4, total_tests: 5 }
  AND  la conexión SSE DEBE cerrarse después de eval_completed
```

##### Scenario: REQ-EVAL-03-S2 — Reconexión SSE
```
GIVEN  el frontend pierde conexión SSE a mitad de una eval
WHEN   se reconecta a GET /api/eval/{id}/stream
THEN   si la eval sigue corriendo, DEBE recibir los eventos restantes
  AND  si la eval ya terminó, DEBE recibir un evento eval_completed con los resultados finales
```

##### Scenario: REQ-EVAL-03-S3 — Frontend no conecta SSE
```
GIVEN  el usuario lanza una eval pero cierra el browser
WHEN   la eval sigue corriendo en background
THEN   el backend DEBE completar la eval normalmente
  AND  los resultados DEBEN estar disponibles en GET /api/eval/{id} cuando el usuario vuelva
```

---

#### REQ-EVAL-04: Persistencia de Resultados

**MUST**: Cada eval completada DEBE guardarse en PostgreSQL con:
- `evaluations` table: metadata, skill content, yaml content, config (JSONB), status, timestamps
- `eval_results` table: un row por execution result (treatment × test), con métricas en JSONB

**MUST**: Cada eval DEBE tener un `config_hash` (SHA-256 de skill_content + eval_yaml + model + params) para identificar runs con configuración idéntica.

**MUST**: Resultados DEBEN incluir `cost_metrics` y `context_metrics` como JSONB (reutilizando el sistema de métricas implementado en md-evals core).

**MUST**: `user_id` DEBE estar presente en cada eval para aislamiento de datos entre usuarios.

##### Scenario: REQ-EVAL-04-S1 — Resultados persisten
```
GIVEN  una eval completó exitosamente con 3 test cases, 2 treatments
WHEN   el backend guarda los resultados
THEN   DEBE existir 1 row en evaluations con status="completed"
  AND  DEBE existir 6 rows en eval_results (3 tests × 2 treatments)
  AND  cada eval_result DEBE tener cost_metrics y context_metrics como JSONB no-null
```

---

### REQ-DASH: Dashboard de Resultados

#### REQ-DASH-01: Vista de Resultados

**MUST**: Al completar una eval, el dashboard DEBE mostrar:
1. **Summary card**: pass rate, total tests, passed/failed count, duración total
2. **Results table**: cada test case con treatment, pass/fail, score, duration
3. **Bar chart** (Recharts): pass rate por treatment (e.g. CONTROL vs WITH_SKILL)
4. **Line chart** (Recharts): tokens usados por test case
5. **Gauge/radial chart**: context utilization percentage

**MUST**: Los datos de `cost_metrics` y `context_metrics` DEBEN mapearse a los gráficos:
- Cost breakdown: prompt_tokens vs completion_tokens (stacked bar)
- Context utilization: gauge con umbrales de truncation_risk (green <70%, yellow 70-90%, red ≥90%)

##### Scenario: REQ-DASH-01-S1 — Dashboard con resultados completos
```
GIVEN  una eval completó con 10 tests, treatments CONTROL y WITH_SKILL
  AND  pass rates: CONTROL=60%, WITH_SKILL=80%
WHEN   el frontend renderiza el dashboard
THEN   DEBE mostrar summary card con "80% pass rate (WITH_SKILL)"
  AND  DEBE mostrar bar chart con 2 barras: CONTROL=60%, WITH_SKILL=80%
  AND  DEBE mostrar tabla con 20 rows (10 tests × 2 treatments)
  AND  los gráficos DEBEN usar Recharts
```

##### Scenario: REQ-DASH-01-S2 — Métricas de contexto
```
GIVEN  una eval completó y context_utilization_pct = 45.2%
WHEN   el frontend renderiza el gauge de context
THEN   el gauge DEBE mostrar 45.2% con color verde (< 70% = low risk)
  AND  DEBE mostrar label "Context Utilization: 45.2% — Low Risk"
```

---

#### REQ-DASH-02: Historial de Evaluaciones

**MUST**: El endpoint `GET /api/eval/history` DEBE retornar evaluaciones pasadas del usuario autenticado.

**MUST**: Soportar filtros:
- `date_from` / `date_to`: rango de fechas (ISO 8601)
- `model`: filtrar por modelo usado
- `status`: filtrar por status (completed, failed, timeout)

**MUST**: Paginación: `page` (default 1) + `per_page` (default 20, max 100).

**MUST**: Ordenamiento: por `created_at` descendente (más recientes primero).

##### Scenario: REQ-DASH-02-S1 — Listar historial con filtros
```
GIVEN  el usuario tiene 50 evals completadas
WHEN   solicita GET /api/eval/history?model=gpt-4o&status=completed&page=1&per_page=10
THEN   DEBE retornar las 10 evals más recientes que usen gpt-4o y estén completed
  AND  el response DEBE incluir { items: [...], total: N, page: 1, per_page: 10, pages: ceil(N/10) }
```

##### Scenario: REQ-DASH-02-S2 — Historial vacío
```
GIVEN  el usuario no tiene evals previas
WHEN   solicita GET /api/eval/history
THEN   DEBE retornar { items: [], total: 0, page: 1, per_page: 20, pages: 0 }
  AND  el frontend DEBE mostrar estado vacío con CTA "Ejecutá tu primera evaluación"
```

---

#### REQ-DASH-03: Comparación Side-by-Side

**MUST**: El usuario DEBE poder seleccionar 2 evals del historial para comparar side-by-side.

**MUST**: La comparación DEBE mostrar:
- Pass rates de ambas evals lado a lado
- Delta de métricas (tokens, cost, context utilization)
- Resultados por test case con diff visual (pass→fail = rojo, fail→pass = verde)

##### Scenario: REQ-DASH-03-S1 — Comparar dos evals
```
GIVEN  el usuario selecciona eval A (pass rate 60%) y eval B (pass rate 80%)
WHEN   el frontend renderiza la comparación
THEN   DEBE mostrar ambas pass rates lado a lado
  AND  DEBE mostrar delta "+20% improvement"
  AND  DEBE mostrar tabla de test cases con diff:
       - Test que pasó en B pero no en A → ícono verde "Improved"
       - Test que pasó en A pero no en B → ícono rojo "Regressed"
       - Test igual en ambos → ícono gris "Unchanged"
```

---

### REQ-API: Endpoints REST

#### REQ-API-01: Tabla de Endpoints

**MUST**: El backend DEBE exponer los siguientes endpoints:

| Method | Path | Auth | Descripción |
|--------|------|------|-------------|
| `GET` | `/auth/login` | No | Redirige a GitHub OAuth authorize |
| `GET` | `/auth/callback` | No | Procesa OAuth callback, retorna JWT |
| `POST` | `/api/eval/run` | JWT | Lanza una nueva eval (202 Accepted) |
| `GET` | `/api/eval/{id}` | JWT | Obtiene resultados de una eval |
| `GET` | `/api/eval/{id}/stream` | JWT | SSE stream de progreso |
| `GET` | `/api/eval/history` | JWT | Lista evals pasadas con filtros |
| `GET` | `/api/providers` | JWT | Lista provider keys (masked) |
| `POST` | `/api/providers` | JWT | Agrega una provider key |
| `DELETE` | `/api/providers/{provider}` | JWT | Elimina una provider key |
| `POST` | `/api/providers/validate` | JWT | Valida una key sin guardar |
| `GET` | `/api/settings` | JWT | Obtiene settings del usuario |
| `PUT` | `/api/settings` | JWT | Actualiza settings del usuario |
| `GET` | `/health` | No | Health check |

**MUST**: Todos los endpoints bajo `/api/*` DEBEN requerir JWT válido (REQ-AUTH-05).

**MUST**: Responses DEBEN usar JSON con `Content-Type: application/json` (excepto SSE).

**MUST**: Errores DEBEN seguir formato consistente: `{ "error": "error_code", "message": "Human readable message" }`.

---

#### REQ-API-02: CORS

**MUST**: CORS DEBE estar configurado para permitir solo los siguientes origins:

| Environment | Allowed Origins |
|-------------|-----------------|
| Production | `https://{username}.github.io` (GitHub Pages URL) |
| Development | `http://localhost:5173` (Vite dev server) |

**MUST**: Allowed methods: `GET, POST, PUT, DELETE, OPTIONS`.

**MUST**: Allowed headers: `Authorization, Content-Type`.

**MUST**: `credentials: true` para envío de headers de auth.

**MUST NOT**: CORS NO DEBE ser `*` (wildcard) en producción.

##### Scenario: REQ-API-02-S1 — CORS en producción
```
GIVEN  el frontend está deployado en GitHub Pages (https://jnzader.github.io/md-evals)
WHEN   envía un POST a https://api.example.com/api/eval/run
THEN   el backend DEBE incluir Access-Control-Allow-Origin: https://jnzader.github.io
  AND  DEBE incluir Access-Control-Allow-Credentials: true
```

##### Scenario: REQ-API-02-S2 — Origin no permitido
```
GIVEN  una request llega desde https://malicious-site.com
WHEN   el backend evalúa CORS
THEN   NO DEBE incluir Access-Control-Allow-Origin header
  AND  el browser DEBE bloquear la response
```

---

#### REQ-API-03: Rate Limiting

**MUST**: El endpoint `POST /api/eval/run` DEBE tener rate limit de 10 evals por hora por usuario.

**MUST**: El rate limit DEBE retornar 429 Too Many Requests con header `Retry-After`.

**MAY**: Otros endpoints PUEDEN tener rate limits más generosos (100 requests/min).

##### Scenario: REQ-API-03-S1 — Rate limit alcanzado
```
GIVEN  el usuario ejecutó 10 evals en la última hora
WHEN   intenta ejecutar la eval #11
THEN   el backend DEBE retornar 429 Too Many Requests
  AND  body DEBE incluir { error: "rate_limited", message: "Límite de 10 evals por hora alcanzado.", retry_after: N }
  AND  header Retry-After DEBE contener los segundos restantes
```

---

### REQ-DEPLOY: Deployment

#### REQ-DEPLOY-01: Frontend en GitHub Pages

**MUST**: El frontend DEBE deployarse en GitHub Pages via GitHub Actions workflow.

**MUST**: El workflow DEBE:
1. Instalar dependencias (`pnpm install`)
2. Build (`pnpm build`)
3. Deploy a GitHub Pages (branch `gh-pages` o GitHub Pages Action)

**MUST**: El `base` path de Vite DEBE configurarse para el subdirectorio de GitHub Pages (e.g. `/md-evals/`).

**MUST**: La URL del backend DEBE ser configurable via env var en build time (`VITE_API_URL`).

##### Scenario: REQ-DEPLOY-01-S1 — Build y deploy exitoso
```
GIVEN  se hace push a la rama main
WHEN   el GitHub Actions workflow corre
THEN   DEBE instalar deps, build, y deploy a GitHub Pages
  AND  el frontend DEBE ser accesible en https://{username}.github.io/md-evals/
  AND  DEBE conectar al backend configurado en VITE_API_URL
```

---

#### REQ-DEPLOY-02: Backend en Docker

**MUST**: El backend DEBE tener un `Dockerfile` multi-stage:
- Stage 1 (builder): instalar dependencias, copiar código
- Stage 2 (runtime): imagen slim, solo runtime, non-root user

**MUST**: `docker-compose.yml` DEBE levantar:
- `api`: FastAPI app (expone puerto 8000)
- `db`: PostgreSQL 16 (volumen persistente)

**MUST**: Variables de entorno documentadas:

| Variable | Requerida | Descripción |
|----------|-----------|-------------|
| `GITHUB_CLIENT_ID` | Sí | OAuth App client ID |
| `GITHUB_CLIENT_SECRET` | Sí | OAuth App client secret |
| `JWT_SECRET` | Sí | Secret para firmar JWTs |
| `STATE_SECRET` | Sí | Secret para HMAC del state parameter |
| `MD_EVALS_MASTER_KEY` | Sí | Master key para encriptar API keys |
| `DATABASE_URL` | Sí | PostgreSQL connection string |
| `CORS_ORIGINS` | Sí | Comma-separated allowed origins |
| `VITE_API_URL` | Build time | URL del backend para el frontend |

**MUST**: El Dockerfile DEBE usar un non-root user para el runtime.

**MUST NOT**: Ningún secret DEBE tener valor default en el código.

##### Scenario: REQ-DEPLOY-02-S1 — Docker compose up
```
GIVEN  docker-compose.yml existe con services api y db
  AND  todas las env vars requeridas están seteadas
WHEN   se ejecuta docker compose up
THEN   PostgreSQL DEBE iniciar y crear la DB
  AND  Alembic DEBE correr migraciones automáticamente
  AND  FastAPI DEBE iniciar en puerto 8000
  AND  GET /health DEBE retornar 200 { status: "ok" }
```

##### Scenario: REQ-DEPLOY-02-S2 — Missing env var
```
GIVEN  GITHUB_CLIENT_SECRET no está seteado
WHEN   el backend intenta iniciar
THEN   DEBE fallar con error claro listando la variable faltante
  AND  NO DEBE iniciar el servidor
```

---

### REQ-COMPAT: Backward Compatibility

#### REQ-COMPAT-01: CLI Sin Cambios

**MUST**: La CLI existente (`md-evals run`, `md-evals lint`) DEBE seguir funcionando sin ningún cambio.

**MUST**: Agregar la web NO DEBE modificar, mover, ni renombrar ningún módulo en `md_evals/`.

**MUST**: Los imports existentes de md-evals (por la CLI y por consumers externos) DEBEN seguir funcionando.

**MUST**: El `pyproject.toml` del paquete core NO DEBE cambiar por la adición de la web.

##### Scenario: REQ-COMPAT-01-S1 — CLI funciona post-web
```
GIVEN  se agregó apps/ al repo con frontend y backend
  AND  NO se tocó nada en md_evals/
WHEN   un usuario ejecuta md-evals run my-skill/ --model gpt-4o
THEN   DEBE funcionar exactamente igual que antes
  AND  NO DEBE haber import errors ni side effects de la web
```

##### Scenario: REQ-COMPAT-01-S2 — Parity test
```
GIVEN  el mismo SKILL.md + eval.yaml + modelo + parámetros
WHEN   se ejecuta via CLI y via web
THEN   los resultados numéricos DEBEN ser idénticos:
       - Pass/fail por test case
       - Scores por evaluator
       - cost_metrics (si feature flag enabled)
       - context_metrics (si feature flag enabled)
```

#### REQ-COMPAT-02: Estructura de Monorepo

**MUST**: La estructura de directorios DEBE ser:

```
md-evals/
├── md_evals/              # Core (INTOCABLE)
├── apps/
│   ├── web/               # React SPA (frontend)
│   │   ├── src/
│   │   ├── package.json
│   │   ├── vite.config.ts
│   │   └── ...
│   └── server/            # FastAPI (backend)
│       ├── app/
│       │   ├── api/       # Routers
│       │   ├── core/      # Config, security, encryption
│       │   ├── db/        # SQLAlchemy models, migrations
│       │   ├── services/  # Business logic (wraps md_evals)
│       │   └── main.py
│       ├── alembic/
│       ├── Dockerfile
│       └── pyproject.toml
├── docker-compose.yml
├── openspec/
├── pyproject.toml         # Core package (sin cambios)
└── ...
```

**MUST**: `apps/server/` DEBE tener su propio `pyproject.toml` con dependencia a `md-evals` (local path o PyPI).

**MUST**: `apps/web/` DEBE ser un proyecto Node.js independiente con su propio `package.json`.

---

## 5. Edge Cases

### EC-01: Sin conexión a internet durante OAuth
```
GIVEN  el usuario hace click en "Login with GitHub"
  AND  no tiene conexión a internet
WHEN   el browser intenta redirigir a github.com
THEN   el browser mostrará su error de red nativo
  AND  el frontend DEBE detectar el error al volver y mostrar "Sin conexión. Verificá tu internet e intentá de nuevo."
```

### EC-02: OAuth denegado por el usuario
```
GIVEN  el usuario llega a la página de autorización de GitHub
WHEN   hace click en "Deny" o cierra la ventana
THEN   GitHub redirige con error=access_denied
  AND  el frontend DEBE mostrar "Necesitás autorizar la app para usar md-evals web. Tu código no se comparte."
  AND  DEBE ofrecer botón "Intentar de nuevo"
```

### EC-03: Key de provider inválida al ejecutar eval
```
GIVEN  el usuario tiene una key de OpenAI que fue válida al guardarla
  AND  la key fue revocada en OpenAI después
WHEN   intenta ejecutar una eval con modelo OpenAI
THEN   el backend DEBE capturar el error 401 del provider
  AND  DEBE retornar status="failed" con error="provider_auth_failed"
  AND  el SSE DEBE emitir eval_error con message="La API key de OpenAI fue revocada. Actualizala en Settings."
```

### EC-04: Eval timeout
```
GIVEN  una eval con 20 test cases y un provider lento
  AND  el timeout configurado es 10 minutos
WHEN   pasan 10 minutos sin completar
THEN   el backend DEBE cancelar la ejecución
  AND  DEBE guardar resultados parciales (los completados)
  AND  status DEBE ser "timeout"
  AND  el frontend DEBE mostrar "Eval excedió el tiempo límite. Se guardaron N/20 resultados parciales."
```

### EC-05: SKILL.md extremadamente largo (> 400 líneas)
```
GIVEN  el usuario sube un SKILL.md de 450 líneas
WHEN   el frontend procesa el archivo
THEN   DEBE mostrar warning (no error): "Este SKILL.md es muy largo (450 líneas). Skills largos pueden consumir mucho context window y aumentar costos."
  AND  DEBE permitir continuar (no bloquear)
  AND  el gauge de context utilization DEBE reflejar el uso real
```

### EC-06: YAML con modelo no soportado
```
GIVEN  el eval YAML especifica model: "modelo-inexistente-xyz"
WHEN   el backend intenta ejecutar
THEN   DEBE retornar 400 con error="unsupported_model"
  AND  message DEBE listar los modelos disponibles para el usuario
```

### EC-07: Rate limit de GitHub Models
```
GIVEN  el usuario usa GitHub Models con su OAuth token
  AND  ha hecho muchas requests en poco tiempo
WHEN   GitHub Models retorna 429
THEN   el backend DEBE capturar el 429
  AND  DEBE pausar y reintentar con exponential backoff (max 3 retries)
  AND  si sigue fallando, DEBE reportar "rate_limited" al usuario via SSE
  AND  DEBE sugerir "Considerá usar tu propia API key de OpenAI/Anthropic para evitar rate limits."
```

### EC-08: Dos evals simultáneas del mismo usuario
```
GIVEN  el usuario tiene una eval corriendo (status="running")
WHEN   intenta lanzar otra eval
THEN   DEBE permitirlo (evals son independientes)
  AND  DEBE mostrar ambas evals activas en la UI
  AND  cada una con su propio SSE stream
  AND  máximo 3 evals simultáneas por usuario (REQ-API-03 aplica)
```

### EC-09: Backend reinicia durante una eval
```
GIVEN  una eval está corriendo en background
WHEN   el backend se reinicia (deploy, crash, etc.)
THEN   la eval en progreso DEBE quedar con status="running" en la DB
  AND  al reiniciar, un job de cleanup DEBE detectar evals "running" > 15 minutos
  AND  DEBE marcarlas como status="failed" con error="server_restarted"
```

### EC-10: Concurrent key update durante eval
```
GIVEN  una eval está corriendo con la key de OpenAI
  AND  el usuario elimina la key de OpenAI mientras la eval corre
WHEN   la eval intenta usar la key para el siguiente test case
THEN   DEBE fallar gracefully para ese test case
  AND  los test cases que ya completaron DEBEN mantenerse
  AND  status DEBE ser "failed" con error="key_deleted_during_eval"
```

---

## 6. Acceptance Criteria

Checklist verificable. Cada item es un test que DEBE pasar.

### Auth
- [ ] **AC-01**: OAuth login redirige a GitHub con client_id, scope=read:user, y state HMAC-signed.
- [ ] **AC-02**: Callback valida state (HMAC + expiration), intercambia code, genera JWT con claims correctos.
- [ ] **AC-03**: JWT contiene github_user_id, login, avatar_url, exp (iat + 24h).
- [ ] **AC-04**: JWT expirado retorna 401 con error="token_expired".
- [ ] **AC-05**: Request sin JWT a /api/* retorna 401 con error="missing_token".
- [ ] **AC-06**: PAT fallback disponible cuando backend no responde. PAT solo en memory, no localStorage.
- [ ] **AC-07**: Logout limpia localStorage + sessionStorage + React state. Redirige a /login.

### Provider Keys
- [ ] **AC-08**: POST /api/providers guarda key encriptada AES-256-GCM con HKDF per-user.
- [ ] **AC-09**: GET /api/providers retorna solo key_hint (masked), nunca la key completa.
- [ ] **AC-10**: Key se valida contra API real del provider antes de guardar. Key inválida → 400.
- [ ] **AC-11**: DELETE /api/providers/{provider} elimina la key de la DB.
- [ ] **AC-12**: GitHub Models no necesita key extra — usa OAuth token del usuario.
- [ ] **AC-13**: Server no inicia si MD_EVALS_MASTER_KEY no está configurado.

### Eval Execution
- [ ] **AC-14**: POST /api/eval/run retorna 202 con eval_id. Ejecución en background.
- [ ] **AC-15**: Backend importa md_evals.engine directamente (no subprocess, no CLI wrapper).
- [ ] **AC-16**: SSE stream emite eval_started, test_started, test_completed, eval_completed en orden.
- [ ] **AC-17**: Eval timeout (default 10 min) → status="timeout" + resultados parciales guardados.
- [ ] **AC-18**: Engine exception → status="failed" + error logueado server-side.
- [ ] **AC-19**: Frontend valida SKILL.md (≤100KB, no vacío) y YAML (sintaxis, key "tests") antes de enviar.
- [ ] **AC-20**: Drag & drop y paste/textarea funcionan como input.

### Dashboard
- [ ] **AC-21**: Dashboard muestra pass rate, tabla de resultados, bar chart, line chart, context gauge.
- [ ] **AC-22**: Gráficos usan Recharts con datos de cost_metrics y context_metrics.
- [ ] **AC-23**: Context gauge muestra colores por truncation_risk (green/yellow/red).
- [ ] **AC-24**: Historial paginado con filtros por fecha, modelo, status. Default: 20 per page.
- [ ] **AC-25**: Comparación side-by-side de 2 evals con delta de métricas y diff de test results.

### API
- [ ] **AC-26**: Todos los endpoints de la tabla REQ-API-01 existen y retornan el formato especificado.
- [ ] **AC-27**: CORS configurado para GitHub Pages origin + localhost. NO wildcard en producción.
- [ ] **AC-28**: Rate limit: 10 evals/hora/usuario. 429 con Retry-After header.
- [ ] **AC-29**: Errores en formato consistente: { error: "code", message: "Human readable" }.

### Deploy
- [ ] **AC-30**: Frontend build + deploy a GitHub Pages via GitHub Actions.
- [ ] **AC-31**: docker-compose up levanta API + PostgreSQL. Health check en /health retorna 200.
- [ ] **AC-32**: Dockerfile usa multi-stage build y non-root user.
- [ ] **AC-33**: Missing env var → servidor no inicia con error descriptivo.

### Backward Compatibility
- [ ] **AC-34**: CLI `md-evals run` funciona sin cambios después de agregar apps/.
- [ ] **AC-35**: Ningún archivo en md_evals/ fue modificado.
- [ ] **AC-36**: Parity test: mismo input via CLI y web produce resultados numéricos idénticos.

### Security
- [ ] **AC-37**: client_secret nunca aparece en el frontend bundle (verificado en CI con grep).
- [ ] **AC-38**: API keys nunca se retornan completas en ningún endpoint.
- [ ] **AC-39**: JWT_SECRET, STATE_SECRET, MD_EVALS_MASTER_KEY sin valores default en código.
- [ ] **AC-40**: HTTPS required en producción para todos los endpoints.

---

## 7. Fuera de Scope

Los siguientes items están explícitamente excluidos de esta spec (MVP):

- Mobile-specific UI (responsive sí, app nativa no)
- Admin panel / user management (single-user-per-account, no roles)
- Billing / paid tiers
- Self-hosted frontend (solo GitHub Pages)
- Templates de eval YAML pre-armados
- URLs públicas para compartir resultados
- Webhook triggers para evals automáticas
- Multi-user teams / workspaces
- Scheduled evals (cron)
- Export a CSV/PDF
- Refresh tokens (JWT de 24h, re-login al expirar)
- Orquestador real en la web (se usa lo que md-evals core ya soporta)
