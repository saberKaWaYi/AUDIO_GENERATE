import logging
import smtplib

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from google.auth.exceptions import GoogleAuthError

from app.auth import auth_bl
from app.auth.auth_req import EmailLoginRequest, GoogleLoginRequest, SendCodeRequest
from app.auth.auth_res import AuthConfigResponse, UserInfoResponse
from app.auth.auth_service import SESSION_COOKIE_NAME, sign_session
from app.auth.deps import get_current_user
from settings.auth import auth_settings
from settings.email import email_settings

logger = logging.getLogger(__name__)

router = APIRouter()


def _set_session_cookie(response: Response, user_id: int) -> None:
    token = sign_session(user_id)
    response.set_cookie(
        key=SESSION_COOKIE_NAME,
        value=token,
        httponly=True,
        secure=False,
        samesite="lax",
        max_age=auth_settings.session_ttl_seconds,
        path="/",
    )


@router.get(
    "/auth/config",
    response_model=AuthConfigResponse,
    summary="Get public auth config for the login page",
)
async def auth_config():
    smtp_configured = bool(
        email_settings.smtp_host.strip()
        and email_settings.smtp_user.strip()
        and email_settings.smtp_password.strip()
    )
    return AuthConfigResponse(
        google_client_id=auth_settings.google_client_id,
        email_enabled=smtp_configured,
    )


@router.post(
    "/auth/google",
    response_model=UserInfoResponse,
    summary="Log in with a Google ID token",
)
async def login_google(payload: GoogleLoginRequest, request: Request, response: Response):
    try:
        user = auth_bl.login_with_google(request.app.state.mongo, payload.credential)
    except GoogleAuthError:
        raise HTTPException(status_code=401, detail="Google 凭证无效")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        logger.error("google login failed: %s", e)
        raise HTTPException(status_code=500, detail="登录失败")

    _set_session_cookie(response, user.user_id)
    return UserInfoResponse(
        user_id=user.user_id,
        email=user.email,
        name=user.name,
        picture=user.picture,
    )


@router.post(
    "/auth/email/send-code",
    summary="Send a login verification code to the email",
)
async def send_email_code(payload: SendCodeRequest, request: Request):
    try:
        auth_bl.send_email_login_code(request.app.state.mongo, payload.email)
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except smtplib.SMTPException as e:
        logger.error("send email code failed: %s", e)
        raise HTTPException(status_code=502, detail="验证码邮件发送失败")
    except Exception as e:
        logger.error("send email code failed: %s", e)
        raise HTTPException(status_code=500, detail="发送验证码失败")
    return {"ok": True}


@router.post(
    "/auth/email/login",
    response_model=UserInfoResponse,
    summary="Log in with an email verification code",
)
async def login_email(payload: EmailLoginRequest, request: Request, response: Response):
    try:
        user = auth_bl.login_with_email(
            request.app.state.mongo, payload.email, payload.code
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        logger.error("email login failed: %s", e)
        raise HTTPException(status_code=500, detail="登录失败")

    _set_session_cookie(response, user.user_id)
    return UserInfoResponse(
        user_id=user.user_id,
        email=user.email,
        name=user.name,
        picture=user.picture,
    )


@router.get(
    "/auth/me",
    response_model=UserInfoResponse,
    summary="Get the current logged-in user",
)
async def me(user=Depends(get_current_user)):
    return UserInfoResponse(
        user_id=user.user_id,
        email=user.email,
        name=user.name,
        picture=user.picture,
    )


@router.post(
    "/auth/logout",
    summary="Log out and clear the session cookie",
)
async def logout(response: Response):
    response.delete_cookie(key=SESSION_COOKIE_NAME, path="/")
    return {"ok": True}
