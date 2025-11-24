import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    PROJECT_NAME: str = "Autonomous Data Analyst Agent"
    GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./test.db")
    FRONTEND_ORIGINS: str = os.getenv("FRONTEND_ORIGINS", "*")

    @property
    def allowed_origins(self) -> list[str]:
        origins = [origin.strip() for origin in self.FRONTEND_ORIGINS.split(",") if origin.strip()]
        return origins or ["*"]

settings = Settings()
