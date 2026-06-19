from sqlalchemy.orm import Session
from sqlalchemy import func, or_
from app.models import Ticket
from typing import Dict, Any, List

def get_tickets(
    db: Session,
    skip: int = 0,
    limit: int = 50,
    category: str = None,
    priority: str = None,
    status: str = None,
    search: str = None
):
    """Obtiene una lista de tickets aplicando filtros opcionales, paginación y búsqueda."""
    query = db.query(Ticket)
    
    if category:
        query = query.filter(Ticket.ai_category == category)
    if priority:
        query = query.filter(Ticket.ai_priority == priority)
    if status:
        query = query.filter(Ticket.ticket_status == status)
    if search:
        search_filter = f"%{search}%"
        query = query.filter(
            or_(
                Ticket.customer_name.like(search_filter),
                Ticket.customer_email.like(search_filter),
                Ticket.ticket_subject.like(search_filter),
                Ticket.ticket_description.like(search_filter),
                Ticket.product_purchased.like(search_filter)
            )
        )
        
    total = query.count()
    tickets = query.offset(skip).limit(limit).all()
    
    return tickets, total

def get_metrics(db: Session) -> Dict[str, Any]:
    """Calcula las métricas agregadas esenciales para el Dashboard."""
    total_tickets = db.query(Ticket).count()
    
    # Cantidad por prioridad
    priority_counts = db.query(Ticket.ai_priority, func.count(Ticket.ticket_id)).group_by(Ticket.ai_priority).all()
    priority_dict = {p: count for p, count in priority_counts if p}
    
    # Cantidad por categoría
    category_counts = db.query(Ticket.ai_category, func.count(Ticket.ticket_id)).group_by(Ticket.ai_category).all()
    category_dict = {c: count for c, count in category_counts if c}

    # Cantidad por estado
    status_counts = db.query(Ticket.ticket_status, func.count(Ticket.ticket_id)).group_by(Ticket.ticket_status).all()
    status_dict = {s: count for s, count in status_counts if s}
    
    # Satisfacción promedio (usualmente en cerrados)
    avg_sat = db.query(func.avg(Ticket.customer_satisfaction_rating)).filter(Ticket.customer_satisfaction_rating.isnot(None)).scalar()
    
    # Top 5 productos más problemáticos
    product_counts = db.query(Ticket.product_purchased, func.count(Ticket.ticket_id))\
        .group_by(Ticket.product_purchased)\
        .order_by(func.count(Ticket.ticket_id).desc())\
        .limit(5).all()
    product_dict = {p: count for p, count in product_counts if p}

    return {
        "total_tickets": total_tickets,
        "priorities": priority_dict,
        "categories": category_dict,
        "statuses": status_dict,
        "average_satisfaction": round(avg_sat, 2) if avg_sat else 0.0,
        "top_products": product_dict
    }

def get_all_tickets_for_context(db: Session, limit: int = 150) -> List[Ticket]:
    """Retorna una lista de tickets relevantes para inyectar como contexto en el LLM."""
    return db.query(Ticket).order_by(Ticket.ticket_id.desc()).limit(limit).all()
