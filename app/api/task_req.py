from pydantic import BaseModel, Field

from models.schemas_task import TaskLanguage, TaskType


class CreateTaskRequest(BaseModel):

    user_id: int = Field(..., ge=1, description="用户身份")
    type: TaskType = Field(..., description="任务类型：ASMR_TEXT / ASMR_BACKEND_MUSIC")
    title: str = Field(..., min_length=1, description="作品标题")
    reference_ids: list[str] = Field(..., min_length=1, description="参与角色 ID")
    theme: str = Field(..., min_length=1, description="详细创作主题")
    duration_minutes: int = Field(..., ge=1, description="目标时长（分钟）")
    language: TaskLanguage = Field(..., description="语言：zh / ja / en / ko")
