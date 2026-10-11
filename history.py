"""Historial de auditorias (almacenamiento en analysis_history.json).

La interfaz solo usa estas cuatro funciones: en la Fase 2 se sustituye este modulo por
una version respaldada en Google Drive sin tocar el resto.
"""
import os
import json
from datetime import datetime

from config import HISTORY_FILE


def load_history():
    if os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []
    return []


def _write_history(history):
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(history, f, ensure_ascii=False, indent=4)


def update_analysis_details(record_id, part_number, project_name, vendor):
    """Actualiza part number, proyecto y vendor de un registro del historial."""
    history = load_history()
    updated = False
    for item in history:
        if item.get("id") == record_id:
            item["part_number"] = part_number.strip()
            item["project_name"] = project_name.strip()
            item["vendor"] = vendor.strip()
            updated = True
            break
    if updated:
        _write_history(history)
    return updated


def save_analysis(part_number, project_name, vendor, files_payload, report_html, metrics_text="", record_id=None):
    history = load_history()

    if record_id:
        for item in history:
            if item.get("id") == record_id:
                item["files_data"] = files_payload
                item["filenames"] = [f.get("name", "doc.pdf") if isinstance(f, dict) else getattr(f, "name", "doc.pdf") for f in files_payload]
                item["report"] = report_html
                item["metrics"] = metrics_text
                item["date"] = datetime.now().strftime("%Y-%m-%d")
                break
    else:
        new_entry = {
            "id": datetime.now().strftime("%Y%m%d_%H%M%S"),
            "date": datetime.now().strftime("%Y-%m-%d"),
            "part_number": part_number,
            "project_name": project_name,
            "vendor": vendor,
            "files_data": files_payload,
            "filenames": [f.get("name", "doc.pdf") if isinstance(f, dict) else getattr(f, "name", "doc.pdf") for f in files_payload],
            "report": report_html,
            "metrics": metrics_text
        }
        history.insert(0, new_entry)

    _write_history(history)


def delete_analysis(record_id):
    history = load_history()
    history = [item for item in history if item.get("id") != record_id]
    _write_history(history)
