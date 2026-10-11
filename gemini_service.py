"""Servicios de Gemini: subida de archivos, auditoria y chat en streaming.

Este modulo no usa Streamlit: la auditoria se ejecuta en un hilo y la cache de archivos
del chat se recibe como parametro.
"""
import os
import time
import tempfile
import traceback

from config import MODEL_NAME
from files_util import decode_file, files_signature
from reports import build_modern_html_report


class AuditCancelled(Exception):
    """Se lanza cuando el usuario cancela una auditoria en curso."""


def upload_to_gemini(client, files_payload_list, cancel_event=None):
    """Sube los archivos a Gemini y devuelve las referencias. Limpia los temporales siempre."""
    uploaded = []
    for fitem in files_payload_list:
        if cancel_event is not None and cancel_event.is_set():
            raise AuditCancelled()
        decoded = decode_file(fitem)
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


def get_chat_files(client, files_payload_list, chat_id, cache, force=False):
    """Sube los documentos una sola vez por auditoria y reutiliza las referencias en cada mensaje.

    `cache` es un dict que mantiene el llamador (st.session_state["gemini_file_cache"]).
    """
    signature = files_signature(files_payload_list)
    entry = cache.get(chat_id)
    if entry and entry["sig"] == signature and not force:
        return entry["files"]
    files = upload_to_gemini(client, files_payload_list)
    cache[chat_id] = {"sig": signature, "files": files}
    return files


def chat_stream(client, files_payload_list, chat_id, prompt_text, cache):
    """Generador de texto en streaming. Si la referencia a los archivos caduco, los vuelve a subir una vez."""
    for attempt in (0, 1):
        started = False
        try:
            files = get_chat_files(client, files_payload_list, chat_id, cache, force=(attempt == 1))
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
