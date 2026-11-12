from functools import lru_cache
from pinecone import Pinecone, ServerlessSpec
from openai import OpenAI
from app.config import settings

@lru_cache()
def clients():
    if not settings.openrouter_api_key or not settings.pinecone_api_key:
        raise ValueError("OPENROUTER_API_KEY and PINECONE_API_KEY must be set in the environment variables.")
    
    ai = OpenAI(
        base_url=getattr(settings, "openrouter_base_url", "https://openrouter.ai/api/v1"),
        api_key=settings.openrouter_api_key
    )
    pc = Pinecone(api_key=settings.pinecone_api_key)
    return ai, pc


def ensure_index():
    _, pc = clients()
    if not pc.has_index(settings.pinecone_index):
        pc.create_index(
            name=settings.pinecone_index,
            dimension=3072,
            metric='cosine',
            spec=ServerlessSpec(cloud='aws', region='us-east-1')
        )
    return pc.Index(settings.pinecone_index)


def embed(texts):
    ai, _ = clients()
    embed_model = getattr(settings, 'google_embed_model', 'google/gemini-embedding-001')
    response = ai.embeddings.create(model=embed_model, input=texts)
    return [x.embedding for x in response.data]


def search_kb(query, top_k=5):
    index = ensure_index()
    vector = embed([query])[0]
    result = index.query(vector=vector, top_k=top_k, include_metadata=True)
    return [
        {
            'page': m.metadata.get('page'),
            'text': m.metadata.get('text', ''),
            'score': round(m.score, 3),
            'source': 'Gale Encyclopedia (2002)'
        }
        for m in result.matches
        if m.score >= 0.30
    ]
