# مزارع جو — Windows live demo

Double-click **START_MAZAREJO.bat** in this folder. Keep its terminal open.
The app opens at **http://127.0.0.1:8765/ar/** after Django passes readiness.
One Django process serves the Arabic frontend, chat endpoint, static assets, and
the existing LangGraph agent. No React, FastAPI, Node, Redis, or Docker server is
part of this launch.

## Before demo day

After cloning from GitHub, copy `.env.example` to `.env` and enter your own
`GEMINI_API_KEY` locally. Install the dependencies below, then run the launcher.
The `.env`, runtime secret, session database, and demo screenshots are ignored
by Git; do not force-add them. The launcher creates a fresh local database and
runtime secret when needed.

Dependencies have been installed and tested with this laptop's existing
`C:\Program Files\Python310\python.exe` (Python 3.10.6). The launcher uses
`.venv\Scripts\python.exe` when present, otherwise that known Python installation,
then Python from PATH if necessary. It never installs packages.

To prepare dependencies again, run in PowerShell from this folder:

```powershell
& 'C:\Program Files\Python310\python.exe' -m pip install -r requirements.txt
```

Use the virtual environment's Python for that command if you create a `.venv`.
Keep the existing `.env` with `GEMINI_API_KEY` populated. `.env.example` lists
the variable names and contains no real key. `DJANGO_SECRET_KEY` is optional;
the app generates a persistent local key under `.runtime/` when it is absent.

Gemini and live weather require internet access. Ensure Gemini quota is
available before judging. The launcher checks configuration and imports; it
does not consume Gemini quota to test an AI request.

## What the launcher does

It enters its own project folder, selects Python, verifies Django, LangGraph,
MemorySaver, Gemini, dotenv and requests imports, checks `.env` and the key
without printing it, validates the two existing JSON objects and local frontend
assets, checks the fixed port, checks SQLite integrity/write access, runs Django
checks and migrations, and starts Django with the autoreloader disabled.

A background readiness poll confirms `/health/` reports this folder's project
identity and the new server's PID before opening the default browser. An
already-running server is reused only if it reports the same project identity.
An unrelated process occupying port 8765 causes a clear error; nothing is killed.
The terminal remains open on failure and gives dependency installation guidance
when an import is missing. Technical analysis errors stay in that terminal.

Stop the server with Ctrl+C (or Ctrl+Break). If Windows asks `Terminate batch
job (Y/N)?`, choose Y. Double-click the batch file again to restart, then refresh
any existing browser tabs. A real restart clears farm inputs, crop/goal selections,
conversation history, dashboard results, weather, and old browser drafts. The app
returns to empty onboarding. Opening the launcher while the server is still
running reuses that process and does not reset anything.

The fixed host and port live in `demo_config.py`. The frontend uses Django's
generated same-origin URLs, so there is no separate API URL to configure.
JavaScript MIME is set explicitly for Windows, and local static responses use
`Cache-Control: no-store` to avoid stale demo scripts/themes.

## Using the demo

1. Enter location, land, and budget in the existing three-step onboarding. Water
   is optional: leave it blank to see the plan's calculated water needs, or enter
   your available amount to include it in the conversation.
2. Choose a supported planning goal and optionally specific crops.
3. Open the decision dashboard and ask for a plan. No plan appears before an
   actual optimizer result exists.
4. Use the plan selector to compare balanced, highest-margin, and best-water-
   efficiency plans. All five KPIs and the land, water, and production charts
   use the selected real plan.
5. Ask a follow-up in the same browser session. Reloading retains conversation
   history while this server process remains running. A new conversation button
   creates a new LangGraph thread while retaining farm information.

Example prompts: `شو أفضل محصول أزرع؟`, `وازنلي بين الربح واستهلاك المياه`,
`قارنلي بين سوق عمّان وإربد`.

Changing farm inputs or the planning goal starts a fresh conversation and clears
the previous dashboard so results from an old farm setup are not reused.

## HTTP contract and frontend handoff

The current final application uses Django browser sessions, not the earlier
FastAPI `session_id` contract. The browser sends its HttpOnly session cookie;
the Django integration stores a UUID in that session and passes it as LangGraph
`configurable.thread_id`. Different browser sessions receive different threads.
Session cookies and `X-CSRFToken` are required for POST requests. Do not put a
Gemini key in frontend code.

```text
GET  /health/                  readiness, no AI request
GET  /ar/                      dashboard, or redirects to onboarding
POST /ar/start                 save farm and planning preferences
POST /ar/api/farm/chat/         invoke the existing graph
POST /ar/api/farm/reset/        start a new conversation
```

Save setup request:

