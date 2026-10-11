"""Technical Records Review (TRR): punto de entrada de la app Streamlit."""
import os

import streamlit as st
from google import genai

from auth import require_login
from page_history import render_audits_page
from styles import inject_styles

# --- CONFIGURACION DE PAGINA (debe ser la primera llamada a Streamlit) ---
st.set_page_config(
    page_title="Technical Records Review",
    page_icon="logo.png" if os.path.exists("logo.png") else None,
    layout="wide"
)

inject_styles()

# --- CONTROL DE ACCESO ---
require_login()

# --- INICIALIZACION DE GEMINI ---
API_KEY = st.secrets["GEMINI_API_KEY"]
client = genai.Client(api_key=API_KEY)

# Avisos breves (toast) dejados por acciones anteriores: cancelar, borrar, guardar...
_flash_message = st.session_state.pop("_flash", None)
if _flash_message:
    st.toast(_flash_message)

# --- ENCABEZADO ---
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

# --- PAGINA UNICA: lista de auditorias; el formulario de nuevo analisis se abre desde ella ---
render_audits_page(client)
