import os
import sys
import re
import time
import pandas as pd
import logging
from datetime import datetime

# Añadir directorio raíz al path para importar módulos de la app
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import engine, Base, SessionLocal
from app.models import Ticket
from app.services.ai_service import enrich_ticket, LLM_PROVIDER

# Configuración de Logs
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def parse_custom_date(val) -> str:
    """Parsea fechas en múltiples formatos (numéricos y verbales en español) a YYYY-MM-DD."""
    if not val or pd.isna(val):
        return None
    val_str = str(val).strip()

    # Formatos de fecha verbales en español como "19 de diciembre 2020" o "20 de mayo 2021"
    spanish_months = {
        "enero": "01", "febrero": "02", "marzo": "03", "abril": "04",
        "mayo": "05", "junio": "06", "julio": "07", "agosto": "08",
        "septiembre": "09", "octubre": "10", "noviembre": "11", "diciembre": "12"
    }
    
    verbal_match = re.match(
        r'(\d+)\s+de\s+([a-zA-Záéíóú]+)\s+(\d{4})', val_str, re.IGNORECASE
    )
    if verbal_match:
        day, month_name, year = verbal_match.groups()
        month_clean = month_name.lower()\
            .replace('á', 'a')\
            .replace('é', 'e')\
            .replace('í', 'i')\
            .replace('ó', 'o')\
            .replace('ú', 'u')
        month_num = spanish_months.get(month_clean, "01")
        return f"{year}-{int(month_num):02d}-{int(day):02d}"

    # Intentar parsing con formatos numéricos estándares
    formats = [
        "%Y-%m-%d",    # 2021-07-19
        "%d/%m/%Y",    # 28/04/2021
        "%m-%d-%Y",    # 05-13-2021
        "%Y/%m/%d",    # 2020/12/31
        "%Y-%m-%d %H:%M:%S"
    ]

    for fmt in formats:
        try:
            return datetime.strptime(val_str, fmt).strftime("%Y-%m-%d")
        except ValueError:
            continue

    return val_str


def normalize_priority(priority_val) -> str:
    """Estandariza los diferentes formatos de prioridad encontrados."""
    if not priority_val or pd.isna(priority_val):
        return "Medium"
    val = str(priority_val).strip().lower()
    
    if "critical" in val:
        return "Critical"
    elif "high" in val:
        return "High"
    elif "low" in val or "p4" in val:
        return "Low"
    elif "medium" in val:
        return "Medium"
    return "Medium"


def normalize_category(type_val) -> str:
    """Normaliza y unifica categorías/tipos de tickets."""
    if not type_val or pd.isna(type_val):
        return "Technical Issue"
    val = str(type_val).strip().lower().replace("_", " ")
    
    if "cancel" in val:
        return "Cancellation Request"
    elif "refund" in val or "reembolso" in val:
        return "Refund Request"
    elif "billing" in val or "factur" in val:
        return "Billing Inquiry"
    elif "inquiry" in val or "consult" in val:
        return "Product Inquiry"
    elif "technical" in val or "issue" in val or "setup" in val or "install" in val:
        return "Technical Issue"
    
    return "Technical Issue"


def clean_email(email_val) -> str:
    """Normaliza y limpia la columna de correos electrónicos."""
    if not email_val or pd.isna(email_val):
        return ""
    return str(email_val).strip().lower()


def clean_satisfaction(sat_val) -> float:
    """Limpia el rating de satisfacción del cliente."""
    if not sat_val or pd.isna(sat_val):
        return None
    try:
        val = float(sat_val)
        if 1.0 <= val <= 5.0:
            return round(val, 1)
        return None
    except ValueError:
        return None


