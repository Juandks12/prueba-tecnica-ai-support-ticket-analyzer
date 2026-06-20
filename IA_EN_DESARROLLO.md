# 🤖 Uso de Inteligencia Artificial Durante el Desarrollo

Se adoptó un enfoque de **Desarrollo Aumentado por IA** usando las siguientes
herramientas:

| Herramienta | Modelo base | Rol en el desarrollo |
|---|---|---|
| **OpenCode** | DeepSeek V4 Pro | Agente principal: análisis de código, debugging, implementación de features, refactorización, documentación |
| **Gemini** | gemini-3.5-flash | Bootstrapping inicial del proyecto: estructura FastAPI, parser de fechas, consultas SQLAlchemy |
| **DeepSeek** | deepseek-chat | Proveedor LLM del producto: enriquecimiento de tickets y chat RAG |

---

## Tareas concretas donde se usó IA

### 1. Estructuración inicial del backend

**Herramienta:** Gemini

Gemini generó el esqueleto del proyecto FastAPI con rutas, modelos Pydantic, ORM de
SQLAlchemy, el script de ingesta y la integración inicial con Gemini y OpenAI.
Se validó manualmente la resolución de rutas de archivos en Docker vs ejecución
local, la configuración de CORS y la inicialización condicional de los SDKs de
LLM (evitando imports fallidos cuando las API keys están vacías).

### 2. Parser de fechas multi-formato y normalización de datos

**Herramienta:** Gemini

Gemini diseñó la expresión regular para interpretar fechas escritas en español
("19 de diciembre 2020", "20 de mayo 2021") junto con formatos numéricos
estándar. También implementó la normalización de prioridades (P4 → Low,
Critical → Critical), categorías y limpieza de correos electrónicos. Se validó
manualmente contra los 400 registros reales del CSV, verificando que todos los
formatos de fecha, prioridades inconsistentes y valores nulos se procesaran
correctamente.

### 3. Diseño del dashboard (CSS vanilla)

**Herramienta:** Gemini

Gemini definió la paleta de colores HSL, el sistema de glassmorphism con
fondos semitransparentes, efectos de blur y transiciones CSS. Se ajustó
manualmente el diseño responsivo (Grid/Flexbox), los estilos de la tabla de
tickets, el modal de detalle y la integración con Chart.js para evitar
colisiones de canvas al refrescar datos en tiempo real.

### 4. Integración de DeepSeek como proveedor LLM

**Herramienta:** OpenCode

OpenCode implementó la inicialización del cliente de DeepSeek usando el SDK de
OpenAI apuntando a `https://api.deepseek.com`, los branches en
`enrich_ticket()` y `ask_question()` con el modelo `deepseek-chat`, y el
sistema de limpieza de bloques markdown en respuestas JSON. Se validó
manualmente contra la API real verificando respuestas JSON válidas, correcto
parseo de los 5 campos enriquecidos (categoría, prioridad, resumen, sentimiento,
equipo) y el correcto funcionamiento del límite de 40 tickets con IA real + 360
con mock.

### 5. Corrección de incompatibilidad de versiones

**Herramienta:** OpenCode

OpenCode diagnosticó el error `Client.__init__() got an unexpected keyword
argument 'proxies'` causado por la incompatibilidad entre `openai==1.14.1` (que
pasa el argumento `proxies` al crear el cliente HTTP) y `httpx>=0.28` (que
eliminó ese parámetro). Se actualizó `openai>=1.55.0` en `requirements.txt`,
se reconstruyó la imagen Docker y se verificó que los tres proveedores
(Gemini, OpenAI, DeepSeek) funcionaran sin errores de inicialización.

### 6. Sistema de toggle Mock/DeepSeek en el chat

**Herramienta:** OpenCode

