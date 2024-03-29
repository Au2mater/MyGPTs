import streamlit as st
from streamlit import runtime
from streamlit.runtime.scriptrunner import get_script_run_ctx


def get_remote_ip() -> str:
    """Get remote ip."""

    try:
        ctx = get_script_run_ctx()
        if ctx is None:
            return None

        session_info = runtime.get_instance().get_client(ctx.session_id)
        if session_info is None:
            return None
    except Exception:
        return None

    return session_info.request.remote_ip


def get(key, default=None):
    """get value from session state, if not present, return default"""
    return st.session_state.get(key, default)


def init(key, default=None):
    """initialize session state variable if not present"""
    if get(key) is None:
        st.session_state[key] = default


def set_to(key, value):
    """set value in session state"""
    st.session_state[key] = value


def append(key, value):
    """append value to session state list"""
    st.session_state[key].append(value)


def nav_to(url):
    """navigate to url"""
    nav_script = """
        <meta http-equiv="refresh" content="0; url='%s'">
    """ % (url)
    st.write(nav_script, unsafe_allow_html=True)
