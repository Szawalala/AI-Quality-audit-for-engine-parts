"""Componentes de interfaz compartidos: informe, errores, borrado y auditoria cancelable."""
import time
import threading

import streamlit as st

from config import MAX_AUDIT_SECONDS
from gemini_service import run_gemini_audit
from history import delete_analysis
from reports import report_for_markdown


def render_report(report_html, metrics):
    st.markdown("### Audit Report")
    st.markdown(report_for_markdown(report_html), unsafe_allow_html=True)
    if metrics and st.secrets.get("SHOW_DEBUG", False):
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
