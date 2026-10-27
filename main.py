import os
import logging
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from gigachat import GigaChat
from gigachat.models import Chat, Messages, MessagesRole
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()
templates = Jinja2Templates(directory="templates")

giga = GigaChat(
    credentials=os.getenv("GIGACHAT_CREDENTIALS"),
    scope=os.getenv("GIGACHAT_SCOPE"),
    model="GigaChat",
    verify_ssl_certs=False 
)

SYSTEM_PROMPT = """Ты — вежливый и профессиональный администратор парикмахерской "Стиль".
Отвечай кратко и дружелюбно. Услуги: Стрижка мужская - 1500 руб, Женская - 2500 руб, Окрашивание - от 4000 руб, Укладка - 1000 руб.
"""

class ChatRequest(BaseModel):
    message: str

class ChatResponse(BaseModel):
    answer: str

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/api/chat", response_model=ChatResponse)
async def chat(req: ChatRequest):
    try:
        response = giga.chat(
            Chat(messages=[
                Messages(role=MessagesRole.SYSTEM, content=SYSTEM_PROMPT),
                Messages(role=MessagesRole.USER, content=req.message)
            ])
        )
        return ChatResponse(answer=response.choices[0].message.content)
    except Exception as e:
        logger.error(f"Ошибка в /api/chat: {e}")
        return ChatResponse(answer="Извините, временные трудности. Попробуйте позже.")

@app.post("/salut-webhook")
async def salut_webhook(request: Request):
    try:
        body = await request.json()
    except Exception:
        return JSONResponse(content={"error": "Invalid JSON"}, status_code=400)

    user_text = ""
    try:
        user_text = body["payload"]["message"]["original_text"]
    except (KeyError, TypeError):
        pass

    if not user_text:
        return JSONResponse(content={"payload": {"pronounceText": "", "items": [], "finished": False}})

    try:
        response = giga.chat(
            Chat(messages=[
                Messages(role=MessagesRole.SYSTEM, content=SYSTEM_PROMPT),
                Messages(role=MessagesRole.USER, content=user_text)
            ])
        )
        answer = response.choices[0].message.content
    except Exception as e:
        logger.error(f"Ошибка GigaChat в webhook: {e}")
        answer = "Извините, у меня временные трудности. Попробуйте позже."

    return JSONResponse(content={
        "payload": {
            "pronounceText": answer,
            "items": [{"bubble": {"text": answer}}],
            "finished": False
        }
    })
