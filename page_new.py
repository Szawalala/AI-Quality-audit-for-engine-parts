"""Formulario de nuevo analisis. Se abre desde la pagina de auditorias (page_history.py)."""
import base64

import streamlit as st

from history import save_analysis
from prompts import load_system_prompt
from ui_common import (
    audit_busy,
    audit_start_requested,
    clear_audit_notice,
    queue_audit,
    run_audit_guarded,
    show_audit_notice,
    stop_with_notice,
)


def _close_new_form():
    st.session_state["show_new_form"] = False
    clear_audit_notice()


def render_new_audit_form(client):
    # Mientras hay un analisis en curso, todo el formulario se dibuja deshabilitado
    run_now = audit_start_requested()
    busy = audit_busy()

    col_title, col_back = st.columns([5, 1], vertical_alignment="center")
    col_title.markdown("### Launch New Audit")
    col_back.button("Back", key="back_to_audits", on_click=_close_new_form,
                    disabled=busy, use_container_width=True)

    col1, col2, col3 = st.columns(3)
    with col1:
        part_number = st.text_input("Part Number (P/N)", placeholder="e.g. 305-001-201-0", disabled=busy)
    with col2:
        project_name = st.text_input("Project Name", placeholder="e.g. CFM56-7B Engine Overhaul", disabled=busy)
    with col3:
        vendor = st.text_input("Vendor / Seller", placeholder="e.g. Lufthansa Technik AG", disabled=busy)

    uploaded_files = st.file_uploader(
        "Upload paperwork",
        type=["pdf", "png", "jpg", "jpeg"],
        accept_multiple_files=True,
        key="upload_new",
        disabled=busy
    )

    st.button("Run Analysis", key="run_new", type="primary", on_click=queue_audit,
              disabled=busy, use_container_width=True)
    show_audit_notice("new")

    if not run_now:
        return

    # --- Esta pasada ejecuta el analisis en cola ---
    if not part_number or not project_name or not vendor:
        stop_with_notice("new", "info", "Please provide Part Number, Project Name, and Vendor before running the audit.")
    if not uploaded_files:
        stop_with_notice("new", "warning", "Please upload at least one document to analyze.")

    system_prompt = load_system_prompt(part_number, project_name, vendor)
    if not system_prompt:
        stop_with_notice("new", "error", "Archivo 'prompt.txt' no encontrado en la carpeta TRR.")

    files_payload = [
        {"name": f.name, "content": base64.b64encode(f.getvalue()).decode("utf-8")}
        for f in uploaded_files
    ]

    html_report, metrics_info, error_details = run_audit_guarded(client, files_payload, system_prompt)

    if html_report:
        new_id = save_analysis(part_number, project_name, vendor, files_payload, html_report, metrics_info)
        # Se vuelve a la lista con el analisis nuevo seleccionado. Al no dibujarse el formulario,
        # sus campos y archivos se descartan y la proxima vez se abre limpio.
        st.session_state["history_select"] = new_id
        st.session_state["show_new_form"] = False
        st.session_state["_flash"] = "Audit completed and saved to history."
        st.rerun()
    else:
        stop_with_notice("new", "error", "No se pudo completar el análisis.", error_details)
