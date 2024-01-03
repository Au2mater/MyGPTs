# Chat_med_din_assistent.py
# streamlit run app/Opret_assistent.py
""" load and chat with saved assistent """
import os
import streamlit as st

# add root directory to path for relative import
import sys
from random import randint

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.chroma.chroma_utils import retriever_from_directory
from src.openai.openai_utils import prepare_request, generate_response
from src.config_assistant import load_assistant_config
from src.path_urls.path_url_utilities import unpack

st.set_page_config(
    page_title="Min GPT:Chat",
    page_icon=":left_speech_bubble:",
    initial_sidebar_state="expanded",
)


def display_config(config):
    """given a configuration, display the configuration"""
    st.markdown(f"_navn:_ {config['assistant_name']}")
    st.markdown(f"_model:_ {config['chat_model_name']}")
    st.markdown(f"_grundvilkår:_ {config['system_prompt']}")
    st.markdown(f"_kilder:_ {config['sources']}")
    st.markdown(f"_oprettet:_ {config['created_at']}")


icons = {"assistant": "images/assistant_icon.png", "user": "images/user_icon.png"}

title = st.title("Min GPT")

with st.sidebar:
    with st.spinner("Indlæser..."):
        uploaded_file = st.file_uploader(
            "Indlæs din assistent",
            type=["zip"],
            accept_multiple_files=False,
            key=st.session_state.get("upc_key"),
        )

    if uploaded_file:
        st.session_state.dir = unpack(uploaded_file)
        st.session_state.config = load_assistant_config(st.session_state.dir)
        st.session_state.messages = None
        st.session_state.upc_key = str(randint(1, 1000000))

    if "config" in st.session_state:
        title.markdown("# " + st.session_state.config["assistant_name"])
        with st.spinner("Indlæser vidensbase..."):
            st.session_state.retriever = retriever_from_directory(st.session_state.dir)

        display_config(st.session_state.config)


if "config" in st.session_state:
    # Store LLM generated responses
    if st.session_state.get("messages", None) is None:
        st.session_state.messages = [
            {"role": "system", "content": st.session_state.config["system_prompt"]},
            {
                "role": "assistant",
                "content": f"Hej, jeg er {st.session_state.config['assistant_name']}. \
                                        Hvordan kan jeg hjælpe dig?",
            },
        ]

    # # Display chat messages
    for message in st.session_state.messages[1:]:  # we skip the first system message
        with st.chat_message(message["role"], avatar=icons[message["role"]]):
            st.write(message["content"])


# User-provided prompt
if prompt := st.chat_input(disabled="config" not in st.session_state):
    st.session_state.messages.append({"role": "user", "content": prompt})
    request = prepare_request(
        retriever=st.session_state.retriever,
        question=prompt,
        messages=st.session_state.messages,
    )
    with st.chat_message("user"):
        st.write(prompt)

# Generate a new response if last message is not from assistant
if st.session_state.get("messages", [{"role": "assistant"}])[-1]["role"] != "assistant":
    with st.chat_message("assistant", avatar=icons["assistant"]):
        with st.spinner("Tænker..."):
            response = generate_response(
                prompt_input=prompt,
                chat_model=st.session_state.config["chat_model_name"],
                messages=request,
            )
            st.write(response)
    message = {"role": "assistant", "content": response}
    st.session_state.messages.append(message)
