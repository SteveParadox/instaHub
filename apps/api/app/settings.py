from pydantic_settings import BaseSettings, SettingsConfigDict
class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file="../../.env", extra="ignore")
    environment: str = "development"
    database_url: str = "postgresql+psycopg://instahub:instahub@localhost:5432/instahub"
    redis_url: str = "redis://localhost:6379/0"
    supabase_jwt_secret: str = ""
    web_origin: str = "http://localhost:3000"
settings = Settings()
