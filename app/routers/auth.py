from fastapi import APIRouter, Request, Cookie, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from typing import Optional
from app.config import settings
import app.db as db

router = APIRouter()


def get_current_user(session: Optional[str]) -> Optional[dict]:
    if not session or not settings.secret_key:
        return None
    return db.parse_session(session, settings.secret_key)


LOGIN_HTML = """<!DOCTYPE html>
<html lang="ru"><head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Extella Sales Hub</title>
<style>
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;background:#0f1117;color:#e2e8f0;min-height:100vh;display:flex;align-items:center;justify-content:center}
.wrap{width:100%;max-width:420px;padding:24px}
.logo{font-size:26px;font-weight:800;color:#68d391;letter-spacing:-0.5px}.logo span{color:#e2e8f0}
.sub{font-size:13px;color:#4a5568;margin-bottom:36px;margin-top:4px}
.card{background:#1a1f2e;border:1px solid #2d3748;border-radius:16px;padding:36px}
label{display:block;font-size:12px;font-weight:600;color:#718096;text-transform:uppercase;letter-spacing:.5px;margin-bottom:6px;margin-top:20px}
input{width:100%;background:#0f1117;border:1px solid #2d3748;border-radius:8px;padding:12px 16px;color:#e2e8f0;font-size:15px;outline:none;transition:border .2s}
input:focus{border-color:#68d391}
.btn{width:100%;background:#276749;color:#9ae6b4;border:none;border-radius:8px;padding:14px;font-size:15px;font-weight:700;cursor:pointer;margin-top:28px;letter-spacing:.3px}
.btn:hover{background:#2f7a55}
.err{color:#fc8181;font-size:13px;margin-top:16px;padding:12px 16px;background:#1a1a2e;border-radius:8px;border-left:3px solid #fc8181}
</style></head><body>
<div class="wrap">
  <div class="logo">Extella <span>Sales Hub</span></div>
  <div class="sub">Система управления B2B продажами</div>
  <div class="card">
    <!-- ERROR -->
    <form method="POST" action="/login">
      <label>Email</label>
      <input type="email" name="email" autofocus placeholder="you@extella.ai" required value="<!-- EMAIL -->">
      <label>Пароль</label>
      <input type="password" name="password" placeholder="••••••••" required>
      <button class="btn" type="submit">Войти →</button>
    </form>
  </div>
</div>
</body></html>"""


INVITE_HTML = """<!DOCTYPE html>
<html lang="ru"><head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Extella Sales Hub — Установка пароля</title>
<style>
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;background:#0f1117;color:#e2e8f0;min-height:100vh;display:flex;align-items:center;justify-content:center}
.wrap{width:100%;max-width:420px;padding:24px}
.logo{font-size:26px;font-weight:800;color:#68d391}.logo span{color:#e2e8f0}
.sub{font-size:13px;color:#4a5568;margin-bottom:36px;margin-top:4px}
.card{background:#1a1f2e;border:1px solid #2d3748;border-radius:16px;padding:36px}
h2{font-size:18px;font-weight:700;margin-bottom:4px}
.nm{color:#68d391;font-size:14px;margin-bottom:20px}
label{display:block;font-size:12px;font-weight:600;color:#718096;text-transform:uppercase;letter-spacing:.5px;margin-bottom:6px;margin-top:20px}
input{width:100%;background:#0f1117;border:1px solid #2d3748;border-radius:8px;padding:12px 16px;color:#e2e8f0;font-size:15px;outline:none}
input:focus{border-color:#68d391}
.btn{width:100%;background:#276749;color:#9ae6b4;border:none;border-radius:8px;padding:14px;font-size:15px;font-weight:700;cursor:pointer;margin-top:28px}
.btn:hover{background:#2f7a55}
.err{color:#fc8181;font-size:13px;margin-top:16px;padding:12px;background:#1a1a2e;border-radius:8px;border-left:3px solid #fc8181}
</style></head><body>
<div class="wrap">
  <div class="logo">Extella <span>Sales Hub</span></div>
  <div class="sub">Добро пожаловать в команду!</div>
  <div class="card">
    <h2>Установка пароля</h2>
    <div class="nm">{{NAME}}</div>
    <!-- ERROR -->
    <form method="POST" action="/invite/{{TOKEN}}">
      <label>Новый пароль</label>
      <input type="password" name="password" placeholder="Минимум 6 символов" required>
      <label>Повторите пароль</label>
      <input type="password" name="password2" placeholder="Повторите" required>
      <button class="btn" type="submit">Активировать аккаунт →</button>
    </form>
  </div>
</div>
</body></html>"""


@router.get("/login", response_class=HTMLResponse)
async def login_page():
    return HTMLResponse(LOGIN_HTML.replace("<!-- EMAIL -->", "").replace("<!-- ERROR -->", ""))


@router.post("/login")
async def do_login(request: Request, email: str = Form(""), password: str = Form("")):
    pw_hash = db.hash_pw(password)
    user = db.get_user_by_email_and_pass(email, pw_hash)
    if not user:
        err = '<div class="err">Неверный email или пароль</div>'
        html = LOGIN_HTML.replace("<!-- ERROR -->", err).replace("<!-- EMAIL -->", email)
        return HTMLResponse(html, status_code=401)
    token = db.make_session(user["id"], settings.secret_key)
    resp = RedirectResponse("/", status_code=302)
    resp.set_cookie("session", token, httponly=True, max_age=86400 * 30)
    return resp


@router.get("/logout")
async def logout():
    resp = RedirectResponse("/login", status_code=302)
    resp.delete_cookie("session")
    return resp


@router.get("/invite/{token}", response_class=HTMLResponse)
async def invite_page(token: str):
    user = db.get_user_by_invite(token)
    if not user:
        return HTMLResponse("<h2 style='font-family:sans-serif;color:#fc8181;padding:40px'>Ссылка недействительна или устарела</h2>")
    html = INVITE_HTML.replace("{{TOKEN}}", token).replace("{{NAME}}", user.get("name", "")).replace("<!-- ERROR -->", "")
    return HTMLResponse(html)


@router.post("/invite/{token}")
async def do_invite(token: str, password: str = Form(""), password2: str = Form("")):
    user = db.get_user_by_invite(token)
    if not user:
        return HTMLResponse("<h2 style='color:#fc8181;padding:40px'>Ссылка недействительна</h2>")
    if password != password2 or len(password) < 6:
        err = '<div class="err">Пароли не совпадают или слишком короткий (мин. 6 символов)</div>'
        html = INVITE_HTML.replace("{{TOKEN}}", token).replace("{{NAME}}", user.get("name", "")).replace("<!-- ERROR -->", err)
        return HTMLResponse(html, status_code=400)
    db.update_user(user["id"], password_hash=db.hash_pw(password), active=1, password_set=1, invite_token=None)
    return RedirectResponse("/login", status_code=302)
