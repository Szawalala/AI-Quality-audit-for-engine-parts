"""Pagina unica: lista de auditorias guardadas y acceso al formulario de nuevo analisis."""
import base64
from html import escape

import streamlit as st

from files_util import file_name
from history import load_history, save_analysis, update_analysis_details
from page_new import render_new_audit_form
from prompts import load_system_prompt
from ui_chat import render_audit_chat
from ui_common import (
    audit_busy,
    audit_start_requested,
    clear_audit_notice,
    confirm_delete_dialog,
    queue_audit,
    render_report,
    run_audit_guarded,
    show_audit_notice,
    stop_with_notice,
)


def _open_new_form():
    st.session_state["show_new_form"] = True
    clear_audit_notice()


def render_audits_page(client):
    # Solo se dibuja una vista a la vez: el formulario o la lista (asi no hay dos chats a la vez)
    if st.session_state.get("show_new_form"):
        render_new_audit_form(client)
        return

    # Mientras hay un analisis en curso, los controles de esta vista se dibujan deshabilitados
    run_now = audit_start_requested()
    busy = audit_busy()

    col_title, col_new = st.columns([5, 1], vertical_alignment="center")
    col_title.markdown("### Saved Audits")
    col_new.button("New Analysis", key="open_new_form", type="primary",
                   on_click=_open_new_form, disabled=busy, use_container_width=True)

    history_data = load_history()

    if not history_data:
        st.info("No saved audits found yet. Press New Analysis to run the first one.")
        return

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
        key="history_select",
        disabled=busy
    )
    record = next(item for item in history_data if item["id"] == selected_id)
    rid = record["id"]

    st.markdown("---")

    with st.container(key="record_header"):
        col_info, col_del = st.columns([6, 1], vertical_alignment="center")
        with col_info:
            st.markdown(
                '<div class="rec-label">Part Number</div>'
                f'<div class="rec-title">{escape(record["part_number"])}</div>'
                '<div class="rec-fields">'
                f'<div><span class="rec-label">Project</span><span class="rec-value">{escape(record["project_name"])}</span></div>'
                f'<div><span class="rec-label">Vendor</span><span class="rec-value">{escape(record.get("vendor", "N/A"))}</span></div>'
                f'<div><span class="rec-label">Date</span><span class="rec-value">{escape(record["date"])}</span></div>'
                '</div>',
                unsafe_allow_html=True
            )
        with col_del:
            if st.button("Delete", key="delete_audit", disabled=busy, use_container_width=True):
                confirm_delete_dialog(rid, f"{record['project_name']} | P/N {record['part_number']}")

    # ---------- Editar datos ----------
    with st.expander("Edit details", expanded=False):
        e1, e2, e3 = st.columns(3)
        new_pn = e1.text_input("Part Number (P/N)", value=record["part_number"], key=f"edit_pn_{rid}", disabled=busy)
        new_project = e2.text_input("Project Name", value=record["project_name"], key=f"edit_project_{rid}", disabled=busy)
        new_vendor = e3.text_input("Vendor / Seller", value=record.get("vendor", ""), key=f"edit_vendor_{rid}", disabled=busy)
        st.caption("Changes apply to the saved record. Re-run the analysis to refresh the report with the new data.")
        if st.button("Save changes", type="primary", key=f"save_details_{rid}", disabled=busy):
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
                if st.checkbox(file_name(fitem), value=True, key=f"keep_{rid}_{gen}_{idx}", disabled=busy):
                    kept_files.append(fitem)
            st.caption("Uncheck a document to remove it from the audit when you re-run.")
        else:
            st.caption("No documents associated with this record.")

        additional_files = st.file_uploader(
            "Add more documents (optional):",
            type=["pdf", "png", "jpg", "jpeg"],
            accept_multiple_files=True,
            key=f"extra_files_{rid}_{gen}",
            disabled=busy
        )
        st.caption("This replaces the saved report with a new analysis of the documents selected above.")
        st.button("Re-run Analysis", type="primary", key=f"rerun_{rid}", on_click=queue_audit,
                  disabled=busy, use_container_width=True)
        show_audit_notice(rid)

        if run_now:
            # --- Esta pasada ejecuta el analisis en cola ---
            system_prompt = load_system_prompt(
                record["part_number"], record["project_name"], record.get("vendor", "N/A")
            )
            if not system_prompt:
                stop_with_notice(rid, "error", "Archivo 'prompt.txt' no encontrado.")

            current_payload = list(kept_files)
            for af in additional_files or []:
                current_payload.append({
                    "name": af.name,
                    "content": base64.b64encode(af.getvalue()).decode("utf-8")
                })
            if not current_payload:
                stop_with_notice(rid, "warning",
                                 "There are no documents left to analyze. Keep at least one or upload a new one.")

            html_report, metrics_info, error_details = run_audit_guarded(client, current_payload, system_prompt)

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
                stop_with_notice(rid, "error", "No se pudo completar la reejecución.", error_details)

    render_report(record["report"], record.get("metrics"))

    render_audit_chat(
        client=client,
        files_payload_list=record.get("files_data", []),
        report_html=record["report"],
        part_number=record["part_number"],
        vendor=record.get("vendor", "N/A"),
        chat_id=rid
    )
