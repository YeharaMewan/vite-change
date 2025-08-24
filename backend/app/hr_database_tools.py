import os
from datetime import datetime
from langchain.tools import tool
from dotenv import load_dotenv
from sqlalchemy import text, inspect
from sqlalchemy.engine import Engine
import sqlparse
from langchain_openai import ChatOpenAI

from .database import SessionLocal, engine
from . import models

load_dotenv()

# --- Helper Function to get DB Schema ---
def get_db_schema(engine: Engine) -> str:
    """Retrieves the schema of the database for the LLM's context."""
    inspector = inspect(engine)
    schema_info = []
    table_names = inspector.get_table_names()
    # Filter out pgvector and other system tables
    filtered_tables = [name for name in table_names if not name.startswith('pg_') and not name.startswith('vector_')]
    for table_name in filtered_tables:
        columns = [f"{col['name']}({col['type']})" for col in inspector.get_columns(table_name)]
        schema_info.append(f"Table '{table_name}': {', '.join(columns)}")
    return "\n".join(schema_info)

# --- Security Helper Function ---
def is_read_only_query(sql_query: str) -> bool:
    """Checks if the query is a safe, read-only SELECT statement."""
    clean_query = sql_query.strip().upper()
    # Basic check for query type
    if not clean_query.startswith("SELECT"):
        return False
    # More robust check using sqlparse
    parsed = sqlparse.parse(sql_query)
    stmt = parsed[0]
    return stmt.get_type() == 'SELECT'

# --- HR Database Tools ---
@tool
def answer_database_question(natural_language_query: str) -> str:
    """
    Use this SUPER tool to answer any general, open-ended questions about employees, attendance, leaves, or departments from the database.
    This tool is very powerful and can translate a user's natural language question into a SQL query and execute it.
    Provide the user's complete original question as the input.
    Examples: 'who was present on August 4th 2025?', 'how many people work in the IT/Rise AI department?', 'show me all leave requests for Thavindu', 'මේ මාසයේ පැමිණීමේ විස්තර'.
    """
    db_schema = get_db_schema(engine)
    sql_generation_llm = ChatOpenAI(model="gpt-4o", temperature=0)
    
    # Few-shot examples
    few_shot_examples = """
    Here are some example questions and their corresponding SQL queries:
    
    Question: list all employees from the GAMES/RamStudios department
    SQL: SELECT e.name FROM employees e JOIN departments d ON e.department_id = d.id WHERE d.name ILIKE '%GAMES/RamStudios%';

    Question: who took a lieu leave on 2025-08-04?
    SQL: SELECT e.name FROM employees e JOIN attendances a ON e.id = a.employee_id WHERE a.attendance_date = '2025-08-04' AND a.status ILIKE 'Lieu leave';

    Question: what is the total leave balance for Kamal?
    SQL: SELECT b.total_days, b.days_used, (b.total_days - b.days_used) AS remaining_days FROM leave_balances b JOIN employees e ON b.employee_id = e.id WHERE e.name ILIKE '%Kamal%';
    """

    # SQL generation prompt
    sql_prompt_text = f"""
    You are a PostgreSQL expert. Your task is to write a single, safe, read-only SQL query to answer a user's question based on the provided database schema.
    
    Database Schema:
    {db_schema}

    Instructions:
    - Today's date is {datetime.now().strftime('%Y-%m-%d')}. Use this to resolve relative date questions like "this month" or "last week".
    - For string comparisons on names or statuses, ALWAYS use `ILIKE` for case-insensitivity.
    - If a user asks about a department, you MUST JOIN the `employees` and `departments` tables.
    - If a user asks about attendance, you MUST JOIN the `employees` and `attendances` tables.
    - ONLY generate a single `SELECT` statement. Do not generate any other SQL command.
    - Do not add any explanation or markdown formatting around the SQL.
    
    {few_shot_examples}

    User Question: "{natural_language_query}"
    SQL Query:
    """
    
    generated_sql = sql_generation_llm.invoke(sql_prompt_text).content.strip()
    print(f"--- Generated SQL: {generated_sql} ---")

    if not is_read_only_query(generated_sql):
        return "Error: An invalid or unsafe query was generated. I cannot proceed with this request."
        
    with SessionLocal() as db:
        try:
            result = db.execute(text(generated_sql))
            rows = result.fetchall()
            if not rows:
                return "I looked into the database, but couldn't find any information matching your request."
            
            column_names = result.keys()
            result_list = [dict(zip(column_names, row)) for row in rows]
            
            # Synthesis
            synthesis_llm = ChatOpenAI(model="gpt-4o", temperature=0.1)
            synthesis_prompt = f"""
            You are a helpful assistant. Your task is to present database results to a user in a clear and friendly manner.
            Use the same language as the original question (Sinhala or English).

            **Formatting Rules:**
            - For lists of items with a single column (like a list of names or departments), ALWAYS use a Markdown bulleted list (using '*' or '-').
            - If the data has multiple columns (e.g., name and email), ALWAYS format it as a Markdown table.
            - Begin your response with a brief, friendly introductory sentence.
            - Do not just show the raw data structure.

            Original Question: "{natural_language_query}"
            
            Retrieved Data:
            {result_list}

            Friendly Answer (in Markdown format):
            """
            final_answer = synthesis_llm.invoke(synthesis_prompt).content
            return final_answer

        except Exception as e:
            print(f"--- SQL Execution Error: {e} ---")
            return f"I encountered an error while trying to fetch the data. It seems there's a problem with the generated query: {e}"

@tool
def list_all_departments() -> str:
    """
    Use this tool when a user asks for a list of all available departments.
    This tool is fast and efficient for listing all department names.
    """
    with SessionLocal() as db:
        try:
            departments = db.query(models.Department.name).all()
            if not departments:
                return "No departments found in the database."
            department_names = [name for (name,) in departments]
            return f"Here are all the departments: {department_names}"
        except Exception as e:
            return f"An error occurred while fetching departments: {e}"

@tool
def list_all_employees() -> str:
    """
    Use this tool when a user asks for a list of all employees in the company.
    This tool is fast and efficient for listing all employee names.
    """
    with SessionLocal() as db:
        try:
            employees = db.query(models.Employee.name).all()
            if not employees:
                return "No employees found in the database."
            employee_names = [name for (name,) in employees]
            return f"Here are all the employees: {employee_names}"
        except Exception as e:
            return f"An error occurred while fetching employees: {e}"

@tool
def get_employee_details(employee_name: str) -> str:
    """
    Get detailed information about a specific employee including their department, role, contact information.
    """
    with SessionLocal() as db:
        try:
            employee = db.query(models.Employee).filter(
                models.Employee.name.ilike(f"%{employee_name}%")
            ).first()
            
            if not employee:
                return f"Employee '{employee_name}' not found in the database."
            
            dept_name = employee.department.name if employee.department else "Not assigned"
            
            details = {
                "name": employee.name,
                "email": employee.email,
                "role": employee.role or "Not specified",
                "department": dept_name,
                "phone": employee.phone_number or "Not provided",
                "status": "Active" if employee.is_active else "Inactive"
            }
            
            return f"""Employee Details for {employee.name}:
- **Email:** {details['email']}
- **Role:** {details['role']}
- **Department:** {details['department']}
- **Phone:** {details['phone']}
- **Status:** {details['status']}"""
            
        except Exception as e:
            return f"An error occurred while fetching employee details: {e}"

# Export all database tools
database_tools = [
    answer_database_question,
    list_all_departments,
    list_all_employees,
    get_employee_details
]