from pydantic import BaseModel, Field


class GoogleLoginRequest(BaseModel):

    credential: str = Field(min_length=1, description="Google ID token")
