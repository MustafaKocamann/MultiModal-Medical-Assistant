import base64
import io
import uuid
import streamlit as st
from PIL import Image

# ----------------- PAGE CONFIG -----------------
st.set_page_config(
    page_title="MedGuide AI — Klinik Triyaj ve Asistan",
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
        padding-bottom: 3rem;
        max-width: 1050px;
    }

    /* Modern Clinical Header */
    .clinical-header {
        background: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 16px;
        padding: 20px 24px;
        margin-bottom: 1.25rem;
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
        width: 48px;
        height: 48px;
        background: linear-gradient(135deg, #0284c7 0%, #0369a1 100%);
        color: white;
        border-radius: 12px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 24px;
        box-shadow: 0 4px 10px rgba(2, 132, 199, 0.25);
    }

    .clinical-title {
        margin: 0;
        font-size: 1.45rem;
        font-weight: 700;
        color: #0f172a;
        letter-spacing: -0.3px;
    }

    .clinical-subtitle {
        margin: 2px 0 0 0;
        font-size: 0.88rem;
        color: #64748b;
        font-weight: 400;
    }

    /* Emergency Disclaimer Bar */
    .triage-alert {
        background-color: #fff1f2;
        border: 1px solid #fecdd3;
        border-left: 4px solid #e11d48;
        border-radius: 10px;
        padding: 12px 16px;
        margin-bottom: 1.5rem;
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

    /* Buttons */
    div.stButton > button {
        border-radius: 8px;
        font-weight: 500;
        font-size: 0.85rem;
        transition: all 0.15s ease-in-out;
        border: 1px solid #e2e8f0;
        background-color: #ffffff;
        color: #1e293b;
        text-align: left;
    }

    div.stButton > button:hover {
        border-color: #0284c7;
        color: #0284c7;
        background-color: #f0f9ff;
        transform: translateY(-1px);
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
if "messages" not in st.session_state:
    st.session_state.messages = [
        {
            "role": "assistant",
            "content": "Merhaba! Ben **MedGuide AI** klinik triyaj ve medikal eğitim asistanıyım. 🩺\n\nSemptomlarınızı detaylandırabilir, tıbbi terminoloji veya ilaç etkileşimleri hakkında danışabilir, cilt lezyonu veya reçete görseli yükleyebilir ya da sesli danışma gerçekleştirebilirsiniz.\n\n*Nasıl yardımcı olabilirim?*",
            "sources": [],
            "tools": []
        }
    ]

if "thread_id" not in st.session_state:
    st.session_state.thread_id = str(uuid.uuid4())

if "pending_prompt" not in st.session_state:
    st.session_state.pending_prompt = None

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
    st.markdown('<div class="sidebar-section-title">🏥 Konsültasyon Ayarları</div>', unsafe_allow_html=True)
    
    # System Status
    if APP_CONFIGURED:
        st.markdown('<div class="badge badge-success">● Medikal Motor Çevrimiçi</div>', unsafe_allow_html=True)
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
    if st.button("🔄 Yeni Konsültasyon Başlat", use_container_width=True):
        st.session_state.messages = [st.session_state.messages[0]]
        st.session_state.thread_id = str(uuid.uuid4())
        st.session_state.pending_prompt = None
        st.rerun()

    st.caption("© 2026 MedGuide AI • Tıbbi Karar Destek Sistemi")

# ----------------- MAIN WORKSPACE -----------------

# 1. Header Bar
st.markdown("""
<div class="clinical-header">
    <div class="clinical-title-box">
        <div class="clinical-icon-badge">⚕️</div>
        <div>
            <h1 class="clinical-title">MedGuide AI <span style="font-size:0.75rem; font-weight:600; background:#f0f9ff; color:#0284c7; padding:3px 8px; border-radius:6px; border:1px solid #bae6fd; vertical-align:middle;">Klinik Destek v1.0</span></h1>
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
        <strong>ACİL TIBBİ UYARI:</strong> MedGuide AI bir hekim veya resmi tanı aracı değildir. Ani göğüs ağrısı, konuşma güçlüğü, nefes darlığı, kontrolsüz kanama veya bilinç bulanıklığı gibi kritik belirtilerde lütfen vakit kaybetmeden <strong>112 Acil Çağrı Merkezi</strong>'ni arayınız.
    </div>
</div>
""", unsafe_allow_html=True)

# 3. Multimodal Media Panel (Image & Audio)
attached_image_bytes = None
attached_mime = "image/jpeg"

with st.expander("📎 Çok Modlu Klinik Girdi (Reçete/Görüntü İnceleme veya Sesli Danışma)", expanded=False):
    col_img, col_audio = st.columns(2)
    
    with col_img:
        st.markdown("<small><strong>📷 Tıbbi Görsel / Reçete / Dermatoloji</strong></small>", unsafe_allow_html=True)
        img_upload = st.file_uploader("Görsel seçiniz (PNG, JPG, WEBP - Max 5MB)", type=["png", "jpg", "jpeg", "webp"], key="img_upload", label_visibility="collapsed")
        if img_upload:
            attached_image_bytes = img_upload.read()
            attached_mime = img_upload.type
            st.image(attached_image_bytes, caption="Yüklenen İnceleme Görseli", use_container_width=True)
            
    with col_audio:
        st.markdown("<small><strong>🎙️ Sesli Soru / Transkripsiyon (Whisper)</strong></small>", unsafe_allow_html=True)
        try:
            audio_data = st.audio_input("Ses kaydetmek için tıklayın", label_visibility="collapsed")
        except AttributeError:
            audio_data = st.file_uploader("Ses dosyası yükleyin (WAV/MP3)", type=["wav", "mp3", "webm"], label_visibility="collapsed")
        
        if audio_data:
            st.audio(audio_data)
            if st.button("Transkribe Et ve Soruya Ekle", key="transcribe_action_btn"):
                with st.spinner("Whisper modeli ile ses çözümleniyor..."):
                    result_txt = transcribe_audio_whisper(audio_data.read(), filename="voice.wav")
                    if result_txt:
                        st.session_state.pending_prompt = result_txt
                        st.success(f"Metin: {result_txt}")
                        st.rerun()

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

# 5. User Input Handling
user_input = st.chat_input("Klinik sorunuzu, semptomlarınızı veya ilaç adını buraya yazınız...")

# If pending prompt from sidebar button or voice transcription
if st.session_state.pending_prompt:
    user_input = st.session_state.pending_prompt
    st.session_state.pending_prompt = None

if user_input:
    if not APP_CONFIGURED:
        st.error("Sistem API anahtarları `.env` içerisinde yapılandırılmalıdır.")
        st.stop()

    # Append User Message
    st.session_state.messages.append({
        "role": "user",
        "content": user_input,
        "sources": [],
        "tools": []
    })

    with st.chat_message("user", avatar="🧑‍💼"):
        st.markdown(user_input)

    # Assistant Response Generation
    with st.chat_message("assistant", avatar="🩺"):
        status_box = st.status("Klinik vaka değerlendiriliyor...", expanded=True)
        
        # Step A: Multimodal Vision Check
        image_findings = ""
        if attached_image_bytes:
            status_box.write("👁️ Tıbbi görsel analiz ediliyor (Nemotron Vision)...")
            image_findings = analyze_image_with_vision(attached_image_bytes, mime_type=attached_mime)
        
        # Step B: Retrieval & Routing via LangGraph
        status_box.write("📚 Tıp kütüphanesi taranıyor ve güncel kılavuzlar araştırılıyor...")
        
        formatted_history = []
        for m in st.session_state.messages[-8:]:
            if m["role"] in ("user", "assistant"):
                formatted_history.append({"role": m["role"], "content": m["content"]})

        try:
            config = {"configurable": {"thread_id": st.session_state.thread_id}}
            enriched_question = f"[{triage_context}] {user_input}"
            
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

            # Display Tools
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

            # Store in session state
            st.session_state.messages.append({
                "role": "assistant",
                "content": answer,
                "sources": sources_pkg,
                "tools": tools_list
            })

        except Exception as exc:
            status_box.update(label="Hata oluştu", state="error", expanded=False)
            st.error(f"Klinik asistan işlem sırasında bir hata ile karşılaştı: {exc}")
