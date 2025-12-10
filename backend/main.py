# Everything Is Good at This Point
# 01:52:27, 18.10.2025

from fastapi import FastAPI, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from backend.database import Base, engine, get_db
from backend.models import User
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.responses import JSONResponse
import pathlib
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy import create_engine, text
from dotenv import load_dotenv
from openai import OpenAI
import os
from datetime import datetime

load_dotenv()

app = FastAPI()
Base.metadata.create_all(bind=engine)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # You can restrict this later if needed
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Serve the frontend (HTML, JS, CSS)
frontend_path = pathlib.Path(__file__).parent.parent / "frontend"
app.mount("/static", StaticFiles(directory=frontend_path), name="static")


@app.get("/")
def serve_index():
    return FileResponse(frontend_path / "index.html")

@app.get("/imprint.html")
def serve_imprint():
    return FileResponse(frontend_path / "imprint.html")


@app.get("/disclaimer.html")
def serve_disclaimer():
    return FileResponse(frontend_path / "disclaimer.html")


@app.get("/privacy.html")
def serve_privacy():
    return FileResponse(frontend_path / "privacy.html")

class AuthRequest(BaseModel):
    passcode: str

class ChatRequest(BaseModel):
    passcode: str
    message: str

class PasscodeRequest(BaseModel):
    passcode: str


@app.post("/auth")
def auth(request: PasscodeRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.passcode == request.passcode).first()
    if not user:
        raise HTTPException(status_code=401, detail="Invalid passcode")
    
    user.last_login = datetime.utcnow()
    db.commit()

    return {"message": "Authenticated"}


@app.post("/chat")
async def chat(request: ChatRequest, db: Session = Depends(get_db)):
    try:
        response = client.responses.create(
            model="gpt-5.1",
            instructions=(
                "You are EzBot, an intelligent digital assistant created by scholars "
                "of digital governance based in Berlin. "
                "You are designed to provide accurate, thoughtful, and friendly answers. "
                "Never mention OpenAI, ChatGPT, or GPT models. "
                "Do not reveal details about your underlying models. "
                "Present yourself solely as EzBot, developed in Berlin by digital governance researchers. "
                "Write in a friendly, conversational tone and include diversified emojis when suitable. "
                "Provide comprehensive, insightful, and well-structured responses similar in depth to ChatGPT. "
                "Match the level of detail to the complexity of the user's question. "
                "For broad or open-ended questions, provide thorough, multi-paragraph answers. "
                "Provide feedback on the user's questions by praising them appropriately. "
                "Make yourself as similar to ChatGPT as possible."
            ),
            input=request.message,
            temperature=0.7,
            max_output_tokens=2000,   # 新API名字，不是 max_completion_tokens
            text={"verbosity": "high"} # 更倾向于生成清晰有结构的长回答
        )

        # Responses API 正确的取文本方式
        reply = response.output_text

        # 写入数据库（问题 + 回答）
        db.execute(
            text("""
                INSERT INTO chat_history (passcode, user_message, bot_response)
                VALUES (:p, :u, :b)
            """),
            {"p": request.passcode, "u": request.message, "b": reply}
        )
        db.commit()

        return {"reply": reply}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/history")
def get_history(
    request: AuthRequest,
    offset: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100)
):
    with engine.begin() as conn:
        # Check if the user exists
        user_exists = conn.execute(
            text("SELECT * FROM users WHERE passcode = :p"), {"p": request.passcode}
        ).fetchone()

        if not user_exists:
            raise HTTPException(status_code=401, detail="Invalid passcode")

        # Get total count (for frontend reference)
        total = conn.execute(
            text("SELECT COUNT(*) FROM chat_history WHERE passcode = :p"),
            {"p": request.passcode}
        ).scalar()

        # Fetch paginated chat history (most recent first)
        result = conn.execute(
            text("""
                SELECT user_message, bot_response, timestamp
                FROM chat_history
                WHERE passcode = :p
                ORDER BY timestamp DESC
                OFFSET :o LIMIT :l
            """),
            {"p": request.passcode, "o": offset, "l": limit}
        ).fetchall()

        # Convert to structured messages (most recent first)
        messages = []
        for row in result:
            messages.append({"sender": "bot", "text": row.bot_response})
            messages.append({"sender": "user", "text": row.user_message})

        # Reverse to chronological order before sending
        messages.reverse()

        return JSONResponse(content={"history": messages, "total": total})


@app.post("/add_passcode")
def add_passcode(passcode: str, db: Session = Depends(get_db)):
    existing_user = db.query(User).filter(User.passcode == passcode).first()

    if existing_user:
        # ✅ Update last login for existing user
        existing_user.last_login = datetime.utcnow()
        db.commit()
        return {"message": f"Passcode '{passcode}' already exists — last login updated."}
    else:
        # ✅ Create new user with current timestamp
        new_user = User(passcode=passcode, last_login=datetime.utcnow())
        db.add(new_user)
        db.commit()
        return {"message": f"Passcode '{passcode}' added successfully!"}


@app.get("/list_passcodes")
def list_passcodes(db: Session = Depends(get_db)):
    users = db.query(User).all()
    return {"passcodes": [u.passcode for u in users]}


@app.delete("/delete_passcode")
def delete_passcode(passcode: str, db: Session = Depends(get_db)):
    # Check if passcode exists
    user = db.query(User).filter(User.passcode == passcode).first()
    if not user:
        raise HTTPException(status_code=404, detail=f"Passcode '{passcode}' not found.")

    # Delete user
    db.delete(user)
    db.commit()

    return {"message": f"Passcode '{passcode}' deleted successfully!"}