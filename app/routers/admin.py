from fastapi import APIRouter, Cookie, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from typing import Optional
from app.config import settings
from app.routers.auth import get_current_user
import app.db as db

router = APIRouter()


def require_admin(session: Optional[str]):
    user = get_current_user(session)
    if not user or user.get("role") != "admin":
        return None
    return user


ADMIN_HTML = """<!DOCTYPE html>
<html lang="ru"><head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Extella Sales Hub — Админ</title>
<style>
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;background:#0f1117;color:#e2e8f0;min-height:100vh}
.hdr{background:#1a1f2e;border-bottom:1px solid #2d3748;padding:0 24px;height:56px;display:flex;align-items:center;justify-content:space-between;position:fixed;top:0;left:0;right:0;z-index:100}
.logo{font-size:17px;font-weight:700;color:#68d391}.logo span{color:#e2e8f0}
.nav{display:flex;align-items:center;gap:16px}
.nav a{color:#718096;font-size:13px;text-decoration:none;padding:6px 12px;border-radius:6px}
.nav a:hover,.nav a.act{background:#276749;color:#9ae6b4}
.badge{background:#742a2a;color:#fc8181;font-size:11px;padding:2px 8px;border-radius:10px;font-weight:600}
.main{padding:72px 24px 40px;max-width:1100px;margin:0 auto}
h1{font-size:22px;font-weight:700;margin-bottom:24px}
.card{background:#1a1f2e;border:1px solid #2d3748;border-radius:12px;overflow:hidden;margin-bottom:24px}
.ch{padding:16px 20px;border-bottom:1px solid #2d3748;display:flex;justify-content:space-between;align-items:center}
.ct{font-size:15px;font-weight:600}
table{width:100%;border-collapse:collapse}
th{padding:10px 20px;text-align:left;font-size:11px;font-weight:600;color:#4a5568;text-transform:uppercase;letter-spacing:.5px;border-bottom:1px solid #2d3748}
td{padding:12px 20px;font-size:14px;border-bottom:1px solid #1e2533}
tr:last-child td{border-bottom:none}
tr:hover td{background:#1e2533}
.rl{padding:3px 10px;border-radius:20px;font-size:12px;font-weight:500}
.rl-admin{background:#742a2a;color:#fc8181}
.rl-office{background:#2a4365;color:#63b3ed}
.rl-manager{background:#276749;color:#9ae6b4}
.act-y{color:#68d391;font-size:12px}
.act-n{color:#4a5568;font-size:12px}
.btn-sm{padding:5px 12px;border-radius:6px;font-size:12px;font-weight:600;cursor:pointer;border:none}
.btn-inv{background:#2b6cb0;color:#bee3f8}
.btn-del{background:#742a2a;color:#fc8181}
.btn-tog{background:#2d3748;color:#a0aec0}
.btn-primary{background:#276749;color:#9ae6b4;border:none;border-radius:8px;padding:10px 20px;font-size:14px;font-weight:600;cursor:pointer}
.btn-primary:hover{background:#2f7a55}
form.inline{display:flex;gap:12px;flex-wrap:wrap;padding:20px;align-items:flex-end}
form.inline label{display:block;font-size:11px;color:#718096;margin-bottom:4px;text-transform:uppercase;letter-spacing:.4px}
form.inline input,form.inline select{background:#0f1117;border:1px solid #2d3748;border-radius:7px;padding:9px 14px;color:#e2e8f0;font-size:14px;outline:none;min-width:180px}
form.inline input:focus,form.inline select:focus{border-color:#68d391}
.msg{padding:12px 20px;font-size:13px;background:#276749;color:#9ae6b4;margin:0 20px 16px;border-radius:8px}
.empty{padding:40px;text-align:center;color:#4a5568}
.inv-box{background:#0f1117;border:1px solid #2d3748;border-radius:8px;padding:14px 18px;margin:16px 20px;font-size:13px;color:#718096;word-break:break-all}
.inv-box span{color:#68d391;font-weight:600}
</style></head><body>
<div class="hdr">
  <div class="logo">Extella <span>Sales Hub</span></div>
  <div class="nav">
    <a href="/">Дашборд</a>
    <a href="/admin" class="act">Админ <span class="badge">Админ</span></a>
    <a href="/logout">Выйти</a>
  </div>
</div>
<div class="main">
  <h1>Управление пользователями</h1>
  <!-- MSG -->
  <!-- INVITE_LINK -->
  <div class="card">
    <div class="ch"><span class="ct">Пригласить пользователя</span></div>
    <form class="inline" method="POST" action="/admin/invite">
      <div><label>Email</label><input type="email" name="email" placeholder="user@extella.ai" required></div>
      <div><label>Имя</label><input type="text" name="name" placeholder="Иван Иванов" required></div>
      <div><label>Роль</label><select name="role"><option value="manager">Менеджер</option><option value="office">Офис</option><option value="admin">Админ</option></select></div>
      <div><button class="btn-primary" type="submit">Сгенерировать ссылку</button></div>
    </form>
  </div>
  <div class="card">
    <div class="ch"><span class="ct">Пользователи</span><span style="font-size:12px;color:#4a5568">{{COUNT}} чел.</span></div>
    {{USERS_TABLE}}
  </div>
</div>
</body></html>"""


