# 🌱 مزارع جو | Muzare3 JO

**AI decision agent for agricultural investment in Jordan.**
 
مزارع جو helps farm owners make better decisions about:

- 🌾 What crops to plant
- 💧 Water consumption
- 💰 Budget allocation
- 📈 Estimated financial margin
- 🏪 Market prices in Amman and Irbid

Built for **AI Quest 2026**.

---

## What is مزارع جو?

Most agricultural assistants answer questions like:

> "How do I grow tomatoes?"

مزارع جو focuses on a different question:

> **"What should I plant with the land, budget and water I have?"**

The system combines agricultural data with an AI agent and a deterministic optimizer to generate a practical farm investment plan.

The LLM does not invent the crop allocation. The optimizer calculates it, and the AI explains the result in Arabic.

---

## Features

- Arabic AI agricultural decision agent
- Automatic crop comparison
- Budget-aware crop planning
- Water-efficiency comparison
- Balanced plan vs highest-margin plan
- Live weather information
- Amman and Irbid market comparison
- Conversation memory
- Interactive dashboard and charts
- Designed around Jordanian agricultural data

---

## How it works

```text
Farmer Question
      ↓
AI Agent
      ↓
Weather + Crop Data + Market Data
      ↓
Mathematical Optimizer
      ↓
Recommended Farm Plan
      ↓
Arabic Explanation + Dashboard
```

---

## Tech Stack

- Python
- Django
- LangGraph
- Gemini
- JavaScript
- HTML / CSS
- Open-Meteo
- Jordan agricultural market data

---

## Run the project

### 1. Install dependencies

```powershell
pip install -r requirements.txt
```

### 2. Create `.env`

Copy:

```text
.env.example
```

to:

```text
.env
```

Then add:

```env
GEMINI_API_KEY=your_key_here
```

### 3. Start مزارع جو

On Windows, run:

```text
START_MAZAREJO.bat
```

The application will open automatically in your browser.

The final application runs through one Django server.

---

## Example Question

> عندي 100 دونم وميزانيتي 45 ألف دينار، وما بعرف شو أزرع. بدي أفضل خطة توازن بين الربح واستهلاك المياه، وقارنلي الأسعار بين سوق عمّان وإربد.

مزارع جو can compare available crops and produce:

- Land allocation
- Estimated production
- Water consumption
- Estimated planning margin
- Remaining budget
- Market price comparison

---

## Important Note

The financial result is an **estimated planning margin**, not guaranteed net profit.

Current market prices are reference snapshots, and production costs are reference values.

---

## Goal

مزارع جو is not designed to replace agricultural experts.

Its goal is to help farm owners and agricultural investors combine:

**land + water + capital + crops + markets**

into one actionable decision.

---

### AI Quest 2026 🇯🇴
