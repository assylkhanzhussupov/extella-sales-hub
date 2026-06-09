from fastapi import APIRouter, Request, Cookie
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from typing import Optional
import httpx
import hashlib
from app.config import settings

router = APIRouter()


def _check_auth(session: Optional[str]) -> bool:
    if not session or not settings.secret_key:
        return False
    return session == hashlib.sha256(settings.secret_key.encode()).hexdigest()[:24]


def _token() -> str:
    return hashlib.sha256(settings.secret_key.encode()).hexdigest()[:24]


@router.get("/", response_class=HTMLResponse)
async def index(session: Optional[str] = Cookie(default=None)):
    if not _check_auth(session):
        return RedirectResponse("/login", status_code=302)
    return HTMLResponse(DASHBOARD_HTML)


@router.get("/login", response_class=HTMLResponse)
async def login_page():
    return HTMLResponse(LOGIN_HTML)


@router.post("/login")
async def do_login(request: Request):
    form = await request.form()
    if form.get("password", "") == settings.secret_key:
        resp = RedirectResponse("/", status_code=302)
        resp.set_cookie("session", _token(), httponly=True, max_age=86400 * 30)
        return resp
    return HTMLResponse(LOGIN_HTML.replace("<!-- ERROR -->", '<p class="error">Неверный пароль</p>'))


@router.get("/logout")
async def logout():
    resp = RedirectResponse("/login", status_code=302)
    resp.delete_cookie("session")
    return resp


@router.get("/api/stats")
async def api_stats(session: Optional[str] = Cookie(default=None)):
    if not _check_auth(session):
        return JSONResponse({"error": "unauthorized"}, status_code=401)

    out = {
        "tasks": [], "tasks_total": 0,
        "b24_tasks": [], "b24_tasks_total": 0,
        "activity": [], "activity_total": 0,
        "managers": [],
    }

    sb_url = settings.supabase_url
    sb_key = settings.supabase_key

    if sb_url and sb_key:
        hdrs = {"apikey": sb_key, "Authorization": f"Bearer {sb_key}"}
        async with httpx.AsyncClient(timeout=10) as c:
            for key, path in [
                ("tasks", "tasks?select=*&order=created_at.desc&limit=20"),
                ("activity", "activity_log?select=*&order=created_at.desc&limit=20"),
                ("managers", "managers?select=*"),
            ]:
                try:
                    r = await c.get(f"{sb_url}/rest/v1/{path}", headers=hdrs)
                    if r.ok:
                        out[key] = r.json()
                        if key in ("tasks", "activity"):
                            out[f"{key}_total"] = len(out[key])
                except Exception:
                    pass

    if settings.b24_webhook:
        async with httpx.AsyncClient(timeout=10) as c:
            try:
                r = await c.post(
                    f"{settings.b24_webhook}tasks.task.list.json",
                    json={
                        "filter": {">=CREATED_DATE": "2026-06-01", "ONLY_MY_TASKS": "N"},
                        "select": ["ID", "TITLE", "STATUS", "DEADLINE", "RESPONSIBLE_ID", "CREATED_DATE"],
                    },
                )
                if r.ok:
                    data = r.json()
                    items = data.get("result", {})
                    if isinstance(items, dict):
                        items = items.get("tasks", [])
                    out["b24_tasks"] = items[:15]
                    out["b24_tasks_total"] = data.get("total", 0)
            except Exception:
                pass

    return JSONResponse(out)


