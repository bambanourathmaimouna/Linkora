from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime, Table
from sqlalchemy.orm import relationship, Mapped, mapped_column
from datetime import datetime, timezone
from database import Base


membres_groupe = Table(
    "membres_groupe",
    Base.metadata,
    Column("utilisateur_id", ForeignKey("utilisateurs.id"), primary_key=True),
    Column("groupe_id", ForeignKey("groupes.id"), primary_key=True)
)

class Utilisateur(Base):
    __tablename__ = "utilisateurs"
    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(50), unique=True)
    email: Mapped[str] = mapped_column(String(100), unique=True)
    mot_de_passe: Mapped[str] = mapped_column(String(255))
    groupes = relationship("Groupe",secondary=membres_groupe, back_populates="membres")
    messages = relationship("Message", back_populates="auteur")

class Groupe(Base):
    __tablename__ = "groupes"
    id: Mapped[int] = mapped_column(primary_key=True)
    nom: Mapped[str] = mapped_column(String(100), unique=True)
    description: Mapped[str] = mapped_column(Text, nullable=True)
    membres = relationship( "Utilisateur",secondary=membres_groupe, back_populates="groupes")
    messages = relationship("Message", back_populates="groupe")


class Message(Base):
    __tablename__ = "messages"
    id: Mapped[int] = mapped_column(primary_key=True)
    contenu: Mapped[str | None] = mapped_column(Text, nullable=True)
    image: Mapped[str | None] = mapped_column(String(255), nullable=True)
    date_envoi: Mapped[datetime] = mapped_column(DateTime(timezone=True),default=lambda: datetime.now(timezone.utc))
    utilisateur_id: Mapped[int] = mapped_column(ForeignKey("utilisateurs.id"))
    groupe_id: Mapped[int] = mapped_column(ForeignKey("groupes.id"))
    auteur = relationship("Utilisateur", back_populates="messages")
    groupe = relationship("Groupe", back_populates="messages")



