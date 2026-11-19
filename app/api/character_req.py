from pydantic import BaseModel, Field


class InsertCharacterRequest(BaseModel):

    reference_id: str = Field(..., min_length=1, description="Fish Audio 音色模型 ID")
