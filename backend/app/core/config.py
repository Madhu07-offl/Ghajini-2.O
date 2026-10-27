from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    PROJECT_NAME: str = "Ghajini 2.0"
    API_V1_STR: str = "/v1"
    DATABASE_URL: str = "sqlite:///./ghajini.db"

    # Face engine thresholds
    FACE_T_HIGH: float = 0.50
    FACE_T_LOW: float = 0.38

    # Ollama settings
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "llama3.2:3b"
    OLLAMA_TEMPERATURE: float = 0.2
    OLLAMA_MAX_TOKENS: int = 120
    OLLAMA_TIMEOUT_SECONDS: float = 15.0

    # Data directories
    DATA_DIR: str = "./data"
    UPLOAD_DIR: str = "./data/uploads"

    # Default patient ID for single-patient mode
    DEFAULT_PATIENT_ID: int = 1

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    def init_directories(self) -> None:
        Path(self.DATA_DIR).mkdir(parents=True, exist_ok=True)
        Path(self.UPLOAD_DIR).mkdir(parents=True, exist_ok=True)


settings = Settings()
