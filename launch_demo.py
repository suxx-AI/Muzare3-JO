"""Preflight and one Django server. No pip installation, process killing, or AI calls."""
import importlib
import json
import os
import socket
import sqlite3
import sys
import threading
import time
import traceback
import urllib.error
import urllib.request
import webbrowser
from demo_config import PROJECT_ROOT, PROJECT_ID, DEMO_HOST, DEMO_PORT, RUNTIME_DIR

BASE_URL = f"http://{DEMO_HOST}:{DEMO_PORT}"


def log(kind, message):
    print(f"[{kind}] {message}", flush=True)


def fail(message):
    log("ERROR", message)
    return 1


def readiness():
    # Ignore configured system proxies for this localhost readiness request.
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    with opener.open(BASE_URL + "/health/", timeout=2) as response:
        result = json.load(response)
    return result


def is_our_server(result):
    return isinstance(result, dict) and result.get("status") == "ok" and result.get("app") == "mazarejo" and result.get("project_id") == PROJECT_ID


def open_app(url):
    if not webbrowser.open(url, new=2):
        log("WARNING", f"The server is ready but the default browser could not be opened. Open {url}")
    else:
        log("OK", "Browser opened after the readiness check: " + url)


def main():
    os.chdir(PROJECT_ROOT)
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    log("INFO", f"Python {sys.version.split()[0]}: {sys.executable}")
    if sys.version_info < (3, 10):
        return fail("Python 3.10 or newer is required for the existing agent.")
    missing = []
    required = {
        "django": "Django", "dotenv": "python-dotenv", "requests": "requests",
        "langgraph.graph": "LangGraph", "langgraph.checkpoint.memory": "LangGraph MemorySaver",
        "langchain_core.messages": "LangChain core", "langchain_google_genai": "Gemini library",
    }
    for module, label in required.items():
        try:
            importlib.import_module(module)
        except Exception:
            missing.append(label)
    if missing:
        log("ERROR", "Missing or broken imports: " + ", ".join(missing))
        log("FIX", f'"{sys.executable}" -m pip install -r "{PROJECT_ROOT / "requirements.txt"}"')
        return 1
    log("OK", "Django, LangGraph, Gemini, dotenv, and requests imports")
    env_path = PROJECT_ROOT / ".env"
    if not env_path.is_file():
        return fail(".env is missing. Copy .env.example to .env and set GEMINI_API_KEY before the demo.")
    from dotenv import load_dotenv
    load_dotenv(env_path)
    if not os.environ.get("GEMINI_API_KEY", "").strip():
        return fail("GEMINI_API_KEY is missing. Set it in .env. The key is never printed by this launcher.")
    log("OK", ".env and GEMINI_API_KEY present (key hidden)")
    for name in ["Agent.py", "tools.py", "manage.py", "config/settings.py", "dashboard/templates/dashboard/home.html"]:
        if not (PROJECT_ROOT / name).is_file():
            return fail("Required project file is missing: " + name)
    for name in ["crop_resources.json", "market_prices.json"]:
        try:
            with (PROJECT_ROOT / name).open(encoding="utf-8") as file:
                if not isinstance(json.load(file), dict):
                    return fail(name + " must contain a JSON object.")
        except (OSError, ValueError):
            return fail("Required JSON data file is missing, unreadable, or invalid: " + name)
    for name in ["static/css/style.css", "static/js/dashboard.js", "static/js/dashboardTransform.js", "static/js/mazarejoApi.js", "static/vendor/marked.umd.js", "static/vendor/purify.min.js"]:
        if not (PROJECT_ROOT / name).is_file():
            return fail("Required frontend asset is missing: " + name)
    log("OK", "Agent, agricultural JSON files, and local frontend assets")

    try:
        with socket.socket() as probe:
            probe.bind((DEMO_HOST, DEMO_PORT))
    except OSError:
        try:
            existing = readiness()
        except Exception:
            existing = None
        if is_our_server(existing):
            log("OK", f"This project's Django server is already ready on port {DEMO_PORT}; reusing it safely.")
            open_app(BASE_URL + "/ar/")
            return 0
        return fail(f"Port {DEMO_PORT} is occupied by another service. Close that service or free the port; no process was killed.")

    db_path = PROJECT_ROOT / "db.sqlite3"
    try:
        RUNTIME_DIR.mkdir(exist_ok=True)
        # Check write access before starting without changing agricultural files.
        check_path = RUNTIME_DIR / "write-check.tmp"
        check_path.write_text("ok", encoding="utf-8")
        check_path.unlink()
        if db_path.exists():
            with sqlite3.connect(f"file:{db_path.as_posix()}?mode=ro", uri=True) as db:
                if db.execute("PRAGMA quick_check").fetchone()[0] != "ok":
                    return fail("SQLite database integrity check failed. Restore a working database before the demo.")
    except (OSError, sqlite3.Error):
        return fail("The project/database folder is not accessible. Check folder permissions and SQLite availability.")
    log("OK", "Database availability and project write access")

    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
    try:
        import django
        django.setup()
        from django.core.management import call_command
        call_command("check")
        call_command("migrate", interactive=False, verbosity=1)
        from dashboard.agent_service import agent_app
        if agent_app.checkpointer is None:
            return fail("The existing LangGraph checkpointer is not configured.")
    except Exception:
        log("ERROR", "Django/agent initialization or migrations failed. Technical details follow; browser will stay closed.")
        traceback.print_exc()
        return 1
    log("OK", "Database migrations, Django checks, and existing LangGraph initialization")

    startup_failed = threading.Event()
    ready = threading.Event()

    def wait_and_open():
        deadline = time.monotonic() + 30
        while time.monotonic() < deadline:
            try:
                result = readiness()
                if is_our_server(result) and result.get("pid") == os.getpid():
                    ready.set()
                    open_app(BASE_URL + "/ar/")
                    return
            except Exception:
                pass
            time.sleep(0.3)
        startup_failed.set()
        log("ERROR", "Server did not pass readiness within 30 seconds. Browser was not opened. Stop with Ctrl+C and inspect the logs.")

    log("INFO", f"Starting the single Django server at {BASE_URL}; Ctrl+C stops it.")
    threading.Thread(target=wait_and_open, name="demo-readiness", daemon=True).start()
    try:
        call_command("runserver", f"{DEMO_HOST}:{DEMO_PORT}", use_reloader=False)
    except KeyboardInterrupt:
        log("INFO", "Demo server stopped.")
    except Exception:
        log("ERROR", "Server failed to start. Technical details follow; the browser is opened only after readiness.")
        traceback.print_exc()
        return 1
    return 1 if startup_failed.is_set() or not ready.is_set() else 0


if __name__ == "__main__":
    raise SystemExit(main())
