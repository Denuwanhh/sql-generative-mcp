import logging
import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from anthropic import Anthropic
from db_config import DBConfig
from fastmcp import FastMCP

# Configure standard logging to stderr since the MCP server communicates via stdio (stdout)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stderr)]
)
logger = logging.getLogger(__name__)

# Load environment variables on startup
current_dir = Path(__file__).resolve().parent
env_path = current_dir / ".env"
if not env_path.exists():
    env_path = Path(".env")
if env_path.exists():
    load_dotenv(dotenv_path=env_path)
else:
    logger.warning(".env file not found, relying on system environment variables.")

# Initialize FastMCP Server
mcp = FastMCP("Database Natural Language Query Server")

def get_anthropic_code(ddl: str, user_request: str) -> str:
    """Send DDL and request to Anthropic API to generate query Python code."""
    logger.info("Preparing prompt and requesting Python query code from Anthropic API.")
    
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        logger.error("ANTHROPIC_API_KEY is not defined in the environment variables.")
        raise ValueError("ANTHROPIC_API_KEY is missing.")
        
    client = Anthropic(api_key=api_key)
    
    prompt = f"""You are an expert Python data analyst. Given the following PostgreSQL database schema (DDL):

{ddl}

The user wants to perform this request:
"{user_request}"

Please write Python code using SQLAlchemy to execute the appropriate database query and retrieve the requested data.

Instructions:
1. Use the 'DATABASE_URL' environment variable (available in the environment) to connect to the database.
2. Formulate the query using SQLAlchemy (either raw text SQL or SQLAlchemy ORM/Expression constructs).
3. Store the final result in a variable named 'result'. The 'result' variable MUST be a valid, well-formed XML string representing the requested data (e.g., wrapping lists in tags like <data><item>...</item></data>, counts in <result><count>X</count></result>, etc.).
4. Do not include any print statements in the code block.
5. Provide ONLY the executable Python code block wrapped in ```python and ```. Do not output any other text or explanation.
"""

    try:
        message = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=4000,
            temperature=0.0,
            system="You only output valid Python code blocks wrapped in ```python and ```.",
            messages=[
                {"role": "user", "content": prompt}
            ]
        )
        response_text = message.content[0].text
        logger.info("Successfully received response from Anthropic API.")
        
        # Extract python code block
        if "```python" in response_text:
            code = response_text.split("```python")[1].split("```")[0].strip()
        elif "```" in response_text:
            code = response_text.split("```")[1].split("```")[0].strip()
        else:
            code = response_text.strip()
            
        logger.info("Python code block extracted successfully.")
        return code
    except Exception as e:
        logger.error(f"Failed to communicate with Anthropic API or parse the response: {e}")
        raise

def run_python_code(code: str, database_url: str) -> any:
    """Execute the generated python script using exec()."""
    logger.info("Executing the generated Python query code using exec().")
    
    # Setup standard global context including database_url
    global_context = {
        "__builtins__": __builtins__,
        "os": os,
        "sys": sys,
    }
    
    # We execute in a local context to retrieve variables defined by the script
    local_context = {}
    
    try:
        # Pre-import sqlalchemy for convenience
        import sqlalchemy
        global_context["sqlalchemy"] = sqlalchemy
        
        exec(code, global_context, local_context)
        
        if "result" not in local_context:
            logger.warning("The executed script did not define a 'result' variable.")
            return None
            
        logger.info("Execution completed successfully.")
        return local_context["result"]
    except Exception as e:
        logger.error(f"Error during execution of the generated Python code: {e}")
        logger.debug(f"Code attempted:\n{code}")
        raise

@mcp.tool()
def query_database(user_query: str) -> str:
    """Run a plain-English natural language query against the connected database and return the result as structured XML.

    Args:
        user_query: The database query request in plain English (e.g. 'Show a list of all expense items').
    """
    logger.info(f"MCP Tool 'query_database' called with query: '{user_query}'")
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        logger.error("DATABASE_URL is missing in the environment.")
        return "<error>DATABASE_URL is not set in server environment variables</error>"
        
    try:
        # Step 2: Get DB DDL using DBConfig
        logger.info("Extracting database DDL structure.")
        db_config = DBConfig(database_url)
        ddl_string = db_config.get_db_ddl()
        
        # Step 3: Request the python query code from LLM
        query_code = get_anthropic_code(ddl_string, user_query)
        
        # Step 4: Run the code
        result = run_python_code(query_code, database_url)
        return str(result)
    except Exception as e:
        logger.error(f"Error executing natural language query: {e}")
        return f"<error>{str(e)}</error>"

if __name__ == "__main__":
    logger.info("Starting Database Query MCP Server...")
    mcp.run()
