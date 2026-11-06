from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase

# Adresse de notre base de données
DATABASE_URL = "sqlite:///./whatsapp.db"

# Création de la connexion
engine = create_engine( DATABASE_URL,connect_args={"check_same_thread": False})

# Création de la classe de base
class Base(DeclarativeBase):
    pass

# Création des sessions
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
# Fonction pour obtenir une session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()