OpenCode diseñó e implementó el parámetro `force_provider` en
`ai_service.ask_question()`, el campo opcional `provider` en el modelo
`QuestionRequest` de FastAPI, el componente toggle en HTML/CSS/JS con
animaciones de deslizamiento, y el listener que actualiza el indicador
`LLM: Mock` / `LLM: DeepSeek` en el header del dashboard. Se validó
manualmente la comunicación completa frontend → Nginx → backend → DeepSeek,
el cambio en tiempo real entre mock y real sin modificar `.env`, y la correcta
actualización del mensaje "Consultando con Mock..." / "Consultando con
DeepSeek...".

### 7. Reorganización de la estructura del proyecto

**Herramienta:** OpenCode

OpenCode analizó la estructura de carpetas y propuso:
- Unificar la base de datos en `backend/tickets.db` eliminando carpetas `db/`
  duplicadas
- Mover `tickets.csv` y `diccionario-de-datos.md` a `dataset/` como indica
  `prueba-tecnica.md`
- Eliminar el volumen `db_data` del `docker-compose.yml` y simplificar la
  configuración de `DATABASE_URL`
- Remover `ANTHROPIC_API_KEY` sin implementar y `version: '3.8'` obsoleto

Se validó manualmente que la ingesta, el dashboard y todos los endpoints
funcionaran correctamente tras cada cambio estructural.

### 8. Documentación integral

**Herramienta:** OpenCode y Manual

OpenCode redactó y actualizó el `README.md` completo, incluyendo:
- Guía de instalación y despliegue con Docker
- Guía alternativa de ejecución sin Docker (venv + pip + uvicorn)
- Tabla de los 4 proveedores LLM con ejemplos de configuración
- Documentación detallada de endpoints con el nuevo campo `provider`
- Límite de 40 tickets con IA real documentado
- Este mismo archivo `IA_EN_DESARROLLO.md`

Se revisó manualmente la precisión de todas las rutas, comandos de terminal
(Windows y Linux/macOS), URLs de acceso y enlaces internos.

---

## Qué se validó manualmente

A lo largo de cada iteración de desarrollo, se verificó manualmente lo
siguiente:

- **Rutas de archivos en Docker vs ejecución local:** paths de CSV, base de
  datos y knowledge_base que difieren entre ambos entornos.
- **Resolución de `DATABASE_URL`:** comportamiento de `database.py` al
  convertir rutas relativas SQLite a absolutas.
- **Inicialización de SDKs sin errores de importación:** los 3 proveedores
  (Gemini, OpenAI, DeepSeek) se importan condicionalmente y fallan
  silenciosamente a mock si las API keys están vacías.
- **Formato de respuestas JSON del LLM:** DeepSeek puede devolver bloques
  markdown (\`\`\`json), se validó la lógica de limpieza antes del parseo.
- **Refresco de gráficos Chart.js:** se destruyen instancias previas antes de
  crear nuevas para evitar colisiones de canvas.
- **Proxy reverso Nginx → backend:** se verificó que las peticiones del
  frontend a `/api/*` llegaran correctamente al backend en el puerto 8000.
- **Timeouts y concurrencia en ingesta:** las 40 llamadas a DeepSeek con
  0.6s de retardo entre cada una no bloquean el dashboard ni las consultas al
  chat.
- **Encoding de caracteres acentuados:** se verificó que las respuestas en
  español con tildes y eñes se renderizan correctamente en el navegador,
  independientemente del encoding de la terminal.

---

## Configuraciones de agentes y herramientas

- **OpenCode:** se usó como agente principal de desarrollo en modo CLI.
  No se configuraron agentes personalizados ni subagentes; se utilizó el
  comportamiento por defecto con `deepseek-v4-pro` como modelo subyacente.
- **Gemini:** se usó directamente vía API (`google-genai`) sin agentes
  intermediarios, tanto en el producto como en el bootstrapping inicial.
- **DeepSeek:** se usó como proveedor LLM del producto (vía SDK de OpenAI)
  y como modelo subyacente de OpenCode para tareas de desarrollo.

No se utilizaron archivos `AGENTS.md`, prompts reutilizables ni configuraciones
personalizadas de agentes más allá de las instrucciones directas dadas en cada
sesión de desarrollo.
