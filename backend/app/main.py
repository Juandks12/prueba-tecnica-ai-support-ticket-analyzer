import os
from fastapi import FastAPI, Depends, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional

from app.database import engine, Base, get_db
from app.services import db_service, ai_service
from scripts.ingest_data import run_ingestion

# Asegurar la creación de tablas al iniciar
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="AI Support Ticket Analyzer API",
    description="Backend API para ingerir, filtrar y analizar tickets de soporte con IA.",
    version="1.0.0"
)

# Permitir CORS para comunicación de contenedores y desarrollo local
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class QuestionRequest(BaseModel):
    question: str


@app.get("/")
def read_root():
    return {
        "message": "AI Support Ticket Analyzer API está corriendo. Ve a /docs para la documentación OpenAPI."
    }


@app.get("/api/tickets")
def read_tickets(
    skip: int = 0,
    limit: int = 50,
    category: Optional[str] = None,
    priority: Optional[str] = None,
    status: Optional[str] = None,
    search: Optional[str] = None,
    db: Session = Depends(get_db)
):
    tickets, total = db_service.get_tickets(
        db=db,
        skip=skip,
        limit=limit,
        category=category,
        priority=priority,
        status=status,
        search=search
    )
    
    tickets_list = []
    for t in tickets:
        tickets_list.append({
            "ticket_id": t.ticket_id,
            "customer_name": t.customer_name,
            "customer_email": t.customer_email,
            "customer_age": t.customer_age,
            "customer_gender": t.customer_gender,
            "product_purchased": t.product_purchased,
            "date_of_purchase": t.date_of_purchase,
            "ticket_type": t.ticket_type,
            "ticket_subject": t.ticket_subject,
            "ticket_description": t.ticket_description,
            "ticket_status": t.ticket_status,
            "ticket_priority": t.ticket_priority,
            "ticket_channel": t.ticket_channel,
            "first_response_time": t.first_response_time,
            "time_to_resolution": t.time_to_resolution,
            "customer_satisfaction_rating": t.customer_satisfaction_rating,
            
            # Enriquecidos por IA
            "ai_category": t.ai_category,
            "ai_priority": t.ai_priority,
            "ai_summary": t.ai_summary,
            "ai_sentiment": t.ai_sentiment,
            "ai_team": t.ai_team
        })
        
    return {
        "tickets": tickets_list,
        "total": total,
        "skip": skip,
        "limit": limit
    }


@app.get("/api/metrics")
def read_metrics(db: Session = Depends(get_db)):
    try:
        return db_service.get_metrics(db)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error al calcular las métricas: {str(e)}"
        )


@app.post("/api/ingest")
def start_ingest(background_tasks: BackgroundTasks):
    background_tasks.add_task(run_ingestion)
    return {
        "status": "success",
        "message": "Proceso de ingesta de datos iniciado en segundo plano. La base de datos se estará actualizando."
    }


@app.post("/api/ask")
def ask_ai(req: QuestionRequest, db: Session = Depends(get_db)):
    if not req.question.strip():
        raise HTTPException(
            status_code=400,
            detail="La pregunta del usuario no puede estar vacía."
        )
    
    # 1. Cargar políticas de soporte como base de conocimientos
    policies_text = ""
    for filename in ["policies.md", "routing_rules.md"]:
        path = f"/knowledge_base/{filename}"
        if not os.path.exists(path):
            # Fallback para desarrollo local fuera de Docker
            path = os.path.join(
                os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
                "knowledge_base",
                filename
            )
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                policies_text += f"\n--- Archivo: {filename} ---\n" + f.read()
                
    if not policies_text:
        policies_text = "No se encontraron políticas de la base de conocimientos."

    # 2. Obtener los tickets más recientes para el contexto
    tickets = db_service.get_all_tickets_for_context(db, limit=120)
    tickets_list = []
    for t in tickets:
        tickets_list.append({
            "ticket_id": t.ticket_id,
            "customer_name": t.customer_name,
            "customer_age": t.customer_age,
            "product_purchased": t.product_purchased,
            "ticket_subject": t.ticket_subject,
            "ticket_description": t.ticket_description,
            "ticket_status": t.ticket_status,
            "customer_satisfaction_rating": t.customer_satisfaction_rating,
            "ai_category": t.ai_category,
            "ai_priority": t.ai_priority,
            "ai_summary": t.ai_summary,
            "ai_sentiment": t.ai_sentiment,
            "ai_team": t.ai_team
        })

    try:
        answer = ai_service.ask_question(
            question=req.question,
            context_tickets=tickets_list,
            policies_text=policies_text
        )
        return {"answer": answer}
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error en el servicio de IA: {str(e)}"
        )

# Servir archivos estáticos del frontend si existen en el entorno local
frontend_dir = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "frontend",
    "src"
)
if os.path.exists(frontend_dir):
    app.mount("/", StaticFiles(directory=frontend_dir, html=True), name="static")
