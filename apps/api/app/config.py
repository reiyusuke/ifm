from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # DB
    # docker-compose.yml で host側は 5433 -> container 5432
    DATABASE_URL: str = "postgresql+psycopg://ifm:ifm@localhost:5433/ifm"

    # JWT（開発用のデフォルト。あとで必ず変更）
    JWT_SECRET: str = "dev-secret-change-me"
    JWT_ALG: str = "HS256"
    JWT_EXPIRES_MINUTES: int = 60 * 24  # 1 day


settings = Settings()
