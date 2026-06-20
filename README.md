# AI Support Ticket Analyzer 🤖📊

¡Bienvenido! Este proyecto es un **Analizador de Tickets de Soporte con IA** diseñado para procesar, limpiar y analizar de un vistazo los reportes de clientes. El sistema cuenta con una arquitectura de microservicios completamente orquestada con **Docker Compose**, un backend veloz en **FastAPI**, persistencia en **SQLite** y un frontend premium en **HTML/Vanilla CSS/JS** servido por **Nginx**.

---

## 🛠️ Arquitectura y Decisiones Tecnológicas

La solución está construida sobre los siguientes pilares técnicos:

1.  **Orquestación Multicontenedor ([docker-compose.yml](file:///C:/Users/juand/Downloads/prueba-tecnica-ai-support-ticket-analyzer/docker-compose.yml)):** Separa el Backend del Frontend emulando un entorno real de producción.
2.  **Servidor Web y Proxy Inverso ([nginx.conf](file:///C:/Users/juand/Downloads/prueba-tecnica-ai-support-ticket-analyzer/frontend/nginx.conf)):** Nginx actúa como servidor de archivos estáticos para el Dashboard y como proxy inverso, redirigiendo todas las llamadas `/api/*` al backend de forma transparente para evitar problemas de CORS.
3.  **Backend REST API ([main.py](file:///C:/Users/juand/Downloads/prueba-tecnica-ai-support-ticket-analyzer/backend/app/main.py)):** Desarrollado con FastAPI por su alto rendimiento físico, facilidad de validación con Pydantic y documentación interactiva automática en `/docs`.
4.  **Limpieza y Normalización ([ingest_data.py](file:///C:/Users/juand/Downloads/prueba-tecnica-ai-support-ticket-analyzer/backend/scripts/ingest_data.py)):** El script de ingesta procesa y limpia el dataset [tickets.csv](file:///C:/Users/juand/Downloads/prueba-tecnica-ai-support-ticket-analyzer/dataset/tickets.csv) (normaliza correos, estandariza prioridades como `P4` o `Critical`, resuelve fechas complejas escritas en lenguaje verbal en español e inglés y formatea números de satisfacción).
5.  **Motor de Inteligencia Artificial Multi-Proveedor ([ai_service.py](file:///C:/Users/juand/Downloads/prueba-tecnica-ai-support-ticket-analyzer/backend/app/services/ai_service.py)):** 
    *   **Modo Productivo (3 proveedores):**
        *   **DeepSeek** — modelo `deepseek-chat` vía SDK de OpenAI apuntando a `https://api.deepseek.com`. Rápido, económico y con excelente soporte para español.
        *   **Gemini** — usando `google-genai` con el modelo `gemini-2.5-flash`.
        *   **OpenAI** — usando `gpt-4o-mini`.
    *   **Modo Simulador (Mock):** Sistema heurístico inteligente por reglas que clasifica, resume y asigna equipos al instante. **No requiere configurar API keys de pago para ejecutarse.**
    *   **Toggle en el chat:** El dashboard incluye un interruptor para alternar entre **Mock** y **DeepSeek** en tiempo real, sin modificar variables de entorno ni reiniciar.
6.  **Base de Conocimientos RAG ([knowledge_base/](file:///C:/Users/juand/Downloads/prueba-tecnica-ai-support-ticket-analyzer/knowledge_base/)):** Las políticas de SLA ([policies.md](file:///C:/Users/juand/Downloads/prueba-tecnica-ai-support-ticket-analyzer/knowledge_base/policies.md)) y las reglas de ruteo ([routing_rules.md](file:///C:/Users/juand/Downloads/prueba-tecnica-ai-support-ticket-analyzer/knowledge_base/routing_rules.md)) se inyectan en tiempo de ejecución junto con una muestra de tickets a los LLMs para responder preguntas de negocio complejas en el endpoint `/api/ask`.

---

## 🚀 Guía de Instalación y Despliegue Rápido

### Requisitos Previos
- Tener instalado **Docker** y **Docker Compose**.
- (Opcional) Una API Key de **DeepSeek**, **Google Gemini** u **OpenAI** si deseas usar modelos reales de IA. El proyecto funciona completamente sin ellas gracias al modo Mock.

### Paso 1: Configurar Variables de Entorno
Clona el archivo de configuración copiando el archivo de ejemplo:
```bash
# Crea tu archivo .env local
cp .env.example .env
```
Por defecto, el archivo [.env](file:///C:/Users/juand/Downloads/prueba-tecnica-ai-support-ticket-analyzer/.env) viene configurado con `LLM_PROVIDER=mock`, lo que te permite probar toda la aplicación localmente sin gastar créditos. Si deseas activar la IA real, edita el archivo `.env` configurando uno de los siguientes proveedores:

**Opción A — DeepSeek (recomendado):**
```env
LLM_PROVIDER=deepseek
DEEPSEEK_API_KEY=sk-tu_api_key_de_deepseek
```

**Opción B — Google Gemini:**
```env
LLM_PROVIDER=gemini
GEMINI_API_KEY=tu_api_key_de_gemini
```

**Opción C — OpenAI:**
```env
LLM_PROVIDER=openai
OPENAI_API_KEY=sk-tu_api_key_de_openai
```

### Paso 2: Levantar el Proyecto con Docker Compose

> **¿No usas Docker?** Ve directamente a la sección [Ejecución sin Docker (Manual)](#alternativa-ejecucion-sin-docker-manual).

Ejecuta el siguiente comando en la raíz del proyecto para construir y arrancar las imágenes:
```bash
docker compose up --build -d
```
Este comando levantará:
- El **Backend** en el puerto `8000`.
- El **Frontend Nginx** en el puerto `8080`.
- Creará un volumen compartido `db_data` para almacenar de forma persistente la base de datos SQLite `tickets.db`.

### Paso 3: Inicializar la Ingesta de Datos
Para limpiar los datos originales de [tickets.csv](file:///C:/Users/juand/Downloads/prueba-tecnica-ai-support-ticket-analyzer/dataset/tickets.csv), analizarlos con la IA y guardarlos en la base de datos, puedes hacer una de las siguientes opciones:
1.  **Desde la Interfaz Gráfica:** Haz clic en el botón **"🔄 Iniciar Ingesta / Recargar"** ubicado en el panel lateral izquierdo del Dashboard.
2.  **Mediante Comando en el Contenedor:**
    ```bash
    docker exec ticket-analyzer-backend python scripts/ingest_data.py
    ```

> **Nota sobre créditos:** Si configuraste un LLM real (`deepseek`, `gemini` u `openai`), los **primeros 40 tickets** se procesarán con IA real y los **360 restantes** con el motor de reglas heurístico (mock), para no exceder cuotas ni presupuestos gratuitos. Si usas `LLM_PROVIDER=mock`, los 400 tickets se procesan con reglas.

---

## 🖥️ Alternativa: Ejecución sin Docker (Manual)

Si prefieres no instalar Docker, puedes ejecutar el proyecto directamente con Python. Solo necesitas Python 3.9+ y pip.

### Paso 1: Clonar y crear entorno virtual

```bash
git clone <url-del-repositorio>
cd prueba-tecnica-ai-support-ticket-analyzer
python -m venv venv
```

**Activar el entorno virtual:**
```bash
# Windows (PowerShell o CMD):
venv\Scripts\activate

# Linux / macOS:
source venv/bin/activate
```

### Paso 2: Instalar dependencias

```bash
pip install -r backend/requirements.txt
```

Esto instala todos los paquetes listados en la tabla de arriba. La instalación toma aproximadamente 1-2 minutos.

### Paso 3: Configurar variables de entorno

```bash
# Windows:
copy .env.example .env

# Linux / macOS:
cp .env.example .env
```

Edita el archivo `.env` con tu editor de texto y configura el proveedor de IA deseado. Ejemplo con DeepSeek:

```env
LLM_PROVIDER=deepseek
DEEPSEEK_API_KEY=sk-tu_api_key_de_deepseek
```

Si no tienes una API key, deja `LLM_PROVIDER=mock` y el sistema usará respuestas simuladas.

### Paso 4: Ejecutar el backend

```bash
cd backend
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

Uvicorn arrancará en `http://localhost:8000`. El flag `--reload` reinicia el servidor automáticamente cuando detecta cambios en el código (ideal para desarrollo).

El backend **sirve el frontend automáticamente** como archivos estáticos desde `frontend/src/`. No necesitas un servidor web adicional.

### Paso 5: Ejecutar la ingesta de datos

En **otra terminal**, con el entorno virtual activado y desde la raíz del proyecto:

```bash
cd backend
python scripts/ingest_data.py
```

El script buscará `dataset/tickets.csv` automáticamente en la raíz del proyecto, limpiará los datos crudos, los enriquecerá con IA y los guardará en la base de datos SQLite (`tickets.db`).

### Paso 6: Acceder a la aplicación

| Recurso | URL |
|---|---|
| **Dashboard principal** | http://localhost:8000/index.html |
| **API raíz (JSON)** | http://localhost:8000 |
| **Documentación Swagger** | http://localhost:8000/docs |
| **Tickets (API)** | http://localhost:8000/api/tickets |
| **Métricas (API)** | http://localhost:8000/api/metrics |

### Notas importantes para ejecución manual

- **El dashboard funciona sin Nginx** porque el backend monta los archivos estáticos de `frontend/src/` en la raíz. La variable `API_BASE = '/api'` del frontend resuelve correctamente al compartir origen con el backend en `localhost:8000`.
- **Base de datos:** `tickets.db` se crea automáticamente dentro de la carpeta `backend/` en la primera ejecución. Para reiniciar desde cero, borra ese archivo y vuelve a ejecutar la ingesta.
- **Base de conocimientos:** Los archivos `knowledge_base/policies.md` y `knowledge_base/routing_rules.md` se cargan automáticamente. El backend los busca en la raíz del proyecto.
- **Desarrollo del frontend:** Si necesitas modificar el frontend y ver cambios en tiempo real, puedes servir los archivos estáticos por separado con Python y editar `API_BASE` en `app.js` para apuntar al backend:
  ```bash
  cd frontend/src
  python -m http.server 8080
  # Edita app.js: const API_BASE = 'http://localhost:8000/api';
  ```
- La carpeta `venv/` está en `.gitignore` y no se sube al repositorio.

---

## 🖥️ Cómo Probar la Aplicación

1.  **Dashboard de Control:** Abre tu navegador web e ingresa a `http://localhost:8080`. Verás el panel con métricas de KPI animadas, gráficos interactivos de Chart.js, buscador inteligente con filtros y una consola de chat de IA.
2.  **Toggle Mock / DeepSeek:** En el panel de chat, usa el interruptor para alternar entre el **modo Mock** (respuestas heurísticas instantáneas y gratuitas) y **DeepSeek** (respuestas reales del modelo `deepseek-chat` analizando los tickets y políticas). El indicador `LLM:` en el header se actualiza automáticamente.
3.  **Detalles del Ticket:** En la tabla de tickets, haz clic en el botón **"Ver Detalle"** en cualquier fila para abrir un modal con la información limpia del cliente, el resumen estructurado de la IA y el sentimiento detectado.
4.  **Documentación Interactiva de la API:** Accede a `http://localhost:8000/docs` para ver e interactuar con Swagger UI y hacer peticiones de prueba a los endpoints directamente.

---

## 📡 Endpoints Principales de la API

*   `GET /api/tickets`: Obtiene el listado de tickets enriquecidos.
    *   **Parámetros query opcionales:** `skip` (paginación), `limit`, `category` (filtrar por categoría IA), `priority` (filtrar por prioridad IA), `status` (filtrar por estado), y `search` (búsqueda de texto libre).
*   `GET /api/metrics`: Retorna métricas cuantitativas clave estructuradas para renderizar gráficos y KPI Cards.
*   `POST /api/ingest`: Encola y ejecuta la limpieza e ingesta en segundo plano.
*   `POST /api/ask`: Envía preguntas en lenguaje natural (RAG).
    *   **Body JSON:** `{"question": "¿Cuáles son las prioridades críticas y qué SLA les aplica?", "provider": "deepseek"}`
    *   **`provider` (opcional):** `"mock"`, `"deepseek"`, `"gemini"` u `"openai"`. Permite elegir el motor de IA por consulta, sin modificar el `.env`. Si se omite, usa el proveedor configurado en `LLM_PROVIDER`.
    *   **Respuesta:** Genera una respuesta en español contextualizada en base a las políticas operativas del negocio y los datos reales de los tickets.

---

## 🤖 Uso de Inteligencia Artificial Durante el Desarrollo

Se adoptó un enfoque de **Desarrollo Aumentado por IA** usando **OpenCode** (con DeepSeek V4 Pro), **Gemini** (gemini-3.5-flash) y **DeepSeek** (deepseek-chat).

| Herramienta | Rol principal |
|---|---|
| **OpenCode** | Agente de desarrollo: debugging, features, refactorización, documentación |
| **Gemini** | Bootstrapping inicial: estructura FastAPI, parser de fechas, CSS |
| **DeepSeek** | Proveedor LLM del producto y modelo subyacente de OpenCode |

Las tareas incluyeron: estructuración del backend, parser de fechas en español, diseño del dashboard, integración del proveedor DeepSeek, corrección de incompatibilidad de versiones (`openai` vs `httpx`), sistema de toggle Mock/DeepSeek en el chat, reorganización de la estructura del proyecto, y documentación integral.

Cada componente generado o modificado por IA fue validado manualmente: rutas de archivos en Docker vs local, resolución de `DATABASE_URL`, inicialización condicional de SDKs, formato JSON del LLM, refresco de Chart.js, proxy Nginx, timeouts de ingesta y encoding de caracteres.

> **Documento completo:** [IA_EN_DESARROLLO.md](IA_EN_DESARROLLO.md) — incluye el detalle de cada tarea, qué herramienta se usó, qué se validó manualmente y las configuraciones de agentes utilizadas.

---

## ⚠️ Limitaciones y Mejoras con Más Tiempo

Si tuviera más tiempo de desarrollo, consideraría las siguientes mejoras de ingeniería:
- **Integración con Azure Cloud:** Desplegar la solución en Azure Container Instances (ACI) o Azure Kubernetes Service (AKS), migrar SQLite a Azure SQL Database para entornos productivos multi-instancia, y agregar monitorización con Azure Application Insights.
- **Pipeline de Ingesta Asíncrona:** Integrar Celery con Redis para manejar colas de tareas pesadas durante ingestas masivas de millones de registros, enviando notificaciones por WebSockets al frontend sobre el progreso.
- **Autenticación y Roles:** Implementar OAuth2 con JWT en FastAPI para controlar qué agentes de soporte pueden gestionar, modificar o responder tickets sensibles.
