# Generative Tool: Database Natural Language Query MCP Server

An interactive Model Context Protocol (MCP) server that translates plain English queries into SQLAlchemy operations, queries a PostgreSQL database under strict read-only execution modes, and returns the query results formatted as structured XML.

---

## 🌟 Key Features

- **Natural Language DB Querying:** Translate user queries in plain English to corresponding database results dynamically.
- **SQLAlchemy Table Reflection:** Reflects database schemas dynamically across multiple namespaces using standard ORM capabilities (no direct `pg_dump` client tools needed).
- **Enforced Read-Only Transactions:** Database URL connections are injected with query options (`?options=-c%20default_transaction_read_only%3Don`) to natively block any modifications (`CREATE`, `UPDATE`, `DELETE`, `DROP`) at the database engine level.
- **Dynamic XML Response Formatting:** Converts database records into a clean, well-formed XML structure automatically compiled by Claude.
- **FastMCP Protocol Integration:** Built on top of the standard `fastmcp` SDK to run as a local stdio MCP server.

---

## 🏗️ Architecture

```mermaid
graph TD
    User["User Request (Claude Desktop)"] -->|Query String| Server["main.py (FastMCP Server)"]
    Server -->|Read Config| Env[".env Config"]
    Server -->|Reflect Metadata| Database[("PostgreSQL Database")]
    Server -->|Request Query Script| Anthropic["Anthropic API (Claude)"]
    Anthropic -->|Returns Python Code| Server
    Server -->|Runs code under read-only transaction via exec()| Database
    Database -->|Query Results| Server
    Server -->|Outputs Structured XML| User
```

---

## 🛠️ Setup & Installation

### Prerequisites
- Python 3.13+
- [uv](https://github.com/astral-sh/uv) (fast Python package installer and resolver)
- PostgreSQL Server with an active database

### 1. Project Initialization & Dependencies
Initialize the project environment and install dependencies:
```bash
uv sync
```

### 2. Environment Configuration
Create a `.env` file in the root directory and configure the database URL along with your Anthropic API key:
```env
# Database connection for local development (enforced read-only mode via query options)
DATABASE_URL=postgresql://postgres:admin@localhost:5432/expence_db?options=-c%20default_transaction_read_only%3Don

# Anthropic API Key
ANTHROPIC_API_KEY="your-anthropic-api-key-here"
```

---

## 🚀 Running the Server

Start the stdio-based MCP server locally:
```bash
uv run python main.py
```

---

## 🔌 Integration with Claude Desktop

To configure Claude Desktop to use this database query tool on Windows, configure your `claude_desktop_config.json` file.

1. Press `Win + R`, type `%APPDATA%\Claude` and press Enter.
2. Open `claude_desktop_config.json` and insert the following server config:

```json
{
  "mcpServers": {
    "db-query-server": {
      "command": "uv",
      "args": [
        "--directory",
        "c:/Projects/generative-tool",
        "run",
        "python",
        "main.py"
      ]
    }
  }
}
```
3. Restart Claude Desktop. You will see the tools icon 🔌 in the chat input area.

---

## 📈 Usage Examples

Once connected, you can ask Claude queries like:
- *"Show a list of all tables in the database"*
- *"How many expense entries are recorded for AWS?"*
- *"Show a list of all rows in table exp_expence_core_t"*

The server returns results formatted as well-formed XML:
```xml
<data>
  <item>
    <exp_expence_core_id>26</exp_expence_core_id>
    <title>AWS Bill</title>
    <amount>100.00</amount>
  </item>
</data>
```
