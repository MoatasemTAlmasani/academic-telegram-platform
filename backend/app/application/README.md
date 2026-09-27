# Application layer

Use cases belong here. They orchestrate domain objects and depend on
interfaces from `ports.py`; they should not depend directly on FastAPI,
aiogram, SQLAlchemy sessions, or Redis clients.