from pydantic import BaseModel, Field


class InsertCharacterRequest(BaseModel):

    user_id: int = Field(..., ge=1, description="用户身份")
    reference_id: str = Field(..., min_length=1, description="Fish Audio 音色模型 ID")
