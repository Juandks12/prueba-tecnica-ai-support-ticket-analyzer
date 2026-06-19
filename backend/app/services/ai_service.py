import os
import json
import logging
from typing import Dict, Any, List

# Configurar logs
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

LLM_PROVIDER = os.getenv("LLM_PROVIDER", "mock").lower()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "")

# Inicializar clientes condicionalmente para evitar errores si las keys están vacías
genai_client = None
openai_client = None

if LLM_PROVIDER == "gemini":
    if GEMINI_API_KEY:
        try:
            from google import genai
            genai_client = genai.Client(api_key=GEMINI_API_KEY)
            logger.info("Cliente de Gemini inicializado correctamente.")
        except Exception as e:
            logger.error(f"Error al inicializar cliente de Gemini: {e}. Se usará modo 'mock'.")
            LLM_PROVIDER = "mock"
    else:
        logger.warning("GEMINI_API_KEY no configurada. Se usará modo 'mock'.")
        LLM_PROVIDER = "mock"

elif LLM_PROVIDER == "openai":
    if OPENAI_API_KEY:
        try:
            from openai import OpenAI
            openai_client = OpenAI(api_key=OPENAI_API_KEY)
            logger.info("Cliente de OpenAI inicializado correctamente.")
        except Exception as e:
            logger.error(f"Error al inicializar cliente de OpenAI: {e}. Se usará modo 'mock'.")
            LLM_PROVIDER = "mock"
    else:
        logger.warning("OPENAI_API_KEY no configurada. Se usará modo 'mock'.")
        LLM_PROVIDER = "mock"

elif LLM_PROVIDER == "deepseek":
    if DEEPSEEK_API_KEY:
        try:
            from openai import OpenAI
            openai_client = OpenAI(
                api_key=DEEPSEEK_API_KEY,
                base_url="https://api.deepseek.com"
            )
            logger.info("Cliente de DeepSeek inicializado correctamente.")
        except Exception as e:
            logger.error(f"Error al inicializar cliente de DeepSeek: {e}. Se usará modo 'mock'.")
            LLM_PROVIDER = "mock"
    else:
        logger.warning("DEEPSEEK_API_KEY no configurada. Se usará modo 'mock'.")
        LLM_PROVIDER = "mock"


def get_mock_enrichment(subject: str, description: str, product: str, ticket_type: str) -> Dict[str, str]:
    """Genera análisis simulado (mock) basado en reglas para cuando no hay API keys."""
    subject_lower = (subject or "").lower()
    desc_lower = (description or "").lower()
    type_lower = (ticket_type or "").lower()
    
    # 1. Clasificación de Categoría
    category = "Technical Issue"
    if any(k in subject_lower or k in desc_lower or k in type_lower for k in ["cancel", "anular", "baja"]):
        category = "Cancellation Request"
    elif any(k in subject_lower or k in desc_lower or k in type_lower for k in ["refund", "reembolso", "devolver", "dinero", "cobro", "pago"]):
        category = "Refund Request"
    elif any(k in subject_lower or k in desc_lower or k in type_lower for k in ["setup", "install", "configur", "instalar", "iniciar", "activar"]):
        category = "Product Inquiry" if "inquiry" in type_lower else "Technical Issue"
    elif any(k in subject_lower or k in desc_lower or k in type_lower for k in ["inquiry", "pregunt", "duda", "consult", "info", "saber"]):
        category = "Product Inquiry"
    elif "billing" in type_lower or "factur" in subject_lower:
        category = "Billing Inquiry"

    # 2. Clasificación de Prioridad
    priority = "Medium"
    if any(k in desc_lower for k in ["urgent", "critico", "critical", "grave", "urgente", "inmediato", "no puedo", "loss", "seguridad", "crashed"]):
        priority = "Critical"
    elif any(k in desc_lower or k in subject_lower for k in ["error", "fallo", "high", "alta", "malo", "roto", "malfuncion"]):
        priority = "High"
    elif any(k in desc_lower for k in ["low", "baja", "cuando", "como", "duda", "hola"]):
        priority = "Low"

    # 3. Sentimiento
    sentiment = "Neutral"
    if priority == "Critical":
        sentiment = "Angry / Urgent"
    elif priority == "High":
        sentiment = "Frustrated"
    elif priority == "Low":
        sentiment = "Calm"

    # 4. Equipo responsable
    team = "Soporte Técnico"
    if category in ["Cancellation Request", "Refund Request", "Billing Inquiry"]:
        team = "Facturación y Cuentas"
    elif "setup" in desc_lower or "install" in desc_lower or "configur" in desc_lower:
        team = "Soporte de Instalación"
    elif category == "Product Inquiry":
        team = "Atención al Cliente"

    # 5. Resumen
    summary_words = []
    if product:
        summary_words.append(f"Problema con {product}:")
    
    clean_subj = subject.replace("I'm having an issue with the", "").replace("Please assist", "").strip()
    summary_words.append(clean_subj[:35] + ("..." if len(clean_subj) > 35 else ""))
    
    summary = " ".join(summary_words) if summary_words else "Consulta o reporte del cliente."

    return {
        "category": category,
        "priority": priority,
        "summary": summary,
        "sentiment": sentiment,
        "team": team
    }


