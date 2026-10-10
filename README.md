# 🌱 مزارع جو | Muzare3 JO

**An Arabic AI decision agent for agricultural investment in Jordan.**

Built for **AI Quest 2026 🇯🇴**.

مزارع جو helps farm owners compare crops, allocate their budget, estimate water needs, and understand potential financial margins using Jordanian agricultural and market data.

---

## What does it do?

مزارع جو helps answer:

> **“What should I plant with my land and budget?”**

The system combines an AI agent with a deterministic optimizer to calculate farm plans and explain them in Arabic.

**The optimizer calculates crop allocation and financial estimates. The AI explains the results.**

---

## Features

- Arabic conversational agricultural assistant
- Automatic comparison of supported crops
- Budget-aware crop allocation
- Balanced, highest-margin, and best-water-efficiency plans
- Estimated production and water consumption
- Estimated planning margin and remaining budget
- Market price comparison between Amman and Irbid
- Live weather information
- Conversation memory during the server session
- Dashboard and charts based on actual optimizer results

---

## How it works

```text
Farm information + user question
                ↓
        LangGraph AI agent
                ↓
   Crop, market, and weather tools
                ↓
       Deterministic optimizer
                ↓
      Calculated planning options
                ↓
    Arabic explanation + dashboard
```

The agent calls tools as needed. Dashboard values come from the optimizer’s actual output.

---

## Tech stack

| Layer | Technology |
|---|---|
| Backend and API | Python + Django |
| AI workflow | LangGraph |
| Language model | Google Gemini |
| Conversation memory | LangGraph MemorySaver |
| Frontend | Django templates, HTML, CSS, vanilla JavaScript |
| Charts | SVG and CSS using optimizer data |
| Session storage | SQLite through Django |
| Weather | Open-Meteo |
| Agricultural and market data | Local JSON files |

**One Django server runs the frontend, API, and existing AI agent.**

---

## Run locally

### 1. Install dependencies

Requires **Python 3.10 or newer**.

From the project folder:

```powershell
python -m pip install -r requirements.txt
```

### 2. Configure your Gemini key

Copy `.env.example` to `.env`:

```powershell
Copy-Item .env.example .env
```

Open `.env` and set:

```env
GEMINI_API_KEY=your_key_here
```

Keep your real `.env` private. It is excluded from Git.

### 3. Start the application

On Windows, double-click:

```text
START_MAZAREJO.bat
```

Or run from PowerShell:

```powershell
.\START_MAZAREJO.bat
```

Keep the terminal open. The browser opens automatically after the server passes its readiness checks.

Local address:

```text
http://127.0.0.1:8765/ar/
```

Internet access and available Gemini quota are required for AI requests.

---

## Using the demo

1. Enter the farm location, land area, and seasonal budget.
2. Optionally enter available water.
3. Choose a planning goal and optionally select crops.
4. Open the dashboard and ask for a farm plan.
5. Compare the calculated plans using the plan selector.

Land area must be a positive multiple of **10 dunums**, matching the current optimizer.

### Example question

> عندي 20 دونم وميزانيتي 10 آلاف دينار. بدي خطة توازن بين الهامش المالي واستهلاك المياه، وقارنلي أسعار محاصيل الخطة بين سوق عمّان وإربد.

The result can include:

- Crop allocation in dunums
- Expected production
- Estimated water consumption
- Estimated planning margin
- Total cost and remaining budget
- Market price comparison

Charts appear after an actual optimizer result is available.

---

## Water and weather handling

**Available water is optional.**

If left blank, the system can still calculate a plan and report its estimated water needs.

If provided, the amount is passed to the agent as farm context. The current optimizer **does not enforce an available-water limit**.

Live weather is supporting information. It does not currently change the optimizer’s calculations.

---

## Conversation memory and restarting

Each browser session uses a separate LangGraph conversation thread.

Conversation memory lasts while the server process is running.

To restart with a completely fresh demo:

1. Press **Ctrl+C** in the server terminal.
2. If prompted, enter **Y**.
3. Run `START_MAZAREJO.bat` again.
4. Refresh existing browser tabs.

A real restart clears farm setup, crop selections, chat history, dashboard results, weather results, and old browser drafts.

Opening the launcher while the server is already running reuses that process and does not reset it.

The **محادثة جديدة** button resets the conversation and results while keeping farm inputs during the same server run.

---

## Project structure

```text
Agent.py             Existing LangGraph agent
tools.py             Agricultural tools and optimizer
crop_resources.json  Crop reference data
market_prices.json   Market price snapshots

config/              Django configuration
dashboard/           API integration and page templates
static/              Frontend scripts, styles, and assets
tests/               Launcher and transformation tests

START_MAZAREJO.bat   Windows launcher
launch_demo.py       Startup and readiness checks
requirements.txt    Current application dependencies
```

The earlier `api.py`, `frontend/`, and `requirements-api.txt` prototype files are retained but are not used by the current Django launcher.

---

## Verification

```powershell
python manage.py check
python manage.py test dashboard
python -m unittest discover -s tests -p test_launcher.py
```

Integration tests exercise the existing compiled graph and real optimizer with the language model mocked.

---

## Important limitations

- Financial results are **estimated planning margins**, not guaranteed net profits.
- Market prices are dated reference snapshots.
- Production, water, and cost estimates depend on the available reference data.
- Large land areas and many crop candidates can make the current exhaustive optimizer slow.
- The local Django server is intended for demo use.

مزارع جو supports agricultural decision-making. Local conditions and expert judgment remain essential.

---

**From farm data to a clearer investment decision.**

### AI Quest 2026 🇯🇴
