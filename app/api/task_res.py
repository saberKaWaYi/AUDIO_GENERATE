from datetime import datetime

from pydantic import BaseModel, Field

from models.schemas_task import TaskInfo, TaskResult, TaskStatus, TaskType


class CreateTaskResponse(BaseModel):

    task_id: str = Field(..., description="任务标识")
    status: TaskStatus = Field(..., description="任务状态")


class ReleaseTaskResponse(BaseModel):

    subtask_id: str = Field(..., description="子任务标识")
    status: TaskStatus = Field(..., description="放行后的状态")


class UpdateTextResponse(BaseModel):

    subtask_id: str = Field(..., description="子任务标识")
    status: TaskStatus = Field(..., description="修改后的状态")


class TaskListItem(BaseModel):

    task_id: str = Field(..., description="任务标识")
    title: str = Field(..., description="作品标题")
    status: TaskStatus = Field(..., description="任务状态")
    is_public: bool = Field(..., description="是否公开")
    create_time: datetime = Field(..., description="创建时间")


class TaskListResponse(BaseModel):

    items: list[TaskListItem] = Field(..., description="任务列表")


class TaskSubtaskResponse(BaseModel):

    subtask_id: str = Field(..., description="子任务标识")
    type: TaskType = Field(..., description="子任务类型")
    info: TaskInfo = Field(..., description="业务参数")
    status: TaskStatus = Field(..., description="子任务状态")
    result: TaskResult = Field(..., description="处理结果；未处理为空")
    create_time: datetime = Field(..., description="创建时间")
    update_time: datetime = Field(..., description="更新时间")
    is_public: bool = Field(False, description="是否公开展示")


class TaskQueryResponse(BaseModel):

    task_id: str = Field(..., description="任务标识")
    user_id: int = Field(..., description="提交者身份")
    status: TaskStatus = Field(..., description="任务状态")
    subtasks: list[TaskSubtaskResponse] = Field(..., description="该任务下的子任务")
    create_time: datetime = Field(..., description="创建时间")
    update_time: datetime = Field(..., description="更新时间")
    is_public: bool = Field(False, description="是否公开展示")
