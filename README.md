# QueryMind — Text to SQL AI Agent

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white"/>
  <img src="https://img.shields.io/badge/Text--to--SQL-AI%20Agent-blueviolet?style=for-the-badge"/>
  <img src="https://img.shields.io/badge/Groq-LLaMA3.3-orange?style=for-the-badge"/>
  <img src="https://img.shields.io/badge/Plotly-Visualisation-3F4F75?style=for-the-badge&logo=plotly"/>
  <img src="https://img.shields.io/badge/Streamlit-UI-FF4B4B?style=for-the-badge&logo=streamlit"/>
</p>

> Ask questions about your data in plain English. QueryMind writes the SQL, executes it, shows the results as a table, generates a chart, and explains the answer — all automatically.

---

## Demo

![QueryMind Demo](demo.png)

---

## What It Does

```
You ask: "Which region has the highest total sales?"
            ↓
QueryMind generates SQL:
  SELECT region, SUM(total_amount) as total_sales
  FROM sales_data
  GROUP BY region
  ORDER BY total_sales DESC
  LIMIT 1
            ↓
Executes query on your data
            ↓
Shows: Table + Bar Chart + "North region has the highest sales at ₹4,15,000"
```

---

## Features

- Upload CSV files or SQLite databases
- Multiple CSV support — each becomes a table you can query
- AI generates accurate SQL from natural language
- Self-correcting — if SQL fails, agent retries with a fix
- Results shown as interactive table + auto chart
- SQL query always visible for transparency
- Query history for the session
- Sample dataset included to try immediately

---

## Tech Stack

| Component | Technology |
|---|---|
| LLM | Groq LLaMA 3.3 70B |
| SQL Generation | LangChain + Custom Prompts |
| Database | SQLite (in-memory) |
| Data Loading | Pandas |
| Visualisation | Plotly Express |
| UI | Streamlit |

---

## Setup

### 1. Clone the repo
```bash
git clone https://github.com/chhabralovish/querymind-text-to-sql.git
cd querymind-text-to-sql
```

### 2. Create virtual environment
```bash
python -m venv venv
venv\Scripts\activate        # Windows
source venv/bin/activate     # Mac/Linux
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Add API key
```bash
cp .env.example .env
# Add your GROQ_API_KEY
```

### 5. Run
```bash
streamlit run app.py
```

---

## Try It With Sample Data

A sample sales dataset is included at `sample_data/sales_data.csv`.

Upload it and try:
- *"Show total sales by category"*
- *"Which region has the highest revenue?"*
- *"Top 5 products by quantity sold"*
- *"What is the average order value?"*
- *"Show monthly sales trend"*
- *"How many orders were completed in January?"*

---

## Project Structure

```
querymind-text-to-sql/
│
├── app.py              # Streamlit UI
├── sql_agent.py        # Text-to-SQL logic + self-correction
├── db_utils.py         # CSV/SQLite loading + schema extraction
├── chart_utils.py      # Auto chart generation with Plotly
├── sample_data/
│   └── sales_data.csv  # Sample dataset to test with
├── requirements.txt
├── .env.example
└── README.md
```

---

## Author

**Lovish Chhabra** — Data Scientist & AI Engineer

[![LinkedIn](https://img.shields.io/badge/LinkedIn-Connect-0A66C2?style=flat-square&logo=linkedin)](https://www.linkedin.com/in/lovish-chhabra/)
[![GitHub](https://img.shields.io/badge/GitHub-Follow-181717?style=flat-square&logo=github)](https://github.com/chhabralovish)

---

## License

MIT License