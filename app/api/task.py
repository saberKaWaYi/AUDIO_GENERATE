from fastapi import APIRouter, HTTPException, Query, Request

from app.api.task_bl import create_task as create_task_bl
from app.api.task_bl import query_task as query_task_bl
from app.api.task_req import CreateTaskRequest
from app.api.task_res import CreateTaskResponse, TaskQueryResponse

import logging

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post(
    "/audio/tasks",
    response_model=CreateTaskResponse,
    summary="Create an audio generation task",
)
async def create_task(payload: CreateTaskRequest, request: Request):
    try:
        return create_task_bl(request.app.state.mongo, payload)
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
    user_id: int = Query(..., ge=1, description="提交者身份；别人的任务返回 404"),
):
    try:
        task = query_task_bl(request.app.state.mongo, task_id, user_id)
    except RuntimeError:
        raise HTTPException(status_code=503, detail="数据库未就绪")
    except Exception as e:
        logger.error("query audio task failed: %s", e)
        raise HTTPException(status_code=500, detail="任务查询失败")
    if task is None:
        raise HTTPException(status_code=404, detail=f"任务不存在：{task_id}")
    return task
