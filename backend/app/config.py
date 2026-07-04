from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    GEMINI_API_KEY: str = ""
    GROQ_API_KEY: str = ""
    XAI_API_KEY: str = ""

    GEMINI_RPM_LIMIT: int = 8
    GEMINI_RPD_LIMIT: int = 200
    GROQ_RPM_LIMIT: int = 25
    GROQ_RPD_LIMIT: int = 10000

    DATABASE_URL: str = "sqlite:///./data/app.db"
    REDIS_URL: str = "redis://redis:6379/0"

    UPLOAD_DIR: str = "./data/uploads"
    OUTPUT_DIR: str = "./data/outputs"
    FIXED_TOPIC_LIST_PATH: str = ""

    class Config:
        env_file = ".env"

settings = Settings()
