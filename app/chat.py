import streamlit as st
from src.streamlit_utils import get, set_to, append
from src.sqlite.gov_db_utils import get_global_setting
from src.chroma.chroma_utils import add_context
from src.openai.openai_utils import generate_response


def new_conversation():
    assistant = get("current_assistant")
    set_to("page", "chat")
    set_to(
        "messages",
        [
            {"role": "system", "content": assistant.system_prompt},
            {"role": "assistant", "content": assistant.welcome_message},
        ],
    )


def chat_page():
    assistant = get("current_assistant")

    col1, _, col3 = st.columns([1, 1, 1])
    with st.container():
        with col1:
            if not get("shared_assistant_view"):
                st.button(
                    label="← Mine assistenter ",
                    key="my_assistants",
                    on_click=set_to,
                    args=("page", "my assistants"),
                    use_container_width=True,
                )

        with col3:
            st.button(
                label=":sparkles: Ny samtale\n",
                key="ny_samtale",
                on_click=new_conversation,
                use_container_width=True,
            )
    st.markdown(
        "__" + assistant.name + "__",
    )

    # # Display chat messages
    icons = {
        "assistant": "images/assistant_icon.png",
        "user": "images/user_icon.png",
    }
    names = {
        "assistant": "ai",
        "user": "human",
    }
    for message in get("messages")[1:]:  # we skip the first system message
        with st.chat_message(
            name=names[message["role"]],
            avatar=icons[message["role"]],
        ):
            st.write(message["content"])

    if prompt := st.chat_input(placeholder="Skriv din besked her..."):
        with st.chat_message(
            name=names["user"],
            avatar=icons["user"],
        ):
            st.write(prompt)
        with st.spinner("Søger..."):
            if get("number_of_sources") > 0:
                request_messages = add_context(
                    prompt=prompt,
                    messages=get("messages"),
                    assistant=assistant,
                    top_k=3,
                )
                # st.write(request_messages)
            else:
                request_messages = get("messages")
        with st.spinner("Skriver..."):
            response = generate_response(
                prompt_input=prompt,
                chat_model=assistant.chat_model_name,
                messages=request_messages,
                max_tokens=int(get_global_setting("max_tokens").value),
                temperature=assistant.temperature,
            )
        # response = "test"
        append("messages", {"role": "user", "content": prompt})
        append("messages", {"role": "assistant", "content": response})
        with st.chat_message(
            name=names["assistant"],
            avatar=icons["assistant"],
        ):
            st.write(response)