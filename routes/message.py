from fastapi import APIRouter, Request, Depends, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from database import get_db
from models import Groupe, Message

router = APIRouter()
templates = Jinja2Templates(directory="templates")

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
    messages = db.query(Message).filter_by( groupe_id=groupe_id).order_by(Message.date_envoi.asc()).all()
    return templates.TemplateResponse(
        request=request,
        name="discussion.html",
        context={"groupe": groupe,"messages": messages})


# Envoyer un message
@router.post("/envoyer_message")
def envoyer_message(
    request: Request,
    groupe_id: int = Form(...),
    contenu: str = Form(...),
    db: Session = Depends(get_db)
):
    utilisateur_id = request.session.get("utilisateur_id")
    if not utilisateur_id:
        raise HTTPException( status_code=401, detail="Vous devez vous connecter.")

    groupe = db.query(Groupe).filter_by(id=groupe_id).first()
    if not groupe:
        raise HTTPException(status_code=404,detail="Groupe introuvable")
    nouveau_message = Message(contenu=contenu,utilisateur_id=utilisateur_id, groupe_id=groupe_id)

    db.add(nouveau_message)
    db.commit()
    return RedirectResponse( url=f"/discussion/{groupe_id}", status_code=303)