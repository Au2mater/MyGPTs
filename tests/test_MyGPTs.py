from streamlit.testing.v1 import AppTest
from pathlib import Path

app_path = Path("app/test_app.py")
at = AppTest.from_file(str(app_path), default_timeout=60)
at.text_input("user_name").input("test_user").run()
(at.get("text_input").input("test_user").run())
