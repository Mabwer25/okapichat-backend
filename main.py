# app/main.py
from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def root():
    return {"message": "Bienvenue sur l'API OkapiChat 🚀"}

@app.get("/ping")
def ping():
    return {"pong": True}