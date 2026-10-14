"""Constantes de configuracion de la app."""

MODEL_NAME = "gemini-3.6-flash"
CHAT_MODEL_NAME = "gemini-3.1-flash-lite" 
MAX_AUDIT_SECONDS = 600          # tiempo maximo de espera de una auditoria
CHAT_HEIGHT = 480                # alto de la zona de mensajes del chat (px)
EMAIL_SUGGESTION = "Write an email to the seller requesting the missing paperwork"
CHAT_SUGGESTIONS = [EMAIL_SUGGESTION]

PROMPT_FILE = "prompt.txt"
HISTORY_FILE = "analysis_history.json"
