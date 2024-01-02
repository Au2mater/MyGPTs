import streamlit as st


# chose profile picture
def profile_pic():
    html = """
    <div class="profile-pic">
    <label class="-label" for="file">
        <span class="glyphicon glyphicon-camera"></span>
        <span>Change Image</span>
    </label>
    <input id="file" type="file" onchange="loadFile(event)"/>
    <img src="https://cdn.pixabay.com/photo/2017/08/06/21/01/louvre-2596278_960_720.jpg" id="output" width="200" />
    </div>
    """
    js = """
    var loadFile = function (event) {
    var image = document.getElementById("output");
    image.src = URL.createObjectURL(event.target.files[0]);
    };

    """
    css = """
    @mixin object-center {
    display: flex;
    justify-content: center;
    align-items: center;
    }

    $circleSize: 165px;
    $radius: 100px;
    $shadow: 0 0 10px 0 rgba(255,255,255,.35);
    $fontColor: rgb(250,250,250);

    .profile-pic {
    color: transparent;
    transition: all .3s ease;
    @include object-center;
    position: relative;
    transition: all .3s ease;
    
    input {
        display: none;
    }
    
    img {
        position: absolute;
        object-fit: cover;
        width: $circleSize;
        height: $circleSize;
        box-shadow: $shadow;
        border-radius: $radius;
        z-index: 0;
    }
    
    .-label {
        cursor: pointer;
        height: $circleSize;
        width: $circleSize;
    }
    
    &:hover {
        .-label {
        @include object-center;
        background-color: rgba(0,0,0,.8);
        z-index: 10000;
        color: $fontColor;
        transition: background-color .2s ease-in-out;
        border-radius: $radius;
        margin-bottom: 0;
        }
    }
    
    span {
        display: inline-flex;
        padding: .2em;
        height: 2em;
    }
    }

    /////////////////////////
    // Body styling 🐾
    /////////---------->

    body {
    height: 100vh;
    background-color: rgb(25, 24, 21);
    @include object-center;
    
    a:hover {
        text-decoration: none;
    }
    }
    """
    # combine all three components to a complete html document
    html_full = f"<html><head><style>{css}</style></head><body>{html}</body><script>{js}</script></html>"
    return html_full


# write html to a file
def write_html(html, file_name="test.html"):
    with open(file_name, "w") as file:
        file.write(html)


write_html(profile_pic(), "data/test.html")
