import streamlit as st
import pandas as pd
import os
from dotenv import load_dotenv
from db_utils import (
    load_csv_to_sqlite, load_sqlite_db,
    get_schema_info, get_sample_data
)
from sql_agent import TextToSQLAgent
from chart_utils import auto_chart

load_dotenv()

# ── Page Config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="QueryMind — Text to SQL Agent",
    page_icon="🔍",
    layout="wide"
)

# ── Header ────────────────────────────────────────────────────────────────────
st.title("QueryMind")
st.caption("Ask questions about your data in plain English. AI writes the SQL, executes it, and visualises the results.")
st.divider()

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.header("Configuration")

    groq_api_key = st.text_input(
        "Groq API Key",
        type="password",
        placeholder="Enter your Groq API key",
        value=os.getenv("GROQ_API_KEY", "")
    )

    st.divider()
    st.header("Load Data")

    data_source = st.radio(
        "Choose data source:",
        ["Upload CSV", "Upload SQLite DB"]
    )

    conn = None
    table_names = []
    schema_info = ""

    if data_source == "Upload CSV":
        uploaded_files = st.file_uploader(
            "Upload CSV file(s)",
            type=["csv"],
            accept_multiple_files=True,
            help="Upload one or more CSV files — each becomes a table"
        )

        if uploaded_files:
            try:
                import sqlite3
                conn = sqlite3.connect(":memory:")
                table_names = []

                for f in uploaded_files:
                    _, tname, df = load_csv_to_sqlite(f, ":memory:")
                    df.to_sql(tname, conn, if_exists='replace', index=False)
                    table_names.append(tname)

                schema_info = get_schema_info(conn, table_names)
                st.success(f"Loaded {len(table_names)} table(s): {', '.join(table_names)}")

            except Exception as e:
                st.error(f"Error loading CSV: {str(e)}")

    else:
        db_file = st.file_uploader(
            "Upload SQLite database",
            type=["db", "sqlite", "sqlite3"],
            help="Upload an existing SQLite database file"
        )

        if db_file:
            try:
                conn, table_names = load_sqlite_db(db_file)
                schema_info = get_schema_info(conn, table_names)
                st.success(f"Loaded {len(table_names)} table(s): {', '.join(table_names)}")
            except Exception as e:
                st.error(f"Error loading database: {str(e)}")

    if conn and table_names:
        st.divider()
        st.markdown("**Tables loaded:**")
        for t in table_names:
            st.markdown(f"- `{t}`")

        with st.expander("View Schema"):
            st.code(schema_info)

        with st.expander("Sample Data"):
            selected_table = st.selectbox("Select table", table_names)
            sample = get_sample_data(conn, selected_table)
            st.dataframe(sample, use_container_width=True)

    st.divider()
    st.markdown("Built by [Lovish Chhabra](https://www.linkedin.com/in/lovish-chhabra/)")

# ── Main Area ─────────────────────────────────────────────────────────────────
if not groq_api_key:
    st.info("Enter your Groq API key in the sidebar to get started.")
    st.stop()

if not conn or not table_names:
    st.info("Upload a CSV or SQLite database in the sidebar to get started.")

    with st.expander("Don't have data? Use our sample dataset"):
        st.markdown("""
        Download the sample sales data from the repo:
        `sample_data/sales_data.csv`

        Or try questions like:
        - *"Show total sales by category"*
        - *"Which region has the highest revenue?"*
        - *"Top 5 customers by order value"*
        """)
    st.stop()

# Initialise agent
if "agent" not in st.session_state or st.session_state.get("agent_key") != groq_api_key:
    st.session_state["agent"] = TextToSQLAgent(groq_api_key)
    st.session_state["agent_key"] = groq_api_key
    st.session_state["history"] = []

# ── Chat Interface ─────────────────────────────────────────────────────────────
st.subheader("Ask a question about your data")

# Example questions
with st.expander("Example questions to try"):
    cols = st.columns(2)
    examples = [
        "How many rows are in the dataset?",
        "Show the top 5 records by value",
        "What is the average value per category?",
        "Count records grouped by each category",
        "Show total by month",
        "Which entry has the highest value?"
    ]
    for i, ex in enumerate(examples):
        with cols[i % 2]:
            if st.button(ex, key=f"ex_{i}"):
                st.session_state["question_input"] = ex

# Question input
question = st.chat_input("Ask anything about your data...")

if question:
    # Display user message
    with st.chat_message("user"):
        st.markdown(question)

    # Run agent
    with st.chat_message("assistant"):
        with st.spinner("Thinking and writing SQL..."):
            try:
                result = st.session_state["agent"].run(
                    question=question,
                    schema=schema_info,
                    conn=conn
                )

                # Show natural language answer
                st.markdown(f"**Answer:** {result['answer']}")

                # Show SQL query
                if result["sql"]:
                    with st.expander("View SQL Query", expanded=True):
                        st.code(result["sql"], language="sql")

                # Show results table
                if result["dataframe"] is not None and not result["dataframe"].empty:
                    st.markdown(f"**Results** ({len(result['dataframe'])} rows)")
                    st.dataframe(
                        result["dataframe"],
                        use_container_width=True,
                        height=min(400, 35 * len(result["dataframe"]) + 38)
                    )

                    # Auto chart
                    fig = auto_chart(result["dataframe"], question)
                    if fig:
                        st.plotly_chart(fig, use_container_width=True)

                elif result["error"]:
                    st.error(f"Error: {result['error']}")

                # Save to history
                st.session_state["history"].append({
                    "question": question,
                    "sql": result["sql"],
                    "answer": result["answer"]
                })

            except Exception as e:
                st.error(f"Error: {str(e)}")

# ── Query History ─────────────────────────────────────────────────────────────
if st.session_state.get("history"):
    st.divider()
    st.subheader("Query History")
    for i, h in enumerate(reversed(st.session_state["history"][-5:])):
        with st.expander(f"Q: {h['question'][:60]}..."):
            st.markdown(f"**Answer:** {h['answer']}")
            if h["sql"]:
                st.code(h["sql"], language="sql")

    if st.button("Clear History"):
        st.session_state["history"] = []
        st.rerun()