def enrich_ticket(subject: str, description: str, product: str, ticket_type: str) -> Dict[str, str]:
    """Enriquece un ticket utilizando el LLM configurado o el Mock en su defecto."""
    if LLM_PROVIDER == "mock":
        return get_mock_enrichment(subject, description, product, ticket_type)

    prompt = f"""Analiza el siguiente ticket de soporte técnico y responde ÚNICAMENTE con un objeto JSON válido. No incluyas explicaciones, introducciones ni bloques de código markdown.
El objeto JSON debe tener exactamente esta estructura y tipos de datos:
{{
  "category": "string (Debe ser una de: [Technical Issue, Billing Inquiry, Refund Request, Cancellation Request, Product Inquiry])",
  "priority": "string (Debe ser una de: [Low, Medium, High, Critical])",
  "summary": "string (Un resumen en español de máximo 12 palabras)",
  "sentiment": "string (Debe ser una de: [Calm, Neutral, Frustrated, Angry / Urgent])",
  "team": "string (Debe ser una de: [Soporte Técnico, Facturación y Cuentas, Soporte de Instalación, Atención al Cliente])"
}}

Información del ticket a analizar:
- Producto asociado: {product}
- Tipo original: {ticket_type}
- Asunto del ticket: {subject}
- Mensaje del cliente: {description}
"""

    if LLM_PROVIDER == "gemini" and genai_client:
        try:
            # Usar Gemini 2.5 Flash
            response = genai_client.models.generate_content(
                model='gemini-2.5-flash',
                contents=prompt,
                config={'response_mime_type': 'application/json'}
            )
            data = json.loads(response.text.strip())
            return {
                "category": data.get("category", "Technical Issue"),
                "priority": data.get("priority", "Medium"),
                "summary": data.get("summary", "Resumen automático de soporte"),
                "sentiment": data.get("sentiment", "Neutral"),
                "team": data.get("team", "Soporte Técnico")
            }
        except Exception as e:
            logger.error(f"Error llamando a Gemini: {e}. Usando mock como alternativa.")
            return get_mock_enrichment(subject, description, product, ticket_type)

    elif LLM_PROVIDER == "openai" and openai_client:
        try:
            response = openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "Eres un asistente experto que responde en formato JSON estructurado."},
                    {"role": "user", "content": prompt}
                ],
                response_format={"type": "json_object"}
            )
            data = json.loads(response.choices[0].message.content.strip())
            return {
                "category": data.get("category", "Technical Issue"),
                "priority": data.get("priority", "Medium"),
                "summary": data.get("summary", "Resumen automático de soporte"),
                "sentiment": data.get("sentiment", "Neutral"),
                "team": data.get("team", "Soporte Técnico")
            }
        except Exception as e:
            logger.error(f"Error llamando a OpenAI: {e}. Usando mock como alternativa.")
            return get_mock_enrichment(subject, description, product, ticket_type)

    elif LLM_PROVIDER == "deepseek" and openai_client:
        try:
            response = openai_client.chat.completions.create(
                model="deepseek-chat",
                messages=[
                    {"role": "system", "content": "Eres un asistente experto que responde exclusivamente en formato JSON válido, sin markdown ni explicaciones."},
                    {"role": "user", "content": prompt}
                ]
            )
            raw = response.choices[0].message.content.strip()
            if raw.startswith("```"):
                raw = raw.split("\n", 1)[-1].rsplit("```", 1)[0].strip()
            data = json.loads(raw)
            return {
                "category": data.get("category", "Technical Issue"),
                "priority": data.get("priority", "Medium"),
                "summary": data.get("summary", "Resumen automático de soporte"),
                "sentiment": data.get("sentiment", "Neutral"),
                "team": data.get("team", "Soporte Técnico")
            }
        except Exception as e:
            logger.error(f"Error llamando a DeepSeek: {e}. Usando mock como alternativa.")
            return get_mock_enrichment(subject, description, product, ticket_type)

    return get_mock_enrichment(subject, description, product, ticket_type)


