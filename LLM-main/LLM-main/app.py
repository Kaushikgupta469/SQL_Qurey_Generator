import streamlit as st
from llm import load_excel_to_sql, handle_user_input

# Initialize session state for messages and database loaded flag
if "messages" not in st.session_state:
    st.session_state.messages = []

if "db_loaded" not in st.session_state:
    st.session_state.db_loaded = False

excel_file = "vehicle.csv"
db_file = "vehicle.db"

# Load database only once in a session
if not st.session_state.db_loaded:
    load_excel_to_sql(excel_file, db_file)
    st.session_state.db_loaded = True  # Mark as loaded

# Apply custom CSS for fixed header
st.markdown(
    """
    <style>
    .fixed-header {
        position: fixed;
        top: 0;
        width: 100%;
        background-color: #0E1117;
        padding: 10px;
        z-index: 100;
        display: flex;
        justify-content: space-between;
        align-items: center;
    }
    .header-content {
        display: flex;
        justify-content: flex-start;
        align-items: center;
    }
    .header-content h2 {
        margin-right: 10px;
        margin-bottom: 0;
    }
    .main-content {
        margin-top: 80px; /* Adjust this value to push content below the fixed header */
    }
    footer {visibility: hidden;} /* Hide Streamlit footer */
    header {visibility: hidden;} /* Hide Streamlit top-right bar */
    </style>
    """,
    unsafe_allow_html=True
)

# Fixed header HTML
header_html = """
    <div class="fixed-header">
        <div class="header-content">
            <h2>SQL Query Generator</h2>
        </div>
    </div>
"""
st.markdown(header_html, unsafe_allow_html=True)

# Main content container
st.markdown('<div class="main-content">', unsafe_allow_html=True)

for message in st.session_state.get('messages', []):
    with st.chat_message(message["role"]):

        if message["role"] == "user":
            st.markdown(message["content"])
            
        elif message["role"] == "assistant":
            st.write("Query:")
            st.code(message["query"])
            st.write("Result:")
            st.dataframe(message["result"])

# Handle new user input
if user_input := st.chat_input("Message "):
    st.session_state.messages.append({"role": "user", "content": user_input})

    with st.chat_message("user"):
        st.markdown(user_input)

    with st.chat_message("assistant"):
        query, result = handle_user_input(user_input, db_file)

        # Display query and result
        st.write("Query:")
        st.code(query)
        st.write("Result:")
        st.dataframe(result)

        # Store query and result in session state
        st.session_state.messages.append({
            "role": "assistant",
            "query": query,
            "result": result  # Store as a dictionary
        })

st.markdown('</div>', unsafe_allow_html=True)
