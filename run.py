"""一键启动：python run.py"""
import threading
import time
import webbrowser
import uvicorn


def open_browser_later() -> None:
    time.sleep(1.2)
    webbrowser.open("http://127.0.0.1:8000")


if __name__ == "__main__":
    threading.Thread(target=open_browser_later, daemon=True).start()
    uvicorn.run("backend.app.main:app", host="127.0.0.1", port=8000, reload=False)
