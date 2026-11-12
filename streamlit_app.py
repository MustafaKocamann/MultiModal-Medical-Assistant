import base64
import io
import json
import uuid
import secrets
import streamlit as st
import streamlit.components.v1 as components
from PIL import Image

# ----------------- PAGE CONFIG -----------------
st.set_page_config(
    page_title="Novacura AI — Akıllı Klinik Triyaj & Medikal Zeka",
    page_icon="🩺",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ----------------- REFINED CLINICAL THEME (CSS) -----------------
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, sans-serif;
        color: #0f172a;
    }

    /* Container Spacing */
    .block-container {
        padding-top: 1.2rem;
        padding-bottom: 2rem;
        max-width: 1000px;
    }

    /* Modern Clinical Header */
    .clinical-header {
        background: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 16px;
        padding: 18px 24px;
        margin-bottom: 1rem;
        box-shadow: 0 4px 16px -2px rgba(15, 23, 42, 0.05);
        display: flex;
        justify-content: space-between;
        align-items: center;
        flex-wrap: wrap;
        gap: 16px;
    }

    .clinical-title-box {
        display: flex;
        align-items: center;
        gap: 14px;
    }

    .clinical-icon-badge {
        width: 44px;
        height: 44px;
        background: linear-gradient(135deg, #0284c7 0%, #0369a1 100%);
        color: white;
        border-radius: 12px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 22px;
        box-shadow: 0 4px 10px rgba(2, 132, 199, 0.25);
    }

    .clinical-title {
        margin: 0;
        font-size: 1.35rem;
        font-weight: 700;
        color: #0f172a;
        letter-spacing: -0.3px;
    }

    .clinical-subtitle {
        margin: 2px 0 0 0;
        font-size: 0.85rem;
        color: #64748b;
        font-weight: 400;
    }

    /* Emergency Disclaimer Bar */
    .triage-alert {
        background-color: #fff1f2;
        border: 1px solid #fecdd3;
        border-left: 4px solid #e11d48;
        border-radius: 10px;
        padding: 10px 16px;
        margin-bottom: 1.2rem;
        display: flex;
        align-items: flex-start;
        gap: 12px;
        font-size: 0.84rem;
        line-height: 1.45;
        color: #9f1239;
    }

    /* Sidebar Styling */
    section[data-testid="stSidebar"] {
        background-color: #ffffff;
        border-right: 1px solid #e2e8f0;
    }
    
    section[data-testid="stSidebar"] .block-container {
        padding-top: 1.5rem;
    }

    .sidebar-section-title {
        font-size: 0.78rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.7px;
        color: #64748b;
        margin-top: 1.2rem;
        margin-bottom: 0.6rem;
    }

    /* Badges */
    .badge {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        padding: 4px 10px;
        border-radius: 9999px;
        font-size: 0.75rem;
        font-weight: 600;
    }

    .badge-success {
        background-color: #f0fdf4;
        color: #166534;
        border: 1px solid #bbf7d0;
    }

    .badge-tool {
        background-color: #f8fafc;
        color: #0284c7;
        border: 1px solid #e2e8f0;
        margin-right: 6px;
        margin-bottom: 6px;
        font-size: 0.76rem;
        padding: 3px 9px;
        border-radius: 6px;
    }

    /* Source Citation Cards */
    .citation-card {
        background-color: #f8fafc;
        border: 1px solid #e2e8f0;
        border-radius: 8px;
        padding: 10px 14px;
        margin-top: 8px;
        font-size: 0.84rem;
        line-height: 1.4;
    }

    .citation-card strong {
        color: #0f172a;
    }

    /* Custom Chat Message Styling */
    .assistant-bubble {
        background-color: #ffffff;
        border: 1px solid #e2e8f0;
        border-left: 3px solid #0284c7;
        border-radius: 12px;
        padding: 16px 20px;
        margin-bottom: 12px;
        box-shadow: 0 2px 6px rgba(15, 23, 42, 0.03);
        font-size: 0.95rem;
        line-height: 1.6;
    }

    /* Sidebar Buttons */
    section[data-testid="stSidebar"] div.stButton > button {
        border-radius: 8px;
        font-weight: 500;
        font-size: 0.85rem;
        border: 1px solid #e2e8f0;
        background-color: #ffffff;
        color: #1e293b;
        text-align: left;
    }

    section[data-testid="stSidebar"] div.stButton > button:hover {
        border-color: #0284c7;
        color: #0284c7;
        background-color: #f0f9ff;
    }

    /* Input Textarea */
    .stTextArea textarea {
        border-radius: 10px 10px 0 0 !important;
        border: 1px solid #cbd5e1 !important;
        border-bottom: 1px dashed #e2e8f0 !important;
        font-size: 0.95rem !important;
        padding: 12px 16px !important;
        box-shadow: none !important;
        background-color: #ffffff !important;
    }

    .stTextArea textarea:focus {
        border-color: #0b5c63 !important;
        box-shadow: none !important;
    }

    /* Action Toolbar Container */
    .chat-input-box {
        background: #ffffff;
        border: 1px solid #cbd5e1;
        border-radius: 12px;
        padding: 6px;
        margin-top: 10px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.03);
    }

    /* Action Buttons in Toolbar */
    .toolbar-row div.stButton > button {
        background-color: #f1f5f9 !important;
        border: 1px solid #e2e8f0 !important;
        border-radius: 6px !important;
        color: #334155 !important;
        font-size: 0.82rem !important;
        font-weight: 500 !important;
        padding: 5px 12px !important;
        text-align: center !important;
    }

    .toolbar-row div.stButton > button:hover {
        background-color: #e2e8f0 !important;
        color: #0f172a !important;
        border-color: #cbd5e1 !important;
    }

    /* Send Button */
    .send-col div.stButton > button {
        background-color: #0b5c63 !important;
        color: #ffffff !important;
        border: none !important;
        border-radius: 6px !important;
        font-weight: 600 !important;
        font-size: 0.85rem !important;
        padding: 5px 20px !important;
        text-align: center !important;
    }

    .send-col div.stButton > button:hover {
        background-color: #08494f !important;
        color: #ffffff !important;
    }
