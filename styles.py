"""Estilos CSS de la app (paleta navy/verde). Se inyectan una vez desde app.py."""
import streamlit as st

STYLES_HTML = """
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

        
        /* ---------- Cabecera del registro (historial) ---------- */
        .st-key-record_header {
            background-color: var(--card);
            border: 1px solid var(--border);
            border-left: 4px solid var(--green);
            border-radius: var(--radius);
            padding: 22px 24px 24px 24px;
            box-shadow: 0 2px 8px rgba(15, 23, 42, 0.04);
        }
        .rec-label {
            display: block;
            color: var(--muted);
            font-size: 0.7rem;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }
        .rec-title {
            color: var(--navy);
            font-size: 1.6rem;
            font-weight: 700;
            letter-spacing: -0.01em;
            line-height: 1.2;
            margin-bottom: 12px;
            word-break: break-word;
        }
        .rec-fields { display: flex; flex-wrap: wrap; gap: 8px 40px; }
        .rec-value { display: block; color: var(--text); font-size: 0.98rem; font-weight: 600; }
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

        /* Panel del chat y caja de entrada (en linea, dentro del panel) */
        .st-key-chat_panel {
            background-color: var(--card);
            border: 1px solid var(--border);
            border-radius: var(--radius);
            padding: 14px 18px 18px 18px;
            box-shadow: 0 2px 8px rgba(15, 23, 42, 0.04);
        }
        [data-testid="stChatInput"] {
            border-radius: 26px !important;
            border: 1px solid var(--border) !important;
            background: var(--card) !important;
            box-shadow: none;
        }
        [data-testid="stChatInput"]:focus-within {
            border-color: var(--green) !important;
            box-shadow: 0 0 0 3px rgba(46, 204, 143, 0.18);
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

        /* ---------- Tabla del informe (HTML nativo, sin iframe) ---------- */
        .modern-table-container {
            border-radius: 12px;
            box-shadow: 0 4px 16px rgba(20, 48, 90, 0.08);
            border: 1px solid #e3e8ef;
            margin: 2px 0 10px 0;
            overflow: hidden;
            background-color: #ffffff;
        }
        .modern-table-container table.modern-table {
            display: table !important;
            width: 100% !important;
            border-collapse: collapse !important;
            border: none !important;
            margin: 0 !important;
            text-align: left;
            font-size: 14px;
            color: #374151;
        }
        .modern-table-container .modern-table thead { background-color: #14305a !important; }
        .modern-table-container .modern-table th {
            background-color: #14305a !important;
            color: #ffffff !important;
            padding: 12px 16px !important;
            font-weight: 600 !important;
            text-transform: uppercase;
            font-size: 11px !important;
            letter-spacing: 0.05em;
            text-align: left !important;
            border: none !important;
        }
        .modern-table-container .modern-table td {
            padding: 14px 16px !important;
            border: none !important;
            border-bottom: 1px solid #f3f4f6 !important;
            vertical-align: top !important;
            line-height: 1.5;
            font-size: 14px !important;
            background-color: transparent !important;
            color: #374151;
        }
        .modern-table-container .modern-table tbody tr:last-child td { border-bottom: none !important; }
        .modern-table-container .modern-table tbody tr:hover td { background-color: #f5f9ff !important; }
        .modern-table-container .modern-table td.doc-title { font-weight: 700 !important; color: #14305a !important; }
        .modern-table-container .badge {
            display: inline-flex;
            align-items: center;
            padding: 4px 10px;
            border-radius: 9999px;
            font-size: 12px;
            font-weight: 600;
            white-space: nowrap;
            gap: 6px;
        }
        .modern-table-container .badge::before {
            content: "";
            width: 7px;
            height: 7px;
            border-radius: 50%;
            background-color: currentColor;
        }
        .modern-table-container .badge-yes { background-color: #dcfce7; color: #166534; }
        .modern-table-container .badge-discrepancy,
        .modern-table-container .badge-incomplete { background-color: #fef3c7; color: #92400e; }
        .modern-table-container .badge-no { background-color: #fee2e2; color: #991b1b; }

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
"""


def inject_styles():
    st.markdown(STYLES_HTML, unsafe_allow_html=True)
