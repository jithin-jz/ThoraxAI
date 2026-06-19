from functools import cached_property

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # MongoDB
    DATABASE_URL: str
    DB_NAME: str = "ai_xray_master"
    REDIS_URL: str = "redis://localhost:6379/0"

    # Email
    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""

    # WebAuthn
    RP_ID: str = "localhost"
    RP_NAME: str = "AI XRay App"
    ORIGIN: str = "http://localhost:5173"
    EXTRA_CORS_ORIGINS: str = (
        "https://thorax-ai-analyzer.web.app,"
        "https://thorax-ai-analyzer.firebaseapp.com,"
        "https://thoraxai.web.app"
    )

    # JWT Security
    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # Platform
    APP_NAME: str = "AI X-Ray Analyzer"
    API_VERSION: str = "v1"
    DEBUG: bool = False

    # Multi-tenancy (subdomain routing)
    BASE_DOMAIN: str = "localhost"
    # Production-safe defaults: https with no explicit port. Local dev overrides
    # these via backend/.env (TENANT_URL_SCHEME=http, TENANT_URL_PORT=5173).
    TENANT_URL_SCHEME: str = "https"
    TENANT_URL_PORT: str = ""
    RESERVED_SUBDOMAINS: str = (
        "www,api,app,admin,dashboard,mail,smtp,ftp,blog,docs,help,support,"
        "status,assets,static,cdn,auth,login,signup,register,public,health"
    )

    # File Storage
    STORAGE_BACKEND: str = "local"
    STORAGE_BUCKET: str = "xray-uploads"
    S3_ENDPOINT: str = ""
    S3_ACCESS_KEY: str = ""
    S3_SECRET_KEY: str = ""

    # Hugging Face Hub (cloud model & dataset storage)
    HF_TOKEN: str = ""  # Optional for public repos
    HF_MODEL_REPO: str = "jithinjz/xray-models"  # Where .pth weights are hosted
    HF_DATASET_REPO: str = "jithinjz/xray-chest-pneumonia"  # Where training zip is hosted

    # Groq LLM
    GROQ_API_KEY: str = ""
    GROQ_MODEL: str = "llama-3.3-70b-versatile"

    @field_validator("JWT_SECRET_KEY")
    @classmethod
    def jwt_secret_min_length(cls, v: str) -> str:
        if len(v) < 32:
            raise ValueError("JWT_SECRET_KEY must be at least 32 characters")
        return v

    @field_validator("BASE_DOMAIN")
    @classmethod
    def base_domain_not_empty(cls, v: str) -> str:
        v = v.strip().lower()
        if not v:
            raise ValueError("BASE_DOMAIN cannot be empty")
        return v

    @cached_property
    def reserved_subdomains_set(self) -> frozenset[str]:
        return frozenset(
            s.strip().lower() for s in self.RESERVED_SUBDOMAINS.split(",") if s.strip()
        )


settings = Settings()