</style>
""", unsafe_allow_html=True)

# ----------------- BACKEND CONNECTIVITY -----------------
try:
    from app.config import settings
    from app.agent import graph
    from openai import OpenAI
    APP_CONFIGURED = bool(settings.openrouter_api_key and settings.pinecone_api_key)
except Exception as e:
    APP_CONFIGURED = False
    settings = None
    graph = None

# ----------------- SESSION STATE INIT -----------------
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

# Auto-login via URL Query Parameter ?token=...
if not st.session_state.authenticated and settings and settings.api_token:
    param_token = st.query_params.get("token")
    if param_token and secrets.compare_digest(param_token, settings.api_token):
        st.session_state.authenticated = True

# ----------------- ACCESS TOKEN BARRIER -----------------
if settings and settings.api_token and not st.session_state.authenticated:
    _, col_login, _ = st.columns([1, 1.8, 1])
    with col_login:
        st.markdown("<br><br>", unsafe_allow_html=True)
        st.markdown("""
        <div style="background:#ffffff; border:1px solid #e2e8f0; border-radius:18px; padding:32px 28px; box-shadow:0 10px 25px -5px rgba(15,23,42,0.08); text-align:center;">
            <div style="width:56px; height:56px; background:linear-gradient(135deg, #0284c7 0%, #0369a1 100%); color:white; border-radius:14px; margin:0 auto 16px; display:flex; align-items:center; justify-content:center; font-size:28px; box-shadow:0 4px 12px rgba(2,132,199,0.25);">
                🔒
            </div>
            <h2 style="font-size:1.45rem; font-weight:700; color:#0f172a; margin:0 0 6px;">Novacura AI</h2>
            <p style="font-size:0.88rem; color:#64748b; margin:0 0 20px;">Yetkili Medikal Karar Destek ve Triyaj Portalı</p>
            <div style="background:#f8fafc; border:1px solid #e2e8f0; border-radius:10px; padding:12px 14px; margin-bottom:20px; font-size:0.8rem; color:#475569; text-align:left; line-height:1.45;">
                🛡️ <strong>Güvenlik Protokolü:</strong> Bu platform hasta triyajı ve klinik algoritmalar barındırdığından yalnızca yetkilendirilmiş personelin erişimine açıktır.
            </div>
        </div>
        """, unsafe_allow_html=True)

        with st.form("access_gate_form", clear_on_submit=False):
            token_input = st.text_input("Erişim Anahtarı (Access Token)", type="password", placeholder="API_TOKEN anahtarınızı giriniz...")
            submit_btn = st.form_submit_button("Sisteme Giriş Yap ➜", use_container_width=True)

            if submit_btn:
                if token_input and secrets.compare_digest(token_input.strip(), settings.api_token):
                    st.session_state.authenticated = True
                    st.success("Yetkilendirme başarılı! Yönlendiriliyorsunuz...")
                    st.rerun()
                else:
                    st.error("❌ Geçersiz Erişim Anahtarı. Lütfen sistem yöneticisiyle iletişime geçiniz.")

        st.markdown("<p style='text-align:center; font-size:0.75rem; color:#94a3b8; margin-top:20px;'>Novacura HealthTech • HIPAA / KVKK Uyumlu İstemci</p>", unsafe_allow_html=True)
    st.stop()

if "messages" not in st.session_state:
    st.session_state.messages = [
        {
            "role": "assistant",
            "content": "Merhaba! Ben **Novacura AI** akıllı klinik triyaj ve medikal karar destek asistanıyım. 🩺\n\nSemptomlarınızı detaylandırabilir, tıbbi terminoloji veya ilaç etkileşimleri hakkında danışabilir, cilt lezyonu veya reçete görseli yükleyebilir ya da sesli danışma gerçekleştirebilirsiniz.\n\n*Nasıl yardımcı olabilirim?*",
            "sources": [],
            "tools": []
        }
    ]

if "thread_id" not in st.session_state:
    st.session_state.thread_id = str(uuid.uuid4())

if "pending_prompt" not in st.session_state:
    st.session_state.pending_prompt = None

if "active_multimodal" not in st.session_state:
    st.session_state.active_multimodal = None  # None, 'image', 'camera', 'voice'

if "attached_image_bytes" not in st.session_state:
    st.session_state.attached_image_bytes = None

if "attached_mime" not in st.session_state:
    st.session_state.attached_mime = "image/jpeg"

if "last_answer_for_tts" not in st.session_state:
    st.session_state.last_answer_for_tts = ""

if "tts_trigger_text" not in st.session_state:
    st.session_state.tts_trigger_text = None

# ----------------- HELPER FUNCTIONS -----------------
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
        st.warning(f"Görsel inceleme uyarısı: {err}")
        return ""

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
            st.info("💡 Whisper STT servisi için OpenRouter hesabında en az $0.50 bakiye gereklidir. Sorunuzu metin olarak iletebilirsiniz.")
        else:
            st.warning(f"Ses transkripsiyonu uyarısı: {err}")
        return ""

# ----------------- SIDEBAR -----------------
with st.sidebar:
    st.markdown('<div class="sidebar-section-title">🏥 Novacura Konsültasyon Paneli</div>', unsafe_allow_html=True)
    
    # System Status
    if APP_CONFIGURED:
        st.markdown('<div class="badge badge-success">● Novacura Motoru Çevrimiçi</div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="badge" style="background:#fee2e2;color:#991b1b;">⚠ API Anahtarları Eksik</div>', unsafe_allow_html=True)

    # Patient Context / Clinical Category Filter
    st.markdown('<div class="sidebar-section-title">Triyaj Bağlamı</div>', unsafe_allow_html=True)
    triage_context = st.selectbox(
        "Klinik Öncelik Seviyesi",
        ["Standart Danışma (Rutin)", "Akut Belirtiler (Son 24 saat)", "Kronik Takip / İlaç", "Pediatrik Danışma"],
        index=0,
        label_visibility="collapsed"
    )

    st.markdown('<div class="sidebar-section-title">💡 Örnek Klinik Senaryolar</div>', unsafe_allow_html=True)
    quick_cases = [
        ("🤕 Baş Ağrısı Triyajı", "Migren ve gerilim tipi baş ağrısının klinik ayrımı nedir?"),
        ("🫁 Astım Semptomları", "Astım alevlenmesinde ilk basamak ne olmalıdır?"),
        ("🌡️ Yüksek Ateş & Döküntü", "Erişkinde yüksek ateş ile döküntü ne zaman acildir?"),
        ("💊 Hipertansiyon Kılavuzu", "Yüksek tansiyon için güncel kılavuz tedavi hedefleri nelerdir?")
    ]
    for label, query in quick_cases:
        if st.button(label, key=f"btn_{label}", use_container_width=True):
            st.session_state.pending_prompt = query
            st.rerun()

    st.markdown('<div class="sidebar-section-title">⚙️ Mimarisi & Altyapı</div>', unsafe_allow_html=True)
    with st.expander("Aktif Klinik Pipeline", expanded=False):
        st.caption(f"**LLM:** `{settings.openai_chat_model if settings else '-'}`")
        st.caption(f"**Vision:** `{settings.openai_vision_model if settings else '-'}`")
        st.caption(f"**Vektör DB:** `Pinecone ({settings.pinecone_index if settings else '-'})`")
        st.caption(f"**Arama:** `Tavily Clinical Search`")
        st.caption(f"**Oturum ID:** `{st.session_state.thread_id[:8]}...`")

    st.markdown("---")
    col_reset, col_logout = st.columns(2)
    with col_reset:
        if st.button("🔄 Sıfırla", use_container_width=True, help="Sohbet geçmişini sıfırlar"):
            st.session_state.messages = [st.session_state.messages[0]]
            st.session_state.thread_id = str(uuid.uuid4())
            st.session_state.pending_prompt = None
            st.session_state.attached_image_bytes = None
            st.session_state.active_multimodal = None
            st.rerun()
    with col_logout:
        if settings and settings.api_token:
            if st.button("🔒 Çıkış", use_container_width=True, help="Oturumu sonlandırır"):
                st.session_state.authenticated = False
                st.rerun()

    st.caption("© 2026 Novacura AI • Akıllı Biyomedikal Triyaj Sistemi")

# ----------------- MAIN WORKSPACE -----------------

# 1. Header Bar
st.markdown("""
<div class="clinical-header">
    <div class="clinical-title-box">
        <div class="clinical-icon-badge">⚕️</div>
        <div>
            <h1 class="clinical-title">Novacura AI <span style="font-size:0.75rem; font-weight:600; background:#f0f9ff; color:#0284c7; padding:3px 8px; border-radius:6px; border:1px solid #bae6fd; vertical-align:middle;">Klinik Zeka v1.0</span></h1>
            <p class="clinical-subtitle">Gale Tıp Ansiklopedisi (RAG) • Canlı Literatür & Kılavuz Taraması • Multimodal Görüntüleme</p>
        </div>
    </div>
    <div style="font-size:0.8rem; color:#64748b; background:#f8fafc; padding:6px 12px; border-radius:8px; border:1px solid #e2e8f0;">
        🛡️ HIPAA/KVKK Uyumlu Güvenli İstemci
    </div>
