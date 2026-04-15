from fastapi import APIRouter, Request, Form
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
import os

from panel.controllers import (
    get_dashboard_data, get_users_list,
    handle_create_user, handle_reset_password,
    handle_assign_license, get_license_options,
)

router = APIRouter()
templates = Jinja2Templates(
    directory=os.path.join(os.path.dirname(os.path.dirname(__file__)), "views")
)


# ── Dashboard ─────────────────────────────────────────────────────────────────

@router.get("/", response_class=HTMLResponse)
def dashboard(request: Request, msg: str = "", cat: str = ""):
    stats = get_dashboard_data()
    return templates.TemplateResponse("dashboard.html", {
        "request": request, "stats": stats, "msg": msg, "cat": cat
    })


# ── User Directory ────────────────────────────────────────────────────────────

@router.get("/users", response_class=HTMLResponse)
def users(request: Request, msg: str = "", cat: str = ""):
    all_users = get_users_list()
    return templates.TemplateResponse("users.html", {
        "request": request, "users": all_users, "msg": msg, "cat": cat
    })


# ── Create User ───────────────────────────────────────────────────────────────

@router.get("/users/create", response_class=HTMLResponse)
def create_user_get(request: Request, msg: str = "", cat: str = ""):
    return templates.TemplateResponse("create_user.html", {
        "request": request, "msg": msg, "cat": cat
    })

@router.post("/users/create")
def create_user_post(
    name:  str = Form(...),
    email: str = Form(...),
    role:  str = Form("Employee"),
):
    return handle_create_user(name, email, role)


# ── Reset Password ────────────────────────────────────────────────────────────

@router.get("/users/reset-password", response_class=HTMLResponse)
def reset_password_get(request: Request, msg: str = "", cat: str = ""):
    return templates.TemplateResponse("reset_password.html", {
        "request": request, "msg": msg, "cat": cat
    })

@router.post("/users/reset-password")
def reset_password_post(email: str = Form(...)):
    return handle_reset_password(email)


# ── Assign License ────────────────────────────────────────────────────────────

@router.get("/users/assign-license", response_class=HTMLResponse)
def assign_license_get(request: Request, msg: str = "", cat: str = ""):
    licenses = get_license_options()
    return templates.TemplateResponse("assign_license.html", {
        "request": request, "licenses": licenses, "msg": msg, "cat": cat
    })

@router.post("/users/assign-license")
def assign_license_post(email: str = Form(...), license: str = Form("None")):
    return handle_assign_license(email, license)