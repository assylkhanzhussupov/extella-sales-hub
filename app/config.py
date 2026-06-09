from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    telegram_bot_token: str = ""
    b24_webhook: str = ""
    supabase_url: str = ""
    supabase_key: str = ""          # anon key
    supabase_service_key: str = ""  # service_role key
    app_env: str = "development"
    secret_key: str = ""
    admin_email: str = "assylkhan.zhussupov@gmail.com"

    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()
