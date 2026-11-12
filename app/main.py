import base64
import io
import secrets
from pathlib import Path
from fastapi import FastAPI, File, Form, Header, HTTPException, UploadFile
from fastapi.responses import HTMLResponse, Response
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from openai import OpenAI
from uuid import uuid4
from app.config import settings
from app.agent import graph

ROOT = Path(__file__).resolve().parent.parent
app = FastAPI(title='Medical Agent Educational API', version='1.0.0')
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins.split(','),
    allow_credentials=False,
    allow_methods=['GET', 'POST'],
    allow_headers=['Authorization', 'Content-Type']
)
app.mount('/static', StaticFiles(directory=ROOT / 'static'), name='static')


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=4000)
    history: list[dict[str, str]] = Field(default_factory=list, max_length=10)
    image_data: str | None = None


def auth(authorization: str | None):
    if settings.api_token and not secrets.compare_digest(authorization or '', f'Bearer {settings.api_token}'):
        raise HTTPException(status_code=401, detail='Invalid API token')


def inspect_image(data: str | None) -> str:
    if not data:
        return ''
    try:
        header, payload = data.split(',', 1)
        mime = header.split(';')[0].split(':')[1]
        raw = base64.b64decode(payload, validate=True)
        if mime not in ('image/jpeg', 'image/png', 'image/webp') or len(raw) > 5_000_000:
            raise ValueError('Only JPEG/PNG/WebP under 5MB supported')
    except (ValueError, IndexError) as exc:
        raise HTTPException(status_code=400, detail=f'Invalid image: {exc}')

    client = OpenAI(
        base_url=settings.openrouter_base_url,
        api_key=settings.openrouter_api_key or settings.openai_api_key,
        timeout=45
    )
    result = client.chat.completions.create(
        model=settings.openai_vision_model,
        messages=[{
            'role': 'user',
            'content': [
                {'type': 'text', 'text': 'Describe only objectively visible medical-relevant features. Do not diagnose, estimate severity, or assert absence of illness. If image unclear, say so.'},
                {'type': 'image_url', 'image_url': {'url': data}}
            ]
        }],
        max_tokens=300
    )
    return result.choices[0].message.content or ''


@app.get('/', response_class=HTMLResponse)
def home():
    return (ROOT / 'templates' / 'index.html').read_text(encoding='utf-8')


@app.get('/api/health')
def health():
    return {
        'status': 'ok',
        'configured': bool(settings.openrouter_api_key and settings.pinecone_api_key),
        'tavily': bool(settings.tavily_api_key),
        'stt_model': settings.openrouter_stt_model
    }


@app.post('/api/chat')
def chat(
    payload: ChatRequest,
    authorization: str | None = Header(default=None),
    conversation_id: str | None = Header(default=None, alias='X-Conversation-ID')
):
    auth(authorization)

    if not settings.openrouter_api_key or not settings.pinecone_api_key:
        raise HTTPException(503, 'Set OPENROUTER_API_KEY and PINECONE_API_KEY in .env')

    history = [
        x for x in payload.history
        if x.get('role') in ('user', 'assistant') and isinstance(x.get('content'), str)
    ][:10]

    # SQLite persistent memory: reuse the same conversation thread
    thread_id = conversation_id or str(uuid4())
    config = {"configurable": {"thread_id": thread_id}}

    try:
        observation = inspect_image(payload.image_data)

        state = graph.invoke(
            {
                'question': payload.message,
                'history': history,
                'image_description': observation,
                'kb': [],
                'web': [],
                'answer': '',
                'route': ''
            },
            config=config
        )

        return {
            'answer': state['answer'],
            'sources': [
                {'type': 'pdf', 'page': x['page'], 'score': x['score']}
                for x in state['kb']
            ] + [
                {'type': 'web', 'url': x['url'], 'title': x['title']}
                for x in state['web']
            ],
            'tools': ['pinecone'] + (['tavily'] if state['route'] == 'web' and settings.tavily_api_key else []) + (['vision'] if observation else []),
            'conversation_id': thread_id
        }

    except HTTPException:
        raise
    except Exception as exc:
        print('Chat error:', repr(exc), flush=True)
        raise HTTPException(502, 'AI service failed. Check server logs, credentials, Pinecone index, and connectivity.')


@app.post('/api/transcribe')
async def transcribe(file: UploadFile = File(...), authorization: str | None = Header(default=None)):
    auth(authorization)
    data = await file.read(10_000_001)
    if len(data) > 10_000_000:
        raise HTTPException(413, 'Audio exceeds 10 MB')
    
    if not settings.openrouter_api_key and not settings.openai_api_key:
        raise HTTPException(503, 'Set OPENROUTER_API_KEY in .env')

    audio = io.BytesIO(data)
    audio.name = file.filename or 'voice.webm'
    
    try:
        # OpenRouter ile OpenAI Whisper STT transkripsiyonu
        client = OpenAI(
            base_url=settings.openrouter_base_url,
            api_key=settings.openrouter_api_key or settings.openai_api_key
        )
        result = client.audio.transcriptions.create(
            model=settings.openrouter_stt_model,
            file=audio
        )
        return {'text': result.text}
    except Exception as exc:
        print('Transcription error:', repr(exc), flush=True)
        err_msg = str(exc)
        if '402' in err_msg or 'balance' in err_msg.lower():
            raise HTTPException(502, 'OpenRouter audio requires at least $0.50 balance')
        raise HTTPException(502, f'Speech transcription unavailable: {exc}')


@app.post('/api/speak')
def speak(payload: dict, authorization: str | None = Header(default=None)):
    auth(authorization)
    text = str(payload.get('text', ''))[:3000]
    if not text:
        raise HTTPException(400, 'Missing text')

    api_key = settings.openai_api_key or settings.openrouter_api_key
    base_url = None if settings.openai_api_key else settings.openrouter_base_url
    try:
        client = OpenAI(api_key=api_key, base_url=base_url)
        speech = client.audio.speech.create(model='tts-1', voice='alloy', input=text)
        return Response(content=speech.content, media_type='audio/mpeg')
    except Exception as exc:
        print('Speak error:', repr(exc), flush=True)
        raise HTTPException(502, 'Speech synthesis unavailable (TTS requires OpenAI API key)')
