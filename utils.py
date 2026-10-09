import os
import json
import re
from datetime import datetime

PROMPT_FILE = "prompt.txt"
HISTORY_FILE = "analysis_history.json"

def build_modern_html_report(json_data_input):
    """
    Procesa la respuesta de Gemini (lista o diccionario) y construye la tabla HTML moderna.
    Incluye script JS con ResizeObserver para auto-ajustar la altura en Streamlit sin huecos ni cortes.
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
                # Retornar el wrapper dinámico con el contenido extraído
                return f"""
                <div id="table-wrapper">
                    <style>
                        html, body {{ margin: 0; padding: 0; font-family: -apple-system, sans-serif; }}
                    </style>
                    {html_content}
                </div>
                <script>
                    function sendH() {{
                        const el = document.getElementById('table-wrapper');
                        if (el) window.parent.postMessage({{ type: 'streamlit:setFrameHeight', height: el.offsetHeight + 20 }}, '*');
                    }}
                    window.addEventListener('load', sendH);
                    setTimeout(sendH, 100);
                </script>
                """

        # Si devolvió {"categories": [...]} o {"results": [...]}
        for key in ["categories", "audit", "results", "documents", "data"]:
            if key in data and isinstance(data[key], list):
                data = data[key]
                break

    # 3. Si sigue sin ser una lista, intentar parsear elementos individuales
    if not isinstance(data, list):
        return f"""
        <div style="padding: 15px; background-color: #fee2e2; border: 1px solid #f87171; border-radius: 8px; color: #991b1b; font-family: sans-serif;">
            ⚠️ <strong>Error en el formato del análisis:</strong> No se pudo estructurar el informe correctamente.
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
        
        rows_html += f"""
      <tr>
        <td class="doc-title">{cat}</td>
        <td><span class="badge {badge_class}">{status}</span></td>
        <td>{comments}</td>
      </tr>"""

    return f"""
<div id="table-wrapper">
  <style>
    html, body {{
      margin: 0;
      padding: 0;
      background-color: transparent;
      font-family: "Inter", -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
    }}

    .modern-table-container {{
      border-radius: 12px;
      box-shadow: 0 4px 16px rgba(20, 48, 90, 0.08);
      border: 1px solid #e3e8ef;
      margin: 2px 0 10px 0;
      overflow: hidden;
      background-color: #ffffff;
    }}

    .modern-table {{
      width: 100%;
      border-collapse: collapse;
      text-align: left;
      font-size: 14px;
      color: #374151;
    }}

    .modern-table thead {{
      background-color: #14305a;
    }}

    .modern-table th {{
      padding: 12px 16px;
      font-weight: 600;
      color: #ffffff;
      text-transform: uppercase;
      font-size: 11px;
      letter-spacing: 0.05em;
    }}

    .modern-table td {{
      padding: 14px 16px;
      border-bottom: 1px solid #f3f4f6;
      vertical-align: top;
      line-height: 1.5;
    }}

    .modern-table tbody tr:last-child td {{
      border-bottom: none;
    }}

    .modern-table tbody tr:hover {{
      background-color: #f5f9ff;
    }}

    .badge {{
      display: inline-flex;
      align-items: center;
      padding: 4px 10px;
      border-radius: 9999px;
      font-size: 12px;
      font-weight: 600;
      white-space: nowrap;
      gap: 6px;
    }}
    .badge::before {{
      content: "";
      width: 7px;
      height: 7px;
      border-radius: 50%;
      background-color: currentColor;
    }}

    .badge-yes {{ background-color: #dcfce7; color: #166534; }}
    .badge-discrepancy, .badge-incomplete {{ background-color: #fef3c7; color: #92400e; }}
    .badge-no {{ background-color: #fee2e2; color: #991b1b; }}
    .doc-title {{ font-weight: 700; color: #14305a; }}
  </style>

  <div class="modern-table-container">
    <table class="modern-table">
      <thead>
        <tr>
          <th style="width: 18%;">Documents</th>
          <th style="width: 14%;">Available</th>
          <th style="width: 68%;">Comments</th>
        </tr>
      </thead>
      <tbody>
        {rows_html}
      </tbody>
    </table>
  </div>
</div>

<script>
  function updateHeight() {{
    const wrapper = document.getElementById('table-wrapper');
    if (wrapper) {{
      const height = wrapper.offsetHeight + 15;
      window.parent.postMessage({{
        type: 'streamlit:setFrameHeight',
        height: height
      }}, '*');
    }}
  }}
  window.addEventListener('load', updateHeight);
  window.addEventListener('resize', updateHeight);
  setTimeout(updateHeight, 50);
  setTimeout(updateHeight, 200);
</script>
"""

def estimate_report_height(report_html, chars_per_line=100, line_px=21, row_padding=30,
                           header_px=48, extra_px=40, min_px=200):
    """
    Estima la altura (px) necesaria para mostrar la tabla del informe dentro de
    st.components.v1.html, que no se autoajusta. Se calcula a partir del texto de
    cada fila de comentarios; es conservador (mejor que sobre a que se corte).
    """
    if not isinstance(report_html, str):
        return 400
    rows = re.findall(
        r'<tr>\s*<td class="doc-title">.*?</td>\s*<td>.*?</td>\s*<td>(.*?)</td>\s*</tr>',
        report_html, flags=re.S)
    if not rows:
        return 450
    total = header_px + extra_px
    for comment in rows:
        text = re.sub(r"<[^>]+>", "", comment)
        lines = max(1, -(-len(text) // chars_per_line))  # ceil
        total += lines * line_px + row_padding
    return max(min_px, total)


def load_system_prompt(part_number, project_name, vendor):
    if not os.path.exists(PROMPT_FILE):
        return None
    with open(PROMPT_FILE, "r", encoding="utf-8") as f:
        template = f.read()
    return template.format(part_number=part_number, project_name=project_name, vendor=vendor)

def load_history():
    if os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []
    return []

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
        
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(history, f, ensure_ascii=False, indent=4)

def delete_analysis(record_id):
    history = load_history()
    history = [item for item in history if item.get("id") != record_id]
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(history, f, ensure_ascii=False, indent=4)