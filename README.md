# social-media-api
A FastAPI-based social media backend that supports user signup and login, database integration, and uploading and viewing posts with images and videos, paired with a basic Streamlit frontend.

## Configuration ✅

### Environment variables (.env)

- Copy the example file and set real credentials:
  - cp .env.example .env
  - Edit `.env` and set `DATABASE_URL` (example):
    - `DATABASE_URL=postgresql+asyncpg://user:pass@host:5432/dbname`
- The repository already includes `python-dotenv` in `requirements.txt`, and `.env` is listed in `.gitignore` so it won't be committed.
- Restart your app (e.g. stop/restart `uvicorn` or your container) to pick up changes.

### Optional: use Pydantic `BaseSettings` for robust configuration 🔧

- Benefits: type-checked settings, validation, default values, and a centralized place for configuration.
- Quick example (create `app/settings.py`):

```py
from pydantic import BaseSettings

class Settings(BaseSettings):
    DATABASE_URL: str

    class Config:
        env_file = ".env"

settings = Settings()
```

- Use it in code:

```py
from app.settings import settings
DATABASE_URL = settings.DATABASE_URL
```

- For production, prefer injecting environment variables via your deployment platform / secret manager rather than a `.env` file.
