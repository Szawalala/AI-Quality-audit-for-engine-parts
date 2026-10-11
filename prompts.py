"""Prompts: plantilla del email, prompt de auditoria (prompt.txt) y prompt del chat."""
import os

from config import PROMPT_FILE

EMAIL_PROMPT_TEMPLATE = """You are an expert technical aviation records auditor drafting an email to a vendor requesting missing or corrected documentation based on an audit result. Write the email in English.
Your goal: Extract ONLY actionable findings (discrepancies, missing documents, commercial trace gaps, or missing tags) and present them in a clear, bulleted request for the vendor.

STRICT RULES:
1. NO conversational filler, intros, or outros (do NOT write greetings like "Dear Vendor", "Hope this finds you well", or "Best regards").
2. DO NOT mention or summarize items that were compliant, verified, or marked "Yes". Focus strictly on findings marked as "Discrepancy", "Incomplete", or "No" (document not provided). 
3. Group findings dynamically by the identifier used in the audit (e.g., ESN / Quantity, Part Number, Document type, or Batch) if applicable. If no specific grouping exists, list them directly.
4. Keep bullet points direct, concise, and professional, specifying exactly what document is needed, what discrepancy needs clarification, or what commercial trace link is missing.

AUDIT RESULT TO PROCESS:
{audit_result_text}
"""


def load_system_prompt(part_number, project_name, vendor):
    if not os.path.exists(PROMPT_FILE):
        return None
    with open(PROMPT_FILE, "r", encoding="utf-8") as f:
        template = f.read()
    return template.format(part_number=part_number, project_name=project_name, vendor=vendor)


def build_chat_prompt(part_number, vendor, report_text, history, user_query):
    convo = "\n".join(
        f"{'User' if m['role'] == 'user' else 'Assistant'}: {m['content']}"
        for m in history[-12:]
    )
    return f"""You are an expert aeronautical quality auditor for engine parts (Non-LLP).

Context of the current Technical Records Review (TRR):
- Part Number: {part_number}
- Vendor / Seller: {vendor}
- Audit findings per document:
{report_text}

Conversation so far:
{convo if convo else "(this is the first message)"}

Latest user message:
{user_query}

Instructions:
- Use the uploaded paperwork and the audit findings above. Take the whole conversation into account, including any correction or change the user asked for earlier.
- Reply in the same language as the user's message, unless the user asks for a deliverable (for example an email) in another language.
- If the user asks for an email to the seller/vendor requesting paperwork: be professional, clear and assertive; only request what is missing or must be corrected, citing the specific documents, values and discrepancies from the audit; do not recap what has been verified as correct unless asked; no unnecessary prose.
- Otherwise answer concisely, directly and accurately.
"""
