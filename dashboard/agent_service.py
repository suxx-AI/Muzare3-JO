"""Integration only. The compiled graph, tools, and calculations live in Agent.py."""
import json
from threading import Lock
from weakref import WeakValueDictionary
from langchain_core.messages import AIMessage, HumanMessage, ToolMessage
from Agent import app as agent_app
from demo_config import PROJECT_ROOT

_locks = WeakValueDictionary()
_guard = Lock()


def thread_lock(thread_id):
    with _guard:
        lock = _locks.get(thread_id)
        if lock is None:
            lock = Lock()
            _locks[thread_id] = lock
        return lock


def read_data(name):
    with (PROJECT_ROOT / name).open(encoding="utf-8") as file:
        return json.load(file)


def extract_text(messages):
    for message in reversed(messages):
        if not isinstance(message, AIMessage) or message.tool_calls:
            continue
        if isinstance(message.content, str):
            return message.content
        if isinstance(message.content, list):
            return "\n".join(block["text"] for block in message.content
                             if isinstance(block, dict) and block.get("type") == "text"
                             and isinstance(block.get("text"), str))
    return ""


def latest_optimizer(messages):
    for message in reversed(messages):
        if isinstance(message, ToolMessage) and message.name == "optimize_farm_plan":
            try:
                data = json.loads(message.content)
                return data if isinstance(data, dict) else None
            except (TypeError, ValueError):
                return None
    return None


def weather_results(messages):
    results = {}
    for message in messages:
        if isinstance(message, ToolMessage) and message.name == "get_live_weather":
            try:
                data = json.loads(message.content)
                if isinstance(data, dict) and isinstance(data.get("location"), str):
                    results[data["location"]] = data
            except (TypeError, ValueError):
                pass
    return list(results.values())


GOAL_LABELS = {
    "balanced": "التوازن بين الهامش المالي التقديري واستهلاك المياه",
    "margin": "أعلى هامش مالي تقديري",
    "water_efficiency": "أفضل كفاءة للمياه",
}


def invoke_agent(question, farm, setup, thread_id):
    # Human-provided farm context, not a new system prompt or a new graph node.
    context = {
        "موقع المزرعة": farm["location"], "المساحة بالدونم": farm["land"],
        "ميزانية الموسم بالدينار": farm["budget"],
        "الهدف الذي اختاره المستخدم": GOAL_LABELS[setup["goal"]],
        "المحاصيل التي اختارها المستخدم": setup["crops"],
    }
    if farm.get("water") is not None:
        context["المياه المتاحة بالمتر المكعب"] = farm["water"]
    message = "معلومات المزرعة التي أدخلها المستخدم:\n" + json.dumps(context, ensure_ascii=False)
    message += "\n\nرسالة المستخدم:\n" + question
    result = agent_app.invoke(
        {"messages": [HumanMessage(content=message)]},
        config={"configurable": {"thread_id": thread_id}},
    )
    messages = result.get("messages") or []
    answer = extract_text(messages)
    if not answer.strip():
        raise RuntimeError("The agent did not return final text")
    return {"answer": answer, "dashboard": latest_optimizer(messages), "weather": weather_results(messages)}
