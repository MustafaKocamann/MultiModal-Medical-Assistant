import os 
import certifi 
from dotenv import load_dotenv

# --- AUTOMATIC SSL FIX FOR CONDA/PYTHON ENVIRONMENTS ---
ssl_cert = os.environ.get('SSL_CERT_FILE')
if ssl_cert and not os.path.exists(ssl_cert):
    os.environ['SSL_CERT_FILE'] = certifi.where()
elif not ssl_cert:
    os.environ['SSL_CERT_FILE'] = certifi.where()
# --------------------------------------------------------

load_dotenv()
from pydantic_settings import BaseSettings, SettingsConfigDict



class Settings(BaseSettings):
    openrouter_api_key: str = ''
    openrouter_base_url: str = 'https://openrouter.ai/api/v1'
    openai_api_key: str = ''
    pinecone_api_key: str = ''
    tavily_api_key: str = ''
    pinecone_index: str = 'medical-agent-demo'
    openai_chat_model: str = 'nvidia/nemotron-3-ultra-550b-a55b:free'
    openrouter_stt_model: str = 'openai/whisper-large-v3-turbo'
    google_embed_model: str = 'google/gemini-embedding-001'
    google__model: str = 'google/gemini-embedding-001'
    openai_vision_model: str = 'nvidia/nemotron-3-nano-omni-30b-a3b-reasoning:free'
    google_api_key: str = ''
    embedding_dimension: int = 3072
    api_token: str = ''
    allowed_origins: str = 'http://localhost:8000,http://127.0.0.1:8000'
    model_config = SettingsConfigDict(env_file='.env', extra='ignore')



settings = Settings()