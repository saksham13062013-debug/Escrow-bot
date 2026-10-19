from fastapi import FastAPI, Request, Form, Depends, HTTPException, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import ADMIN_SECRET
from database import (
    get_stats, get_all_deals, get_deal, get_active_deals, get_all_users,
    get_banned_users, update_deal_status, delete_deal, set_deal_payment,
    get_fee, set_fee, get_setting, set_setting, ban_user, unban_user, is_maintenance
)

app = FastAPI(title="MM Escrow Admin", docs_url=None, redoc_url=None)
app.add_middleware(SessionMiddleware, secret_key=ADMIN_SECRET)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "templates"))


def require_login(request: Request):
    if not request.session.get("logged_in"):
        raise HTTPException(status_code=status.HTTP_303_SEE_OTHER, headers={"Location": "/login"})
    return True


@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request, "error": None})


@app.post("/login")
async def login(request: Request, secret: str = Form(...)):
    if secret == ADMIN_SECRET:
        request.session["logged_in"] = True
        return RedirectResponse("/", status_code=303)
    return templates.TemplateResponse("login.html", {"request": request, "error": "Invalid secret"})


@app.get("/logout")
async def logout(request: Request):
    request.session.clear()
    return RedirectResponse("/login", status_code=303)


@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request, _: bool = Depends(require_login)):
    stats = await get_stats()
    fee = await get_fee()
    maint = await is_maintenance()
    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "stats": stats,
        "fee": fee,
        "maintenance": maint
    })


@app.get("/deals", response_class=HTMLResponse)
async def deals_page(request: Request, _: bool = Depends(require_login)):
    deals = await get_all_deals(80)
    return templates.TemplateResponse("deals.html", {"request": request, "deals": deals})


@app.get("/deals/{deal_id}", response_class=HTMLResponse)
async def deal_detail(request: Request, deal_id: int, _: bool = Depends(require_login)):
    deal = await get_deal(deal_id)
    if not deal:
        return RedirectResponse("/deals", status_code=303)
    return templates.TemplateResponse("deal_detail.html", {"request": request, "deal": deal})


@app.post("/deals/{deal_id}/action")
async def deal_action(
    request: Request, deal_id: int,
    action: str = Form(...),
    payment_details: str = Form(None),
    payment_note: str = Form(None),
    _: bool = Depends(require_login)
):
    deal = await get_deal(deal_id)
    if not deal:
        return RedirectResponse("/deals", status_code=303)

    if action == "set_payment" and payment_details:
        await set_deal_payment(deal_id, payment_details, payment_note)
        await update_deal_status(deal_id, "payment_set")
    elif action == "confirm":
        await update_deal_status(deal_id, "paid")
    elif action == "release":
        await update_deal_status(deal_id, "completed", "Released via web panel")
    elif action == "refund":
        await update_deal_status(deal_id, "refunded", "Refunded via web panel")
    elif action == "dispute":
        await update_deal_status(deal_id, "disputed")
    elif action == "cancel":
        await update_deal_status(deal_id, "cancelled", "Cancelled via web panel")
    elif action == "delete":
        await delete_deal(deal_id)
        return RedirectResponse("/deals", status_code=303)

    return RedirectResponse(f"/deals/{deal_id}", status_code=303)


@app.get("/users", response_class=HTMLResponse)
async def users_page(request: Request, _: bool = Depends(require_login)):
    users = await get_all_users(100)
    banned = await get_banned_users()
    return templates.TemplateResponse("users.html", {
        "request": request, "users": users, "banned_count": len(banned)
    })


@app.post("/users/{user_id}/ban")
async def ban(request: Request, user_id: int, _: bool = Depends(require_login)):
    await ban_user(user_id)
    return RedirectResponse("/users", status_code=303)


@app.post("/users/{user_id}/unban")
async def unban(request: Request, user_id: int, _: bool = Depends(require_login)):
    await unban_user(user_id)
    return RedirectResponse("/users", status_code=303)


@app.get("/settings", response_class=HTMLResponse)
async def settings_page(request: Request, _: bool = Depends(require_login)):
    return templates.TemplateResponse("settings.html", {
        "request": request,
        "fee": await get_fee(),
        "support": await get_setting("support_contact"),
        "crypto_wallet": await get_setting("default_crypto_wallet"),
        "upi": await get_setting("default_upi_id"),
        "maintenance": await is_maintenance(),
        "min_amount": await get_setting("min_amount"),
        "max_amount": await get_setting("max_amount"),
    })


@app.post("/settings")
async def save_settings(
    request: Request,
    fee: float = Form(...),
    support: str = Form(...),
    crypto_wallet: str = Form(...),
    upi: str = Form(...),
    min_amount: str = Form(...),
    max_amount: str = Form(...),
    maintenance: str = Form("0"),
    _: bool = Depends(require_login)
):
    await set_fee(fee)
    await set_setting("support_contact", support)
    await set_setting("default_crypto_wallet", crypto_wallet)
    await set_setting("default_upi_id", upi)
    await set_setting("min_amount", min_amount)
    await set_setting("max_amount", max_amount)
    await set_setting("maintenance_mode", "1" if maintenance == "1" else "0")
    return RedirectResponse("/settings", status_code=303)
