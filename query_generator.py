import logging
from anthropic import Anthropic

logger = logging.getLogger(__name__)

class QueryGenerator:
    """Generates Python/SQLAlchemy queries using the Anthropic Claude API."""

    def __init__(self, api_key: str):
        if not api_key:
            raise ValueError("Anthropic API key is required.")
        self.client = Anthropic(api_key=api_key)

    def generate_query_code(self, ddl: str, user_request: str) -> str:
        """Sends database DDL and user request to Anthropic API to generate SQLAlchemy query code.

        Args:
            ddl: The PostgreSQL database schema (DDL).
            user_request: The plain-English query request.

        Returns:
            The extracted executable Python code string.
        """
        logger.info("Preparing prompt and requesting Python query code from Anthropic API.")
        
        prompt = f"""You are an expert Python data analyst. Given the following PostgreSQL database schema (DDL):

<database_ddl>
{ddl}
</database_ddl>

The user wants to perform this request:
<user_request>
{user_request}
</user_request>

Please write Python code using SQLAlchemy to execute the appropriate database query and retrieve the requested data.

Instructions:
1. **DO NOT RETURN** any connection string data, DB configuration data, env variable data, API key data, credentials.
2. Use the 'DATABASE_URL' environment variable (available in the environment) to connect to the database.
3. Formulate the query using SQLAlchemy (either raw text SQL or SQLAlchemy ORM/Expression constructs).
4. Store the final result in a variable named 'result'. The 'result' variable MUST be a valid, well-formed XML string representing the requested data (e.g., wrapping lists in tags like <data><item>...</item></data>, counts in <result><count>X</count></result>, etc.).
5. Do not include any print statements in the code block.
6. Provide ONLY the executable Python code block wrapped in ```python and ```. Do not output any other text or explanation.
"""

        try:
            message = self.client.messages.create(
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
            logger.error(f"Failed to generate query code from Anthropic API: {e}")
            raise
