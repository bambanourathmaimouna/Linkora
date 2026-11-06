from fastapi import (
    APIRouter, Request, Depends, Form,
    HTTPException, UploadFile, File
)
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from database import get_db
from models import Groupe, Message
from pathlib import Path
from uuid import uuid4

router = APIRouter()
templates = Jinja2Templates(directory="templates")

# Dossier de stockage des images
DOSSIER_IMAGES = Path("static/images")
DOSSIER_IMAGES.mkdir(parents=True, exist_ok=True)


# Afficher la discussion
@router.get("/discussion/{groupe_id}", response_class=HTMLResponse)
def afficher_discussion(
    request: Request,
    groupe_id: int,
    db: Session = Depends(get_db)
):
    groupe = db.query(Groupe).filter_by(id=groupe_id).first()

    if not groupe:
        raise HTTPException(status_code=404, detail="Groupe introuvable")

    messages = (
        db.query(Message)
        .filter_by(groupe_id=groupe_id)
        .order_by(Message.date_envoi.asc())
        .all()
    )

    return templates.TemplateResponse(
        request=request,
        name="discussion.html",
        context={
            "groupe": groupe,
            "messages": messages
        }
    )


# Envoyer un message texte ou une image
@router.post("/envoyer_message")
def envoyer_message(
    request: Request,
    groupe_id: int = Form(...),
    contenu: str = Form(""),
    image: UploadFile | None = File(None),
    db: Session = Depends(get_db)
):
    utilisateur_id = request.session.get("utilisateur_id")

    if not utilisateur_id:
        raise HTTPException(
            status_code=401,
            detail="Vous devez vous connecter."
        )

    groupe = db.query(Groupe).filter_by(id=groupe_id).first()

    if not groupe:
        raise HTTPException(status_code=404, detail="Groupe introuvable")

    chemin_image = None

    # Vérifier et enregistrer l'image
    if image and image.filename:

        if not image.content_type or not image.content_type.startswith("image/"):
            raise HTTPException(
                status_code=400,
                detail="Veuillez sélectionner une image."
            )

        extensions_autorisees = {".jpg", ".jpeg", ".png", ".gif", ".webp"}
        extension = Path(image.filename).suffix.lower()

        if extension not in extensions_autorisees:
            raise HTTPException(
                status_code=400,
                detail="Format d'image non autorisé."
            )

        contenu_image = image.file.read()

        if len(contenu_image) > 5 * 1024 * 1024:
            raise HTTPException(
                status_code=400,
                detail="L'image ne doit pas dépasser 5 Mo."
            )

        nom_image = f"{uuid4().hex}{extension}"
        chemin_fichier = DOSSIER_IMAGES / nom_image

        with open(chemin_fichier, "wb") as fichier:
            fichier.write(contenu_image)

        chemin_image = f"images/{nom_image}"

    # Vérifier qu'il existe au moins un contenu
    if not contenu.strip() and not chemin_image:
        raise HTTPException(
            status_code=400,
            detail="Veuillez écrire un message ou sélectionner une image."
        )

    nouveau_message = Message(
    contenu=contenu.strip() or "",
    image=chemin_image,
    utilisateur_id=utilisateur_id,
    groupe_id=groupe_id
)

    db.add(nouveau_message)
    db.commit()

    return RedirectResponse(
        url=f"/discussion/{groupe_id}",
        status_code=303
    )