import streamlit as st
from google import genai
import tempfile
import os
import base64
import time
import threading
import hashlib
import traceback

# Importamos las utilidades del archivo local
from utils import (
    load_system_prompt,
    load_history,
    save_analysis,
    delete_analysis,
    update_analysis_details,
    build_modern_html_report,
    estimate_report_height,
    report_to_text,
)

MODEL_NAME = "gemini-3.5-flash"
MAX_AUDIT_SECONDS = 600          # tiempo maximo de espera de una auditoria
CHAT_HEIGHT = 480                # alto de la zona de mensajes del chat (px)
CHAT_SUGGESTIONS = [
    "Write an email to the seller requesting the missing paperwork and corrections",
    "Summarize the discrepancies found in this audit",
    "Which documents are missing or incomplete?",
]
PAGES = ["New Analysis", "Saved Analyses / History"]

# --- CONFIGURACION DE PAGINA ---
st.set_page_config(
    page_title="Technical Records Review",
    page_icon="logo.png" if os.path.exists("logo.png") else None,
    layout="wide"
)

# --- ESTILOS CSS ---
st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

        :root {
            --navy: #14305a;
            --navy-dark: #0e2342;
            --green: #2ecc8f;
            --green-dark: #1fae75;
            --red: #dc2626;
            --red-dark: #b91c1c;
            --bg: #f5f7fb;
            --card: #ffffff;
            --border: #e3e8ef;
            --text: #1f2937;
            --muted: #6b7280;
            --radius: 12px;
        }

        /* ---------- Base ---------- */
        html, body, [class*="css"], .stApp {
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif !important;
        }
        .stApp { background-color: var(--bg); }
        [data-testid="stHeader"], [data-testid="stSidebar"] { display: none !important; }
        .block-container {
            padding-top: 1.2rem !important;
            padding-bottom: 8rem !important;   /* espacio para la caja de chat fija abajo */
            max-width: 1280px;
        }

        /* ---------- Titles ---------- */
        h1 {
            padding-top: 0rem !important;
            padding-bottom: 0.5rem !important;
            margin-top: 0rem !important;
            color: var(--navy) !important;
            font-weight: 700 !important;
        }
        h3, h4 {
            color: var(--navy) !important;
            font-weight: 700 !important;
            letter-spacing: -0.01em;
        }
        hr {
            border: none !important;
            border-top: 1px solid var(--border) !important;
            margin: 1.2rem 0 !important;
        }

        /* ---------- Navigation (radio con aspecto de pestanas) ---------- */
        [data-testid="stRadio"] [role="radiogroup"] {
            gap: 6px;
            border-bottom: 1px solid var(--border);
            flex-wrap: nowrap;
        }
        [data-testid="stRadio"] label {
            padding: 10px 18px !important;
            margin: 0 !important;
            border-radius: 10px 10px 0 0;
            border-bottom: 3px solid transparent;
            cursor: pointer;
            transition: all 0.15s ease;
        }
        [data-testid="stRadio"] label > div:first-child { display: none !important; }
        [data-testid="stRadio"] label p {
            color: var(--muted) !important;
            font-size: 0.95rem !important;
            font-weight: 600 !important;
        }
        [data-testid="stRadio"] label:hover { background: rgba(20, 48, 90, 0.05); }
        [data-testid="stRadio"] label:hover p { color: var(--navy) !important; }
        [data-testid="stRadio"] label:has(input:checked) { border-bottom-color: var(--green); }
        [data-testid="stRadio"] label:has(input:checked) p { color: var(--navy) !important; }

        /* ---------- Inputs ---------- */
        [data-baseweb="input"] > div,
        [data-baseweb="select"] > div,
        [data-baseweb="base-input"] {
            border-radius: 10px !important;
            background-color: var(--card) !important;
            border-color: var(--border) !important;
        }
        [data-baseweb="input"] > div:focus-within,
        [data-baseweb="select"] > div:focus-within {
            border-color: var(--green) !important;
            box-shadow: 0 0 0 3px rgba(46, 204, 143, 0.18) !important;
        }
        [data-testid="stWidgetLabel"] p {
            color: var(--navy) !important;
            font-weight: 600 !important;
            font-size: 0.88rem !important;
        }

        /* ---------- File uploader ---------- */
        [data-testid="stFileUploaderDropzone"] {
            background-color: var(--card);
            border: 2px dashed #c9d3e0;
            border-radius: var(--radius);
            padding: 1.2rem;
            transition: all 0.2s ease;
        }
        [data-testid="stFileUploaderDropzone"]:hover {
            border-color: var(--green);
            background-color: #f1fbf7;
        }

        /* ---------- Buttons ---------- */
        button[kind="primary"], [data-testid="stBaseButton-primary"] {
            background: linear-gradient(135deg, var(--navy) 0%, #1d4a85 100%) !important;
            border: none !important;
            border-radius: 10px !important;
            color: #ffffff !important;
            font-weight: 600 !important;
            padding: 0.55rem 1rem !important;
            box-shadow: 0 2px 8px rgba(20, 48, 90, 0.25);
            transition: all 0.2s ease;
        }
        button[kind="primary"]:hover, [data-testid="stBaseButton-primary"]:hover {
            background: linear-gradient(135deg, var(--green-dark) 0%, var(--green) 100%) !important;
            box-shadow: 0 4px 14px rgba(46, 204, 143, 0.4);
            transform: translateY(-1px);
        }
        button[kind="secondary"], [data-testid="stBaseButton-secondary"] {
            border-radius: 10px !important;
            border: 1px solid var(--border) !important;
            color: var(--navy) !important;
            font-weight: 600 !important;
            background-color: var(--card) !important;
        }
        button[kind="secondary"]:hover, [data-testid="stBaseButton-secondary"]:hover {
            border-color: var(--green) !important;
            color: var(--green-dark) !important;
        }

        /* Delete (boton de la ficha y confirmacion del dialogo): rojo */
        .st-key-delete_audit button:hover {
            border-color: var(--red) !important;
            color: var(--red) !important;
            background-color: #fef2f2 !important;
        }
        .st-key-confirm_delete button {
            background: var(--red) !important;
            box-shadow: 0 2px 8px rgba(220, 38, 38, 0.3) !important;
        }
        .st-key-confirm_delete button:hover {
            background: var(--red-dark) !important;
            box-shadow: 0 4px 14px rgba(220, 38, 38, 0.4) !important;
        }

        /* ---------- Metric cards ---------- */
        [data-testid="stMetric"] {
            background-color: var(--card);
            border: 1px solid var(--border);
            border-left: 4px solid var(--green);
            border-radius: var(--radius);
            padding: 12px 16px;
            box-shadow: 0 2px 8px rgba(15, 23, 42, 0.04);
        }
        [data-testid="stMetricLabel"] p {
            color: var(--muted) !important;
            font-size: 0.75rem !important;
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }
        [data-testid="stMetricValue"] {
            color: var(--navy);
            font-size: 1.25rem !important;
            font-weight: 700;
        }

        /* ---------- Expander ---------- */
        [data-testid="stExpander"] {
            background-color: var(--card);
            border: 1px solid var(--border) !important;
            border-radius: var(--radius) !important;
            box-shadow: 0 2px 8px rgba(15, 23, 42, 0.04);
        }

        /* ---------- Alerts ---------- */
        [data-testid="stAlert"] { border-radius: var(--radius); }

        /* ---------- Chat ---------- */
        /* Mensajes: sin avatares ni tarjetas. Usuario = burbuja a la derecha; asistente = texto limpio */
        [data-testid="stChatMessage"] {
            background: transparent !important;
            border: none !important;
            box-shadow: none !important;
            padding: 0.35rem 0 !important;
        }
        [data-testid="stChatMessageAvatarUser"],
        [data-testid="stChatMessageAvatarAssistant"],
        [data-testid="stChatMessageAvatarCustom"],
        [data-testid^="chatAvatarIcon"] {
            display: none !important;
        }
        [data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarUser"]) {
            flex-direction: row-reverse;
        }
        [data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarUser"]) [data-testid="stChatMessageContent"] {
            background: #e6ecf5;
            border-radius: 18px;
            padding: 10px 16px;
            width: fit-content;
            max-width: 80%;
            margin-left: auto;
        }
        [data-testid="stChatMessageContent"] { color: var(--text); line-height: 1.6; }

        /* Caja de entrada fija abajo, estilo ChatGPT / Gemini */
        [data-testid="stBottom"] > div {
            background: linear-gradient(to top, var(--bg) 65%, rgba(245, 247, 251, 0)) !important;
        }
        [data-testid="stChatInput"] {
            border-radius: 26px !important;
            border: 1px solid var(--border) !important;
            background: var(--card) !important;
            box-shadow: 0 4px 18px rgba(20, 48, 90, 0.10);
        }
        [data-testid="stChatInput"]:focus-within {
            border-color: var(--green) !important;
            box-shadow: 0 4px 18px rgba(46, 204, 143, 0.18);
        }
        [data-testid="stChatInput"] textarea { background: transparent !important; }
        [data-testid="stChatInputSubmitButton"] {
            background: var(--navy) !important;
            color: #ffffff !important;
            border-radius: 50% !important;
        }
        [data-testid="stChatInputSubmitButton"]:hover { background: var(--green-dark) !important; }

        .chat-empty {
            text-align: center;
            color: var(--muted);
            padding: 1.6rem 0 0.8rem 0;
            font-size: 1.05rem;
            font-weight: 500;
        }

        /* ---------- Captions ---------- */
        [data-testid="stCaptionContainer"] { color: var(--muted); }

        /* ---------- Hidden elements ---------- */
        button[title="View fullscreen"],
        button[aria-label="View fullscreen"],
        [data-testid="stImage"] button,
        [data-testid="StyledFullScreenButton"] {
            display: none !important;
            visibility: hidden !important;
            pointer-events: none !important;
        }
        .stMarkdown h1 a, .stMarkdown h2 a, .stMarkdown h3 a,
        .stMarkdown h4 a, .stMarkdown h5 a, .stMarkdown h6 a,
        [data-testid="stHeaderActionElements"] {
            display: none !important;
            visibility: hidden !important;
        }
    </style>
""", unsafe_allow_html=True)


# =====================================================================
#  UTILIDADES DE ARCHIVOS Y GEMINI
# =====================================================================
class AuditCancelled(Exception):
    """Se lanza cuando el usuario cancela una auditoria en curso."""


def _decode_file(fitem):
    """Devuelve (nombre, bytes) para cualquier formato de archivo que maneja la app."""
    if isinstance(fitem, dict):
        return fitem.get("name", "document.pdf"), base64.b64decode(fitem["content"])
    if hasattr(fitem, "name") and hasattr(fitem, "getvalue"):
        return fitem.name, fitem.getvalue()
    if isinstance(fitem, str):
        return "document.pdf", fitem.encode("utf-8")
    return None


def _file_name(fitem):
    if isinstance(fitem, dict):
        return fitem.get("name", "document.pdf")
    return getattr(fitem, "name", "document.pdf")


def _files_signature(files_payload_list):
    """Firma estable de un conjunto de archivos (para saber si hay que volver a subirlos)."""
    parts = []
    for f in files_payload_list:
        content = f.get("content", "") if isinstance(f, dict) else ""
        parts.append(f"{_file_name(f)}:{len(content)}")
    return hashlib.md5("|".join(parts).encode("utf-8")).hexdigest()


def upload_to_gemini(client, files_payload_list, cancel_event=None):
    """Sube los archivos a Gemini y devuelve las referencias. Limpia los temporales siempre."""
    uploaded = []
    for fitem in files_payload_list:
        if cancel_event is not None and cancel_event.is_set():
            raise AuditCancelled()
        decoded = _decode_file(fitem)
        if not decoded:
            continue
        fname, fbytes = decoded
        ext = fname.split(".")[-1] if "." in fname else "pdf"
        tmp_path = None
        try:
            with tempfile.NamedTemporaryFile(delete=False, suffix=f".{ext}") as tmp:
                tmp.write(fbytes)
                tmp_path = tmp.name
            uploaded.append(client.files.upload(file=tmp_path))
        finally:
            if tmp_path and os.path.exists(tmp_path):
                os.remove(tmp_path)
    return uploaded


# =====================================================================
#  MOTOR DE AUDITORIA
# =====================================================================
def run_gemini_audit(client, files_payload_list, system_prompt, cancel_event=None):
    """Ejecuta la auditoria. No usa ninguna llamada de Streamlit (se ejecuta en un hilo)."""
    try:
        uploaded_gemini_files = upload_to_gemini(client, files_payload_list, cancel_event)
        contents = uploaded_gemini_files + [system_prompt]

        response = None
        max_retries = 3
        for attempt in range(max_retries):
            if cancel_event is not None and cancel_event.is_set():
                raise AuditCancelled()
            try:
                response = client.models.generate_content(
                    model=MODEL_NAME,
                    contents=contents,
                    config={"response_mime_type": "application/json"}
                )
                if response and response.text:
                    break
            except Exception as e:
                err_str = str(e)
                if ("503" in err_str or "UNAVAILABLE" in err_str) and attempt < max_retries - 1:
                    time.sleep(3)
                    continue
                return None, None, f"Error en el modelo {MODEL_NAME}: {err_str}"

        if cancel_event is not None and cancel_event.is_set():
            raise AuditCancelled()

        if response and response.text:
            metrics_info = f"Modelo: {MODEL_NAME}"
            if hasattr(response, "usage_metadata") and response.usage_metadata:
                metrics_info += (
                    f" | Tokens: {response.usage_metadata.prompt_token_count} in / "
                    f"{response.usage_metadata.candidates_token_count} out"
                )
            html_report = build_modern_html_report(response.text)
            return html_report, metrics_info, None

        return None, None, "No se recibió respuesta válida del modelo Gemini."

    except AuditCancelled:
        return None, None, "Análisis cancelado."
    except Exception as global_e:
        return None, None, (
            f"Error general en la auditoría: {str(global_e)}\n\n"
            f"```\n{traceback.format_exc()}\n```"
        )


def _request_cancel():
    """Callback del boton Cancel: avisa al hilo y deja un aviso para la siguiente recarga."""
    event = st.session_state.get("audit_cancel_event")
    if event is not None:
        event.set()
    st.session_state["_flash"] = "Analysis cancelled."


def run_audit_cancellable(client, files_payload_list, system_prompt):
    """
    Lanza la auditoria en un hilo y muestra un boton Cancel mientras espera.
    Al pulsar Cancel, Streamlit interrumpe este script en la siguiente actualizacion
    de pantalla (cada 0,5 s) y el resultado del hilo se descarta.
    """
    cancel_event = threading.Event()
    st.session_state["audit_cancel_event"] = cancel_event
    result = {}

    def worker():
        try:
            result["out"] = run_gemini_audit(client, files_payload_list, system_prompt, cancel_event)
        except Exception as e:
            result["out"] = (None, None, f"Error general en la auditoría: {e}")

    thread = threading.Thread(target=worker, daemon=True)
    thread.start()

    box = st.container()
    with box:
        col_status, col_cancel = st.columns([5, 1], vertical_alignment="center")
        status = col_status.empty()
        col_cancel.button("Cancel", key="cancel_audit", on_click=_request_cancel, use_container_width=True)

    start = time.time()
    while thread.is_alive():
        elapsed = int(time.time() - start)
        status.markdown(f"**Analyzing documents...** {elapsed}s")
        if elapsed > MAX_AUDIT_SECONDS:
            cancel_event.set()
            box.empty()
            return None, None, "El análisis ha superado el tiempo máximo de espera. Inténtalo de nuevo."
        time.sleep(0.5)

    box.empty()
    return result.get("out", (None, None, "No se obtuvo resultado de la auditoría."))


# =====================================================================
#  CHAT
# =====================================================================
def _queue_prompt(pending_key, text):
    st.session_state[pending_key] = text


def _clear_chat(chat_key):
    st.session_state[chat_key] = []


def get_chat_files(client, files_payload_list, chat_id, force=False):
    """Sube los documentos una sola vez por auditoria y reutiliza las referencias en cada mensaje."""
    cache = st.session_state.setdefault("gemini_file_cache", {})
    signature = _files_signature(files_payload_list)
    entry = cache.get(chat_id)
    if entry and entry["sig"] == signature and not force:
        return entry["files"]
    files = upload_to_gemini(client, files_payload_list)
    cache[chat_id] = {"sig": signature, "files": files}
    return files


def build_chat_prompt(part_number, vendor, report_text, history, user_query):
    convo = "\n".join(
        f"{'User' if m['role'] == 'user' else 'Assistant'}: {m['content']}"
        for m in history[-12:]
    )
    return f"""You are an expert aeronautical quality auditor for engine parts (Non-LLP).

Context of the current Technical Records Review (TRR):
- Part Number: {part_number}
- Vendor / Seller: {vendor}
- Audit findings per document:
{report_text}

Conversation so far:
{convo if convo else "(this is the first message)"}

Latest user message:
{user_query}

Instructions:
- Use the uploaded paperwork and the audit findings above. Take the whole conversation into account, including any correction or change the user asked for earlier.
- Reply in the same language as the user's message, unless the user asks for a deliverable (for example an email) in another language.
- If the user asks for an email to the seller/vendor requesting paperwork: be professional, clear and assertive; only request what is missing or must be corrected, citing the specific documents, values and discrepancies from the audit; do not recap what has been verified as correct unless asked; no unnecessary prose.
- Otherwise answer concisely, directly and accurately.
"""


def chat_stream(client, files_payload_list, chat_id, prompt_text):
    """Generador de texto en streaming. Si la referencia a los archivos caduco, los vuelve a subir una vez."""
    for attempt in (0, 1):
        started = False
        try:
            files = get_chat_files(client, files_payload_list, chat_id, force=(attempt == 1))
            for chunk in client.models.generate_content_stream(
                model=MODEL_NAME, contents=files + [prompt_text]
            ):
                if chunk.text:
                    started = True
                    yield chunk.text
            return
        except Exception:
            if started or attempt == 1:
                raise


def render_audit_chat(client, files_payload_list, report_html, part_number, vendor, chat_id):
    """
    Chat estilo ChatGPT / Gemini: mensajes en una zona con scroll y caja de entrada fija abajo.
    IMPORTANTE: st.chat_input solo se fija al borde inferior de la pantalla si se llama en el
    nivel raiz de la pagina (no dentro de pestanas, columnas ni contenedores).
    """
    chat_key = f"chat_{chat_id}"
    pending_key = f"{chat_key}_pending"
    messages = st.session_state.setdefault(chat_key, [])

    st.markdown("---")
    col_title, col_new = st.columns([6, 1], vertical_alignment="center")
    col_title.markdown("### Assistant")
    if messages:
        col_new.button("New chat", key=f"new_chat_{chat_id}", on_click=_clear_chat,
                       args=(chat_key,), use_container_width=True)

    typed = st.chat_input("Ask anything about this audit...", key=f"chat_input_{chat_id}")
    prompt = typed or st.session_state.pop(pending_key, None)

    box = st.container(height=CHAT_HEIGHT, border=False)
    with box:
        if not messages and not prompt:
            st.markdown("<div class='chat-empty'>How can I help with this audit?</div>", unsafe_allow_html=True)
            for i, suggestion in enumerate(CHAT_SUGGESTIONS):
                st.button(suggestion, key=f"suggestion_{chat_id}_{i}", on_click=_queue_prompt,
                          args=(pending_key, suggestion), use_container_width=True)

        for message in messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

        if prompt:
            history_before = list(messages)
            messages.append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.markdown(prompt)

            with st.chat_message("assistant"):
                answer = ""
                try:
                    prompt_text = build_chat_prompt(
                        part_number, vendor, report_to_text(report_html), history_before, prompt
                    )
                    stream = chat_stream(client, files_payload_list, chat_id, prompt_text)
                    with st.spinner("Thinking..."):
                        first = next(stream, None)

                    def full_stream():
                        if first:
                            yield first
                        yield from stream

                    answer = st.write_stream(full_stream())
                    if not answer:
                        answer = "No se pudo obtener respuesta del modelo."
                        st.markdown(answer)
                except Exception as e:
                    answer = f"Error procesando la consulta: {e}"
                    st.markdown(answer)

            messages.append({"role": "assistant", "content": answer})


# =====================================================================
#  COMPONENTES DE INTERFAZ
# =====================================================================
def render_report(report_html, metrics):
    st.markdown("### Audit Report")
    st.components.v1.html(report_html, height=estimate_report_height(report_html), scrolling=True)
    if metrics:
        st.caption(metrics)


def show_audit_error(message, details):
    st.error(message)
    if details:
        st.markdown(details)


@st.dialog("Delete audit")
def confirm_delete_dialog(record_id, label):
    st.write(f"Are you sure you want to delete **{label}**?")
    st.caption("This will permanently remove the audit and its documents from the history. It cannot be undone.")
    col_cancel, col_confirm = st.columns(2)
    if col_cancel.button("Cancel", key="cancel_delete", use_container_width=True):
        st.rerun()
    if col_confirm.button("Delete", key="confirm_delete", type="primary", use_container_width=True):
        delete_analysis(record_id)
        st.session_state.pop("history_select", None)
        st.session_state["_flash"] = "Audit deleted."
        st.rerun()


# =====================================================================
#  CONTROL DE ACCESO
# =====================================================================
ACCESO_PASSWORD = st.secrets["ACCESO_PASSWORD"]

if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:
    @st.dialog("Acceso restringido - Kaito Aero")
    def login_dialog():
        st.write("Introduce la contraseña para acceder a la herramienta TRR.")
        with st.form("login_form", clear_on_submit=False):
            user_pass = st.text_input("Contraseña", type="password", key="pass_input")
            submit = st.form_submit_button("Ingresar", use_container_width=True, type="primary")
            if submit:
                if user_pass == ACCESO_PASSWORD:
                    st.session_state.authenticated = True
                    st.rerun()
                else:
                    st.error("Contraseña incorrecta. Inténtalo de nuevo.")

    login_dialog()
    st.stop()

# --- INICIALIZACION DE GEMINI ---
API_KEY = st.secrets["GEMINI_API_KEY"]
client = genai.Client(api_key=API_KEY)

# Avisos breves (toast) dejados por acciones anteriores: cancelar, borrar, guardar...
_flash_message = st.session_state.pop("_flash", None)
if _flash_message:
    st.toast(_flash_message)

# =====================================================================
#  ENCABEZADO Y NAVEGACION
# =====================================================================
col_logo, col_title = st.columns([1, 5], vertical_alignment="center", gap="medium")

with col_logo:
    if os.path.exists("logo.png"):
        st.image("logo.png", width=170)

with col_title:
    st.markdown(
        """
        <div style="font-size:2.2rem; font-weight:700; color:#14305a; letter-spacing:-0.02em; line-height:1.15;">
            Technical Records Review
        </div>
        <div style="height:4px; width:72px; margin-top:10px; border-radius:4px;
                    background:linear-gradient(90deg,#14305a,#2ecc8f);"></div>
        """,
        unsafe_allow_html=True
    )

# Se usa un selector horizontal (con estilo de pestanas) en lugar de st.tabs porque st.chat_input
# solo queda fijado abajo del todo si esta en el nivel raiz de la pagina.
page = st.radio("Section", PAGES, horizontal=True, label_visibility="collapsed", key="page")


# =====================================================================
#  PAGINA 1: NUEVO ANALISIS
# =====================================================================
if page == PAGES[0]:
    st.markdown("### Launch New Audit")

    col1, col2, col3 = st.columns(3)
    with col1:
        part_number = st.text_input("Part Number (P/N)", placeholder="e.g. 305-001-201-0")
    with col2:
        project_name = st.text_input("Project Name", placeholder="e.g. CFM56-7B Engine Overhaul")
    with col3:
        vendor = st.text_input("Vendor / Seller", placeholder="e.g. Lufthansa Technik AG")

    uploaded_files = st.file_uploader(
        "Upload paperwork (Form 1 / FAA 8130-3, Removal Tag, Workshop Report, NIS/ICS, Commercial Trace, ATA Spec 106)",
        type=["pdf", "png", "jpg", "jpeg"],
        accept_multiple_files=True,
        key="upload_new"
    )

    if st.button("Run Analysis", type="primary", use_container_width=True):
        if not part_number or not project_name or not vendor:
            st.info("Please provide Part Number, Project Name, and Vendor before running the audit.")
        elif not uploaded_files:
            st.warning("Please upload at least one document to analyze.")
        else:
            system_prompt = load_system_prompt(part_number, project_name, vendor)
            if not system_prompt:
                st.error("Archivo 'prompt.txt' no encontrado en la carpeta TRR.")
            else:
                files_payload = [
                    {"name": f.name, "content": base64.b64encode(f.getvalue()).decode("utf-8")}
                    for f in uploaded_files
                ]

                html_report, metrics_info, error_details = run_audit_cancellable(
                    client, files_payload, system_prompt
                )

                if html_report:
                    save_analysis(part_number, project_name, vendor, files_payload, html_report, metrics_info)
                    st.session_state["current_audit"] = {
                        "id": f"new_{int(time.time())}",
                        "report": html_report,
                        "metrics": metrics_info,
                        "part_number": part_number,
                        "vendor": vendor,
                        "files": files_payload
                    }
                    st.success("Audit completed and saved to history.")
                else:
                    show_audit_error("No se pudo completar el análisis.", error_details)

    # Si hay una auditoria reciente, se muestra con su chat
    if "current_audit" in st.session_state:
        curr = st.session_state["current_audit"]
        st.markdown("---")
        render_report(curr["report"], curr["metrics"])
        render_audit_chat(
            client=client,
            files_payload_list=curr["files"],
            report_html=curr["report"],
            part_number=curr["part_number"],
            vendor=curr["vendor"],
            chat_id=curr["id"]
        )


# =====================================================================
#  PAGINA 2: HISTORIAL
# =====================================================================
else:
    st.markdown("### Saved Audits")
    history_data = load_history()

    if not history_data:
        st.info("No saved audits found yet. Run a new analysis to populate history.")
    else:
        ids = [item["id"] for item in history_data]
        labels = {
            item["id"]: f"[{item['date']}] {item['project_name']} | P/N: {item['part_number']} ({item.get('vendor', 'N/A')})"
            for item in history_data
        }
        # Si el registro seleccionado ya no existe (p. ej. se acaba de borrar), se descarta la seleccion
        if st.session_state.get("history_select") not in ids:
            st.session_state.pop("history_select", None)

        # Se selecciona por id (no por texto) para que editar los datos no cambie la seleccion
        selected_id = st.selectbox(
            "Select a previous audit to review:",
            ids,
            format_func=lambda i: labels[i],
            key="history_select"
        )
        record = next(item for item in history_data if item["id"] == selected_id)
        rid = record["id"]

        st.markdown("---")

        col_a, col_b, col_c, col_d, col_e = st.columns([2, 2, 2, 2, 1], vertical_alignment="bottom")
        with col_a:
            st.metric("Project Name", record["project_name"])
        with col_b:
            st.metric("Part Number", record["part_number"])
        with col_c:
            st.metric("Vendor", record.get("vendor", "N/A"))
        with col_d:
            st.metric("Date", record["date"])
        with col_e:
            if st.button("Delete", key="delete_audit", use_container_width=True):
                confirm_delete_dialog(rid, f"{record['project_name']} | P/N {record['part_number']}")

        st.caption(f"**Documents:** {', '.join(record.get('filenames', [])) or 'none'}")

        # ---------- Editar datos ----------
        with st.expander("Edit details", expanded=False):
            e1, e2, e3 = st.columns(3)
            new_pn = e1.text_input("Part Number (P/N)", value=record["part_number"], key=f"edit_pn_{rid}")
            new_project = e2.text_input("Project Name", value=record["project_name"], key=f"edit_project_{rid}")
            new_vendor = e3.text_input("Vendor / Seller", value=record.get("vendor", ""), key=f"edit_vendor_{rid}")
            st.caption("Changes apply to the saved record. Re-run the analysis to refresh the report with the new data.")
            if st.button("Save changes", type="primary", key=f"save_details_{rid}"):
                if not (new_pn.strip() and new_project.strip() and new_vendor.strip()):
                    st.warning("Part Number, Project Name and Vendor cannot be empty.")
                else:
                    update_analysis_details(rid, new_pn, new_project, new_vendor)
                    st.session_state["_flash"] = "Details updated."
                    st.rerun()

        # ---------- Re-ejecutar / gestionar documentos ----------
        with st.expander("Re-run audit / manage documents", expanded=False):
            # 'gen' cambia tras cada re-ejecucion para que las casillas y el cargador empiecen limpios
            gen = st.session_state.setdefault(f"gen_{rid}", 0)

            files_data = record.get("files_data", [])
            kept_files = []
            st.markdown("**Documents in this audit**")
            if files_data:
                for idx, fitem in enumerate(files_data):
                    if st.checkbox(_file_name(fitem), value=True, key=f"keep_{rid}_{gen}_{idx}"):
                        kept_files.append(fitem)
                st.caption("Uncheck a document to remove it from the audit when you re-run.")
            else:
                st.caption("No documents associated with this record.")

            additional_files = st.file_uploader(
                "Add more documents (optional):",
                type=["pdf", "png", "jpg", "jpeg"],
                accept_multiple_files=True,
                key=f"extra_files_{rid}_{gen}"
            )

            if st.button("Re-run Analysis Now", type="primary", key=f"rerun_{rid}", use_container_width=True):
                system_prompt = load_system_prompt(
                    record["part_number"], record["project_name"], record.get("vendor", "N/A")
                )

                if not system_prompt:
                    st.error("Archivo 'prompt.txt' no encontrado.")
                else:
                    current_payload = list(kept_files)
                    for af in additional_files or []:
                        current_payload.append({
                            "name": af.name,
                            "content": base64.b64encode(af.getvalue()).decode("utf-8")
                        })

                    if not current_payload:
                        st.warning("There are no documents left to analyze. Keep at least one or upload a new one.")
                    else:
                        html_report, metrics_info, error_details = run_audit_cancellable(
                            client, current_payload, system_prompt
                        )

                        if html_report:
                            save_analysis(
                                part_number=record["part_number"],
                                project_name=record["project_name"],
                                vendor=record.get("vendor", "N/A"),
                                files_payload=current_payload,
                                report_html=html_report,
                                metrics_text=f"Reejecutado con {metrics_info}",
                                record_id=rid
                            )
                            st.session_state[f"gen_{rid}"] = gen + 1
                            st.session_state["_flash"] = "Audit updated successfully."
                            st.rerun()
                        else:
                            show_audit_error("No se pudo completar la reejecución.", error_details)

        render_report(record["report"], record.get("metrics"))

        render_audit_chat(
            client=client,
            files_payload_list=record.get("files_data", []),
            report_html=record["report"],
            part_number=record["part_number"],
            vendor=record.get("vendor", "N/A"),
            chat_id=rid
        )
