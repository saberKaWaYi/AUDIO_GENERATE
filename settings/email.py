from pydantic import Field

from settings.base import EnvSettings


class EmailSettings(EnvSettings):

    smtp_host: str = Field(default="smtp.qq.com", alias="SMTP_HOST")
    smtp_port: int = Field(default=465, alias="SMTP_PORT")
    smtp_user: str = Field(default="", alias="SMTP_USER")
    smtp_password: str = Field(default="", alias="SMTP_PASSWORD")
    email_code_ttl_seconds: int = Field(default=300, alias="EMAIL_CODE_TTL_SECONDS")


email_settings = EmailSettings()
