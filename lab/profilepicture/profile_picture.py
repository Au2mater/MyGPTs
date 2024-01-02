import streamlit as st
from streamlit.components.v1 import html

if "image_index" not in st.session_state:
    st.session_state.image_index = 0
images = [
    'https://www.verdensmaalene.dk/sites/default/files/filarkiv/kommunikationsmateriale/Verdensmaals-white-baggrund-RGB.png',
    'https://img.icons8.com/?size=160&id=fQRzB9r2Qrxf&format=png',
    'https://img.icons8.com/?size=160&id=V4xIeDhASU39&format=png',
    'https://img.icons8.com/?size=160&id=qDMEwWyxjqFc&format=png',
    'https://img.icons8.com/?size=160&id=vSNUnAV0tnsg&format=png'
]
def change_image(n:1):
    st.session_state.image_index = (st.session_state.image_index + n) % len(images)

with open("data/html/profile2.html", "r") as f:
    profile_html = f.read()

st.markdown("""
    <style>
    .st-emotion-cache-7ym5gk {
        padding: 0.15em 0.15em !important;
        height: 4.5em !important;
    }
    </style>
    """, unsafe_allow_html=True)
with st.container(border=False):
    p,c1,n, c2 = st.columns([.3,2,.3,12])
    p.button(label="<", key="previous"
                , help="Klik for at ændre profilbillede"
                , on_click=change_image, args=(-1,))
    
    # c1.image(image=images[st.session_state.image_index], width=20
    #          , use_column_width=False, clamp=False)
    with c1:
        profile_html = profile_html.replace("image_link", images[st.session_state.image_index])
        html(profile_html, height=75,)
    n.button(label="\>", key="next"
                , help="Klik for at ændre profilbillede"
                ,on_click=change_image, args=(1,))
        # assistant name inp
    c2.text_input(label="Assitentens navn*",
                                        value=f""
                                        ,help="Giv assistanten et passende navn."
                                        ,key="assistant_name"
                                        ,kwargs={"height":50
                                                 ,"margin":0})
    # system prompt input