</div>
""", unsafe_allow_html=True)

# 2. Emergency Notice Banner
st.markdown("""
<div class="triage-alert">
    <span style="font-size:1.2rem; line-height:1;">🚨</span>
    <div>
        <strong>ACİL TIBBİ UYARI:</strong> Novacura AI bir hekim veya resmi tanı aracı değildir. Ani göğüs ağrısı, konuşma güçlüğü, nefes darlığı, kontrolsüz kanama veya bilinç bulanıklığı gibi kritik belirtilerde lütfen vakit kaybetmeden <strong>112 Acil Çağrı Merkezi</strong>'ni arayınız.
    </div>
</div>
""", unsafe_allow_html=True)

# 3. Audio Readout (TTS) Execution if triggered
if st.session_state.tts_trigger_text:
    clean_text = st.session_state.tts_trigger_text.replace("\n", " ").replace('"', "'")[:800]
    components.html(f"""
    <script>
        if ('speechSynthesis' in window) {{
            window.speechSynthesis.cancel();
            const utterance = new SpeechSynthesisUtterance({json.dumps(clean_text)});
            utterance.rate = 1.0;
            utterance.pitch = 1.0;
            window.speechSynthesis.speak(utterance);
        }}
    </script>
    """, height=0)
    st.session_state.tts_trigger_text = None

# 4. Chat Feed
for msg in st.session_state.messages:
    if msg["role"] == "user":
        with st.chat_message("user", avatar="🧑‍💼"):
            st.markdown(msg["content"])
    else:
        with st.chat_message("assistant", avatar="🩺"):
            st.markdown(msg["content"])
            
            # Tools Used Badges
            if msg.get("tools"):
                badges_html = " ".join([f'<span class="badge-tool">🔍 {tool}</span>' for tool in msg["tools"]])
                st.markdown(f'<div style="margin-top:6px; margin-bottom:6px;">{badges_html}</div>', unsafe_allow_html=True)

            # Sources Citation Section
            if msg.get("sources"):
                with st.expander(f"📚 Dayanak Literatür & Kaynaklar ({len(msg['sources'])})", expanded=False):
                    for src in msg["sources"]:
                        if src.get("type") == "pdf":
                            st.markdown(f"""
                            <div class="citation-card">
                                <strong>📖 Gale Encyclopedia of Medicine (2002)</strong> — <span style="background:#fef3c7; color:#92400e; padding:2px 6px; border-radius:4px; font-size:0.75rem;">Sayfa {src.get("page")}</span> <span style="color:#64748b; font-size:0.75rem;">(Benzerlik: %{int(float(src.get("score", 0))*100)})</span>
                                <div style="color:#475569; margin-top:4px;">"{src.get("text", "")}"</div>
                            </div>
                            """, unsafe_allow_html=True)
                        elif src.get("type") == "web":
                            st.markdown(f"""
                            <div class="citation-card">
                                <strong>🌐 <a href="{src.get('url')}" target="_blank" style="color:#0284c7; text-decoration:none;">{src.get('title')}</a></strong> — <span style="background:#f1f5f9; color:#475569; padding:2px 6px; border-radius:4px; font-size:0.75rem;">Harici Kılavuz</span>
                                <div style="color:#475569; margin-top:4px;">{src.get('content', '')[:250]}...</div>
                            </div>
                            """, unsafe_allow_html=True)

# ----------------- MULTIMODAL TOOLBAR & INPUT AREA -----------------

# Preview of Attached Image if any
if st.session_state.attached_image_bytes:
    col_prev1, col_prev2 = st.columns([1, 4])
    with col_prev1:
        st.image(st.session_state.attached_image_bytes, caption="Seçilen Görsel", width=140)
    with col_prev2:
        st.markdown("<small style='color:#059669;'>✓ Tıbbi görsel eklendi. Sorunuzla birlikte analiz edilecek.</small>", unsafe_allow_html=True)
        if st.button("Görseli Kaldır ×", key="btn_remove_image"):
            st.session_state.attached_image_bytes = None
            st.rerun()

# Dynamic Tool Display (Image Upload / Camera / Voice)
if st.session_state.active_multimodal == "image":
    st.markdown("##### 📎 Görsel Yükleme (Reçete / Rapor / Lezyon)")
    uploaded_file = st.file_uploader("Bir görsel seçin (PNG, JPG, WEBP)", type=["png", "jpg", "jpeg", "webp"], key="modal_img_uploader")
    if uploaded_file:
        st.session_state.attached_image_bytes = uploaded_file.read()
        st.session_state.attached_mime = uploaded_file.type
        st.session_state.active_multimodal = None
        st.success("Görsel başarıyla eklendi!")
        st.rerun()

elif st.session_state.active_multimodal == "camera":
    st.markdown("##### 📷 Kamera ile Çekim (Kamera İzni Veriniz)")
    camera_photo = st.camera_input("Fotoğraf çekmek için butona basın", key="modal_camera_input")
    if camera_photo:
        st.session_state.attached_image_bytes = camera_photo.read()
        st.session_state.attached_mime = "image/jpeg"
        st.session_state.active_multimodal = None
        st.success("Kamera görüntüsü eklendi!")
        st.rerun()

elif st.session_state.active_multimodal == "voice":
    st.markdown("##### 🎤 Sesli Soru Bırak (Whisper STT)")
    try:
        rec_audio = st.audio_input("Kayda başlamak için mikrofona tıklayınız", key="modal_audio_input")
    except AttributeError:
        rec_audio = st.file_uploader("Ses dosyası yükleyin (WAV/MP3)", type=["wav", "mp3", "webm"], key="modal_audio_input")

    if rec_audio:
        with st.spinner("Whisper modeli ile ses çözümleniyor..."):
            transcribed = transcribe_audio_whisper(rec_audio.read(), filename="mic_voice.wav")
            if transcribed:
                st.session_state.pending_prompt = transcribed
                st.session_state.active_multimodal = None
                st.success(f"Çözümlendi: *{transcribed}*")
                st.rerun()

# Input Form with Custom Toolbar Layout
with st.form("novacura_chat_form", clear_on_submit=True):
    # Textarea matching user's screenshot placeholder
    default_text = st.session_state.pending_prompt or ""
    user_typed_message = st.text_area(
        label="Message",
        value=default_text,
        placeholder="Describe your symptoms or ask a question...",
        label_visibility="collapsed",
        height=75
    )
    if st.session_state.pending_prompt:
        st.session_state.pending_prompt = None

    # Toolbar row matching user's screenshot layout: [Image] [Camera] [Voice] [Read answer] ...... [Send ➜]
    col_t1, col_t2, col_t3, col_t4, col_spacer, col_send = st.columns([1.1, 1.2, 1.1, 1.5, 2.4, 1.2])

    with col_t1:
        img_clicked = st.form_submit_button("📎 Image")
    with col_t2:
        cam_clicked = st.form_submit_button("📷 Camera")
    with col_t3:
        voice_clicked = st.form_submit_button("🎤 Voice")
    with col_t4:
        read_clicked = st.form_submit_button("🔊 Read answer")
    with col_send:
        st.markdown('<div class="send-col">', unsafe_allow_html=True)
        send_clicked = st.form_submit_button("Send ➜")
        st.markdown('</div>', unsafe_allow_html=True)

# Process Toolbar Button Clicks
if img_clicked:
    st.session_state.active_multimodal = "image" if st.session_state.active_multimodal != "image" else None
    st.rerun()

if cam_clicked:
    st.session_state.active_multimodal = "camera" if st.session_state.active_multimodal != "camera" else None
    st.rerun()

if voice_clicked:
    st.session_state.active_multimodal = "voice" if st.session_state.active_multimodal != "voice" else None
    st.rerun()

if read_clicked:
    if st.session_state.last_answer_for_tts:
        st.session_state.tts_trigger_text = st.session_state.last_answer_for_tts
        st.toast("🔊 Yanıt seslendiriliyor...", icon="🔊")
        st.rerun()
    else:
        st.info("Henüz seslendirilecek bir asistan yanıtı bulunmuyor.")

# Process Send Action
if send_clicked and (user_typed_message.strip() or st.session_state.attached_image_bytes):
    if not APP_CONFIGURED:
        st.error("Sistem API anahtarları `.env` içerisinde yapılandırılmalıdır.")
        st.stop()

    prompt_to_send = user_typed_message.strip() or "Lütfen ekteki medikal görseli inceleyip klinik gözlemlerinizi belirtiniz."
    
    # Store User Message in History
    st.session_state.messages.append({
        "role": "user",
        "content": prompt_to_send,
        "sources": [],
        "tools": []
    })

    # Execute Model
    with st.chat_message("assistant", avatar="🩺"):
        status_box = st.status("Klinik vaka değerlendiriliyor...", expanded=True)
        
        # Multimodal Vision Analysis if attached image exists
        image_findings = ""
        if st.session_state.attached_image_bytes:
            status_box.write("👁️ Tıbbi görsel analiz ediliyor (Nemotron Vision)...")
            image_findings = analyze_image_with_vision(st.session_state.attached_image_bytes, mime_type=st.session_state.attached_mime)
            # Clear attached image after submission
            st.session_state.attached_image_bytes = None
        
        status_box.write("📚 Tıp literatürü taranıyor ve kılavuzlar araştırılıyor...")
        
        formatted_history = []
        for m in st.session_state.messages[-8:]:
            if m["role"] in ("user", "assistant"):
                formatted_history.append({"role": m["role"], "content": m["content"]})

        try:
            config = {"configurable": {"thread_id": st.session_state.thread_id}}
            enriched_question = f"[{triage_context}] {prompt_to_send}"
            
            state = graph.invoke(
                {
                    "question": enriched_question,
                    "history": formatted_history,
                    "image_description": image_findings,
                    "kb": [],
                    "web": [],
                    "answer": "",
                    "route": ""
                },
                config=config
            )
            
            status_box.update(label="Değerlendirme tamamlandı.", state="complete", expanded=False)

            answer = state.get("answer", "Klinik değerlendirme tamamlanamadı.")
            st.session_state.last_answer_for_tts = answer
            st.markdown(answer)

            # Tools Tracking
            tools_list = ["Pinecone Literatür"]
            if state.get("route") == "web" and settings.tavily_api_key:
                tools_list.append("Tavily Canlı Kılavuz Taraması")
            if image_findings:
                tools_list.append("Multimodal Görüntü Analizi")

            # Sources Packaging
            sources_pkg = []
            for item in state.get("kb", []):
                sources_pkg.append({
                    "type": "pdf",
                    "page": item.get("page"),
                    "score": item.get("score"),
                    "text": item.get("text", "")
                })
            for item in state.get("web", []):
                sources_pkg.append({
                    "type": "web",
                    "url": item.get("url"),
                    "title": item.get("title"),
                    "content": item.get("content", "")
                })

            # Display Tools Badges
            badges_html = " ".join([f'<span class="badge-tool">🔍 {tool}</span>' for tool in tools_list])
            st.markdown(f'<div style="margin-top:6px; margin-bottom:6px;">{badges_html}</div>', unsafe_allow_html=True)

            # Display Sources
            if sources_pkg:
                with st.expander(f"📚 Dayanak Literatür & Kaynaklar ({len(sources_pkg)})", expanded=False):
                    for src in sources_pkg:
                        if src.get("type") == "pdf":
                            st.markdown(f"""
                            <div class="citation-card">
                                <strong>📖 Gale Encyclopedia of Medicine (2002)</strong> — <span style="background:#fef3c7; color:#92400e; padding:2px 6px; border-radius:4px; font-size:0.75rem;">Sayfa {src.get("page")}</span> <span style="color:#64748b; font-size:0.75rem;">(Benzerlik: %{int(float(src.get("score", 0))*100)})</span>
                                <div style="color:#475569; margin-top:4px;">"{src.get("text", "")}"</div>
                            </div>
                            """, unsafe_allow_html=True)
                        elif src.get("type") == "web":
                            st.markdown(f"""
                            <div class="citation-card">
                                <strong>🌐 <a href="{src.get('url')}" target="_blank" style="color:#0284c7; text-decoration:none;">{src.get('title')}</a></strong> — <span style="background:#f1f5f9; color:#475569; padding:2px 6px; border-radius:4px; font-size:0.75rem;">Harici Kılavuz</span>
                                <div style="color:#475569; margin-top:4px;">{src.get('content', '')[:250]}...</div>
                            </div>
                            """, unsafe_allow_html=True)

            # Save in session state
            st.session_state.messages.append({
                "role": "assistant",
                "content": answer,
                "sources": sources_pkg,
                "tools": tools_list
            })
            st.rerun()

        except Exception as exc:
            status_box.update(label="Hata oluştu", state="error", expanded=False)
            st.error(f"Klinik asistan işlem sırasında bir hata ile karşılaştı: {exc}")
