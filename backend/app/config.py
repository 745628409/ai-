from pydantic import BaseModel
from dotenv import load_dotenv
import os

load_dotenv()


class Settings(BaseModel):
    app_name: str = "Novel2Screen API"
    openai_api_key: str = os.getenv("OPENAI_API_KEY", "")
    openai_base_url: str = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
    replicate_api_token: str = os.getenv("REPLICATE_API_TOKEN", "")
    replicate_base_url: str = os.getenv("REPLICATE_BASE_URL", "https://api.replicate.com/v1")
    mock_mode: bool = os.getenv("MOCK_MODE", "true").lower() == "true"
    backend_public_url: str = os.getenv("BACKEND_PUBLIC_URL", "http://localhost:8000")


settings = Settings()
