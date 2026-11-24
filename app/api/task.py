from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response

from app.api.task_bl import create_task as create_task_bl
from app.api.task_bl import delete_task as delete_task_bl
from app.api.task_bl import get_task_audio as get_task_audio_bl
from app.api.task_bl import list_tasks as list_tasks_bl
from app.api.task_bl import query_task as query_task_bl
from app.api.task_bl import refresh_task as refresh_task_bl
from app.api.task_bl import release_task as release_task_bl
from app.api.task_bl import release_tasks_batch as release_tasks_batch_bl
from app.api.task_bl import set_task_public as set_task_public_bl
from app.auth.deps import get_current_user
from app.api.task_req import BatchReleaseRequest, CreateTaskRequest
from app.api.task_res import BatchReleaseResponse, CreateTaskResponse, ReleaseTaskResponse, TaskListResponse, TaskListItem, TaskQueryResponse

import logging

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get(
    "/audio/tasks",
    response_model=TaskListResponse,
    summary="List my audio generation tasks",
)
async def list_tasks(request: Request, user=Depends(get_current_user)):
    try:
        docs = list_tasks_bl(request.app.state.mongo, user.user_id)
        items = [
            TaskListItem(
                task_id=doc["task_id"],
                title=doc["info"]["title"],
                type=doc["type"],
                status=doc["status"],
                is_public=doc["is_public"],
                create_time=doc["create_time"],
            )
            for doc in docs
        ]
        return TaskListResponse(items=items)
    except RuntimeError:
        raise HTTPException(status_code=503, detail="数据库未就绪")
    except Exception as e:
        logger.error("list audio tasks failed: %s", e)
        raise HTTPException(status_code=500, detail="任务列表查询失败")


@router.post(
    "/audio/tasks",
    response_model=CreateTaskResponse,
    summary="Create an audio generation task",
)
async def create_task(payload: CreateTaskRequest, request: Request, user=Depends(get_current_user)):
    try:
        return create_task_bl(request.app.state.mongo, user.user_id, payload)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except RuntimeError:
        raise HTTPException(status_code=503, detail="数据库未就绪")
    except Exception as e:
        logger.error("create audio task failed: %s", e)
        raise HTTPException(status_code=500, detail="任务下发失败")


@router.get(
    "/audio/tasks/{task_id}",
    response_model=TaskQueryResponse,
    summary="Query a task and its subtasks",
)
async def query_task(
    task_id: str,
    request: Request,
    user=Depends(get_current_user),
):
    try:
        task = query_task_bl(request.app.state.mongo, task_id, user.user_id)
    except RuntimeError:
        raise HTTPException(status_code=503, detail="数据库未就绪")
    except Exception as e:
        logger.error("query audio task failed: %s", e)
        raise HTTPException(status_code=500, detail="任务查询失败")
    if task is None:
        raise HTTPException(status_code=404, detail=f"任务不存在：{task_id}")
    return task


@router.get(
    "/audio/tasks/{subtask_id}/audio",
    summary="Download a generated ASMR subtask audio",
)
async def download_subtask_audio(
    subtask_id: str,
    request: Request,
    user=Depends(get_current_user),
):
    try:
        result = get_task_audio_bl(request.app.state.mongo, user.user_id, subtask_id)
    except RuntimeError:
        raise HTTPException(status_code=503, detail="数据库未就绪")
    except Exception as e:
        logger.error("download subtask audio failed: %s", e)
        raise HTTPException(status_code=500, detail="音频读取失败")
    if result is None:
        raise HTTPException(status_code=404, detail="子任务音频不存在")
    file_name, audio = result
    return Response(
        content=audio,
        media_type="audio/mpeg",
        headers={
            "Content-Disposition": f'attachment; filename="{file_name}"',
            "Cache-Control": "no-store",
        },
    )


@router.post(
    "/audio/tasks/{subtask_id}/release",
    response_model=ReleaseTaskResponse,
    summary="Release a debug subtask to pending",
)
async def release_task_route(
    subtask_id: str,
    request: Request,
    user=Depends(get_current_user),
):
    try:
        task = release_task_bl(request.app.state.mongo, user.user_id, subtask_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except RuntimeError:
        raise HTTPException(status_code=503, detail="数据库未就绪")
    except Exception as e:
        logger.error("release audio task failed: %s", e)
        raise HTTPException(status_code=500, detail="任务放行失败")
    if task is None:
        raise HTTPException(status_code=404, detail=f"子任务不存在：{subtask_id}")
    return task


@router.post(
    "/audio/tasks/{subtask_id}/refresh",
    response_model=ReleaseTaskResponse,
    summary="Refresh a finished GENERATE subtask to pending",
)
async def refresh_task_route(
    subtask_id: str,
    request: Request,
    user=Depends(get_current_user),
):
    try:
        task = refresh_task_bl(request.app.state.mongo, user.user_id, subtask_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except RuntimeError:
        raise HTTPException(status_code=503, detail="数据库未就绪")
    except Exception as e:
        logger.error("refresh audio task failed: %s", e)
        raise HTTPException(status_code=500, detail="任务刷新失败")
    if task is None:
        raise HTTPException(status_code=404, detail=f"子任务不存在：{subtask_id}")
    return task


@router.post(
    "/audio/tasks/batch-release",
    response_model=BatchReleaseResponse,
    summary="Release debug subtasks of a given type in batch",
)
async def batch_release_tasks_route(
    payload: BatchReleaseRequest,
    request: Request,
    user=Depends(get_current_user),
):
    try:
        released = release_tasks_batch_bl(
            request.app.state.mongo, user.user_id, payload.task_id, payload.type
        )
    except RuntimeError:
        raise HTTPException(status_code=503, detail="数据库未就绪")
    except Exception as e:
        logger.error("batch release audio tasks failed: %s", e)
        raise HTTPException(status_code=500, detail="批量放行失败")
    return BatchReleaseResponse(task_id=payload.task_id, type=payload.type, released=released)


@router.patch(
    "/audio/tasks/{task_id}/public",
    summary="Toggle whether a task is public",
)
async def toggle_task_public(
    task_id: str,
    request: Request,
    is_public: bool = Query(..., description="是否公开"),
    user=Depends(get_current_user),
):
    try:
        updated = set_task_public_bl(request.app.state.mongo, user.user_id, task_id, is_public)
    except RuntimeError:
        raise HTTPException(status_code=503, detail="数据库未就绪")
    except Exception as e:
        logger.error("toggle task public failed: %s", e)
        raise HTTPException(status_code=500, detail="公开状态更新失败")
    if not updated:
        raise HTTPException(status_code=404, detail="任务不存在")
    return {"task_id": task_id, "is_public": is_public}


@router.delete(
    "/audio/tasks/{task_id}",
    summary="Delete an audio generation task",
)
async def delete_task_route(
    task_id: str,
    request: Request,
    user=Depends(get_current_user),
):
    try:
        deleted = delete_task_bl(request.app.state.mongo, user.user_id, task_id)
    except RuntimeError:
        raise HTTPException(status_code=503, detail="数据库未就绪")
    except Exception as e:
        logger.error("delete task failed: %s", e)
        raise HTTPException(status_code=500, detail="任务删除失败")
    if not deleted:
        raise HTTPException(status_code=404, detail="任务不存在")
    return {"task_id": task_id, "deleted": True}
