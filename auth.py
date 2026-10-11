"""Control de acceso por contraseña."""
import streamlit as st


def require_login():
    """Muestra el dialogo de contraseña y detiene la ejecucion hasta autenticarse."""
    acceso_password = st.secrets["ACCESO_PASSWORD"]

    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False

    if not st.session_state.authenticated:
        @st.dialog("TRR AI Tool - Access Restricted")
        def login_dialog():
            st.write("Please introduce the password.")
            with st.form("login_form", clear_on_submit=False):
                user_pass = st.text_input("Password", type="password", key="pass_input")
                submit = st.form_submit_button("Login", use_container_width=True, type="primary")
                if submit:
                    if user_pass == acceso_password:
                        st.session_state.authenticated = True
                        st.rerun()
                    else:
                        st.error("Contraseña incorrecta. Inténtalo de nuevo.")

        login_dialog()
        st.stop()
