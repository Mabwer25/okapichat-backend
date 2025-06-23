"""
OkapiChat Backend API
Backend Python FastAPI pour l'application OkapiChat RDC
Déployé sur Render avec Docker
"""

from fastapi import FastAPI, HTTPException, Depends, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import JSONResponse
from pydantic import BaseModel, EmailStr
from typing import Optional, List, Dict, Any
import os
import uvicorn
import aiofiles
import hashlib
import hmac
import jwt
import logging
from datetime import datetime, timedelta
import asyncio
import json
from pathlib import Path

# Configuration logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration environnement
SUPABASE_URL = os.getenv("SUPABASE_URL", "https://xzjqpdnkxiizskqnckox.supabase.co")
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY", "your-anon-key")
JWT_SECRET = os.getenv("JWT_SECRET", "okapichat-jwt-secret-key-rdc-2025")
ENVIRONMENT = os.getenv("ENVIRONMENT", "production")
UPLOAD_DIR = Path("uploads")

# Créer le dossier uploads
UPLOAD_DIR.mkdir(exist_ok=True)

# Initialisation FastAPI
app = FastAPI(
    title="OkapiChat API",
    description="Backend API pour le réseau social congolais OkapiChat 🦌🇨🇩",
    version="1.0.0",
    docs_url="/docs" if ENVIRONMENT == "development" else None,
    redoc_url="/redoc" if ENVIRONMENT == "development" else None
)

# Configuration CORS pour le frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://okapichat-rdc.netlify.app",
        "https://*.netlify.app",
        "http://localhost:3000",
        "http://localhost:8080",
        "http://127.0.0.1:8080",
        "https://okapichat.com",
        "capacitor://localhost",  # Pour l'app mobile
        "ionic://localhost",       # Pour l'app mobile
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security
security = HTTPBearer()

# Models Pydantic
class PostCreate(BaseModel):
    content: str
    user_id: str
    user_name: str
    language: Optional[str] = "fr"
    province: Optional[str] = None

class PostResponse(BaseModel):
    id: str
    content: str
    user_id: str
    user_name: str
    created_at: datetime
    language: Optional[str] = "fr"
    province: Optional[str] = None
    likes_count: int = 0
    comments_count: int = 0

class UserProfile(BaseModel):
    user_id: str
    full_name: str
    email: EmailStr
    bio: Optional[str] = None
    province: Optional[str] = None
    languages: List[str] = ["fr"]
    avatar_url: Optional[str] = None

class AnalyticsData(BaseModel):
    event: str
    user_id: Optional[str] = None
    data: Dict[str, Any] = {}
    timestamp: datetime = datetime.utcnow()

class NotificationRequest(BaseModel):
    user_id: str
    title: str
    body: str
    data: Optional[Dict[str, Any]] = {}

# Fonction pour vérifier le token JWT
def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expiré")
    except jwt.JWTError:
        raise HTTPException(status_code=401, detail="Token invalide")

# Routes principales

@app.get("/")
async def root():
    """Route racine avec informations API"""
    return {
        "message": "🦌 OkapiChat Backend API",
        "description": "Backend pour le réseau social congolais",
        "version": "1.0.0",
        "status": "✅ Opérationnel",
        "rdc": "🇨🇩 Vive la RDC !",
        "languages": ["français", "lingala", "kikongo", "swahili", "tshiluba"],
        "endpoints": {
            "posts": "/api/posts",
            "media": "/api/media",
            "analytics": "/api/analytics",
            "notifications": "/api/notifications",
            "health": "/health"
        }
    }

