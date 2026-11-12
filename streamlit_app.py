import base64
import io
import uuid
import streamlit as st
from PIL import Image

# Streamlit Page Config
st.set_page_config(
    page_title="MedGuide AI — Klinik Asistan",
    page_icon="⚕️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Medical CSS Theme
st.markdown("""
<style>
    /* Google Fonts */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }

    /* Main Container Padding */
    .block-container {
        padding-top: 1.5rem;
        padding-bottom: 2rem;
        max-width: 1100px;
    }

    /* Header Styling */
    .med-header {
        background: linear-gradient(135deg, #0f2b48 0%, #1e4b7a 50%, #0284c7 100%);
        border-radius: 16px;
        padding: 24px 30px;
        color: white;
        margin-bottom: 1.5rem;
        box-shadow: 0 10px 25px -5px rgba(2, 132, 199, 0.25);
        display: flex;
        justify-content: space-between;
        align-items: center;
        flex-wrap: wrap;
        gap: 15px;
    }
    
    .med-header h1 {
        color: #ffffff !important;
        font-size: 1.85rem !important;
        font-weight: 700 !important;
        margin: 0 !important;
        display: flex;
        align-items: center;
        gap: 12px;
    }

    .med-header p {
        color: #e0f2fe !important;
        font-size: 0.95rem;
        margin: 4px 0 0 0 !important;
    }

    /* Emergency Notice Banner */
    .emergency-banner {
        background: linear-gradient(90deg, #fef2f2 0%, #fee2e2 100%);
        border-left: 5px solid #ef4444;
        border-radius: 10px;
        padding: 12px 18px;
        margin-bottom: 1.5rem;
        display: flex;
        align-items: center;
        gap: 12px;
        color: #991b1b;
        font-size: 0.88rem;
        font-weight: 500;
        box-shadow: 0 2px 6px rgba(239, 68, 68, 0.08);
    }

    /* Medical Badges */
    .med-badge {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        padding: 4px 10px;
        border-radius: 20px;
        font-size: 0.78rem;
        font-weight: 600;
        letter-spacing: 0.3px;
    }

    .badge-online {
        background-color: #dcfce7;
        color: #166534;
        border: 1px solid #bbf7d0;
    }

    .badge-tool {
        background-color: #f0f9ff;
        color: #0369a1;
        border: 1px solid #bae6fd;
        margin-right: 6px;
        margin-bottom: 6px;
    }

    .badge-pdf {
        background-color: #fef3c7;
        color: #92400e;
        border: 1px solid #fde68a;
    }

    .badge-web {
        background-color: #f3e8ff;
        color: #6b21a8;
        border: 1px solid #e9d5ff;
    }

    /* Card styling */
    .source-card {
        background-color: #f8fafc;
        border: 1px solid #e2e8f0;
        border-radius: 10px;
        padding: 10px 14px;
        margin-top: 8px;
        font-size: 0.85rem;
    }

    /* Sidebar Tweaks */
    section[data-testid="stSidebar"] {
        background-color: #f8fafc;
        border-right: 1px solid #e2e8f0;
    }

    /* Chat styling */
    .stChatMessage {
        border-radius: 12px;
        padding: 8px 12px;
        margin-bottom: 8px;
    }
</style>
""", unsafe_allow_html=True)

# Backend Imports with error handling
try:
    from app.config import settings
    from app.agent import graph
    from openai import OpenAI
    APP_CONFIGURED = bool(settings.openrouter_api_key and settings.pinecone_api_key)
except Exception as e:
    APP_CONFIGURED = False
    settings = None
    graph = None

# Initialize Session State
if "messages" not in st.session_state:
    st.session_state.messages = [
        {
            "role": "assistant",
            "content": "Merhaba! Ben **MedGuide AI** klinik eğitim ve triyaj asistanıyım. 🩺\n\nSemptomlarınızı anlatabilir, tıbbi sorular sorabilir, reçete veya cilt lezyonu gibi tıbbi görseller yükleyebilir veya sesli mesaj bırakabilirsiniz.\n\n*Not: Sağlanan bilgiler teşhis niteliğinde değildir.*",
            "sources": [],
            "tools": []
        }
    ]

if "thread_id" not in st.session_state:
    st.session_state.thread_id = str(uuid.uuid4())

if "selected_image_b64" not in st.session_state:
    st.session_state.selected_image_b64 = None

# Helper: Inspect Image via OpenRouter Vision
def analyze_image_with_vision(image_bytes: bytes, mime_type: str = "image/jpeg") -> str:
    if not settings or not settings.openrouter_api_key:
        return ""
    try:
        b64_str = base64.b64encode(image_bytes).decode("utf-8")
        data_url = f"data:{mime_type};base64,{b64_str}"
        client = OpenAI(
            base_url=settings.openrouter_base_url,
            api_key=settings.openrouter_api_key,
            timeout=45
        )
        res = client.chat.completions.create(
            model=settings.openai_vision_model,
            messages=[{
                "role": "user",
                "content": [
                    {"type": "text", "text": "Describe only objectively visible medical-relevant features. Do not diagnose, estimate severity, or assert absence of illness. If image unclear, say so."},
                    {"type": "image_url", "image_url": {"url": data_url}}
                ]
            }],
            max_tokens=300
        )
        return res.choices[0].message.content or ""
    except Exception as err:
        st.error(f"Görsel analizi hatası: {err}")
        return ""

# Helper: Transcribe Audio via OpenRouter Whisper
def transcribe_audio_whisper(audio_bytes: bytes, filename: str = "voice.wav") -> str:
    if not settings or not settings.openrouter_api_key:
        return ""
    try:
        audio_file = io.BytesIO(audio_bytes)
        audio_file.name = filename
        client = OpenAI(
            base_url=settings.openrouter_base_url,
            api_key=settings.openrouter_api_key
        )
        res = client.audio.transcriptions.create(
            model=settings.openrouter_stt_model,
            file=audio_file
        )
        return res.text
    except Exception as err:
        err_str = str(err)
        if "402" in err_str or "balance" in err_str.lower():
            st.warning("⚠️ OpenRouter Whisper için hesabınızda en az $0.50 bakiye gereklidir.")
        else:
            st.warning(f"Ses transkripsiyonu uyarısı: {err}")
        return ""

# ----------------- SIDEBAR -----------------
with st.sidebar:
    st.markdown("### 🏥 MedGuide Kontrol Paneli")
    
    # System Status Indicator
    if APP_CONFIGURED:
        st.markdown('<div class="med-badge badge-online">● Sistem Çevrimiçi & Bağlı</div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="med-badge" style="background:#fee2e2;color:#991b1b;">⚠ API Anahtarları Eksik</div>', unsafe_allow_html=True)
        st.caption(".env dosyanızdaki ayarları kontrol ediniz.")

    st.markdown("---")
    
    # Active Models Info
    st.markdown("#### ⚙️ Yapılandırma & Modeller")
    if settings:
        with st.expander("Aktif Model Bilgileri", expanded=False):
            st.text_input("LLM Model", value=settings.openai_chat_model, disabled=True)
            st.text_input("Vision Model", value=settings.openai_vision_model, disabled=True)
            st.text_input("STT (Ses)", value=settings.openrouter_stt_model, disabled=True)
            st.text_input("Vektör DB", value=f"Pinecone ({settings.pinecone_index})", disabled=True)
            st.text_input("Web Arama", value="Tavily Medical Search", disabled=True)

    st.markdown("---")
    
    # Quick Clinical Prompts
    st.markdown("#### 💡 Örnek Klinik Sorular")
    sample_questions = [
        "Migren ve gerilim tipi baş ağrısı farkları nelerdir?",
        "Astım krizinde ilk basamak ne olmalıdır?",
        "Yüksek ateş ve deri döküntüsü ne zaman acildir?",
        "Tansiyon yüksekliği için güncel kılavuz önerileri neler?"
    ]
    for q in sample_questions:
        if st.button(q, key=f"btn_{q[:15]}", use_container_width=True):
            st.session_state.quick_query = q

    st.markdown("---")

    # Reset Conversation Button
    if st.button("🔄 Yeni Görüşme Başlat", use_container_width=True, type="secondary"):
        st.session_state.messages = [st.session_state.messages[0]]
        st.session_state.thread_id = str(uuid.uuid4())
        st.session_state.selected_image_b64 = None
        st.rerun()

    st.markdown("---")
    st.caption("🩺 **MedGuide AI v1.0**\nMultiModal RAG & Agentic Clinical Assistant")

# ----------------- MAIN UI -----------------

# Header Section
st.markdown("""
<div class="med-header">
    <div>
        <h1>⚕️ MedGuide AI <span style="font-size:0.9rem; font-weight:400; opacity:0.85; background:rgba(255,255,255,0.15); padding:3px 10px; border-radius:12px;">Klinik Triyaj & RAG</span></h1>
        <p>Gale Encyclopedia Medikal Veritabanı • Canlı Web Araştırması • Çok Modlu Görüntü Analizi</p>
    </div>
</div>
""", unsafe_allow_html=True)

# Emergency Warning Banner
st.markdown("""
<div class="emergency-banner">
    <span style="font-size:1.4rem;">🚨</span>
    <div>
        <strong>ACİL DURUM UYARISI:</strong> Şiddetli göğüs ağrısı, nefes darlığı, inme belirtileri, aşırı kanama veya bilinç kaybı gibi acil semptomlarda lütfen derhal <strong>112 Acil Servis</strong>'i arayınız veya en yakın acil servise başvurunuz. MedGuide bir teşhis cihazı veya hekim değildir.
    </div>
</div>
""", unsafe_allow_html=True)

# Multimodal Inputs Accordion (Image & Voice)
with st.expander("📷 Görsel Yükle / 🎙️ Sesli Mesaj Bırak (Çok Modlu Girdi)", expanded=False):
    col_img, col_audio = st.columns(2)
    
    uploaded_image_bytes = None
    uploaded_mime = "image/jpeg"
    
    with col_img:
        st.markdown("**Görsel Yükleme (Reçete, Rapor, Lezyon)**")
        img_file = st.file_uploader("Görsel seçin (PNG, JPG, WEBP)", type=["png", "jpg", "jpeg", "webp"], key="img_uploader")
        if img_file:
            uploaded_image_bytes = img_file.read()
            uploaded_mime = img_file.type
            st.image(uploaded_image_bytes, caption="Yüklenen Görsel", use_container_width=True)
            
    with col_audio:
        st.markdown("**Sesli Soru Kaydet / Yükle**")
        audio_val = None
        # Streamlit audio_input or file_uploader fallback
        try:
            audio_val = st.audio_input("Ses kaydetmek için mikrofona tıklayın", key="audio_recorder")
        except AttributeError:
            audio_val = st.file_uploader("Ses dosyası yükleyin (WAV, MP3, WEBM)", type=["wav", "mp3", "webm"], key="audio_uploader")
        
        if audio_val:
            st.audio(audio_val)
            if st.button("🎙️ Sesi Metne Çevir ve Sor", key="transcribe_btn"):
                with st.spinner("Whisper modeli ile ses çözümleniyor..."):
                    transcribed_text = transcribe_audio_whisper(audio_val.read(), filename="user_voice.wav")
                    if transcribed_text:
                        st.session_state.quick_query = transcribed_text
                        st.success(f"Çözümlenen metin: *{transcribed_text}*")
                        st.rerun()

# Display Chat History
for msg in st.session_state.messages:
    with st.chat_message(msg["role"], avatar="🧑‍💼" if msg["role"] == "user" else "⚕️"):
        st.markdown(msg["content"])
        
        # Display Tools Used Badge
        if msg.get("tools"):
            badges_html = " ".join([f'<span class="med-badge badge-tool">🔧 {tool}</span>' for tool in msg["tools"]])
            st.markdown(f'<div style="margin-top:8px;">{badges_html}</div>', unsafe_allow_html=True)

        # Display Sources if available
        if msg.get("sources"):
            with st.expander("📚 Kullanılan Tıbbi Kaynaklar ve Alıntılar", expanded=False):
                for src in msg["sources"]:
                    if src.get("type") == "pdf":
                        st.markdown(f'<div class="source-card"><strong>📖 Gale Medical Encyclopedia (2002)</strong> — <span class="med-badge badge-pdf">Sayfa {src.get("page")}</span> (Relevance: {src.get("score")})<br><small style="color:#64748b;">{src.get("text", "")}</small></div>', unsafe_allow_html=True)
                    elif src.get("type") == "web":
                        st.markdown(f'<div class="source-card"><strong>🌐 <a href="{src.get("url")}" target="_blank">{src.get("title")}</a></strong> — <span class="med-badge badge-web">Klinik Kılavuz / Web</span><br><small style="color:#64748b;">{src.get("content", "")[:280]}...</small></div>', unsafe_allow_html=True)

# User Chat Input
user_prompt = st.chat_input("Tıbbi sorunuzu veya semptomlarınızı buraya yazınız...")

# Handle Quick Query if clicked from sidebar
if "quick_query" in st.session_state and st.session_state.quick_query:
    user_prompt = st.session_state.quick_query
    st.session_state.quick_query = None

if user_prompt:
    if not APP_CONFIGURED:
        st.error("Lütfen `.env` dosyanızda `OPENROUTER_API_KEY` ve `PINECONE_API_KEY` anahtarlarını ayarlayınız.")
        st.stop()

    # Append User Message
    st.session_state.messages.append({
        "role": "user",
        "content": user_prompt,
        "sources": [],
        "tools": []
    })
    
    with st.chat_message("user", avatar="🧑‍💼"):
        st.markdown(user_prompt)

    # Process with Agent
    with st.chat_message("assistant", avatar="⚕️"):
        status_placeholder = st.empty()
        status_placeholder.markdown("🔍 *Klinik bilgi tabanı ve semptomlar taranıyor...*")
        
        # 1. Vision Analysis if image was attached
        image_observation = ""
        if uploaded_image_bytes:
            status_placeholder.markdown("👁️ *Görsel klinik detaylar taranıyor...*")
            image_observation = analyze_image_with_vision(uploaded_image_bytes, mime_type=uploaded_mime)

        # 2. History Formatting
        formatted_history = []
        for m in st.session_state.messages[-8:]:
            if m["role"] in ("user", "assistant"):
                formatted_history.append({"role": m["role"], "content": m["content"]})

        # 3. LangGraph Execution
        try:
            status_placeholder.markdown("🧠 *Klinik karar grafı ve literatür derleniyor...*")
            config = {"configurable": {"thread_id": st.session_state.thread_id}}
            
            state = graph.invoke(
                {
                    "question": user_prompt,
                    "history": formatted_history,
                    "image_description": image_observation,
                    "kb": [],
                    "web": [],
                    "answer": "",
                    "route": ""
                },
                config=config
            )
            
            status_placeholder.empty()

            answer_text = state.get("answer", "Yanıt oluşturulamadı.")
            st.markdown(answer_text)

            # Collect Tools & Sources
            tools_used = ["Pinecone KB (Gale)"]
            if state.get("route") == "web" and settings.tavily_api_key:
                tools_used.append("Tavily Web Clinical Search")
            if image_observation:
                tools_used.append("Nemotron Multimodal Vision")

            sources_list = []
            for item in state.get("kb", []):
                sources_list.append({
                    "type": "pdf",
                    "page": item.get("page"),
                    "score": item.get("score"),
                    "text": item.get("text", "")
                })
            for item in state.get("web", []):
                sources_list.append({
                    "type": "web",
                    "url": item.get("url"),
                    "title": item.get("title"),
                    "content": item.get("content", "")
                })

            # Display Tools
            badges_html = " ".join([f'<span class="med-badge badge-tool">🔧 {tool}</span>' for tool in tools_used])
            st.markdown(f'<div style="margin-top:8px;">{badges_html}</div>', unsafe_allow_html=True)

            # Display Sources Expander
            if sources_list:
                with st.expander("📚 Kullanılan Tıbbi Kaynaklar ve Alıntılar", expanded=False):
                    for src in sources_list:
                        if src.get("type") == "pdf":
                            st.markdown(f'<div class="source-card"><strong>📖 Gale Medical Encyclopedia (2002)</strong> — <span class="med-badge badge-pdf">Sayfa {src.get("page")}</span> (Skor: {src.get("score")})<br><small style="color:#64748b;">{src.get("text", "")}</small></div>', unsafe_allow_html=True)
                        elif src.get("type") == "web":
                            st.markdown(f'<div class="source-card"><strong>🌐 <a href="{src.get("url")}" target="_blank">{src.get("title")}</a></strong> — <span class="med-badge badge-web">Klinik Kılavuz / Web</span><br><small style="color:#64748b;">{src.get("content", "")[:280]}...</small></div>', unsafe_allow_html=True)

            # Save to Session State
            st.session_state.messages.append({
                "role": "assistant",
                "content": answer_text,
                "sources": sources_list,
                "tools": tools_used
            })

        except Exception as exc:
            status_placeholder.empty()
            st.error(f"Medikal Asistan yanıt üretirken bir hata oluştu: {exc}")