def _role_badge(role):
    cls = {"admin": "rl-admin", "office": "rl-office", "manager": "rl-manager"}.get(role, "rl-manager")
    label = db.ROLE_LABELS.get(role, role)
    return f'<span class="rl {cls}">{label}</span>'


def _build_users_table(users):
    if not users:
        return '<div class="empty">Пользователей нет</div>'
    rows = "".join(
        f"""<tr>
        <td>{u.get('id')}</td>
        <td>{u.get('name', '—')}</td>
        <td style="color:#718096">{u.get('email', '')}</td>
        <td>{_role_badge(u.get('role', 'manager'))}</td>
        <td class="{'act-y' if u.get('active') == 1 else 'act-n'}">
          {'\u2022 Активен' if u.get('active') == 1 else '• Неактивен'}
        </td>
        <td>
          <form method="POST" action="/admin/toggle/{u.get('id')}" style="display:inline">
            <button class="btn-sm btn-tog" type="submit">
              {'Откл' if u.get('active') == 1 else 'Вкл'}
            </button>
          </form>
        </td>
      </tr>""" for u in users
    )
    return f"""<table>
      <thead><tr><th>ID</th><th>Имя</th><th>Email</th><th>Роль</th><th>Статус</th><th></th></tr></thead>
      <tbody>{rows}</tbody>
    </table>"""


@router.get("/admin", response_class=HTMLResponse)
async def admin_page(session: Optional[str] = Cookie(default=None), msg: str = ""):
    user = require_admin(session)
    if not user:
        return RedirectResponse("/login", status_code=302)
    users = db.get_all_users()
    html = ADMIN_HTML
    html = html.replace("{{COUNT}}", str(len(users)))
    html = html.replace("{{USERS_TABLE}}", _build_users_table(users))
    html = html.replace("<!-- MSG -->", f'<div class="msg">{msg}</div>' if msg else "")
    html = html.replace("<!-- INVITE_LINK -->", "")
    return HTMLResponse(html)


@router.post("/admin/invite")
async def create_invite(request: Request, email: str = Form(""), name: str = Form(""), role: str = Form("manager"), session: Optional[str] = Cookie(default=None)):
    user = require_admin(session)
    if not user:
        return RedirectResponse("/login", status_code=302)
    base_url = str(request.base_url).rstrip("/")
    invite_url = db.generate_invite(email, name, role, base_url)
    users = db.get_all_users()
    html = ADMIN_HTML
    html = html.replace("{{COUNT}}", str(len(users)))
    html = html.replace("{{USERS_TABLE}}", _build_users_table(users))
    html = html.replace("<!-- MSG -->", f'<div class="msg">Приглашение создано для {name}</div>')
    inv_box = f'<div class="inv-box">🔗 Ссылка: <span>{invite_url}</span><br><small style="color:#4a5568">Отправь пользователю. Действительна 7 дней.</small></div>'
    html = html.replace("<!-- INVITE_LINK -->", inv_box)
    return HTMLResponse(html)


@router.post("/admin/toggle/{uid}")
async def toggle_user(uid: int, session: Optional[str] = Cookie(default=None)):
    user = require_admin(session)
    if not user:
        return RedirectResponse("/login", status_code=302)
    target = db.get_user_by_id(uid)
    if target and target.get("role") != "admin":
        new_active = 0 if target.get("active") == 1 else 1
        db.update_user(uid, active=new_active)
    return RedirectResponse("/admin", status_code=302)
