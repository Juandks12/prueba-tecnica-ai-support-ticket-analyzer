import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Cargar variables de entorno
load_dotenv()

# Obtener URL de base de datos del entorno, o usar SQLite por defecto
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./tickets.db")

# Asegurar que el directorio de la base de datos existe si es SQLite y resolver rutas relativas
if DATABASE_URL.startswith("sqlite"):
    if not DATABASE_URL.startswith("sqlite:////"):
        db_rel_path = DATABASE_URL.replace("sqlite:///", "")
        # Raíz del backend (2 niveles arriba desde backend/app/)
        backend_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        db_abs_path = os.path.abspath(os.path.join(backend_root, db_rel_path))
        DATABASE_URL = f"sqlite:////{db_abs_path}"

    db_path = DATABASE_URL.replace("sqlite:////", "")
    db_dir = os.path.dirname(db_path)
    if db_dir and not os.path.exists(db_dir):
        os.makedirs(db_dir, exist_ok=True)
    engine = create_engine(
        DATABASE_URL, connect_args={"check_same_thread": False}
    )
else:
    engine = create_engine(DATABASE_URL)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

# Dependencia para obtener la sesión de base de datos
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
