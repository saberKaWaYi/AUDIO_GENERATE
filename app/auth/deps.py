from fastapi import HTTPException, Request

from app.auth.auth_service import SESSION_COOKIE_NAME, decode_session, get_user


def get_current_user(request: Request):
    token = request.cookies.get(SESSION_COOKIE_NAME)
    if not token:
        raise HTTPException(status_code=401, detail="未登录")
    try:
        user_id = decode_session(token)
    except Exception:
        raise HTTPException(status_code=401, detail="会话无效")
    user = get_user(request.app.state.mongo, user_id)
    if user is None:
        raise HTTPException(status_code=401, detail="用户不存在")
    return user
