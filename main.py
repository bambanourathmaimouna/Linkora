from fastapi import FastAPI, Request, Depends, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from pwdlib import PasswordHash
from starlette.middleware.sessions import SessionMiddleware
from fastapi import Form
from fastapi.responses import RedirectResponse
from routes import message
from database import engine, Base, get_db
from models import Utilisateur, Groupe, Message


app = FastAPI(title="WhatsApp")
password_hash = PasswordHash.recommended()
app.include_router(message.router)
# Création des tables
Base.metadata.create_all(bind=engine)

# Configuration des templates
templates = Jinja2Templates(directory="templates")

# Configuration des fichiers CSS
app.mount("/static", StaticFiles(directory="static"), name="static")

# Création des groupes
def creer_groupes():
    with Session(engine) as db:
        groupes = [
            {"nom": "Santé", "description": "Discussions autour de la santé"},
            {"nom": "Sport", "description": "Discussions autour du sport"},
            {"nom": "Éducation", "description": "Discussions autour de l'éducation"},
            {"nom": "Mode", "description": "Discussions autour de la mode"}
        ]
        for groupe in groupes:
            existe = db.query(Groupe).filter_by(nom=groupe["nom"]).first()
            if not existe:
                nouveau_groupe = Groupe(nom=groupe["nom"],description=groupe["description"])
                db.add(nouveau_groupe)
        db.commit()
creer_groupes()

# Page d'accueil
@app.get("/", response_class=HTMLResponse)
def accueil(request: Request, db: Session = Depends(get_db)):
    groupes = db.query(Groupe).all()
    return templates.TemplateResponse(request=request, name="accueil.html", context={"groupes": groupes})

# Sélection d'un groupe
@app.get("/connexion/{groupe_id}", response_class=HTMLResponse)
def connexion(request: Request, groupe_id: int,
    db: Session = Depends(get_db)):
    groupe = db.query(Groupe).filter_by(id=groupe_id).first()
    if not groupe:
        raise HTTPException(status_code=404, detail="Groupe introuvable")
    return templates.TemplateResponse(
request=request,name="connexion.html",context={"groupe": groupe})
app.add_middleware(SessionMiddleware,secret_key="ma_cle_secrete_whatsapp_2026")

@app.post("/connexion/{groupe_id}", response_class=HTMLResponse)
def verifier_connexion(
    request: Request,
    groupe_id: int,
    username: str = Form(...),
    mot_de_passe: str = Form(...),
    db: Session = Depends(get_db)
):
    # Rechercher le groupe
    groupe = db.query(Groupe).filter_by(id=groupe_id).first()
    if not groupe:
        raise HTTPException(status_code=404, detail="Groupe introuvable")
    # Rechercher l'utilisateur
    utilisateur = db.query(Utilisateur).filter_by(username=username).first()

    # Vérifier le compte et le mot de passe
    if not utilisateur or not password_hash.verify(mot_de_passe,utilisateur.mot_de_passe):
        return templates.TemplateResponse(
            request=request,name="connexion.html",
            context={"groupe": groupe,"erreur": "Identifiant ou mot de passe incorrect"},status_code=401)

    # Vérifier si l'utilisateur appartient au groupe
    if groupe not in utilisateur.groupes:
        return templates.TemplateResponse(
            request=request,name="connexion.html",
            context={
                "groupe": groupe,
                "erreur": "Vous n'êtes pas membre de ce groupe."
            },status_code=403)

    # Enregistrer l'utilisateur dans la session
    request.session["utilisateur_id"] = utilisateur.id
    request.session["groupe_id"] = groupe.id
    return RedirectResponse(url=f"/discussion/{groupe_id}",status_code=303)

@app.get("/inscription/{groupe_id}", response_class=HTMLResponse)
def afficher_inscription(
    request: Request,
    groupe_id: int,
    db: Session = Depends(get_db)
):
    groupe = db.query(Groupe).filter_by(id=groupe_id).first()
    if not groupe:
        raise HTTPException(status_code=404, detail="Groupe introuvable")
    return templates.TemplateResponse(request=request, name="inscription.html",context={"groupe": groupe})

@app.post("/inscription/{groupe_id}")
def inscrire_utilisateur(
    request: Request,
    groupe_id: int,
    username: str = Form(...),
    email: str = Form(...),
    mot_de_passe: str = Form(...),
    db: Session = Depends(get_db)
):
    groupe = db.query(Groupe).filter_by(id=groupe_id).first()

    if not groupe:
        raise HTTPException(status_code=404, detail="Groupe introuvable")

    # Vérifier si le nom d'utilisateur existe déjà
    utilisateur_existant = db.query(Utilisateur).filter_by(username=username).first()
    if utilisateur_existant:
       return templates.TemplateResponse(
        request=request,name="inscription.html",
        context={"groupe": groupe, "erreur": "Ce nom d'utilisateur existe déjà."},
        status_code=400)
    
    # Vérifier si l'email existe déjà
    email_existant = db.query(Utilisateur).filter_by(email=email).first()
    if email_existant:
        raise HTTPException(status_code=400, detail="Cette adresse email existe déjà.")

    # Créer le nouvel utilisateur
    nouvel_utilisateur = Utilisateur( username=username,email=email,mot_de_passe=password_hash.hash(mot_de_passe))

    # Ajouter l'utilisateur au groupe choisi
    nouvel_utilisateur.groupes.append(groupe)
    db.add(nouvel_utilisateur)
    db.commit()
    return RedirectResponse(url=f"/connexion/{groupe_id}",status_code=303)

@app.get("/health")
def health():
    return {"status": "ok"}