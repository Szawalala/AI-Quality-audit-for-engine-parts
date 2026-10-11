"""Chat del asistente dentro de cada auditoria."""
import streamlit as st

from config import CHAT_HEIGHT, CHAT_SUGGESTIONS, EMAIL_SUGGESTION
from gemini_service import chat_stream
from prompts import EMAIL_PROMPT_TEMPLATE, build_chat_prompt
from reports import report_to_text


def _queue_prompt(pending_key, text):
    st.session_state[pending_key] = text


def _clear_chat(chat_key):
    st.session_state[chat_key] = []


def render_audit_chat(client, files_payload_list, report_html, part_number, vendor, chat_id):
    """
    Chat estilo ChatGPT / Gemini dentro de un panel: zona de mensajes con scroll y, justo debajo,
    la caja de entrada.

    La caja (st.chat_input) se coloca DENTRO de un contenedor a proposito: asi se muestra en linea,
    debajo de los mensajes. Si se llamara en el nivel raiz de la pagina, Streamlit la fijaria al
    borde inferior de la pantalla y llevaria la vista al final de la pagina al cargarla.

    La unica sugerencia (EMAIL_SUGGESTION) usa su propio prompt (EMAIL_PROMPT_TEMPLATE); el resto
    de mensajes pasan por build_chat_prompt.
    """
    chat_key = f"chat_{chat_id}"
    pending_key = f"{chat_key}_pending"
    messages = st.session_state.setdefault(chat_key, [])

    st.markdown("---")
    col_title, col_new = st.columns([6, 1], vertical_alignment="center")
    col_title.markdown("### Assistant")
    if messages:
        col_new.button("New chat", key=f"new_chat_{chat_id}", on_click=_clear_chat,
                       args=(chat_key,), use_container_width=True)

    with st.container(key="chat_panel"):
        box = st.container(height=CHAT_HEIGHT, border=False)
        typed = st.chat_input("Ask anything about this audit...", key=f"chat_input_{chat_id}")

    prompt = typed or st.session_state.pop(pending_key, None)

    with box:
        if not messages and not prompt:
            st.markdown("<div class='chat-empty'>How can I help with this audit?</div>", unsafe_allow_html=True)
            for i, suggestion in enumerate(CHAT_SUGGESTIONS):
                st.button(suggestion, key=f"suggestion_{chat_id}_{i}", on_click=_queue_prompt,
                          args=(pending_key, suggestion), use_container_width=True)

        for message in messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

        if prompt:
            history_before = list(messages)
            messages.append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.markdown(prompt)

            with st.chat_message("assistant"):
                answer = ""
                try:
                    if prompt == EMAIL_SUGGESTION:
                        prompt_text = EMAIL_PROMPT_TEMPLATE.format(
                            audit_result_text=report_to_text(report_html)
                        )
                    else:
                        prompt_text = build_chat_prompt(
                            part_number, vendor, report_to_text(report_html), history_before, prompt
                        )
                    file_cache = st.session_state.setdefault("gemini_file_cache", {})
                    stream = chat_stream(client, files_payload_list, chat_id, prompt_text, file_cache)
                    with st.spinner("Thinking..."):
                        first = next(stream, None)

                    def full_stream():
                        if first:
                            yield first
                        yield from stream

                    answer = st.write_stream(full_stream())
                    if not answer:
                        answer = "No se pudo obtener respuesta del modelo."
                        st.markdown(answer)
                except Exception as e:
                    answer = f"Error procesando la consulta: {e}"
                    st.markdown(answer)

            messages.append({"role": "assistant", "content": answer})