def run_ingestion():
    csv_path = "/app/tickets.csv"
    if not os.path.exists(csv_path):
        # Fallback para ejecución local de desarrollo
        csv_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
            "dataset",
            "tickets.csv"
        )

    logger.info(f"Iniciando ingesta de datos desde {csv_path}...")
    if not os.path.exists(csv_path):
        logger.error(f"Archivo no encontrado en {csv_path}. Abortando ingesta.")
        sys.exit(1)

    # Leer CSV
    df = pd.read_csv(csv_path)
    logger.info(f"Dataset cargado. Total de filas: {len(df)}")
    
    # Limpiar duplicados por Ticket ID y resetear el índice
    df = df.drop_duplicates(subset=['Ticket ID'], keep='first').reset_index(drop=True)
    logger.info(f"Dataset limpio de duplicados. Total de filas únicas: {len(df)}")

    # Crear tablas
    logger.info("Reiniciando tablas en la base de datos SQLite...")
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()

    # Si estamos en modo LLM real, limitamos la cantidad de tickets enriquecidos por LLM real
    # para no exceder las cuotas ni presupuestos gratis en la primera corrida, el resto va por mock.
    llm_enrichment_limit = 40 if LLM_PROVIDER in ["gemini", "openai", "deepseek"] else len(df)
    logger.info(f"Proveedor de LLM seleccionado: '{LLM_PROVIDER}'.")
    if LLM_PROVIDER != "mock":
        logger.info(f"Se procesarán los primeros {llm_enrichment_limit} tickets con el LLM real, y el resto con el motor de reglas heurístico para cuidar tu cuota.")

    start_time = time.time()
    
    try:
        for idx, row in df.iterrows():
            ticket_id = int(row['Ticket ID'])
            customer_name = str(row['Customer Name']).strip() if not pd.isna(row['Customer Name']) else "Anónimo"
            customer_email = clean_email(row['Customer Email'])
            
            try:
                customer_age = int(row['Customer Age']) if not pd.isna(row['Customer Age']) else None
            except ValueError:
                customer_age = None
                
            customer_gender = str(row['Customer Gender']).strip() if not pd.isna(row['Customer Gender']) else "Other"
            product_purchased = str(row['Product Purchased']).strip() if not pd.isna(row['Product Purchased']) else "General"
            date_of_purchase = parse_custom_date(row['Date of Purchase'])
            ticket_type = str(row['Ticket Type']).strip()
            ticket_subject = str(row['Ticket Subject']).strip()
            ticket_description = str(row['Ticket Description']).strip()
            ticket_status = str(row['Ticket Status']).strip()
            ticket_priority = normalize_priority(row['Ticket Priority'])
            ticket_channel = str(row['Ticket Channel']).strip()
            
            first_resp = str(row['First Response Time']).strip() if not pd.isna(row['First Response Time']) else None
            time_res = str(row['Time to Resolution']).strip() if not pd.isna(row['Time to Resolution']) else None
            satisfaction = clean_satisfaction(row['Customer Satisfaction Rating'])

            # Decidir si usar LLM real o Mock en base al índice
            if idx < llm_enrichment_limit:
                enrichment = enrich_ticket(
                    ticket_subject,
                    ticket_description,
                    product_purchased,
                    ticket_type
                )
                # Introducir un pequeño retardo si llamamos a una API externa
                if LLM_PROVIDER != "mock":
                    time.sleep(0.6)
            else:
                # Forzar Mock para cuidar cuotas de API
                enrichment = enrich_ticket(
                    ticket_subject,
                    ticket_description,
                    product_purchased,
                    "mock_fallback"
                )

            # Crear instancia de Ticket
            ticket_db = Ticket(
                ticket_id=ticket_id,
                customer_name=customer_name,
                customer_email=customer_email,
                customer_age=customer_age,
                customer_gender=customer_gender,
                product_purchased=product_purchased,
                date_of_purchase=date_of_purchase,
                ticket_type=normalize_category(ticket_type),
                ticket_subject=ticket_subject,
                ticket_description=ticket_description,
                ticket_status=ticket_status,
                ticket_priority=ticket_priority,
                ticket_channel=ticket_channel,
                first_response_time=first_resp,
                time_to_resolution=time_res,
                customer_satisfaction_rating=satisfaction,
                
                # Campos de IA
                ai_category=enrichment["category"],
                ai_priority=enrichment["priority"],
                ai_summary=enrichment["summary"],
                ai_sentiment=enrichment["sentiment"],
                ai_team=enrichment["team"]
            )
            
            db.add(ticket_db)

            if (idx + 1) % 50 == 0 or (idx + 1) == len(df):
                db.commit()
                logger.info(f"Progreso de Ingesta: {idx + 1} / {len(df)} tickets procesados.")

        duration = time.time() - start_time
        logger.info(f"¡Ingesta completada con éxito en {duration:.2f} segundos!")
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error durante la ingesta de datos: {e}")
        raise e
    finally:
        db.close()


if __name__ == "__main__":
    run_ingestion()
