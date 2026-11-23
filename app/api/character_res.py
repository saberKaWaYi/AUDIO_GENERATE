from datetime import datetime

from pydantic import BaseModel, Field


class CharacterResponse(BaseModel):

    user_id: int = Field(..., description="用户身份")
    reference_id: str = Field(..., description="Fish Audio 音色模型 ID")
    title: str = Field(..., description="角色名称")
    description: str = Field(..., description="角色描述")
    cover_image: str = Field(..., description="封面图")
    type: str = Field(..., description="模型类型")
    train_mode: str = Field(..., description="训练模式")
    state: str = Field(..., description="模型状态")
    visibility: str = Field(..., description="可见性")
    tags: list[str] = Field(..., description="标签")
    languages: list[str] = Field(..., description="语言")
    default_text: str = Field(..., description="默认示例文本")
    source: str | None = Field(..., description="来源")
    created_at: str = Field(..., description="上游创建时间")
    updated_at: str = Field(..., description="上游更新时间")
    create_time: datetime = Field(..., description="入库时间")
    update_time: datetime = Field(..., description="更新时间")
    is_public: bool = Field(False, description="是否公开展示")


class InsertCharacterResponse(BaseModel):

    reference_id: str = Field(..., description="角色 ID")
    title: str = Field(..., description="角色名称")
    created: bool = Field(..., description="是否新建")
    update_time: datetime = Field(..., description="更新时间")


class CreateCharacterResponse(BaseModel):

    reference_id: str = Field(..., description="角色 ID")
    title: str = Field(..., description="角色名称")
    state: str = Field(..., description="模型状态")
    visibility: str = Field(..., description="可见性")
    cover_image: str = Field(..., description="封面图地址")
    created: bool = Field(..., description="是否新建")
    update_time: datetime = Field(..., description="更新时间")


class DeleteCharacterResponse(BaseModel):

    reference_id: str = Field(..., description="角色 ID")
    deleted: bool = Field(..., description="是否已删除")


class CharacterListResponse(BaseModel):

    total: int = Field(..., description="总数")
    page: int = Field(..., description="页码")
    page_size: int = Field(..., description="每页条数")
    items: list[CharacterResponse] = Field(..., description="当前页角色")


class WorkResponse(BaseModel):

    work_id: str = Field(..., description="作品 ID")
    work_type: str = Field(..., description="音频类型")
    title: str = Field(..., description="音色名称")
    cover_image: str = Field(..., description="音色封面")
    text: str = Field(..., description="生成文本")
    file_size: int = Field(..., description="文件字节数")
    is_public: bool = Field(..., description="是否公开")
    create_time: datetime = Field(..., description="入库时间")


class WorkListResponse(BaseModel):

    items: list[WorkResponse] = Field(..., description="作品列表")
