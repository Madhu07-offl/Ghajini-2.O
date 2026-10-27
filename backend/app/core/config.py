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

    # Whisper settings
    WHISPER_MODEL: str = "small"

    # Feature flags & Alerts
    FEATURE_PUSH: bool = False
    FEATURE_SMS: bool = False
    TWILIO_ACCOUNT_SID: str = ""
    TWILIO_AUTH_TOKEN: str = ""
    TWILIO_FROM_NUMBER: str = ""
    CAREGIVER_PHONE: str = "+919876543210"

    # Privacy controls
    STORE_PHOTOS: bool = False  # Do not store raw recognition photos unless true

    # Reminder & Escalation settings
    ESCALATE_AFTER_MIN: int = 10
    QUIET_HOURS_START: int = 22  # 10:00 PM
    QUIET_HOURS_END: int = 6    # 06:00 AM

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
