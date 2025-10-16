from fastapi import FastAPI, Depends, HTTPException
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
engine = create_engine(os.getenv("DATABASE_URL"))

# Serve the frontend (HTML, JS, CSS)
frontend_path = pathlib.Path(__file__).parent.parent / "frontend"
app.mount("/static", StaticFiles(directory=frontend_path), name="static")

@app.get("/")
def serve_index():
    return FileResponse(frontend_path / "index.html")

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
    return {"message": "Authenticated"}


@app.post("/chat")
async def chat(request: ChatRequest):
    try:
        completion = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": request.message}]
        )
        reply = completion.choices[0].message.content
        return {"reply": reply}   # ✅ must be a dict
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


from fastapi import Query

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
    new_user = User(passcode=passcode)
    db.add(new_user)
    db.commit()
    return {"message": f"Passcode '{passcode}' added successfully!"}


@app.get("/list_passcodes")
def list_passcodes(db: Session = Depends(get_db)):
    users = db.query(User).all()
    return {"passcodes": [u.passcode for u in users]}
