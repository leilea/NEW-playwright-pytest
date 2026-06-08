from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    database_url: str = "postgresql+asyncpg://app:app@localhost:5432/dsep_test"
    jwt_secret: str = "dev-only-change-me-32-bytes-min-aaaa"
    jwt_alg: str = "HS256"
    jwt_ttl_min: int = 480
    cors_origins: str = "http://localhost:5173"
    bootstrap_admin_email: str = "admin@local"
    bootstrap_admin_password: str = "admin123"
    log_dir: str = "logs"
    allure_results_dir: str = "allure-results"

    @property
    def cors_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


settings = Settings()