LOGIN_HTML = """<!DOCTYPE html>
<html lang="ru">
<head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Extella Sales Hub</title>
<style>
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;background:#0f1117;color:#e2e8f0;min-height:100vh;display:flex;align-items:center;justify-content:center}
.box{background:#1a1f2e;border:1px solid #2d3748;border-radius:16px;padding:40px;width:100%;max-width:380px}
.logo{font-size:22px;font-weight:700;color:#68d391;margin-bottom:4px}
.logo span{color:#e2e8f0}
.sub{font-size:13px;color:#4a5568;margin-bottom:32px}
label{display:block;font-size:13px;color:#718096;margin-bottom:6px}
input[type=password]{width:100%;background:#0f1117;border:1px solid #2d3748;border-radius:8px;padding:12px 16px;color:#e2e8f0;font-size:15px;outline:none;margin-bottom:20px}
input[type=password]:focus{border-color:#68d391}
button{width:100%;background:#276749;color:#9ae6b4;border:none;border-radius:8px;padding:12px;font-size:15px;font-weight:600;cursor:pointer}
button:hover{background:#2f7a55}
.error{color:#fc8181;font-size:13px;margin-bottom:16px}
</style>
</head>
<body>
<div class="box">
<div class="logo">Extella <span>Sales Hub</span></div>
<div class="sub">Система управления продажами</div>
<!-- ERROR -->
<form method="POST" action="/login">
<label>Пароль</label>
<input type="password" name="password" autofocus placeholder="&#8226;&#8226;&#8226;&#8226;&#8226;&#8226;&#8226;&#8226;">
<button type="submit">Войти →</button>
</form>
</div>
</body>
</html>"""


