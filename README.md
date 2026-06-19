# AI Support Ticket Analyzer 🤖📊

¡Bienvenido! Este proyecto es un **Analizador de Tickets de Soporte con IA** diseñado para procesar, limpiar y analizar de un vistazo los reportes de clientes. El sistema cuenta con una arquitectura de microservicios completamente orquestada con **Docker Compose**, un backend veloz en **FastAPI**, persistencia en **SQLite** y un frontend premium en **HTML/Vanilla CSS/JS** servido por **Nginx**.

---

## 🛠️ Arquitectura y Decisiones Tecnológicas

La solución está construida sobre los siguientes pilares técnicos:

1.  **Orquestación Multicontenedor ([docker-compose.yml](file:///C:/Users/juand/Downloads/prueba-tecnica-ai-support-ticket-analyzer/docker-compose.yml)):** Separa el Backend del Frontend emulando un entorno real de producción.
2.  **Servidor Web y Proxy Inverso ([nginx.conf](file:///C:/Users/juand/Downloads/prueba-tecnica-ai-support-ticket-analyzer/frontend/nginx.conf)):** Nginx actúa como servidor de archivos estáticos para el Dashboard y como proxy inverso, redirigiendo todas las llamadas `/api/*` al backend de forma transparente para evitar problemas de CORS.
3.  **Backend REST API ([main.py](file:///C:/Users/juand/Downloads/prueba-tecnica-ai-support-ticket-analyzer/backend/app/main.py)):** Desarrollado con FastAPI por su alto rendimiento físico, facilidad de validación con Pydantic y documentación interactiva automática en `/docs`.
4.  **Limpieza y Normalización ([ingest_data.py](file:///C:/Users/juand/Downloads/prueba-tecnica-ai-support-ticket-analyzer/backend/scripts/ingest_data.py)):** El script de ingesta procesa y limpia el dataset [tickets.csv](file:///C:/Users/juand/Downloads/prueba-tecnica-ai-support-ticket-analyzer/tickets.csv) (normaliza correos, estandariza prioridades como `P4` o `Critical`, resuelve fechas complejas escritas en lenguaje verbal en español e inglés y formatea números de satisfacción).
5.  **Motor de Inteligencia Artificial Dual ([ai_service.py](file:///C:/Users/juand/Downloads/prueba-tecnica-ai-support-ticket-analyzer/backend/app/services/ai_service.py)):** 
    *   **Modo Productivo:** Conexión directa a **Gemini** (usando `google-genai` con el modelo `gemini-2.5-flash`) u **OpenAI** (usando `gpt-4o-mini`).
    *   **Modo Simulador (Mock):** Sistema heurístico inteligente por reglas que clasifica, resume y asigna equipos al instante. **No requiere configurar API keys de pago para ejecutarse.**
6.  **Base de Conocimientos RAG ([knowledge_base/](file:///C:/Users/juand/Downloads/prueba-tecnica-ai-support-ticket-analyzer/knowledge_base/)):** Las políticas de SLA ([policies.md](file:///C:/Users/juand/Downloads/prueba-tecnica-ai-support-ticket-analyzer/knowledge_base/policies.md)) y las reglas de ruteo ([routing_rules.md](file:///C:/Users/juand/Downloads/prueba-tecnica-ai-support-ticket-analyzer/knowledge_base/routing_rules.md)) se inyectan en tiempo de ejecución junto con una muestra de tickets a los LLMs para responder preguntas de negocio complejas en el endpoint `/api/ask`.

---

## 🚀 Guía de Instalación y Despliegue Rápido

### Requisitos Previos
- Tener instalado **Docker** y **Docker Compose**.
- (Opcional) Una API Key de Google Gemini o de OpenAI si deseas usar modelos reales de IA.

### Paso 1: Configurar Variables de Entorno
Clona el archivo de configuración copiando el archivo de ejemplo:
```bash
# Crea tu archivo .env local
cp .env.example .env
```
Por defecto, el archivo [.env](file:///C:/Users/juand/Downloads/prueba-tecnica-ai-support-ticket-analyzer/.env) viene configurado con `LLM_PROVIDER=mock`, lo que te permite probar toda la aplicación localmente sin gastar créditos. Si deseas activar la IA real, edita el archivo `.env` configurando:
```env
LLM_PROVIDER=gemini
GEMINI_API_KEY=tu_api_key_de_gemini
```

### Paso 2: Levantar el Proyecto con Docker Compose
Ejecuta el siguiente comando en la raíz del proyecto para construir y arrancar las imágenes:
```bash
docker compose up --build -d
```
Este comando levantará:
- El **Backend** en el puerto `8000`.
- El **Frontend Nginx** en el puerto `8080`.
- Creará un volumen compartido `db_data` para almacenar de forma persistente la base de datos SQLite `tickets.db`.

### Paso 3: Inicializar la Ingesta de Datos
Para limpiar los datos originales de [tickets.csv](file:///C:/Users/juand/Downloads/prueba-tecnica-ai-support-ticket-analyzer/tickets.csv), analizarlos con la IA y guardarlos en la base de datos, puedes hacer una de las siguientes opciones:
1.  **Desde la Interfaz Gráfica:** Haz clic en el botón **"🔄 Iniciar Ingesta / Recargar"** ubicado en el panel lateral izquierdo del Dashboard.
2.  **Mediante Comando en el Contenedor:**
    ```bash
    docker exec -it ticket-analyzer-backend python scripts/ingest_data.py
    ```

---

## 🖥️ Cómo Probar la Aplicación

1.  **Dashboard de Control:** Abre tu navegador web e ingresa a `http://localhost:8080`. Verás el panel con métricas de KPI animadas, gráficos interactivos de Chart.js, buscador inteligente con filtros y una consola de chat de IA.
2.  **Detalles del Ticket:** En la tabla de tickets, haz clic en el botón **"Ver Detalle"** en cualquier fila para abrir un modal con la información limpia del cliente, el resumen estructurado de la IA y el sentimiento detectado.
3.  **Documentación Interactiva de la API:** Accede a `http://localhost:8000/docs` para ver e interactuar con Swagger UI y hacer peticiones de prueba a los endpoints directamente.

---

## 📡 Endpoints Principales de la API

*   `GET /api/tickets`: Obtiene el listado de tickets enriquecidos.
    *   **Parámetros query opcionales:** `skip` (paginación), `limit`, `category` (filtrar por categoría IA), `priority` (filtrar por prioridad IA), `status` (filtrar por estado), y `search` (búsqueda de texto libre).
*   `GET /api/metrics`: Retorna métricas cuantitativas clave estructuradas para renderizar gráficos y KPI Cards.
*   `POST /api/ingest`: Encola y ejecuta la limpieza e ingesta en segundo plano.
*   `POST /api/ask`: Envía preguntas en lenguaje natural (RAG).
    *   **Body JSON:** `{"question": "¿Cuáles son las prioridades críticas y qué SLA les aplica?"}`
    *   **Respuesta:** Genera una respuesta en español contextualizada en base a las políticas operativas del negocio y los datos reales de los tickets.

---

## 🤖 Uso de Inteligencia Artificial Durante el Desarrollo

Para optimizar los tiempos de entrega y garantizar la solidez de la arquitectura, se adoptó un enfoque de **Desarrollo Aumentado por IA**:

1.  **Generación y Estructuración de Código:** Se utilizó el modelo Gemini para estructurar las rutas de FastAPI, definir la expresión regular del formateador de fechas complejas y diseñar las consultas agrupadas de SQLAlchemy.
2.  **Diseño Estético (Vanilla CSS):** Se usó IA para definir una paleta de colores HSL consistente, estructurar el diseño responsivo basado en Grid/Flexbox y afinar las transiciones fluidas de los efectos de vidrio del Dashboard.
3.  **Validación Manual:** Cada componente generado por IA fue revisado meticulosamente. Se corrigieron manualmente los enrutamientos de puertos de Docker, la inicialización condicional de los SDK de LLM y el refresco dinámico de Chart.js para evitar colisiones de Canvas.

---

## ⚠️ Limitaciones y Mejoras con Más Tiempo

Si tuviera más tiempo de desarrollo, consideraría las siguientes mejoras de ingeniería:
- **Indexación Vectorial (Vector DB):** Reemplazar la inyección directa de texto de tickets en el prompt por una base de datos vectorial como Chroma o PGVector, generando embeddings para realizar búsquedas semánticas más precisas en `/api/ask`.
- **Pipeline de Ingesta Asíncrona:** Integrar Celery con Redis para manejar colas de tareas pesadas durante ingestas masivas de millones de registros, enviando notificaciones por WebSockets al frontend sobre el progreso.
- **Autenticación y Roles:** Implementar OAuth2 con JWT en FastAPI para controlar qué agentes de soporte pueden gestionar, modificar o responder tickets sensibles.
