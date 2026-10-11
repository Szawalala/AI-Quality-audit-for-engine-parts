"""Construccion y transformacion del informe HTML de la auditoria."""
import json
import re
import html as html_lib


def build_modern_html_report(json_data_input):
    """
    Procesa la respuesta de Gemini (lista o diccionario) y construye la tabla HTML del informe.
    Devuelve solo la estructura (sin <style> ni <script>): el aspecto de la tabla vive en el CSS
    de la app (clases .modern-table-container, .modern-table, .badge...) y se dibuja directamente
    en la pagina con st.markdown.
    """
    data = []

    if isinstance(json_data_input, str):
        cleaned = json_data_input.strip()

        # 1. Limpieza de bloques Markdown (```json ... ```)
        if cleaned.startswith("```json"):
            cleaned = cleaned[7:]
        elif cleaned.startswith("```"):
            cleaned = cleaned[3:]
        if cleaned.endswith("```"):
            cleaned = cleaned[:-3]
        cleaned = cleaned.strip()

        try:
            parsed = json.loads(cleaned)
            data = parsed
        except Exception:
            # Fallback si Gemini coló código HTML dentro del string
            data = json_data_input
    else:
        data = json_data_input

    # 2. Si Gemini devolvió un objeto/diccionario en vez de un array directo
    if isinstance(data, dict):
        # Si Gemini metió la tabla HTML dentro de {"html": "<table>...</table>"}
        if "html" in data and isinstance(data["html"], str):
            html_content = data["html"]
            # Extraer las filas si es una tabla HTML
            if "<table" in html_content or "<tr" in html_content:
                return html_content

        # Si devolvió {"categories": [...]} o {"results": [...]}
        for key in ["categories", "audit", "results", "documents", "data"]:
            if key in data and isinstance(data[key], list):
                data = data[key]
                break

    # 3. Si sigue sin ser una lista, intentar parsear elementos individuales
    if not isinstance(data, list):
        return f"""
        <div style="padding: 15px; background-color: #fee2e2; border: 1px solid #f87171; border-radius: 8px; color: #991b1b; font-family: sans-serif;">
            <strong>Error en el formato del análisis:</strong> No se pudo estructurar el informe correctamente.
        </div>
        """

    # 4. Mapeo de Badges y generación de filas
    status_class_map = {
        "Yes": "badge-yes",
        "Incomplete": "badge-incomplete",
        "Discrepancy": "badge-discrepancy",
        "No": "badge-no"
    }

    rows_html = ""
    for item in data:
        if not isinstance(item, dict):
            continue

        cat = item.get("category", item.get("document", item.get("doc", "N/A")))
        status = str(item.get("status", "No")).strip()
        comments = str(item.get("comments", item.get("finding", ""))).strip()

        badge_class = status_class_map.get(status, "badge-no")

        # Se escapa el texto: el informe se inserta directamente en la pagina
        rows_html += (
            "<tr>"
            f'<td class="doc-title">{html_lib.escape(str(cat))}</td>'
            f'<td><span class="badge {badge_class}">{html_lib.escape(status)}</span></td>'
            f"<td>{html_lib.escape(comments)}</td>"
            "</tr>"
        )

    return (
        '<div class="modern-table-container">'
        '<table class="modern-table">'
        "<thead><tr>"
        '<th style="width: 18%;">Documents</th>'
        '<th style="width: 14%;">Available</th>'
        '<th style="width: 68%;">Comments</th>'
        "</tr></thead>"
        f"<tbody>{rows_html}</tbody>"
        "</table></div>"
    )


def report_for_markdown(report_html):
    """
    Prepara el HTML guardado de un informe para mostrarlo directamente con st.markdown.

    Los informes guardados antes de este cambio llevan su propio <style> (con reglas globales como
    "html, body") y un <script> de autoajuste de altura: ambos se eliminan, porque el estilo de la
    tabla ahora vive en el CSS de la app. Ademas se compacta el HTML para que Markdown no lo trate
    como bloque de codigo (por la indentacion) ni lo corte en las lineas en blanco.
    """
    if not isinstance(report_html, str):
        return ""
    s = re.sub(r"<style.*?</style>", "", report_html, flags=re.S | re.I)
    s = re.sub(r"<script.*?</script>", "", s, flags=re.S | re.I)
    s = re.sub(r">\s+<", "><", s)
    return re.sub(r"\s+", " ", s).strip()


def report_to_text(report_html):
    """
    Convierte el HTML del informe en texto plano compacto (una linea por documento)
    para pasarlo como contexto al chat sin enviar CSS ni etiquetas.
    """
    if not isinstance(report_html, str):
        return str(report_html)

    def clean(s):
        return re.sub(r"\s+", " ", html_lib.unescape(re.sub(r"<[^>]+>", " ", s))).strip()

    rows = re.findall(
        r'<tr>\s*<td class="doc-title">(.*?)</td>\s*<td><span class="badge[^"]*">(.*?)</span></td>\s*<td>(.*?)</td>\s*</tr>',
        report_html, flags=re.S)
    if rows:
        return "\n".join(f"- {clean(c)}: {clean(s)}. {clean(m)}" for c, s, m in rows)

    text = re.sub(r"<style.*?</style>|<script.*?</script>", " ", report_html, flags=re.S)
    return clean(text)
