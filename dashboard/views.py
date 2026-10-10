import json
import logging
import math
import os
from uuid import uuid4
from django.db import connection
from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.views.decorators.http import require_POST, require_GET
from django.contrib.staticfiles.views import serve
from . import agent_service
from demo_config import PROJECT_ID, BOOT_ID

logger = logging.getLogger(__name__)
ERROR_TEXT = "تعذر إكمال التحليل حالياً. حاول مرة أخرى أو تحقق من الاتصال."
LOCATIONS = ["الغور", "المفرق", "عمّان"]


def serve_asset(request, path):
    # Fresh assets on every local demo launch, including MIME metadata. Avoid a
    # cached old script/theme or an old Windows text/plain .js response.
    request.META.pop("HTTP_IF_MODIFIED_SINCE", None)
    response = serve(request, path, insecure=True)
    response["Cache-Control"] = "no-store"
    return response


def thread_id(request):
    # A new demo process starts with empty farm setup and conversation state.
    if request.session.get("mazarejo_boot_id") != BOOT_ID:
        request.session["mazarejo_boot_id"] = BOOT_ID
        request.session["mazarejo_thread_id"] = str(uuid4())
        request.session["mazarejo_messages"] = []
        request.session["mazarejo_dashboard"] = None
        request.session["mazarejo_weather"] = []
        request.session.pop("mazarejo_farm", None)
        request.session.pop("mazarejo_setup", None)
    if not request.session.get("mazarejo_thread_id"):
        request.session["mazarejo_thread_id"] = str(uuid4())
    return request.session["mazarejo_thread_id"]


def stored_setup(request):
    return {"farm": request.session.get("mazarejo_farm", {}), "setup": request.session.get("mazarejo_setup", {})}


def onboarding(request, template, step):
    thread_id(request)
    options = list(agent_service.read_data("crop_resources.json"))
    return render(request, template, {"step": step, "crop_options": options, "locations": LOCATIONS, "saved_setup": {**stored_setup(request), "boot_id": BOOT_ID}})


def index(request):
    return onboarding(request, "dashboard/index.html", 1)


def crops(request):
    return onboarding(request, "dashboard/crops.html", 2)


def ready(request):
    return onboarding(request, "dashboard/ready.html", 3)


def home(request):
    thread_id(request)
    if not request.session.get("mazarejo_farm"):
        return redirect("dashboard:index")
    state = {
        **stored_setup(request),
        "messages": request.session.get("mazarejo_messages", []),
        "dashboard": request.session.get("mazarejo_dashboard"),
        "weather": request.session.get("mazarejo_weather", []),
        "market_data": agent_service.read_data("market_prices.json"),
    }
    return render(request, "dashboard/home.html", {"initial_state": state})


def read_payload(request):
    data = json.loads(request.body.decode("utf-8"))
    if not isinstance(data, dict):
        raise ValueError("JSON body must be an object")
    return data


def numeric(data, key, positive=False):
    value = data.get(key)
    if isinstance(value, bool) or not isinstance(value, (float, int)) or not math.isfinite(value):
        raise ValueError("Missing or invalid numeric field: " + key)
    if value < 0 or (positive and value <= 0):
        raise ValueError("Out-of-range field: " + key)
    return value


