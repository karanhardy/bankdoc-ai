from pathlib import Path

from dotenv import load_dotenv
from pydantic import BaseModel
import os

load_dotenv()

class Settings(BaseModel):
    app_name: str = os.getenv("APP_NAME", "BankDoc AI")
    environment: str = os.getenv("ENVIRONMENT", "development")

    bronze_path: Path = Path(os.getenv("BRONZE_PATH", "data/bronze"))
    silver_path: Path = Path(os.getenv("SILVER_PATH", "data/silver"))
    gold_path: Path = Path(os.getenv("GOLD_PATH", "data/gold"))

    sample_documents_path: Path = Path(os.getenv("SAMPLE_DOCUMENTS_PATH", "data/sample_documents"))

settings = Settings()
