from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response

from app.api.character_bl import delete_work, get_work_audio, list_works, set_work_public
from app.api.character_res import WorkListResponse
from app.auth.deps import get_current_user

import logging

logger = logging.getLogger(__name__)

router = APIRouter()


def _to_response(doc: dict) -> dict:
    return {
        "work_id": doc["work_id"],
        "work_type": doc["work_type"],
        "title": doc["title"],
        "cover_image": doc["cover_image"],
        "text": doc["text"],
        "file_size": doc["file_size"],
        "is_public": doc["is_public"],
        "create_time": doc["create_time"],
    }


@router.get(
    "/audio/works/mine",
    response_model=WorkListResponse,
    summary="List my generated audio works",
)
async def list_my_works(
    request: Request,
    user=Depends(get_current_user),
):
    try:
        docs = list_works(request.app.state.mongo, {"user_id": user.user_id, "is_deleted": False})
        return WorkListResponse(items=[_to_response(doc) for doc in docs])
    except RuntimeError:
        raise HTTPException(status_code=503, detail="数据库未就绪")
    except Exception as e:
        logger.error("list my works failed: %s", e)
        raise HTTPException(status_code=500, detail="作品查询失败")


@router.get(
    "/audio/works/public",
    response_model=WorkListResponse,
    summary="List public audio works",
)
async def list_public_works(
    request: Request,
    user=Depends(get_current_user),
):
    try:
        docs = list_works(
            request.app.state.mongo,
            {"work_type": "tts", "is_public": True, "is_deleted": False},
        )
        return WorkListResponse(items=[_to_response(doc) for doc in docs])
    except RuntimeError:
        raise HTTPException(status_code=503, detail="数据库未就绪")
    except Exception as e:
        logger.error("list public works failed: %s", e)
        raise HTTPException(status_code=500, detail="公开作品查询失败")


@router.patch(
    "/audio/works/{work_id}/public",
    summary="Toggle whether a work is public",
)
async def toggle_work_public(
    work_id: str,
    request: Request,
    is_public: bool = Query(..., description="是否公开"),
    user=Depends(get_current_user),
):
    try:
        updated = set_work_public(request.app.state.mongo, user.user_id, work_id, is_public)
    except RuntimeError:
        raise HTTPException(status_code=503, detail="数据库未就绪")
    except Exception as e:
        logger.error("toggle work public failed: %s", e)
        raise HTTPException(status_code=500, detail="公开状态更新失败")
    if not updated:
        raise HTTPException(status_code=404, detail="作品不存在")
    return {"work_id": work_id, "is_public": is_public}


@router.delete(
    "/audio/works/{work_id}",
    summary="Delete a generated audio work",
)
async def delete_work_route(
    work_id: str,
    request: Request,
    user=Depends(get_current_user),
):
    try:
        deleted = delete_work(request.app.state.mongo, user.user_id, work_id)
    except RuntimeError:
        raise HTTPException(status_code=503, detail="数据库未就绪")
    except Exception as e:
        logger.error("delete work failed: %s", e)
        raise HTTPException(status_code=500, detail="作品删除失败")
    if not deleted:
        raise HTTPException(status_code=404, detail="作品不存在")
    return {"work_id": work_id, "deleted": True}


@router.get(
    "/audio/works/{work_id}/audio",
    summary="Download an audio work",
)
async def download_work(
    work_id: str,
    request: Request,
    public_only: bool = Query(False, description="仅允许读取已公开作品"),
    user=Depends(get_current_user),
):
    try:
        result = get_work_audio(request.app.state.mongo, work_id, user.user_id, public_only)
    except RuntimeError:
        raise HTTPException(status_code=503, detail="数据库未就绪")
    except Exception as e:
        logger.error("get work audio failed: %s", e)
        raise HTTPException(status_code=500, detail="音频读取失败")
    if result is None:
        raise HTTPException(status_code=404, detail="作品不存在")
    file_name, audio = result
    return Response(
        content=audio,
        media_type="audio/mpeg",
        headers={
            "Content-Disposition": f'attachment; filename="{file_name}"',
            "Cache-Control": "no-store",
        },
    )
