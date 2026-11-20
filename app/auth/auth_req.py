from pydantic import BaseModel, Field


class GoogleLoginRequest(BaseModel):

    credential: str = Field(min_length=1, description="Google ID token")


class SendCodeRequest(BaseModel):

    email: str = Field(min_length=1, description="登录邮箱")


class EmailLoginRequest(BaseModel):

    email: str = Field(min_length=1, description="登录邮箱")
    code: str = Field(min_length=1, description="邮箱验证码")
