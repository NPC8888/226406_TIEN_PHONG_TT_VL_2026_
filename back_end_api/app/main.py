from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os
from dotenv import load_dotenv
import app.models
import app.api.admin as admin
import app.api.user as user
import app.api.post_v2 as post

load_dotenv()

app = FastAPI()

frontend_url = os.getenv("FRONTEND_URL", "http://localhost:5173")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[frontend_url],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(user.router)
app.include_router(post.router)
app.include_router(admin.router)

@app.get("/")
def root():
    return {"message": "Smomer backend is running."}
