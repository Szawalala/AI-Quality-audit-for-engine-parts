import streamlit as st
from google import genai
import tempfile
import os
import base64
import time
import traceback

# Importamos las utilidades del archivo local
from utils import (
    load_system_prompt,
    load_history,
    save_analysis,
    delete_analysis,
    build_modern_html_report,
    estimate_report_height
)

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(
    page_title="Technical Records Review",
    page_icon="logo.png" if os.path.exists("logo.png") else "✈️",
    layout="wide"
)

# --- ESTILOS CSS PERSONALIZADOS ---
st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

        :root {
            --navy: #14305a;
            --navy-dark: #0e2342;
            --green: #2ecc8f;
            --green-dark: #1fae75;
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
            padding-bottom: 3rem !important;
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

        /* ---------- Tabs ---------- */
        [data-baseweb="tab-list"] { gap: 6px; border-bottom: 1px solid var(--border); }
        button[data-baseweb="tab"] {
            padding: 10px 18px;
            border-radius: 10px 10px 0 0;
            color: var(--muted);
            font-weight: 600;
        }
        button[data-baseweb="tab"]:hover { color: var(--navy); background: rgba(20, 48, 90, 0.05); }
        button[data-baseweb="tab"][aria-selected="true"] { color: var(--navy); }
        [data-baseweb="tab-highlight"] { background-color: var(--green) !important; height: 3px !important; }

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
        label, [data-testid="stWidgetLabel"] p {
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
        [data-testid="stChatMessage"] {
            background-color: var(--card);
            border: 1px solid var(--border);
            border-radius: var(--radius);
            padding: 0.9rem 1rem;
            box-shadow: 0 2px 8px rgba(15, 23, 42, 0.04);
        }
        [data-testid="stChatInput"] {
            border-radius: 14px !important;
            border: 1px solid var(--border) !important;
            box-shadow: 0 4px 16px rgba(20, 48, 90, 0.08);
        }
        [data-testid="stChatInput"]:focus-within {
            border-color: var(--green) !important;
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

# --- MOTOR DE AUDITORÍA CON GEMINI 3.5 FLASH ---
def run_gemini_audit(client, files_payload_list, system_prompt):
    uploaded_gemini_files = []
    temp_paths = []
    fixed_model = "gemini-3.5-flash"
    
    try:
        for fitem in files_payload_list:
            if isinstance(fitem, dict):
                fname = fitem.get("name", "document.pdf")
                fbytes = base64.b64decode(fitem["content"])
            elif hasattr(fitem, "name") and hasattr(fitem, "getvalue"):
                fname = fitem.name
                fbytes = fitem.getvalue()
            elif isinstance(fitem, str):
                fname = "document.pdf"
                fbytes = fitem.encode("utf-8")
            else:
                continue

            ext = fname.split('.')[-1] if '.' in fname else 'pdf'
            with tempfile.NamedTemporaryFile(delete=False, suffix=f".{ext}") as tmp:
                tmp.write(fbytes)
                temp_paths.append(tmp.name)
                
            gemini_file = client.files.upload(file=tmp.name)
            uploaded_gemini_files.append(gemini_file)

        contents = uploaded_gemini_files + [system_prompt]

        response = None
        max_retries = 3
        for attempt in range(max_retries):
            try:
                response = client.models.generate_content(
                    model=fixed_model,
                    contents=contents,
                    config={
                        "response_mime_type": "application/json"
                    }
                )
                if response and response.text:
                    break
            except Exception as e:
                err_str = str(e)
                if ("503" in err_str or "UNAVAILABLE" in err_str) and attempt < max_retries - 1:
                    time.sleep(3)
                    continue
                else:
                    return None, None, f"Error en el modelo {fixed_model}: {err_str}"

        if response and response.text:
            metrics_info = f"Modelo: {fixed_model}"
            if hasattr(response, 'usage_metadata') and response.usage_metadata:
                metrics_info += f" | Tokens: {response.usage_metadata.prompt_token_count} in / {response.usage_metadata.candidates_token_count} out"
            
            # Convertimos la respuesta JSON en la tabla HTML moderna
            html_report = build_modern_html_report(response.text)
            return html_report, metrics_info, None

        return None, None, "No se recibió respuesta válida del modelo Gemini."

    except Exception as global_e:
        return None, None, f"Error general en la auditoría: {str(global_e)}\n\n```\n{traceback.format_exc()}\n```"

    finally:
        for path in temp_paths:
            if os.path.exists(path):
                os.remove(path)

# --- NAVEGACIÓN Y CHATBOT DE AUDITORÍA ---
def render_audit_chatbot(client, files_payload_list, report_data, part_number, vendor, record_id=None):
    """
    Renderiza un chat interactivo para hacer preguntas sobre los documentos cargados.
    """
    st.markdown("---")
    st.markdown("### 💬 Chat & Actions on this Audit")
    
    # ID único para mantener la memoria del chat por auditoría
    chat_key = f"chat_history_{record_id if record_id else part_number}"
    if chat_key not in st.session_state:
        st.session_state[chat_key] = []

    # Mostrar mensajes previos del historial
    for message in st.session_state[chat_key]:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # Entrada de usuario con el prompt por defecto de sugerencia
    user_query = st.chat_input(
        placeholder="Write an email for the seller of these parts requesting the missing paperwork"
    )

    if user_query:
        st.chat_message("user").markdown(user_query)
        st.session_state[chat_key].append({"role": "user", "content": user_query})

        with st.spinner("Analyzing paperwork and generating response..."):
            uploaded_gemini_files = []
            temp_paths = []
            
            try:
                # Subida temporal de archivos para dar contexto multimodal a Gemini
                for fitem in files_payload_list:
                    if isinstance(fitem, dict):
                        fname = fitem.get("name", "document.pdf")
                        fbytes = base64.b64decode(fitem["content"])
                    elif hasattr(fitem, "name") and hasattr(fitem, "getvalue"):
                        fname = fitem.name
                        fbytes = fitem.getvalue()
                    elif isinstance(fitem, str):
                        fname = "document.pdf"
                        fbytes = fitem.encode("utf-8")
                    else:
                        continue

                    ext = fname.split('.')[-1] if '.' in fname else 'pdf'
                    with tempfile.NamedTemporaryFile(delete=False, suffix=f".{ext}") as tmp:
                        tmp.write(fbytes)
                        temp_paths.append(tmp.name)
                        
                    gemini_file = client.files.upload(file=tmp.name)
                    uploaded_gemini_files.append(gemini_file)

                chat_prompt = f"""
                You are an expert aeronautical quality auditor for engine parts (Non-LLP).
                
                Context of the current Technical Records Review (TRR):
                - Part Number: {part_number}
                - Vendor / Seller: {vendor}
                - Audit Report Data / JSON:
                {report_data}
                
                User Instruction / Question:
                {user_query}
                
                Instructions for response:
                - If the user asks for an email to the seller/vendor requesting missing paperwork, write a professional, clear, and assertive email referencing the specific missing or discrepant documents identified in the audit report.
                - Answer concisely, directly, and accurately using the context of the uploaded paperwork and audit findings.
                """

                contents = uploaded_gemini_files + [chat_prompt]
                response = client.models.generate_content(
                    model="gemini-3.5-flash",
                    contents=contents
                )
                bot_response = response.text if response and response.text else "No se pudo obtener respuesta del modelo."
            except Exception as e:
                bot_response = f"⚠️ Error procesando la consulta: {str(e)}"
            finally:
                for path in temp_paths:
                    if os.path.exists(path):
                        os.remove(path)

        with st.chat_message("assistant"):
            st.markdown(bot_response)
        st.session_state[chat_key].append({"role": "assistant", "content": bot_response})

# --- CONTROL DE ACCESO ---
ACCESO_PASSWORD = st.secrets["ACCESO_PASSWORD"]

if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:
    @st.dialog("🔒 Acceso Restringido - Kaito Aero")
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

# --- INICIALIZACIÓN DE GEMINI ---
API_KEY = st.secrets["GEMINI_API_KEY"]
client = genai.Client(api_key=API_KEY)

# --- INTERFAZ DE USUARIO ---
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

tab_new, tab_history = st.tabs(["➕ New Analysis", "📂 Saved Analyses / History"])

# PESTAÑA 1: NUEVO ANÁLISIS
with tab_new:
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
            st.info("ℹ️ Please provide Part Number, Project Name, and Vendor before running the audit.")
        elif not uploaded_files:
            st.warning("⚠️ Please upload at least one document to analyze.")
        else:
            system_prompt = load_system_prompt(part_number, project_name, vendor)
            if not system_prompt:
                st.error("❌ Archivo 'prompt.txt' no encontrado en la carpeta TRR.")
            else:
                with st.spinner("Processing documents with Gemini 3.5 Flash..."):
                    files_payload = [
                        {
                            "name": f.name,
                            "content": base64.b64encode(f.getvalue()).decode("utf-8")
                        }
                        for f in uploaded_files
                    ]

                    html_report, metrics_info, error_details = run_gemini_audit(
                        client, uploaded_files, system_prompt
                    )

                    if html_report:
                        save_analysis(part_number, project_name, vendor, files_payload, html_report, metrics_info)
                        st.session_state["current_audit"] = {
                            "report": html_report,
                            "metrics": metrics_info,
                            "part_number": part_number,
                            "vendor": vendor,
                            "files": uploaded_files
                        }
                        st.success("✅ Audit completed and saved to history!")
                    else:
                        st.error("❌ No se pudo completar el análisis.")
                        if error_details:
                            st.markdown(error_details)

    # Si hay una auditoría activa generada recientemente, se muestra con su chatbot
    if "current_audit" in st.session_state:
        curr = st.session_state["current_audit"]
        st.markdown("---")
        st.markdown("### 📋 Audit Report")
        st.components.v1.html(curr["report"], height=estimate_report_height(curr["report"]), scrolling=True)
        if curr["metrics"]:
            st.caption(f"📊 {curr['metrics']}")
        
        # Invocación del Chatbot
        render_audit_chatbot(
            client=client,
            files_payload_list=curr["files"],
            report_data=curr["report"],
            part_number=curr["part_number"],
            vendor=curr["vendor"]
        )

# PESTAÑA 2: HISTORIAL
with tab_history:
    st.markdown("### Saved Audits")
    history_data = load_history()

    if not history_data:
        st.info("No saved audits found yet. Run a new analysis to populate history.")
    else:
        options = [
            f"[{item['date']}] {item['project_name']} | P/N: {item['part_number']} ({item.get('vendor', 'N/A')})"
            for item in history_data
        ]
        
        selected_option = st.selectbox("Select a previous audit to review:", options)
        selected_index = options.index(selected_option)
        record = history_data[selected_index]

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
            if st.button("🗑️ Delete", key=f"del_{record['id']}", use_container_width=True):
                delete_analysis(record["id"])
                st.success("Audit deleted successfully!")
                st.rerun()

        st.caption(f"📄 **Current Uploaded Files:** {', '.join(record.get('filenames', []))}")

        with st.expander("🔄 **Re-run Audit or Add Extra Documents**", expanded=False):
            additional_files = st.file_uploader(
                "Upload additional documents (Optional):",
                type=["pdf", "png", "jpg", "jpeg"],
                accept_multiple_files=True,
                key=f"extra_files_{record['id']}"
            )

            if st.button("🚀 Re-run Analysis Now", type="primary", key=f"rerun_{record['id']}", use_container_width=True):
                system_prompt = load_system_prompt(record["part_number"], record["project_name"], record.get("vendor", "N/A"))
                
                if not system_prompt:
                    st.error("❌ Archivo 'prompt.txt' no encontrado.")
                else:
                    current_payload = list(record.get("files_data", []))

                    if additional_files:
                        for af in additional_files:
                            current_payload.append({
                                "name": af.name,
                                "content": base64.b64encode(af.getvalue()).decode("utf-8")
                            })

                    if not current_payload:
                        st.warning("⚠️ No hay archivos asociados a este registro.")
                    else:
                        with st.spinner("Re-running audit with Gemini 3.5 Flash..."):
                            html_report, metrics_info, error_details = run_gemini_audit(
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
                                    record_id=record["id"]
                                )
                                st.success("✅ Audit updated successfully!")
                                st.rerun()
                            else:
                                st.error("❌ No se pudo completar la reejecución.")
                                if error_details:
                                    st.markdown(error_details)

        st.markdown("#### 📋 Audit Report")
        st.components.v1.html(record["report"], height=estimate_report_height(record["report"]), scrolling=True)
        
        if record.get("metrics"):
            st.caption(f"📊 {record['metrics']}")

        # Invocación del Chatbot para el registro seleccionado del historial
        render_audit_chatbot(
            client=client,
            files_payload_list=record.get("files_data", []),
            report_data=record["report"],
            part_number=record["part_number"],
            vendor=record.get("vendor", "N/A"),
            record_id=record["id"]
        )