from fastapi import APIRouter, Depends, Request, Form
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession
import os

from database import get_db
from controllers import (
    get_dashboard_data, get_users_list,
    handle_create_user, handle_reset_password,
    handle_assign_license, get_license_options,
    get_user_by_email, handle_delete_user
)

router = APIRouter()
templates = Jinja2Templates(
    directory=os.path.join(os.path.dirname(os.path.dirname(__file__)), "views")
)


# ── Dashboard ─────────────────────────────────────────────────────────────────

@router.get("/", response_class=HTMLResponse)
async def dashboard(request: Request, msg: str = "", cat: str = "", db: AsyncSession = Depends(get_db)):
    stats = await get_dashboard_data(db)
    return templates.TemplateResponse(request, "dashboard.html", {
        "request": request, "stats": stats, "msg": msg, "cat": cat
    })


# ── User Directory ────────────────────────────────────────────────────────────

@router.get("/users", response_class=HTMLResponse)
async def users(request: Request, msg: str = "", cat: str = "", db: AsyncSession = Depends(get_db)):
    all_users = await get_users_list(db)
    return templates.TemplateResponse(request, "users.html", {
        "request": request, "users": all_users, "msg": msg, "cat": cat
    })


# ── Create User ───────────────────────────────────────────────────────────────

@router.get("/users/create", response_class=HTMLResponse)
def create_user_get(request: Request, msg: str = "", cat: str = ""):
    return templates.TemplateResponse(request, "create_user.html", {
        "request": request, "msg": msg, "cat": cat
    })

@router.post("/users/create")
async def create_user_post(
    name:  str = Form(...),
    email: str = Form(...),
    role:  str = Form("Employee"),
    db: AsyncSession = Depends(get_db),
):
    return await handle_create_user(db, name, email, role)


# ── Manage User ───────────────────────────────────────────────────────────────

@router.get("/users/manage", response_class=HTMLResponse)
async def manage_user_get(request: Request, email: str, msg: str = "", cat: str = "", db: AsyncSession = Depends(get_db)):
    user = await get_user_by_email(db, email.strip().lower())
    if not user:
        from fastapi.responses import RedirectResponse
        return RedirectResponse(f"/users?msg=User not found&cat=error", status_code=303)
        
    licenses = get_license_options()
    return templates.TemplateResponse(request, "manage_user.html", {
        "request": request, "user": user, "licenses": licenses, "msg": msg, "cat": cat
    })

@router.post("/users/reset-password")
async def reset_password_post(
    email: str = Form(...),
    new_password: str = Form(None),
    db: AsyncSession = Depends(get_db)
):
    if not new_password:
        new_password = None
    return await handle_reset_password(db, email, new_password)


# ── Delete User ───────────────────────────────────────────────────────────────

@router.post("/users/delete")
async def delete_user_post(email: str = Form(...), db: AsyncSession = Depends(get_db)):
    return await handle_delete_user(db, email)

@router.post("/users/assign-license")
async def assign_license_post(email: str = Form(...), license: str = Form("None"), db: AsyncSession = Depends(get_db)):
    return await handle_assign_license(db, email, license)