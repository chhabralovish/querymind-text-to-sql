import sqlite3
import re
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate


# ── SQL Generation Prompt ─────────────────────────────────────────────────────
SQL_PROMPT = ChatPromptTemplate.from_messages([
    ("system", """You are QueryMind, an expert SQL assistant.
Your job is to convert natural language questions into accurate SQLite SQL queries.

DATABASE SCHEMA:
{schema}

RULES:
- Write only valid SQLite SQL
- Use exact table and column names from the schema above
- Always use SELECT statements only — never INSERT, UPDATE, DELETE or DROP
- For aggregations use GROUP BY correctly
- For date/time use SQLite date functions
- Limit results to 100 rows maximum unless asked for more
- Return ONLY the SQL query — no explanation, no markdown, no backticks
- If the question cannot be answered from the schema, return: CANNOT_ANSWER
"""),
    ("human", "Question: {question}\n\nSQL Query:")
])


# ── Answer Generation Prompt ──────────────────────────────────────────────────
ANSWER_PROMPT = ChatPromptTemplate.from_messages([
    ("system", """You are QueryMind, a helpful data analyst.
Given a question, the SQL query used, and the query results, provide a clear, concise answer.
Focus on the key insight. Be specific with numbers. Keep it to 2-3 sentences max.
"""),
    ("human", """Question: {question}

SQL Query:
{sql}

Query Results (first 5 rows shown):
{results}

Answer:""")
])


class TextToSQLAgent:
    def __init__(self, groq_api_key: str):
        self.llm = ChatGroq(
            model="llama-3.3-70b-versatile",
            temperature=0,
            groq_api_key=groq_api_key
        )
        self.sql_chain = SQL_PROMPT | self.llm
        self.answer_chain = ANSWER_PROMPT | self.llm

    def generate_sql(self, question: str, schema: str) -> str:
        """Generate SQL query from natural language question."""
        response = self.sql_chain.invoke({
            "question": question,
            "schema": schema
        })
        sql = response.content.strip()

        # Clean up any accidental markdown
        sql = re.sub(r'```sql\s*', '', sql)
        sql = re.sub(r'```\s*', '', sql)
        sql = sql.strip()

        return sql

    def generate_answer(self, question: str, sql: str, results_str: str) -> str:
        """Generate natural language answer from SQL results."""
        response = self.answer_chain.invoke({
            "question": question,
            "sql": sql,
            "results": results_str
        })
        return response.content.strip()

    def run(self, question: str, schema: str, conn: sqlite3.Connection):
        """
        Full pipeline: question → SQL → execute → answer
        Returns dict with sql, dataframe, answer, error
        """
        # Step 1: Generate SQL
        sql = self.generate_sql(question, schema)

        if sql == "CANNOT_ANSWER":
            return {
                "sql": None,
                "dataframe": None,
                "answer": "I couldn't find relevant data in the database to answer this question. Try rephrasing or ask about the available columns.",
                "error": None
            }

        # Step 2: Execute SQL
        from db_utils import execute_query
        df, error = execute_query(conn, sql)

        if error:
            # Try to self-correct once
            correction_prompt = f"""The following SQL query failed with error: {error}

Failed SQL: {sql}

Schema:
{schema}

Please write a corrected SQL query for the question. Return ONLY the SQL query."""

            corrected = self.llm.invoke(correction_prompt).content.strip()
            corrected = re.sub(r'```sql\s*', '', corrected)
            corrected = re.sub(r'```\s*', '', corrected).strip()

            df, error2 = execute_query(conn, corrected)
            if error2:
                return {
                    "sql": sql,
                    "dataframe": None,
                    "answer": f"I generated a SQL query but it failed to execute. Error: {error}",
                    "error": error
                }
            sql = corrected

        if df is None or df.empty:
            return {
                "sql": sql,
                "dataframe": df,
                "answer": "The query executed successfully but returned no results.",
                "error": None
            }

        # Step 3: Generate natural language answer
        results_preview = df.head(5).to_string(index=False)
        answer = self.generate_answer(question, sql, results_preview)

        return {
            "sql": sql,
            "dataframe": df,
            "answer": answer,
            "error": None
        }