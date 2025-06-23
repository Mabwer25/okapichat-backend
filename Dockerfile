# Dockerfile pour OkapiChat Backend
# Image Python optimisée pour déploiement Render

# Image de base Python optimisée
FROM python:3.11-slim

# Métadonnées de l'image
LABEL maintainer="OkapiChat Team <support@okapichat.com>"
LABEL description="Backend API pour OkapiChat - Réseau social RDC 🦌🇨🇩"
LABEL version="1.0.0"

# Variables d'environnement
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    ENVIRONMENT=production \
    PORT=8000

# Créer utilisateur non-root pour la sécurité
RUN groupadd -r okapichat && useradd -r -g okapichat okapichat

# Installer dépendances système
RUN apt-get update && apt-get install -y \
    # Dépendances pour compilation Python packages
    gcc \
    g++ \
    # Dépendances pour images/médias
    libjpeg-dev \
    libpng-dev \
    libwebp-dev \
    # Dépendances pour PostgreSQL
    libpq-dev \
    # Utilitaires
    curl \
    wget \
    # Nettoyage cache
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Définir le répertoire de travail
WORKDIR /app

# Copier et installer les dépendances Python
COPY requirements.txt .
RUN pip install --upgrade pip setuptools wheel && \
    pip install -r requirements.txt && \
    pip cache purge

# Copier le code de l'application
COPY . .

# Créer les dossiers nécessaires
RUN mkdir -p uploads logs static && \
    chown -R okapichat:okapichat /app

# Basculer vers l'utilisateur non-root
USER okapichat

# Exposer le port
EXPOSE $PORT

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:$PORT/health || exit 1

# Commande de démarrage production
CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port $PORT --workers 2 --access-log --log-level info"]

# Alternative avec Gunicorn pour haute performance
# CMD ["sh", "-c", "gunicorn main:app -w 2 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:$PORT --access-logfile - --error-logfile - --log-level info"]