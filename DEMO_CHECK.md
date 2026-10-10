# Demo readiness check — 10 October 2026

Tested on this Windows laptop with its existing Python 3.10.6 and Django 5.2.18.

## Launch and restart

- Closed the previous AiQuest FastAPI and Vite servers after verifying their
  process identities. Unrelated Windows processes were left alone.
- Launched the final application only through `START_MAZAREJO.bat`.
- Preflight imports, environment/key presence, original JSON files, database,
  migrations, and compiled graph/checkpointer checks passed.
- Readiness returned HTTP 200 before the launcher opened Chrome. Chrome's window
  title changed to مزارع جو, and Django logged the browser page/assets requests.
- Native Chrome content inspection was stopped by a URL-verification guard;
  functional browser tests used the in-app browser at the explicit localhost URL.
- Launching the batch file again reused the ready server with the same PID and
  did not create a second project server.
- Stopped and restarted through the batch file again. Preflight, readiness,
  automatic browser opening, and another real Gemini analysis succeeded.
- Only port 8765 remained listening for this project's servers; 8000 and 5173
  were no longer listening.

## Real AI and browser behavior

- Completed all three onboarding steps through the UI, using example farm inputs
  of 20 dunums, 10,000 JOD budget, 10,000 m³ available water, and الغور.
- An initial balanced-plan request for selected tomato/cucumber candidates
  returned a real tomato plan: cost 6,960 JOD, margin 8,476.8 JOD, and water
  7,800 m³. The dashboard and crop/market/weather sections updated.
- After farm preferences changed to water efficiency with all candidates, a real
  request returned a cauliflower plan: 20 dunums, cost 5,740 JOD, remaining budget
  4,260 JOD, water 6,160 m³, production 55,700 kg, margin 27,680 JOD, and efficiency
  4.494 JOD/m³. No optimizer calculations were changed.
- In that unchanged conversation, a follow-up recalled the exact name
  `حقل النور 824`, supplied only in an earlier user message, not in farm setup.
- Reload retained the session's transcript/dashboard during the same server run.
- Before the later full-reset update, restart retained farm/preferences and cleared transcript/dashboard to match
  the existing RAM-only MemorySaver. A fresh real request after restart succeeded
  with the same optimizer totals and fresh returned weather data.
- DOM checks confirmed all five KPI values matched the selected backend plan.
  Land donut, water bars, and production columns use the real allocation fields.
  The one-crop result is the optimizer's actual output, not a fabricated split.
- Market rows used actual file prices, including 0.6 versus 0.275 JOD/kg, with
  source dates displayed. No market percentages, transport costs, demand
  estimates, risk scores, or cost-category splits were fabricated.
- Sending disabled input/submit controls until completion. Loading stages were
  explicitly labelled illustrative. Gemini lists rendered as lists; extras and
  raw message/tool objects were excluded by the adapter.
- Desktop 1440×1000 and mobile 390×844 checks showed no horizontal page overflow.
  Visible text contained none of `undefined`, `NaN`, or `null`.
- Final screenshots: `artifacts/mazarejo-dashboard.png` and
  `artifacts/mazarejo-real-charts.png`.

## Automated verification

Django system checks passed. Seven Django integration tests, three launcher
failure/reuse tests, and two JavaScript transformation tests passed.

Coverage includes actual compiled graph/tool invocation with a mocked model,
memory isolation, clean Gemini block extraction, missing/malformed tool output,
validation, CSRF, safe Arabic AI failures without fake success, session reset and
restart, correct Windows JavaScript MIME, missing imports/environment/key/data,
and safe handling of occupied ports.

SHA-256 checks confirmed `tools.py`, `crop_resources.json`, and
`market_prices.json` are byte-for-byte unchanged. Reversing the single approved
Agent.py branding replacement reproduced the original Agent.py hash; no other
agent change was made.

## Full-reset update

- Restart now clears farm/preferences, transcript, optimizer dashboard, weather,
  and drafts from previous server runs. The existing agent and tools are unchanged.
- Seven Django integration tests passed, including restart from dashboard and
  onboarding, stale chat rejection, and optional-water handling with actual
  optimizer calculations and a mocked model.
- Saved an onboarding draft in the browser, stopped the running batch/server,
  and relaunched `START_MAZAREJO.bat`. The default browser request redirected
  from `/ar/` to onboarding. The in-app browser also showed empty location,
  land, budget, and water after the restart, ignoring its old draft.
- Screenshot: `artifacts/mazarejo-fresh-restart.png`.

## Remaining demo limits

Gemini/weather depend on internet access, service availability, and Gemini quota.
The launcher verifies local readiness, not a guarantee of future API service.
MemorySaver resets on server restart. Prices are dated JSON reference data, not
a new live feed. Available water is not a constraint in the existing optimizer.
Large exhaustive optimizer searches can be slow; its algorithm remains locked.
The Django server is localhost demo hosting, not public production hosting.
