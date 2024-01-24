import streamlit as st
from src.streamlit_utils import get, set_to, append
from src.sqlite.gov_db_utils import get_global_setting
from src.openai_utils import generate_response
from src.sqlite.db_utils import get_llm
from src.query_chain import generate_search_queries, add_context_from_queries
import logging


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

def write_message(message):
    # use st.markdown to display the message
    # if the message contains a makrdown image reference, then use st.image(image url) to display the image
    # markdown images are of the form ![alt text](<image url>)
    import re
    image_regex = r"(?<=)(!\[.*\]\(\<.*\>\))(?=)"        
    image_url_regex = r"!\[.*\]\(\<(.*)\>\)"
    # split message into segments of text and images
    segments = re.split(image_regex, message)
    for segment in segments:
        if re.search(image_regex, segment):
            # extract the image url
            image_url = re.search(image_url_regex, segment).group(1)
            # display the image
            st.image(image_url, width=400)
        else:
            # display the text
            st.markdown(segment, unsafe_allow_html=True)



def chat_page():
    assistant = get("current_assistant")

    if isinstance(m := get("messages"), tuple):
        set_to("messages", m[0])
    col1, _, col3 = st.columns([1, 1, 1])
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
            write_message(message["content"])


    if prompt := st.chat_input(placeholder="Skriv din besked her..."):
        with st.chat_message(name=names["user"], avatar=icons["user"]):
            write_message(prompt)
            # st.markdown(prompt, unsafe_allow_html=True)
        if get("number_of_sources") > 0:
            search_queries = generate_search_queries(
                prompt_input=prompt, messages=get("messages")
            )
            str_search_queries = "- " + "\n- ".join(search_queries)
            with st.spinner(f"Søger efter:\n {str_search_queries}"):
                # with st.spinner("Søger..."):
                # request_messages = add_context(
                #     prompt=prompt,
                #     messages=get("messages"),
                #     assistant=assistant,
                #     top_k=4,
                # )
                logging.info(f"search queries: {search_queries}" f"prompt: {prompt}")
                request_messages = add_context_from_queries(
                    messages=get("messages"),
                    queries=search_queries,
                    assistant=assistant,
                    top_k=4,
                )
                context = request_messages[-1]["content"]
                with st.sidebar:
                    st.markdown(
                        "Søgte efter: \n"
                        f"{str_search_queries}"
                        "\n\nResultater:\n\n"
                        f"{context[8:]}",
                        unsafe_allow_html=True,
                    )
        else:
            request_messages = get("messages")
        with st.spinner("Skriver..."):
            response = generate_response(
                prompt_input=prompt,
                llm=get_llm(assistant.chat_model_name),
                messages=request_messages,
                max_tokens=int(get_global_setting("max_tokens").value),
                temperature=assistant.temperature,
            )
        logging.info(
            f"assistant {assistant.name} received prompt: "
            f"{prompt[:100]}{'...' if len(prompt)>100 else ''}"
        )
        logging.info(
            f"assistant {assistant.name} responded with: "
            f"{response[:100]}{'...' if len(response)>100 else ''}"
        )
        # response = "test"
        append("messages", {"role": "user", "content": prompt})
        append("messages", {"role": "assistant", "content": response})
        with st.chat_message(
            name=names["assistant"],
            avatar=icons["assistant"],
        ):
            write_message(response)