```json
{
  "farm": {"location": "الغور", "land": 20, "water": 10000, "budget": 10000},
  "setup": {"goal": "balanced", "crops": ["بندورة", "خيار"]}
}
```

The numbers above are request examples, never frontend defaults. Supported
locations are الغور، المفرق، عمّان. Land must be positive and a multiple of 10,
matching the existing optimizer. Budget must be positive. Water is optional:
omit `water` or send `"water": null` when unspecified; a supplied value must be
nonnegative. An explicit zero remains zero. Unspecified water is omitted from
the agent's farm context, while required water comes from the optimizer result.
Goals: `balanced`, `margin`, `water_efficiency`. Crop options come directly
from `crop_resources.json`; an empty selection lets the agent use all candidates.

Chat request:

```json
{"message": "وازنلي بين الربح واستهلاك المياه"}
```

Successful response:

```json
{"answer": "النص النهائي من Gemini", "dashboard": null, "weather": []}
```

When present, `dashboard` is the parsed latest `optimize_farm_plan` ToolMessage
from the graph result, with its original fields and calculations. It contains
`highest_margin_plan`, `balanced_plan`, and `best_water_efficiency_plan`, with
their `allocation` and totals. A structured unsuccessful optimizer result remains
unsuccessful; it is not replaced with a fake plan. Gemini text blocks are
extracted without extras, signatures, raw tool calls, or message objects.
`weather` contains only actual structured results from weather ToolMessages.

Failures return an appropriate non-2xx status and `{"error":"رسالة عربية"}`.
No technical exception text is sent to the browser. Network/AI failure displays
a visible Arabic error and retains any previously computed dashboard; it creates
no new result. Missing values display an unavailable state, not zero.

Teammate handoff files:

- `static/js/mazarejoApi.js`: the ONLY frontend HTTP adapter. Reuse `sendMessage`,
  `postJson`, and same-origin CSRF/session handling.
- `static/js/dashboardTransform.js`: isolates raw optimizer/market fields from
  presentation and never fills missing numbers with zero.
- This README: routes, request/response shape, session behavior, and limitations.

The replaceable presentation is `dashboard/templates/dashboard/`,
`static/css/style.css`, `static/js/main.js`, `static/js/dashboard.js`, and
`static/images/mazarejo-mark.svg`. Django integration lives in `dashboard/views.py`
and `dashboard/agent_service.py`. Replacing the presentation does not require
editing the agent or tools. Local Markdown vendors are Marked 18.1.0 and
DOMPurify 3.4.16, with their licenses in `static/vendor/`; no CDN or Node runtime
is required. Markdown HTML is sanitized before rendering.

## Backend preservation and meaningful limits

`tools.py`, optimizer logic, crop data, market data, graph nodes/edges and memory
configuration were left unchanged. The ONLY `Agent.py` edit in this Django
integration is the approved system-prompt brand replacement from ميزان to مزارع جو.
Farm context is supplied as a HumanMessage through the existing compiled graph,
not through an added system prompt or redesigned workflow.

The old `api.py`, `frontend/`, `requirements-api.txt`, and `API.md` are retained
as previous work. They are unused by this final launcher. Do not launch their
servers for the live demo.

- MemorySaver is in RAM. Restarting clears farm setup, AI history, the dashboard,
  weather, and browser drafts on the next request/page reload. The new conversation
  button clears chat/results while retaining farm setup during the same server run.
- The optimizer takes land, budget and optional crops. Available water is context,
  not an optimizer constraint; the interface states this clearly.
- These are estimated planning margins, not guaranteed net profits. No fabricated
  risk, transport, demand, capacity, cost category or market-distribution metrics
  are displayed.
- Market comparison uses the unchanged file's representative price fields and
  reports their dates. This is reference data, not a newly fetched live market feed.
- Large land/candidate combinations may make the existing exhaustive optimizer
  slow. The integration does not alter its search or enforce a new arbitrary limit.
- Django's localhost development server is for this laptop demo, not public hosting.

## Verification

```powershell
& 'C:\Program Files\Python310\python.exe' manage.py check
& 'C:\Program Files\Python310\python.exe' manage.py test dashboard
& 'C:\Program Files\Python310\python.exe' -m unittest discover -s tests -p test_launcher.py -v
```

These checks cover real compiled-graph invocation and actual optimizer output
with the model mocked, session isolation/reset/restart, clean text extraction,
validation, Arabic errors, CSRF, readiness, Windows JavaScript MIME, and launcher
missing-dependency/key/data/port failures. `tests/dashboard-transform.test.mjs`
is an optional development-only Node test; Node is not a demo dependency.

The separate real-Gemini browser/restart test is recorded in `DEMO_CHECK.md`.