def ask_question(question: str, context_tickets: List[Dict[str, Any]], policies_text: str) -> str:
    """Responde preguntas en lenguaje natural utilizando el contexto de los tickets y las políticas."""
    
    # Formatear el contexto de los tickets resumidos
    formatted_tickets = ""
    for idx, t in enumerate(context_tickets[:20]): # Limitar a 20 tickets más representativos por contexto
        formatted_tickets += f"- ID {t['ticket_id']}: [{t['ai_priority']}] {t['ai_category']} | Cliente: {t['customer_name']} ({t.get('customer_age', 'N/A')} años) | Producto: {t['product_purchased']} | Asunto: {t['ticket_subject']} | Descripción: {t['ticket_description']} | Resumen IA: {t['ai_summary']} | Equipo: {t['ai_team']} | Estado: {t['ticket_status']} | Calificación: {t.get('customer_satisfaction_rating', 'N/A')}\n"

    prompt = f"""Eres un Analista de Soporte con Inteligencia Artificial. Tu tarea es responder preguntas de negocio sobre los tickets de soporte del cliente.
Para responder, debes basarte en la Base de Conocimiento (Políticas de Soporte y SLA) y el Contexto de los tickets cargados a continuación.

---
BASE DE CONOCIMIENTO (POLÍTICAS INTERNAS):
{policies_text}

---
CONTEXTO DE TICKETS (Muestra de tickets relevantes en la base de datos):
{formatted_tickets}

---
PREGUNTA DEL USUARIO:
{question}

Responde de forma clara, profesional y concisa en español. Si te preguntan estadísticas generales o de qué se quejan más, haz un breve desglose cuantitativo basándote en los datos recibidos. Si la respuesta no se puede deducir del contexto provisto, indícalo educadamente.
"""

    if LLM_PROVIDER == "gemini" and genai_client:
        try:
            response = genai_client.models.generate_content(
                model='gemini-2.5-flash',
                contents=prompt
            )
            return response.text.strip()
        except Exception as e:
            logger.error(f"Error en /ask llamando a Gemini: {e}")
            return f"Error al procesar la respuesta con Gemini: {str(e)}. (Modo LLM activo pero fallando)"

    elif LLM_PROVIDER == "openai" and openai_client:
        try:
            response = openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "Eres un asistente de análisis de tickets y soporte de negocio."},
                    {"role": "user", "content": prompt}
                ]
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            logger.error(f"Error en /ask llamando a OpenAI: {e}")
            return f"Error al procesar la respuesta con OpenAI: {str(e)}"

    elif LLM_PROVIDER == "deepseek" and openai_client:
        try:
            response = openai_client.chat.completions.create(
                model="deepseek-chat",
                messages=[
                    {"role": "system", "content": "Eres un asistente de análisis de tickets y soporte de negocio. Responde en español."},
                    {"role": "user", "content": prompt}
                ]
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            logger.error(f"Error en /ask llamando a DeepSeek: {e}")
            return f"Error al procesar la respuesta con DeepSeek: {str(e)}"

    # Mock Ask (Fallback / Modo Mock)
    logger.info("Respondiendo con el motor de respuestas heurístico (modo Mock).")
    
    question_lower = question.lower()
    
    if any(k in question_lower for k in ["soport", "sla", "tiempo", "política", "politica", "responder"]):
        return f"**Respuesta (Modo Simulado):** Basado en las políticas de la empresa:\n- Los tickets de prioridad **Critical** tienen un SLA de **1 hora**.\n- Los tickets **High** tienen un SLA de **4 horas**.\n- Los de prioridad **Medium/Low** deben responderse en un plazo máximo de **24 horas**.\n\n*Nota: Esto se extrae de la base de conocimientos y es procesado en base al set actual de {len(context_tickets)} tickets.*"
    
    if any(k in question_lower for k in ["crítico", "critico", "urgente", "grave", "prioridad"]):
        criticals = [t for t in context_tickets if t.get('ai_priority') == 'Critical']
        return f"**Respuesta (Modo Simulado):** Actualmente hay **{len(criticals)} tickets** con prioridad **Critical** en la muestra analizada.\n\nEl problema más común entre estos tickets de alta prioridad está relacionado con fallos de hardware y problemas con conexiones a internet en dispositivos como Nintendo Switch o Lenovo ThinkPad."

    if any(k in question_lower for k in ["producto", "queja", "dispositivo", "afectado"]):
        from collections import Counter
        products = [t.get('product_purchased') for t in context_tickets if t.get('product_purchased')]
        common = Counter(products).most_common(2)
        prod_str = ", ".join([f"{p[0]} ({p[1]} quejas)" for p in common])
        return f"**Respuesta (Modo Simulado):** El producto que genera más quejas en el sistema es **{prod_str}**.\n\nLa mayoría son incidencias de configuración de software y problemas de compatibilidad."

    return f"**Respuesta (Modo Simulado):** He analizado la base de datos de tickets ({len(context_tickets)} registros cargados) y la base de conocimiento de políticas.\n\nTu pregunta sobre: *'{question}'* indica que quieres conocer detalles del sistema de soporte. En la base de datos vemos un comportamiento donde el equipo de **Soporte Técnico** concentra la mayoría de las peticiones, seguido de **Facturación**. El promedio general de satisfacción de los tickets cerrados ronda el 3.0 / 5.0."
