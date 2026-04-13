from fastapi.responses import RedirectResponse, HTMLResponse
from fastapi import Request, status
from app.dependencies.auth import IsUserLoggedIn, get_current_user, is_admin, AuthDep
from app.dependencies.session import SessionDep
from . import router, templates


@router.get("/", response_class=RedirectResponse)
async def index_view(
    request: Request,
    user_logged_in: IsUserLoggedIn,
    db: SessionDep
):
    if user_logged_in:
        user = await get_current_user(request, db)
        if await is_admin(user):
            return RedirectResponse(url=request.url_for('admin_home_view'), status_code=status.HTTP_303_SEE_OTHER)
        return RedirectResponse(url=request.url_for('user_home_view'), status_code=status.HTTP_303_SEE_OTHER)
    response = RedirectResponse(url=request.url_for('login_view'), status_code=status.HTTP_303_SEE_OTHER)
    response.delete_cookie(
        key="access_token", 
        httponly=True,
        samesite="none",
        secure=True
    )
    return response

@router.get("/routines/new", response_class=HTMLResponse)
async def create_routine_view(request: Request, user: AuthDep):
    return templates.TemplateResponse(
        request=request,
        name="create-routine.html",
        context={"user": user}
    )

@router.get("/routines", response_class=HTMLResponse)
async def routines_view(request: Request, user: AuthDep):
    return templates.TemplateResponse(
        request=request,
        name="routines.html",
        context={"user": user}
    )


@router.get("/routines/{routine_id}", response_class=HTMLResponse)
async def routine_detail_view(request: Request, user: AuthDep, routine_id: int):
    return templates.TemplateResponse(
        request=request,
        name="routine-detail.html",
        context={"user": user, "routine_id": routine_id}
    )