"""Pestaña 1: nuevo analisis."""
import base64
import time

import streamlit as st

from history import save_analysis
from prompts import load_system_prompt
from ui_chat import render_audit_chat
from ui_common import render_report, run_audit_cancellable, show_audit_error


def render_new_analysis_page(client):
    st.markdown("### Launch New Audit")

    col1, col2, col3 = st.columns(3)
    with col1:
        part_number = st.text_input("Part Number (P/N)", placeholder="e.g. 305-001-201-0")
    with col2:
        project_name = st.text_input("Project Name", placeholder="e.g. CFM56-7B Engine Overhaul")
    with col3:
        vendor = st.text_input("Vendor / Seller", placeholder="e.g. Lufthansa Technik AG")

    uploaded_files = st.file_uploader(
        "Upload paperwork",
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