@app.get("/health")
async def health_check():
    """Health check pour Render"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "service": "okapichat-backend",
        "version": "1.0.0"
    }

# Routes Posts
@app.get("/api/posts")
async def get_posts(limit: int = 50, offset: int = 0):
    """Récupérer les posts avec pagination"""
    try:
        # Ici vous pourriez intégrer avec Supabase ou votre DB
        # Pour l'instant, retour d'exemple
        posts = [
            {
                "id": f"post-{i}",
                "content": f"Post exemple {i} en français 🇨🇩",
                "user_id": "user-1",
                "user_name": "Utilisateur Test",
                "created_at": (datetime.utcnow() - timedelta(hours=i)).isoformat(),
                "language": "fr",
                "province": "Kinshasa",
                "likes_count": i * 2,
                "comments_count": i
            }
            for i in range(1, min(limit + 1, 11))
        ]
        
        return {
            "posts": posts,
            "total": len(posts),
            "limit": limit,
            "offset": offset
        }
        
    except Exception as e:
        logger.error(f"Erreur récupération posts: {e}")
        raise HTTPException(status_code=500, detail="Erreur serveur")

@app.post("/api/posts")
async def create_post(post: PostCreate, user_data: dict = Depends(verify_token)):
    """Créer un nouveau post"""
    try:
        # Validation du contenu
        if len(post.content.strip()) < 1:
            raise HTTPException(status_code=400, detail="Le contenu ne peut pas être vide")
        
        if len(post.content) > 1000:
            raise HTTPException(status_code=400, detail="Le contenu ne peut pas dépasser 1000 caractères")
        
        # Ici vous intégreriez avec votre base de données
        new_post = {
            "id": f"post-{datetime.utcnow().timestamp()}",
            "content": post.content,
            "user_id": post.user_id,
            "user_name": post.user_name,
            "created_at": datetime.utcnow().isoformat(),
            "language": post.language,
            "province": post.province,
            "likes_count": 0,
            "comments_count": 0
        }
        
        logger.info(f"Nouveau post créé: {new_post['id']}")
        return new_post
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erreur création post: {e}")
        raise HTTPException(status_code=500, detail="Erreur serveur")

# Routes Media/Upload
@app.post("/api/media/upload")
async def upload_media(
    file: UploadFile = File(...),
    user_id: str = Form(...),
    user_data: dict = Depends(verify_token)
):
    """Upload d'images/médias"""
    try:
        # Validation du fichier
        if not file.content_type.startswith("image/"):
            raise HTTPException(status_code=400, detail="Seules les images sont autorisées")
        
        if file.size > 5 * 1024 * 1024:  # 5MB max
            raise HTTPException(status_code=400, detail="Fichier trop volumineux (max 5MB)")
        
        # Générer nom de fichier unique
        file_extension = file.filename.split(".")[-1] if "." in file.filename else "jpg"
        unique_filename = f"{user_id}_{datetime.utcnow().timestamp()}.{file_extension}"
        file_path = UPLOAD_DIR / unique_filename
        
        # Sauvegarder le fichier
        async with aiofiles.open(file_path, "wb") as f:
            content = await file.read()
            await f.write(content)
        
        # URL de retour (adaptez selon votre configuration)
        file_url = f"/api/media/{unique_filename}"
        
        logger.info(f"Fichier uploadé: {unique_filename}")
        return {
            "filename": unique_filename,
            "url": file_url,
            "size": len(content),
            "content_type": file.content_type
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erreur upload: {e}")
        raise HTTPException(status_code=500, detail="Erreur upload")

@app.get("/api/media/{filename}")
async def get_media(filename: str):
    """Servir les fichiers média"""
    try:
        file_path = UPLOAD_DIR / filename
        if not file_path.exists():
            raise HTTPException(status_code=404, detail="Fichier non trouvé")
        
        # Ici vous pourriez implémenter la lecture du fichier
        # Pour l'instant, retour d'info sur le fichier
        return {
            "filename": filename,
            "exists": True,
            "path": str(file_path)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erreur récupération média: {e}")
        raise HTTPException(status_code=500, detail="Erreur serveur")

# Routes Analytics
@app.post("/api/analytics/track")
async def track_event(analytics: AnalyticsData):
    """Tracker les événements analytiques"""
    try:
        # Log l'événement (en production, sauvegarder en DB)
        logger.info(f"Analytics: {analytics.event} - User: {analytics.user_id}")
        
        # Ici vous pourriez intégrer avec Google Analytics, Mixpanel, etc.
        
        return {
            "status": "tracked",
            "event": analytics.event,
            "timestamp": analytics.timestamp.isoformat()
        }
        
    except Exception as e:
        logger.error(f"Erreur tracking: {e}")
        raise HTTPException(status_code=500, detail="Erreur tracking")

@app.get("/api/analytics/stats")
async def get_stats(user_data: dict = Depends(verify_token)):
    """Récupérer les statistiques globales"""
    try:
        # Stats exemple (à remplacer par vraies données)
        stats = {
            "total_users": 1337,
            "total_posts": 5678,
            "active_users_today": 234,
            "posts_today": 89,
            "languages_distribution": {
                "français": 45,
                "lingala": 25,
                "kikongo": 15,
                "swahili": 10,
                "tshiluba": 5
            },
            "provinces_top": [
                {"name": "Kinshasa", "users": 456},
                {"name": "Lubumbashi", "users": 234},
                {"name": "Goma", "users": 123},
                {"name": "Kisangani", "users": 89},
                {"name": "Bukavu", "users": 67}
            ]
        }
        
        return stats
        
    except Exception as e:
        logger.error(f"Erreur stats: {e}")
        raise HTTPException(status_code=500, detail="Erreur serveur")

# Routes Notifications
@app.post("/api/notifications/send")
async def send_notification(notification: NotificationRequest, user_data: dict = Depends(verify_token)):
    """Envoyer notification push"""
    try:
        # Ici vous intégreriez avec Firebase Cloud Messaging ou similar
        logger.info(f"Notification envoyée à {notification.user_id}: {notification.title}")
        
        # Simulation envoi
        return {
            "status": "sent",
            "user_id": notification.user_id,
            "title": notification.title,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Erreur notification: {e}")
        raise HTTPException(status_code=500, detail="Erreur notification")

# Routes utilitaires RDC
@app.get("/api/rdc/provinces")
async def get_rdc_provinces():
    """Liste des 26 provinces de la RDC"""
    provinces = [
        "Kinshasa", "Kongo Central", "Kwango", "Kwilu", "Mai-Ndombe",
        "Kasaï", "Kasaï Central", "Kasaï Oriental", "Lomami", "Sankuru",
        "Maniema", "Sud-Kivu", "Nord-Kivu", "Ituri", "Haut-Uele",
        "Bas-Uele", "Tshopo", "Mongala", "Nord-Ubangi", "Sud-Ubangi",
        "Équateur", "Tshuapa", "Tanganyika", "Haut-Lomami", "Lualaba", "Haut-Katanga"
    ]
    return {"provinces": provinces, "total": len(provinces)}

@app.get("/api/rdc/languages")
async def get_rdc_languages():
    """Langues supportées par OkapiChat"""
    languages = {
        "fr": {"name": "Français", "native": "Français", "flag": "🇫🇷"},
        "ln": {"name": "Lingala", "native": "Lingála", "flag": "🇨🇩"},
        "kg": {"name": "Kikongo", "native": "Kikongo", "flag": "🇨🇩"},
        "sw": {"name": "Swahili", "native": "Kiswahili", "flag": "🇨🇩"},
        "lu": {"name": "Tshiluba", "native": "Tshiluba", "flag": "🇨🇩"}
    }
    return {"languages": languages}

# Gestion des erreurs globales
@app.exception_handler(404)
async def not_found_handler(request, exc):
    return JSONResponse(
        status_code=404,
        content={
            "error": "Endpoint non trouvé",
            "message": "Vérifiez l'URL de votre requête",
            "available_endpoints": [
                "/", "/health", "/api/posts", "/api/media/upload",
                "/api/analytics/track", "/api/notifications/send"
            ]
        }
    )

@app.exception_handler(500)
async def internal_error_handler(request, exc):
    logger.error(f"Erreur serveur: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "error": "Erreur interne du serveur",
            "message": "Une erreur est survenue. Veuillez réessayer plus tard.",
            "support": "support@okapichat.com"
        }
    )

# Middleware de logging des requêtes
@app.middleware("http")
async def log_requests(request, call_next):
    start_time = datetime.utcnow()
    
    # Traiter la requête
    response = await call_next(request)
    
    # Logger la requête
    process_time = (datetime.utcnow() - start_time).total_seconds()
    logger.info(
        f"{request.method} {request.url.path} - "
        f"Status: {response.status_code} - "
        f"Time: {process_time:.3f}s"
    )
    
    return response

# Point d'entrée pour le développement local
if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=port,
        reload=ENVIRONMENT == "development",
        log_level="info"
    )