@require_POST
def start_farm(request):
    try:
        data = read_payload(request)
        farm, setup = data.get("farm"), data.get("setup")
        if not isinstance(farm, dict) or not isinstance(setup, dict):
            raise ValueError("Missing farm/setup")
        land = numeric(farm, "land", positive=True)
        if land % 10 != 0 or farm.get("location") not in LOCATIONS:
            raise ValueError("Invalid region or land increment")
        crop_names = setup.get("crops", [])
        supported = agent_service.read_data("crop_resources.json")
        if not isinstance(crop_names, list) or any(not isinstance(c, str) or c not in supported for c in crop_names):
            raise ValueError("Invalid crop selection")
        if setup.get("goal") not in agent_service.GOAL_LABELS:
            raise ValueError("Invalid goal")
        water = numeric(farm, "water") if farm.get("water") is not None else None
        farm = {"location": farm["location"], "land": int(land), "water": water, "budget": numeric(farm, "budget", positive=True)}
        setup = {"crops": list(dict.fromkeys(crop_names)), "goal": setup["goal"]}
        thread_id(request)
        if stored_setup(request) != {"farm": farm, "setup": setup}:
            request.session["mazarejo_farm"] = farm
            request.session["mazarejo_setup"] = setup
            request.session["mazarejo_dashboard"] = None
            request.session["mazarejo_weather"] = []
            request.session["mazarejo_thread_id"] = str(uuid4())
            request.session["mazarejo_messages"] = []
        thread_id(request)
        return JsonResponse({"ok": True})
    except (ValueError, TypeError, UnicodeDecodeError, KeyError):
        return JsonResponse({"ok": False, "error": "راجع بيانات المزرعة. المساحة يجب أن تكون موجبة ومن مضاعفات ١٠، والميزانية موجبة."}, status=400)
    except Exception:
        logger.exception("Failed to save farm setup")
        return JsonResponse({"ok": False, "error": "تعذر حفظ بيانات المزرعة. حاول مرة أخرى."}, status=503)


@require_POST
def farm_chat(request):
    try:
        payload = read_payload(request)
        message = payload.get("message")
        if not isinstance(message, str) or not message.strip():
            raise ValueError("Missing message")
    except (ValueError, TypeError, UnicodeDecodeError):
        return JsonResponse({"error": "اكتب رسالة صالحة ثم حاول مرة أخرى."}, status=400)
    current_thread = thread_id(request)
    farm = request.session.get("mazarejo_farm")
    setup = request.session.get("mazarejo_setup")
    if not farm or not setup:
        return JsonResponse({"error": "أكمل بيانات المزرعة أولاً."}, status=400)
    try:
        with agent_service.thread_lock(current_thread):
            result = agent_service.invoke_agent(message.strip(), farm, setup, current_thread)
            history = request.session.get("mazarejo_messages", [])
            request.session["mazarejo_messages"] = (history + [
                {"role": "user", "text": message.strip()}, {"role": "assistant", "text": result["answer"]},
            ])[-60:]
            if result["dashboard"] is not None:
                request.session["mazarejo_dashboard"] = result["dashboard"]
            request.session["mazarejo_weather"] = result["weather"]
        return JsonResponse(result)
    except Exception:
        logger.exception("LangGraph analysis failed")
        return JsonResponse({"error": ERROR_TEXT}, status=502)


@require_POST
def reset_chat(request):
    thread_id(request)
    request.session["mazarejo_thread_id"] = str(uuid4())
    request.session["mazarejo_messages"] = []
    request.session["mazarejo_dashboard"] = None
    request.session["mazarejo_weather"] = []
    return JsonResponse({"ok": True})


@require_GET
def health(request):
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        if agent_service.agent_app.checkpointer is None:
            raise RuntimeError("Checkpointer unavailable")
        return JsonResponse({"status": "ok", "app": "mazarejo", "project_id": PROJECT_ID, "pid": os.getpid()})
    except Exception:
        logger.exception("Readiness check failed")
        return JsonResponse({"status": "unavailable"}, status=503)


def csrf_failure(request, reason=""):
    if request.path.endswith("/chat/") or request.path.endswith("/reset/") or request.path.endswith("/start"):
        return JsonResponse({"error": "انتهت صلاحية الصفحة. حدّثها ثم حاول مرة أخرى."}, status=403)
    return render(request, "dashboard/error.html", status=403)


def error_page(request, exception=None):
    return render(request, "dashboard/error.html", status=400)


def not_found(request, exception=None):
    return render(request, "dashboard/error.html", status=404)


def server_error(request):
    return render(request, "dashboard/error.html", status=500)
