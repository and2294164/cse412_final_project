# CSE 412 Final Project — Music Library

Flask frontend for the CSE 412 music library project (Phase 3). Currently uses mock data; PostgreSQL integration is planned for a later phase.

## Setup

**Prerequisites:** Python 3.9+

```bash

# 0. Create a new PostgreSQL database. (Default title musicdb, but the name doesn't matter)

Either use PgAdmin or psql.

# 1. Create and activate a virtual environment
python3 -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

# 2. Set env variables
Create a .env file with the following values (change as needed):
DB_HOST="localhost"
DB_NAME="musicdb"
DB_USERNAME="postgres"
DB_PASSWORD="password"
DB_PORT="5432"

# 3. Install dependencies
pip install -r requirements.txt

# 4. Run the development server
python app.py
```

The app runs at `http://localhost:5001` by default (port 5000 is reserved by macOS AirPlay).

To use a different port:

```bash
FLASK_PORT=8080 python app.py
```

## Mock credentials

| Username    | Password      |
|-------------|---------------|
| `jdoe`      | `pass123`     |
| `asmith`    | `music4life`  |
| `mjohnson`  | `vinyl99`     |
| `kwilliams` | `beats2024`   |
| `lbrown`    | `sound_wave`  |

You can also register a new account from the UI (stored in memory only, resets on restart).

