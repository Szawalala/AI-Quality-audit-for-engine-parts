"""Helpers para los archivos adjuntos (dict base64, UploadedFile o texto)."""
import base64
import hashlib


def decode_file(fitem):
    """Devuelve (nombre, bytes) para cualquier formato de archivo que maneja la app."""
    if isinstance(fitem, dict):
        return fitem.get("name", "document.pdf"), base64.b64decode(fitem["content"])
    if hasattr(fitem, "name") and hasattr(fitem, "getvalue"):
        return fitem.name, fitem.getvalue()
    if isinstance(fitem, str):
        return "document.pdf", fitem.encode("utf-8")
    return None


def file_name(fitem):
    if isinstance(fitem, dict):
        return fitem.get("name", "document.pdf")
    return getattr(fitem, "name", "document.pdf")


def files_signature(files_payload_list):
    """Firma estable de un conjunto de archivos (para saber si hay que volver a subirlos)."""
    parts = []
    for f in files_payload_list:
        content = f.get("content", "") if isinstance(f, dict) else ""
        parts.append(f"{file_name(f)}:{len(content)}")
    return hashlib.md5("|".join(parts).encode("utf-8")).hexdigest()
