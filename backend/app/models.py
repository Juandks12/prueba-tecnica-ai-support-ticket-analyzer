from sqlalchemy import Column, Integer, String, Float
from .database import Base

class Ticket(Base):
    __tablename__ = "tickets"

    ticket_id = Column(Integer, primary_key=True, index=True)
    customer_name = Column(String, nullable=True)
    customer_email = Column(String, nullable=True)
    customer_age = Column(Integer, nullable=True)
    customer_gender = Column(String, nullable=True)
    product_purchased = Column(String, nullable=True)
    date_of_purchase = Column(String, nullable=True)  # Guardado unificado como YYYY-MM-DD
    ticket_type = Column(String, nullable=True)
    ticket_subject = Column(String, nullable=True)
    ticket_description = Column(String, nullable=True)
    ticket_status = Column(String, nullable=True)
    ticket_priority = Column(String, nullable=True)
    ticket_channel = Column(String, nullable=True)
    first_response_time = Column(String, nullable=True)
    time_to_resolution = Column(String, nullable=True)
    customer_satisfaction_rating = Column(Float, nullable=True)

    # Campos enriquecidos mediante IA
    ai_category = Column(String, nullable=True)
    ai_priority = Column(String, nullable=True)
    ai_summary = Column(String, nullable=True)
    ai_sentiment = Column(String, nullable=True)
    ai_team = Column(String, nullable=True)
