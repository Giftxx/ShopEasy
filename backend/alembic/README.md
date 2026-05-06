Use Alembic from the `backend/` directory:

```bash
python -m alembic revision --autogenerate -m "init schema"
python -m alembic upgrade head
```
