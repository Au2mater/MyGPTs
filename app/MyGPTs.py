import streamlit as st
import os
import sys

if (
    path := os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
) not in sys.path:
    sys.path.append(path)

# add root directory to path for relative import
from src.sqlite.db_utils import add_or_get_user, get_assistant
from src.streamlit_utils import get_remote_ip, init, get, set_to
from src.chroma_utils import start_chroma_server
from src.basic_data_classes import User

from app.mine_assistenter import mine_assistenter_page, go_to_chat_assistant_page
from app.edit_assistant import edit_assistant_page
from app.chat import chat_page
from app.gov_home import gov_home_page
from app.gov_edit_llm_model import edit_llm_model_page

# changing status to dev display under construction message for ip addresses other than localhost
status = "prod"  # "dev" or "prod"

# ------------------------
# Page header
st.set_page_config(
    page_title="Min GPT",
    page_icon=":left_speech_bubble:",
    initial_sidebar_state="expanded",
)

# initialize session
if get("user") is None:
    # start chroma server  for indexing assistant knwoledge base documents
    with st.spinner("Logger ind..."):
        start_chroma_server()
        # user is initialized by ip address
        print("initializing user")
        ip_adress = str(get_remote_ip())
        init("user", add_or_get_user(User(id=ip_adress, username=ip_adress)))
        if status == "prod" or get("user").id == "::1":
            set_to("online", True)


# ------------------------
# check if app is set to be online
if not get("online", False):
    st.markdown(
        """
        <div style="text-align:center">
        <h1>Vi er i gang med at opdatere løsningen</h1>
        <h2>Vi er tilbage snarest</h2>
        <img src="https://media.giphy.com/media/yJwXlLESRVkFd6yQVr/giphy.gif" alt="GPT-3" width="300" height="300">
        </div>
        """,
        unsafe_allow_html=True,
    )

# check if url is /?shared assistant link
elif "shared_assistant_id" in (params := st._get_query_params()):
    # chat with shared assistant
    shared_assistant_id = params["shared_assistant_id"][0]
    assistant = get_assistant(shared_assistant_id)
    if (a := get("current_assistant")) is None or a.id != assistant.id:
        set_to("shared_assistant_view", True)
        go_to_chat_assistant_page(assistant)

# check if url is /?admin
elif get("user").id == "::1":
    init("page", "admin_home")

else:
    # set start page to my assistants
    init("page", "my assistants")

# NAVIGATION
if get("page") == "admin_home":
    gov_home_page()
if get("page") == "editing_model":
    edit_llm_model_page()
# page 1: my assistants
if get("page") == "my assistants":
    mine_assistenter_page()
# page 2: create and edit assistant
if get("page") == "create assistant":
    edit_assistant_page()
# page 3: chat with assistant
if get("page") == "chat":
    chat_page()
