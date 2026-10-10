# Mizaan frontend integration

This documents the earlier FastAPI prototype, which is unused by the current
Django demo. Use [README.md](README.md#http-contract-and-frontend-handoff) for
the current endpoints, startup instructions, and frontend handoff.

Backend: `http://127.0.0.1:8000`. Interactive specification: `/docs`.

`GET /health` returns `{"status":"ok"}`.

`POST /chat` accepts `Content-Type: application/json`:

```json
{"message":"رسالة المستخدم","session_id":"demo-user"}
```

Both values are required, nonblank strings. The response is:

```json
{"answer":"النص النهائي من Gemini","dashboard":null}
```

`answer` is plain text, without metadata, tool calls, or LangChain objects.
`dashboard` is either null or the latest parsed `optimize_farm_plan` tool output.
It can come from an earlier turn in the same remembered conversation.

On success, the optimizer object includes `success`, `plans_evaluated`,
`balanced_plan`, `highest_margin_plan`, `best_water_efficiency_plan`,
`balanced_rule`, `ignored_crops`, and `important_note`.

Each plan contains:

| Field | Meaning |
| --- | --- |
| `estimated_margin_jod` | Estimated planning margin in JOD |
| `total_water_m3` | Total water in cubic metres |
| `total_cost_jod` | Total reference operating cost in JOD |
| `remaining_budget_jod` | Remaining budget in JOD |
| `water_efficiency_jod_per_m3` | Estimated margin per cubic metre |
| `estimated_revenue_jod` | Estimated revenue in JOD |
| `allocation` | Crop-name-keyed object |

Each `allocation[crop]` includes `dunums`, `water_m3`,
`expected_production_kg`, `reference_cost_jod`, `best_market`,
`market_price_jod_per_kg`, and `estimated_revenue_jod`.

Failed optimizer output has `success: false`, a `message`, and sometimes
`ignored_crops`. It is still returned with HTTP 200 when the agent completes.
Treat all dashboard fields as optional; preserve valid zeros and never invent
missing values. Render `answer` as text rather than injecting it as HTML.

The same `session_id` continues a conversation; different IDs isolate histories.
Memory clears when the backend restarts. Run one backend worker. Session IDs
identify threads and are not authentication credentials.

HTTP 422 means invalid request fields; HTTP 502 means agent execution failed,
with `{"detail":"Arabic error message"}`. Network failures must also be handled.

Reuse `src/api/mizaanApi.js` with `src/config.js`; neither requires React. Set
`API_BASE_URL` in config and call `sendMessage(message, sessionId)` from your UI.
Optional `src/utils/dashboardTransform.js` contains the existing plan/chart
mapping. The temporary UI can be replaced without editing the backend.

Current development CORS origins: `http://localhost:5173` and
`http://127.0.0.1:5173`. Configure another origin in the API if needed.
