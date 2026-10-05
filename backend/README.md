# ClientFlow API

The API is a synchronous FastAPI and SQLAlchemy application backed by PostgreSQL.

From this directory, install the project:

```powershell
python -m pip install -e ".[dev]"
```

Create or update the schema and seed the demo user:

```powershell
alembic upgrade head
python -m app.scripts.seed_demo_user
```

Both commands read `backend/.env`. The seed command is idempotent, so running it again does not create a duplicate user.

Start the API:

```powershell
uvicorn app.main:app --reload
```

Create a new migration after changing a model:

```powershell
alembic revision --autogenerate -m "describe the schema change"
```

Run the tests against PostgreSQL. The default `TEST_DATABASE_URL` points at a `clientflow_test`
database on the Docker Compose server and creates it when missing. Any override must name a
database ending in `_test`, because each run rebuilds its schema from the migrations:

```powershell
$env:TEST_DATABASE_URL = "postgresql+psycopg://clientflow:clientflow@localhost:5432/clientflow_test"
pytest
```
