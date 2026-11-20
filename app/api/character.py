from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, Request, UploadFile
from pydantic import ValidationError

from app.api.character_bl import (
    create_character as create_character_bl,
    insert_character as insert_character_bl,
    list_characters as list_characters_bl,
)
from app.api.character_req import InsertCharacterRequest
from app.api.character_res import (
    CreateCharacterResponse,
    InsertCharacterResponse,
    CharacterListResponse,
)
from app.auth.deps import get_current_user
from services.fish_audio_service import (
    FishAudioError,
    FishAudioNotFoundError,
    FishAudioConfigError,
)

import logging

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post(
    "/audio/characters",
    response_model=InsertCharacterResponse,
    summary="Insert a character",
)
async def insert_character(payload: InsertCharacterRequest, request: Request, user=Depends(get_current_user)):
    try:
        return insert_character_bl(request.app.state.mongo, request.app.state.fish, user.user_id, payload)
    except ValidationError:
        raise HTTPException(status_code=502, detail="上游角色数据结构异常")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except FishAudioNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except FishAudioConfigError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except FishAudioError as e:
        raise HTTPException(status_code=502, detail=str(e))
    except RuntimeError:
        raise HTTPException(status_code=503, detail="数据库未就绪")
    except Exception as e:
        logger.error("insert character failed: %s", e)
        raise HTTPException(status_code=500, detail="角色插入失败")


@router.post(
    "/audio/characters/create",
    response_model=CreateCharacterResponse,
    summary="Create a character from uploaded audio",
)
async def create_character(
    request: Request,
    title: str = Form(...),
    voices: list[UploadFile] = File(...),
    cover_image: UploadFile | None = File(None),
    description: str | None = Form(None),
    duration_seconds: float = Form(...),
    user=Depends(get_current_user),
):
    try:
        voices_payload = [
            (item.filename, await item.read(), item.content_type or "application/octet-stream")
            for item in voices
        ]
        cover_payload = None
        if cover_image is not None:
            cover_payload = (
                cover_image.filename,
                await cover_image.read(),
                cover_image.content_type or "application/octet-stream",
            )
        return create_character_bl(
            request.app.state.mongo,
            request.app.state.fish,
            user.user_id,
            title,
            voices_payload,
            cover_payload,
            description,
            duration_seconds,
        )
    except ValidationError:
        raise HTTPException(status_code=502, detail="上游角色数据结构异常")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except FishAudioConfigError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except FishAudioError as e:
        raise HTTPException(status_code=502, detail=str(e))
    except RuntimeError:
        raise HTTPException(status_code=503, detail="数据库未就绪")
    except Exception as e:
        logger.error("create character failed: %s", e)
        raise HTTPException(status_code=500, detail="角色创建失败")


@router.get(
    "/audio/characters",
    response_model=CharacterListResponse,
    summary="List characters",
)
async def list_characters(
    request: Request,
    user=Depends(get_current_user),
    page: int = Query(1, ge=1, description="页码，从 1 开始"),
    page_size: int = Query(10, ge=1, le=50, description="每页条数，最多 50"),
    keyword: str | None = Query(None, description="名称模糊匹配"),
    tag: str | None = Query(None, description="标签精确匹配"),
    state: str | None = Query(None, description="状态精确匹配"),
    reference_id: str | None = Query(None, description="角色 ID 精确匹配"),
):
    try:
        return list_characters_bl(
            request.app.state.mongo,
            user.user_id,
            page,
            page_size,
            keyword,
            tag,
            state,
            reference_id,
        )
    except RuntimeError:
        raise HTTPException(status_code=503, detail="数据库未就绪")
    except Exception as e:
        logger.error("list characters failed: %s", e)
        raise HTTPException(status_code=500, detail="角色查询失败")
