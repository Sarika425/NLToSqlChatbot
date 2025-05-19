import os
import psycopg2
import streamlit as st
import pandas as pd
import re

from langchain_community.chat_models import ChatOllama
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_community.chat_message_histories import StreamlitChatMessageHistory
from langchain_core.runnables.history import RunnableWithMessageHistory

#  Database Config 
# PostgreSQL config
DB_CONFIG = {
    "dbname": "custom",
    "user": "postgres",
    "password": os.getenv("DB_PASSWORD", "postgres"),
    "host": "localhost",
    "port": 5434,
}

#  DB Schema Reader 
def get_db_schema():
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()
    cur.execute("""
        SELECT table_name, column_name, data_type
        FROM information_schema.columns
        WHERE table_schema = 'public'
    """)
    schema = {}
    for table, column, dtype in cur.fetchall():
        schema.setdefault(table, []).append(f"{column} ({dtype})")
    cur.close()
    conn.close()
    return schema

#  Query Executor 
def run_sql_query(query):
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        cur.execute(query)
        rows = cur.fetchall()
        columns = [desc[0] for desc in cur.description]
        cur.close()
        conn.close()
        return pd.DataFrame(rows, columns=columns)
    except Exception as e:
        return pd.DataFrame([{"error": str(e)}])

# ------------------ LLM & Prompt Setup ------------------
llm = ChatOllama(model="llama3.2:3b")
schema_text = "\n".join([f"{t}: {', '.join(cols)}" for t, cols in get_db_schema().items()])

prompt = ChatPromptTemplate.from_messages([
    ("system", f"You are a helpful assistant that converts natural language to SQL using this schema:\n{schema_text}"),
    MessagesPlaceholder(variable_name="chat_history"),
    ("human", "{input}")
])

msg_history = StreamlitChatMessageHistory()

chain = RunnableWithMessageHistory(
    prompt | llm,
    lambda session_id: msg_history,
    input_messages_key="input",
    history_messages_key="chat_history"
)

# Streamlit App UI 
st.title("🧠 Natural Language → SQL (LLaMA + PostgreSQL)")
user_input = st.chat_input("Ask a question about your database...")

if user_input:
    response = chain.invoke({"input": user_input}, {"configurable": {"session_id": "user-session"}})

    #  Extract pure SQL from code block (or fallback to raw)
    sql_match = re.search(r"```sql\s*(.*?)```", response.content, re.DOTALL | re.IGNORECASE)
    generated_sql = sql_match.group(1).strip() if sql_match else response.content.strip()

    # Display chat
    st.chat_message("user").write(user_input)
    st.chat_message("assistant").write(f"```sql\n{generated_sql}\n```")

    # Run query and show results
    df = run_sql_query(generated_sql)
    if "error" in df.columns:
        st.error(df["error"].iloc[0])
    elif df.empty:
        st.info("No results found.")
    else:
        st.dataframe(df)

# Sidebar Chat History
if msg_history.messages:
    st.sidebar.subheader("💬 Chat History")
    for msg in msg_history.messages:
        st.sidebar.markdown(f"**{msg.type.capitalize()}**: {msg.content}")
