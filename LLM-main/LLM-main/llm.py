import pandas as pd
import sqlite3
import re
from langchain_groq import ChatGroq

# Initialize the LLM API
llm = ChatGroq(
    model="mixtral-8x7b-32768",
    temperature=0,
    max_tokens=None,
    timeout=None,
    max_retries=2,
    groq_api_key='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',
)

# Function to load data from CSV to SQLite database
def load_excel_to_sql(excel_file, db_file):
    df = pd.read_csv(excel_file)
    with sqlite3.connect(db_file) as conn:
        df.to_sql('vehicle', conn, if_exists='replace', index=False)
    print(f"Data successfully loaded into {db_file}")


# Function to extract SQL query from generated response
def extract_sql_query(response):
    try:
        # Updated regex pattern to match complete SQL queries
        match = re.search(
            r"((SELECT|UPDATE|DELETE|INSERT INTO|CREATE TABLE|ALTER TABLE|DESCRIBE|DROP TABLE)\s+.*?;)",
            response,
            re.DOTALL | re.IGNORECASE
        )
        if match:
            sql_query = match.group(1).strip()  # Extract the full query
            return sql_query
        else:
            print(f"Response: {response}")
            print("Failed to extract SQL query.")
            return None
    except Exception as e:
        print(f"Error in extraction logic: {e}")
        return None


# Function to clean SQL query
def clean_sql_query(sql_query):
    sql_keywords = ["SELECT", "FROM", "WHERE", "UPDATE", "DELETE", "INSERT", "CREATE", "ALTER", "GROUP BY", "ORDER BY", "HAVING", "DROP", "TABLE"]

    cleaned_query = "\n".join([line for line in sql_query.splitlines() if any(keyword in line.upper() for keyword in sql_keywords)])

    if not cleaned_query.endswith(";"):
        cleaned_query += ";"

    return cleaned_query

# Function to provide the system prompt
def system_prompt():
    return '''
    You are a SQL query generator which takes input from the user and generates a query to provide the user with desired results.

    The table on which you will be working is called 'vehicle' and it has the following columns:
    id, region, price, year, manufacturer, model, fuel, odometer, transmission, size, type, state.

    When generating SQL queries:
    - For `DELETE`, ensure you specify a `WHERE` condition.
    - For `UPDATE`, include a `SET` clause to define the changes.
    - Always provide complete and syntactically correct SQL queries.
    - For `SELECT`, specify columns or use `*` for all columns.

    Example inputs and expected outputs:

    Input: Delete the vehicle with id 7313406529.
    Output: DELETE FROM vehicle WHERE id = 7313406529;

    Input: Update the price of the vehicle with id 7313406529 to 20000.
    Output: UPDATE vehicle SET price = 20000 WHERE id = 7313406529;

    Input: Select all details of the vehicle with id 7313406529.
    Output: SELECT * FROM vehicle WHERE id = 7313406529;

    Generate a valid SQLite SQL query based on the input provided. Do not include any explanation or additional text.
    Only output the SQL query.
    '''

# Function to generate SQL query using the ChatGroq API
def generate_sql_query(user_input):
    prompt = system_prompt() + user_input
    # response = llm.invoke(prompt)
    # sql_query = response.content
    # return sql_query

    try:
        response = llm.invoke(prompt)
        sql_query = extract_sql_query(response.content)
        
        if sql_query:
            sql_query = clean_sql_query(sql_query)
            return sql_query
        else:
            print("Failed to extract SQL query.")
            return None
    except Exception as e:
        print(f"Error generating SQL query: {e}")
        return None

# Function to execute SQL query and fetch results
def execute_sql_query(db_file, sql_query):
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()

    try:
        cursor.execute(sql_query)

        if sql_query.strip().upper().startswith("SELECT"):
            results = cursor.fetchall()
            if results:
                header = [description[0] for description in cursor.description]
                return pd.DataFrame(data=results, columns=header)
            else:
                return "No results found."
            
        elif sql_query.strip().upper().startswith("INSERT"):
            conn.commit()
            return "Data inserted successfully"
            
        elif sql_query.strip().upper().startswith(("UPDATE", "DELETE")):
            conn.commit()
            affected_rows = cursor.rowcount
            return f"{affected_rows} row(s) affected."
        
        elif sql_query.strip().upper().startswith("DROP"):
            return "Table deleted successfully"

        elif sql_query.strip().upper().startswith("ALTER"):
            return "Table altered successfully" 
        
        else:
            return "Query executed successfully."

    except sqlite3.Error as e:
        if "no such table: vehicle" == e:
            return "Table does not exists"
        else:
            print(f"An error occurred: {e}")
    finally:
        cursor.close()
        conn.close()

# Function to handle user input and generate results
def handle_user_input(user_input, db_file):
    sql_query = generate_sql_query(user_input)

    if sql_query:
        result = execute_sql_query(db_file, sql_query)
        return sql_query, result
    else:
        print("Failed to generate SQL query.")