# Thoughtswap
Allows educators (facilitators) to create channels where they post prompts that participants respond to. Participants join a channel by entering its channel code.
Every response is anonymous to both participants and facilitators.

## How it works
* **Facilitators** create channels from the **Manage** page, each with a name and a channel code. In their own channels they can post new prompts, close submissions, view and save responses, show all responses to the room, or send a random response to each connected user.
* **Participants** pick a channel on the home page, enter its code, and submit responses to the current prompt.
* Choose your role (facilitator or participant) when you sign up.
* Prompts and responses update live over WebSockets (Django Channels).

## Running locally
Requires Python 3.12.

1. Clone the repo and create a virtual environment:
   ```bash
   git clone https://github.com/rryyii/t-swap.git
   cd t-swap
   python -m venv .venv
   ```
   Activate it with `.venv\Scripts\activate` (Windows) or `source .venv/bin/activate` (macOS/Linux).

2. Install the dependencies:
   ```bash
   pip install -r requirements/local.txt
   ```

3. Choose a database. By default the app connects to a local PostgreSQL database named `base_347_example`. To use SQLite instead, set `DATABASE_URL`:
   ```bash
   # macOS/Linux
   export DATABASE_URL=sqlite:///db.sqlite3
   # Windows PowerShell
   $env:DATABASE_URL = "sqlite:///db.sqlite3"
   ```
   Or put `DATABASE_URL=sqlite:///db.sqlite3` in a `.env` file in the project root, which is loaded automatically.

4. Create the tables and start the server:
   ```bash
   python manage.py migrate
   python manage.py runserver
   ```
   Open http://127.0.0.1:8000. Running `python manage.py createsuperuser` also gives you access to the admin.

### Redis (optional)
Locally, the live updates use an in-memory channel layer, so Redis isn't needed. To use Redis, set `REDIS_URL` (e.g. `redis://127.0.0.1:6379/0`) and the app switches to the Redis channel layer. Production always uses Redis.

## Running the tests
```bash
pytest
```
