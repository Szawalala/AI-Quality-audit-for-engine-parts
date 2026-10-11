"""Componentes de interfaz compartidos: informe, errores, borrado y auditoria cancelable.

Estado del analisis en curso (st.session_state["audit_state"]):
    "idle" -> "queued" (al pulsar Run/Re-run) -> "running" (la pasada que lo ejecuta) -> "idle"
Mientras no sea "idle" los controles se dibujan deshabilitados, asi no se puede lanzar otro analisis encima.
"""
import time
import threading

import streamlit as st

from config import MAX_AUDIT_SECONDS
from gemini_service import run_gemini_audit
from history import delete_analysis
from reports import report_for_markdown

AUDIT_STATE = "audit_state"
AUDIT_NOTICE = "audit_notice"


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


# =====================================================================
#  ESTADO DEL ANALISIS (bloqueo mientras hay uno en curso)
# =====================================================================
def queue_audit():
    """on_click de Run/Re-run: deja el analisis en cola; lo ejecuta la siguiente pasada del script."""
    st.session_state[AUDIT_STATE] = "queued"
    st.session_state.pop(AUDIT_NOTICE, None)


def audit_start_requested():
    """
    Llamar al principio de cada vista que lanza analisis. Devuelve True si ESTA pasada debe ejecutar el
    analisis en cola. Si encuentra el estado "running", la pasada anterior se interrumpio sin limpiar:
    se cancela su hilo y se vuelve a "idle" (nunca se relanza un analisis por su cuenta).
    """
    state = st.session_state.get(AUDIT_STATE, "idle")
    if state == "queued":
        st.session_state[AUDIT_STATE] = "running"
        return True
    if state == "running":
        _cancel_previous_audit()
        st.session_state[AUDIT_STATE] = "idle"
        st.toast("The previous analysis was interrupted.")
    return False


def audit_busy():
    return st.session_state.get(AUDIT_STATE, "idle") in ("queued", "running")


def stop_with_notice(scope, kind, message, details=None):
    """Termina la pasada sin analizar: guarda un aviso, vuelve a "idle" y recarga para reactivar los controles."""
    st.session_state[AUDIT_STATE] = "idle"
    st.session_state[AUDIT_NOTICE] = {"scope": scope, "kind": kind, "message": message, "details": details}
    st.rerun()


def clear_audit_notice():
    st.session_state.pop(AUDIT_NOTICE, None)


def show_audit_notice(scope):
    """Muestra el ultimo aviso si pertenece a esta vista (scope: "new" o el id del registro)."""
    notice = st.session_state.get(AUDIT_NOTICE)
    if not notice or notice.get("scope") != scope:
        return
    if notice["kind"] == "error":
        show_audit_error(notice["message"], notice.get("details"))
    elif notice["kind"] == "warning":
        st.warning(notice["message"])
    else:
        st.info(notice["message"])


# =====================================================================
#  EJECUCION CANCELABLE
# =====================================================================
def _cancel_previous_audit():
    """Cancela el hilo del analisis anterior (si sigue vivo) para que no siga gastando llamadas a Gemini."""
    event = st.session_state.get("audit_cancel_event")
    if event is not None:
        event.set()


def _request_cancel():
    """Callback del boton Cancel: avisa al hilo y deja un aviso para la siguiente recarga."""
    _cancel_previous_audit()
    st.session_state[AUDIT_STATE] = "idle"
    st.session_state["_flash"] = "Analysis cancelled."


def run_audit_cancellable(client, files_payload_list, system_prompt):
    """
    Lanza la auditoria en un hilo y muestra un boton Cancel mientras espera.
    Al pulsar Cancel, Streamlit interrumpe este script en la siguiente actualizacion
    de pantalla (cada 0,5 s) y el resultado del hilo se descarta.
    """
    _cancel_previous_audit()  # red de seguridad: nunca quedan dos analisis vivos a la vez
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


def run_audit_guarded(client, files_payload_list, system_prompt):
    """
    run_audit_cancellable + garantia de volver a "idle" pase lo que pase. Si Streamlit interrumpe la pasada
    (por ejemplo, al pulsar otro control mientras se analiza) se deja un aviso para la siguiente recarga.
    """
    completed = False
    try:
        out = run_audit_cancellable(client, files_payload_list, system_prompt)
        completed = True
        return out
    finally:
        try:
            st.session_state[AUDIT_STATE] = "idle"
            if not completed:
                st.session_state["_flash"] = "Analysis interrupted."
        except Exception:
            pass