DASHBOARD_HTML = """<!DOCTYPE html>
<html lang="ru">
<head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Extella Sales Hub</title>
<style>
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;background:#0f1117;color:#e2e8f0;min-height:100vh}
.hdr{background:#1a1f2e;border-bottom:1px solid #2d3748;padding:0 24px;height:56px;display:flex;align-items:center;justify-content:space-between;position:fixed;top:0;left:0;right:0;z-index:100}
.logo{font-size:18px;font-weight:700;color:#68d391}.logo span{color:#e2e8f0}
.hr{display:flex;align-items:center;gap:16px}
.live{background:#276749;color:#9ae6b4;padding:3px 10px;border-radius:20px;font-size:12px;font-weight:600}
.lo{color:#718096;font-size:13px;text-decoration:none}.lo:hover{color:#e2e8f0}
.main{padding:72px 24px 24px;max-width:1200px;margin:0 auto}
.cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:16px;margin-bottom:24px}
.card{background:#1a1f2e;border:1px solid #2d3748;border-radius:12px;padding:20px}
.cl{font-size:11px;color:#718096;text-transform:uppercase;letter-spacing:.5px;margin-bottom:8px}
.cv{font-size:32px;font-weight:700;color:#68d391}
.cs{font-size:11px;color:#4a5568;margin-top:4px}
.tabs{display:flex;gap:4px;margin-bottom:20px;background:#1a1f2e;padding:4px;border-radius:10px;width:fit-content}
.tab{padding:8px 18px;border-radius:7px;cursor:pointer;font-size:14px;font-weight:500;color:#718096;border:none;background:none}
.tab.active{background:#276749;color:#9ae6b4}
.tab:hover:not(.active){color:#e2e8f0}
.sec{background:#1a1f2e;border:1px solid #2d3748;border-radius:12px;overflow:hidden;margin-bottom:20px}
.sh{padding:14px 20px;border-bottom:1px solid #2d3748;display:flex;justify-content:space-between;align-items:center}
.st{font-size:15px;font-weight:600}
.sc{font-size:12px;color:#718096}
table{width:100%;border-collapse:collapse}
th{padding:10px 20px;text-align:left;font-size:11px;font-weight:600;color:#4a5568;text-transform:uppercase;letter-spacing:.5px;border-bottom:1px solid #2d3748}
td{padding:12px 20px;font-size:14px;border-bottom:1px solid #1e2533}
tr:last-child td{border-bottom:none}
tr:hover td{background:#1e2533}
.bb{background:#1a365d;color:#63b3ed;padding:3px 10px;border-radius:20px;font-size:12px;font-weight:500}
.bgr{background:#2d3748;color:#a0aec0;padding:3px 10px;border-radius:20px;font-size:12px;font-weight:500}
.empty{padding:40px;text-align:center;color:#4a5568}
.tc{display:none}.tc.active{display:block}
.mgrid{display:grid;grid-template-columns:repeat(auto-fill,minmax(260px,1fr));gap:16px;padding:20px}
.mc{background:#0f1117;border:1px solid #2d3748;border-radius:10px;padding:16px}
.mn{font-weight:600;font-size:15px;margin-bottom:4px}
.mr{font-size:12px;color:#68d391;margin-bottom:12px}
.mrow{display:flex;justify-content:space-between;font-size:13px;color:#718096;padding:3px 0}
.mrow span:last-child{color:#e2e8f0;font-weight:500}
.rt{font-size:11px;color:#4a5568}
</style>
</head>
<body>
<div class="hdr">
  <div class="logo">Extella <span>Sales Hub</span></div>
  <div class="hr">
    <span class="live">● Live</span>
    <span class="rt" id="rt">—</span>
    <a href="/logout" class="lo">выйти</a>
  </div>
</div>
<div class="main">
  <div class="cards">
    <div class="card"><div class="cl">Задачи (бот)</div><div class="cv" id="s1">—</div><div class="cs">через Telegram</div></div>
    <div class="card"><div class="cl">Задачи B24</div><div class="cv" id="s2">—</div><div class="cs">с июня 2026</div></div>
    <div class="card"><div class="cl">Менеджеры</div><div class="cv" id="s3">—</div><div class="cs">в системе</div></div>
    <div class="card"><div class="cl">Активность</div><div class="cv" id="s4">—</div><div class="cs">записей в логе</div></div>
  </div>
  <div class="tabs">
    <button class="tab active" onclick="sw('tasks',this)">📋 Задачи бота</button>
    <button class="tab" onclick="sw('b24',this)">🏢 Bitrix24</button>
    <button class="tab" onclick="sw('mgr',this)">👥 Менеджеры</button>
    <button class="tab" onclick="sw('act',this)">📊 Активность</button>
  </div>
  <div class="tc active" id="tc-tasks">
    <div class="sec"><div class="sh"><span class="st">Задачи через бота</span><span class="sc" id="c1">—</span></div><div id="b1"><div class="empty">загрузка...</div></div></div>
  </div>
  <div class="tc" id="tc-b24">
    <div class="sec"><div class="sh"><span class="st">Задачи Bitrix24</span><span class="sc" id="c2">—</span></div><div id="b2"><div class="empty">загрузка...</div></div></div>
  </div>
  <div class="tc" id="tc-mgr"><div id="b3"><div class="empty">загрузка...</div></div></div>
  <div class="tc" id="tc-act">
    <div class="sec"><div class="sh"><span class="st">Лог активности</span><span class="sc" id="c4">—</span></div><div id="b4"><div class="empty">загрузка...</div></div></div>
  </div>
</div>
<script>
const BS={'1':'Ждёт','2':'В работе','3':'Завершена','4':'Отложена','5':'Одобрена','6':'Отклонена','7':'Не начата'};
function sw(n,el){document.querySelectorAll('.tc,.tab').forEach(e=>e.classList.remove('active'));document.getElementById('tc-'+n).classList.add('active');el.classList.add('active');}
function fd(s){if(!s)return'—';try{return new Date(s).toLocaleString('ru-RU',{day:'2-digit',month:'2-digit',year:'2-digit',hour:'2-digit',minute:'2-digit'});}catch(e){return s;}}
function fdl(s){if(!s)return'—';try{const d=new Date(s),days=Math.ceil((d-new Date())/86400000),str=d.toLocaleDateString('ru-RU',{day:'2-digit',month:'2-digit'});if(days<0)return'<span style="color:#fc8181">'+str+' просрочено</span>';if(days<=2)return'<span style="color:#f6ad55">'+str+' ('+days+'д)</span>';return str;}catch(e){return s;}}
async function load(){
  try{
    const r=await fetch('/api/stats');
    if(r.status===401){location='/login';return;}
    const d=await r.json();
    document.getElementById('s1').textContent=d.tasks_total??0;
    document.getElementById('s2').textContent=d.b24_tasks_total??0;
    document.getElementById('s3').textContent=(d.managers||[]).length;
    document.getElementById('s4').textContent=d.activity_total??0;
    const T=d.tasks||[];
    document.getElementById('c1').textContent=T.length+' записей';
    document.getElementById('b1').innerHTML=T.length===0?'<div class="empty">Задач нет — создайте через /task в боте</div>':'<table><thead><tr><th>B24 ID</th><th>Задача</th><th>Ответственный</th><th>Дедлайн</th><th>Статус</th><th>Создана</th></tr></thead><tbody>'+T.map(t=>'<tr><td style="color:#4a5568">#'+(t.b24_task_id||'—')+'</td><td>'+(t.title||'—')+'</td><td>'+(t.assignee_name||'—')+'</td><td>'+fdl(t.deadline)+'</td><td><span class="bb">'+(t.status||'created')+'</span></td><td style="color:#4a5568">'+fd(t.created_at)+'</td></tr>').join('')+'</tbody></table>';
    const B=d.b24_tasks||[];
    document.getElementById('c2').textContent=(d.b24_tasks_total??0)+' всего';
    document.getElementById('b2').innerHTML=B.length===0?'<div class="empty">Нет данных из Bitrix24</div>':'<table><thead><tr><th>ID</th><th>Задача</th><th>Статус</th><th>Дедлайн</th><th>Создана</th></tr></thead><tbody>'+B.map(t=>'<tr><td style="color:#4a5568">#'+(t.ID||'—')+'</td><td>'+(t.TITLE||'—')+'</td><td><span class="bgr">'+(BS[t.STATUS]||t.STATUS||'—')+'</span></td><td>'+fdl(t.DEADLINE)+'</td><td style="color:#4a5568">'+fd(t.CREATED_DATE)+'</td></tr>').join('')+'</tbody></table>';
    const M=d.managers||[],tm={};
    T.forEach(t=>{const k=t.assignee_name||'?';tm[k]=(tm[k]||0)+1;});
    document.getElementById('b3').innerHTML=M.length===0?'<div class="sec"><div class="empty">Нет данных о менеджерах</div></div>':'<div class="mgrid">'+M.map(m=>'<div class="mc"><div class="mn">'+m.name+'</div><div class="mr">B24 ID: '+m.b24_user_id+'</div><div class="mrow"><span>Задач создано</span><span>'+(tm[m.name]||0)+'</span></div><div class="mrow"><span>Статус</span><span style="color:#68d391">'+(m.active?'Активен':'Неактивен')+'</span></div></div>').join('')+'</div>';
    const A=d.activity||[];
    document.getElementById('c4').textContent=A.length+' записей';
    document.getElementById('b4').innerHTML=A.length===0?'<div class="empty">Активности пока нет</div>':'<table><thead><tr><th>Chat ID</th><th>Команда</th><th>Текст</th><th>Время</th></tr></thead><tbody>'+A.map(a=>'<tr><td style="color:#4a5568">'+(a.chat_id||'—')+'</td><td><span class="bb">'+(a.command||'—')+'</span></td><td style="color:#718096;max-width:280px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap">'+(a.raw_text||'—')+'</td><td style="color:#4a5568">'+fd(a.created_at)+'</td></tr>').join('')+'</tbody></table>';
    document.getElementById('rt').textContent='обновлено '+new Date().toLocaleTimeString('ru-RU',{hour:'2-digit',minute:'2-digit'});
  }catch(e){console.error(e);}
}
load();setInterval(load,30000);
</script>
</body>
</html>"""
