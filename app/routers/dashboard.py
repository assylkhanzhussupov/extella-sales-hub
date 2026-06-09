from fastapi import APIRouter, Cookie
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from typing import Optional
from app.config import settings
from app.routers.auth import get_current_user
import app.db as db
import httpx

router = APIRouter()


def fmt_money(v):
    try:
        v = float(v or 0)
        if v >= 1_000_000:
            return f"{v/1_000_000:.1f}млн"
        if v >= 1_000:
            return f"{v/1_000:.0f}тыс"
        return str(int(v))
    except Exception:
        return "0"


DASH_HTML = """<!DOCTYPE html>
<html lang="ru"><head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Extella Sales Hub</title>
<style>
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;background:#0f1117;color:#e2e8f0;min-height:100vh}
.hdr{background:#1a1f2e;border-bottom:1px solid #2d3748;padding:0 24px;height:56px;display:flex;align-items:center;justify-content:space-between;position:fixed;top:0;left:0;right:0;z-index:100}
.logo{font-size:17px;font-weight:700;color:#68d391}.logo span{color:#e2e8f0}
.hn{display:flex;align-items:center;gap:16px}
.hn a{color:#718096;font-size:13px;text-decoration:none;padding:6px 12px;border-radius:6px}
.hn a:hover{color:#e2e8f0}.hn a.act{background:#276749;color:#9ae6b4}
.un{font-size:13px;color:#718096}
.rb{font-size:11px;padding:2px 8px;border-radius:10px;font-weight:600;margin-left:8px}
.rb-admin{background:#742a2a;color:#fc8181}
.rb-office{background:#2a4365;color:#63b3ed}
.rb-manager{background:#276749;color:#9ae6b4}
.live{background:#276749;color:#9ae6b4;padding:3px 10px;border-radius:20px;font-size:11px;font-weight:700;letter-spacing:.3px}
.uts{font-size:11px;color:#4a5568}
.main{padding:72px 24px 40px;max-width:1200px;margin:0 auto}
.kpis{display:grid;grid-template-columns:repeat(auto-fit,minmax(210px,1fr));gap:16px;margin-bottom:28px}
.kpi{background:#1a1f2e;border:1px solid #2d3748;border-radius:12px;padding:22px}
.kl{font-size:11px;font-weight:600;color:#718096;text-transform:uppercase;letter-spacing:.5px;margin-bottom:10px}
.kv{font-size:34px;font-weight:800;color:#68d391;letter-spacing:-1px}
.ks{font-size:12px;color:#4a5568;margin-top:6px}
.tabs{display:flex;gap:4px;margin-bottom:20px;background:#1a1f2e;padding:4px;border-radius:10px;width:fit-content;flex-wrap:wrap}
.tab{padding:8px 18px;border-radius:7px;cursor:pointer;font-size:14px;font-weight:600;color:#718096;border:none;background:none}
.tab.act{background:#276749;color:#9ae6b4}
.tab:hover:not(.act){color:#e2e8f0}
.tc{display:none}.tc.act{display:block}
.sec{background:#1a1f2e;border:1px solid #2d3748;border-radius:12px;overflow:hidden;margin-bottom:20px}
.sh{padding:14px 20px;border-bottom:1px solid #2d3748;display:flex;justify-content:space-between;align-items:center}
.st{font-size:15px;font-weight:600}
.sc{font-size:12px;color:#718096}
table{width:100%;border-collapse:collapse}
th{padding:10px 20px;text-align:left;font-size:11px;font-weight:600;color:#4a5568;text-transform:uppercase;letter-spacing:.5px;border-bottom:1px solid #2d3748}
td{padding:12px 20px;font-size:14px;border-bottom:1px solid #1e2533}
tr:last-child td{border-bottom:none}
tr:hover td{background:#1e2533}
.bl{padding:3px 10px;border-radius:20px;font-size:12px;font-weight:500;white-space:nowrap}
.s-lead{background:#2d3748;color:#a0aec0}
.s-meeting{background:#2a4365;color:#63b3ed}
.s-proposal{background:#744210;color:#f6ad55}
.s-partner{background:#276749;color:#9ae6b4}
.s-lost{background:#742a2a;color:#fc8181}
.s-created{background:#276749;color:#9ae6b4}
.empty{padding:48px;text-align:center;color:#4a5568;font-size:14px}
.pipe{display:grid;grid-template-columns:repeat(5,1fr);gap:12px;padding:20px}
.ps{background:#0f1117;border:1px solid #2d3748;border-radius:10px;padding:16px;text-align:center}
.psl{font-size:12px;font-weight:600;color:#718096;margin-bottom:10px;text-transform:uppercase;letter-spacing:.4px}
.psn{font-size:28px;font-weight:800;color:#68d391}
.psa{font-size:12px;color:#4a5568;margin-top:4px}
.mgrd{display:grid;grid-template-columns:repeat(auto-fill,minmax(280px,1fr));gap:16px;padding:20px}
.mc{background:#0f1117;border:1px solid #2d3748;border-radius:10px;padding:18px}
.mn{font-size:16px;font-weight:700;margin-bottom:4px}
.mrl{font-size:12px;color:#68d391;margin-bottom:14px}
.mr{display:flex;justify-content:space-between;font-size:13px;color:#718096;padding:4px 0;border-bottom:1px solid #1a1f2e}
.mr:last-child{border-bottom:none}
.mr span:last-child{color:#e2e8f0;font-weight:600}
.pb{height:6px;background:#2d3748;border-radius:3px;margin-top:12px;overflow:hidden}
.pbf{height:100%;background:#276749;border-radius:3px;transition:width .5s}
</style></head><body>
<div class="hdr">
  <div class="logo">Extella <span>Sales Hub</span></div>
  <div class="hn">
    <span class="live">● Live</span>
    <a href="/" class="act">Дашборд</a>
    <a href="/admin" id="adm-lnk" style="display:none">Админ</a>
    <a href="/logout">Выйти</a>
    <span class="un" id="uname">—</span>
    <span class="uts" id="uts">—</span>
  </div>
</div>
<div class="main">
  <div class="kpis">
    <div class="kpi"><div class="kl">🤝 Партнёры</div><div class="kv" id="k1">—</div><div class="ks">в воронке</div></div>
    <div class="kpi"><div class="kl">💰 Выручка</div><div class="kv" id="k2">—</div><div class="ks">закрытые сделки</div></div>
    <div class="kpi"><div class="kl">📈 Активных сделок</div><div class="kv" id="k3">—</div><div class="ks">лид + встреча + КП</div></div>
    <div class="kpi"><div class="kl">📋 Задачи (бот)</div><div class="kv" id="k4">—</div><div class="ks">через Telegram</div></div>
  </div>
  <div class="tabs">
    <button class="tab act" onclick="sw('ov',this)">🏗 Воронка</button>
    <button class="tab" onclick="sw('deals',this)">🤝 Сделки</button>
    <button class="tab" onclick="sw('mgr',this)">👥 Менеджеры</button>
    <button class="tab" onclick="sw('tasks',this)">📋 Задачи</button>
    <button class="tab" onclick="sw('b24',this)">🏢 Bitrix24</button>
  </div>
  <div class="tc act" id="tc-ov">
    <div class="sec"><div class="sh"><span class="st">Воронка продаж</span></div><div class="pipe" id="pipe"><div class="empty">загрузка...</div></div></div>
    <div class="sec"><div class="sh"><span class="st">Последние сделки</span><span class="sc" id="dc">—</span></div><div id="dtbl"><div class="empty">загрузка...</div></div></div>
  </div>
  <div class="tc" id="tc-deals">
    <div class="sec"><div class="sh"><span class="st">Все сделки</span><span class="sc" id="dall">—</span></div><div id="dall-tbl"><div class="empty">загрузка...</div></div></div>
  </div>
  <div class="tc" id="tc-mgr"><div id="mgrd"><div class="empty">загрузка...</div></div></div>
  <div class="tc" id="tc-tasks">
    <div class="sec"><div class="sh"><span class="st">Задачи через бота</span><span class="sc" id="tc-cnt">—</span></div><div id="ttbl"><div class="empty">загрузка...</div></div></div>
  </div>
  <div class="tc" id="tc-b24">
    <div class="sec"><div class="sh"><span class="st">Задачи Bitrix24</span><span class="sc" id="b24c">—</span></div><div id="b24tbl"><div class="empty">загрузка...</div></div></div>
  </div>
</div>
<script>
const SL={'lead':'Лид','meeting':'Встреча','proposal':'КП','partner':'Партнёр','lost':'Отказ'};
const BS={'1':'Ждёт','2':'В работе','3':'Готово','4':'Отложена','5':'Одобрена','6':'Отклонена','7':'Не начата'};
function sw(n,el){document.querySelectorAll('.tc,.tab').forEach(e=>e.classList.remove('act'));document.getElementById('tc-'+n).classList.add('act');el.classList.add('act');}
function fd(s){if(!s)return'—';try{return new Date(s).toLocaleDateString('ru-RU',{day:'2-digit',month:'2-digit',year:'2-digit'});}catch(e){return s;}}
function fdt(s){if(!s)return'—';try{return new Date(s).toLocaleString('ru-RU',{day:'2-digit',month:'2-digit',hour:'2-digit',minute:'2-digit'});}catch(e){return s;}}
function fmoney(v){v=parseFloat(v||0);if(v>=1e6)return (v/1e6).toFixed(1)+'млн ₸';if(v>=1e3)return Math.round(v/1e3)+'тыс ₸';return v+' ₸';}
function sbadge(s){return '<span class="bl s-'+s+'">'+(SL[s]||s)+'</span>';}
function deals_table(deals,limit){
  const D=limit?deals.slice(0,limit):deals;
  if(!D.length)return '<div class="empty">Сделок нет — добавьте первый партнёр!</div>';
  return '<table><thead><tr><th>Компания</th><th>Менеджер</th><th>Стадия</th><th>Сумма (₸)</th><th>Дата</th></tr></thead><tbody>'+
    D.map(d=>`<tr><td>${d.company_name||'—'}</td><td style="color:#718096">${d.manager_name||'—'}</td><td>${sbadge(d.stage||'lead')}</td><td style="color:#68d391;font-weight:600">${fmoney(d.amount)}</td><td style="color:#4a5568">${fd(d.created_at)}</td></tr>`).join('')+'</tbody></table>';}
async function load(){
  try{
    const r=await fetch('/api/stats');
    if(r.status===401){location='/login';return;}
    const d=await r.json();
    const u=d.user||{};
    document.getElementById('uname').textContent=u.name||'';
    if(u.role==='admin')document.getElementById('adm-lnk').style.display='';
    const p=d.pipeline||{};
    const partners=(p.partner||{}).count||0;
    const revenue=(p.partner||{}).amount||0;
    const active=(['lead','meeting','proposal'].reduce((s,k)=>s+(p[k]||{}).count||0,0));
    const tasks=d.tasks_total||0;
    document.getElementById('k1').textContent=partners;
    document.getElementById('k2').textContent=fmoney(revenue);
    document.getElementById('k3').textContent=active;
    document.getElementById('k4').textContent=tasks;
    const STAGES=['lead','meeting','proposal','partner','lost'];
    document.getElementById('pipe').innerHTML='<style>.pipe{display:grid;grid-template-columns:repeat(5,1fr)}</style>'+STAGES.map(s=>`<div class="ps"><div class="psl">${SL[s]}</div><div class="psn s-${s}" style="font-size:28px;font-weight:800">${(p[s]||{}).count||0}</div><div class="psa">${fmoney((p[s]||{}).amount||0)}</div></div>`).join('');
    const deals=d.deals||[];
    document.getElementById('dc').textContent=deals.length+' сделок';
    document.getElementById('dtbl').innerHTML=deals_table(deals,8);
    document.getElementById('dall').textContent=deals.length+' всего';
    document.getElementById('dall-tbl').innerHTML=deals_table(deals,0);
    const mgrs=d.manager_stats||{};
    const mkeys=Object.keys(mgrs);
    document.getElementById('mgrd').innerHTML=mkeys.length===0?'<div class="sec"><div class="empty">Менеджеров пока нет</div></div>':
      '<div class="mgrd">'+mkeys.map(m=>{
        const s=mgrs[m];
        const conv=s.total>0?Math.round(s.partners/s.total*100):0;
        return `<div class="mc"><div class="mn">${m}</div><div class="mrl">Менеджер</div><div class="mr"><span>Всего сделок</span><span>${s.total}</span></div><div class="mr"><span>Партнёры</span><span style="color:#68d391">${s.partners}</span></div><div class="mr"><span>Выручка</span><span style="color:#68d391">${fmoney(s.revenue)}</span></div><div class="mr"><span>Активных</span><span>${s.active}</span></div><div class="pb"><div class="pbf" style="width:${conv}%"></div></div><div style="font-size:11px;color:#4a5568;margin-top:4px">Конверсия: ${conv}%</div></div>`;}).join('')+'</div>';
    const T=d.tasks||[];
    document.getElementById('tc-cnt').textContent=T.length+' записей';
    document.getElementById('ttbl').innerHTML=T.length===0?'<div class="empty">Задач нет — создайте через /task в боте</div>':
      '<table><thead><tr><th>B24 ID</th><th>Задача</th><th>Ответственный</th><th>Дедлайн</th><th>Создана</th></tr></thead><tbody>'+
      T.map(t=>`<tr><td style="color:#4a5568">#${t.b24_task_id||'—'}</td><td>${t.title||'—'}</td><td>${t.assignee_name||'—'}</td><td style="color:#f6ad55">${fd(t.deadline)||'—'}</td><td style="color:#4a5568">${fdt(t.created_at)}</td></tr>`).join('')+'</tbody></table>';
    const B=d.b24_tasks||[];
    document.getElementById('b24c').textContent=(d.b24_tasks_total||0)+' задач в B24';
    document.getElementById('b24tbl').innerHTML=B.length===0?'<div class="empty">Нет данных из Bitrix24</div>':
      '<table><thead><tr><th>ID</th><th>Задача</th><th>Статус</th><th>Дедлайн</th></tr></thead><tbody>'+
      B.map(t=>`<tr><td style="color:#4a5568">#${t.ID||'—'}</td><td>${t.TITLE||'—'}</td><td><span class="bl s-lead">${BS[t.STATUS]||t.STATUS||'—'}</span></td><td style="color:#4a5568">${fd(t.DEADLINE)||'—'}</td></tr>`).join('')+'</tbody></table>';
    document.getElementById('uts').textContent='обн '+new Date().toLocaleTimeString('ru-RU',{hour:'2-digit',minute:'2-digit'});
  }catch(e){console.error(e);}
}
load();setInterval(load,30000);
</script></body></html>"""


@router.get("/", response_class=HTMLResponse)
async def index(session: Optional[str] = Cookie(default=None)):
    user = get_current_user(session)
    if not user:
        return RedirectResponse("/login", status_code=302)
    return HTMLResponse(DASH_HTML)


@router.get("/api/stats")
async def api_stats(session: Optional[str] = Cookie(default=None)):
    user = get_current_user(session)
    if not user:
        return JSONResponse({"error": "unauthorized"}, status_code=401)

    is_manager = user.get("role") == "manager"
    manager_filter = user.get("name") if is_manager else None

    out = {
        "user": {"name": user.get("name"), "role": user.get("role")},
        "pipeline": {},
        "deals": [],
        "manager_stats": {},
        "tasks": [],
        "tasks_total": 0,
        "b24_tasks": [],
        "b24_tasks_total": 0,
    }

    try:
        deals = db.get_all_deals(limit=500, manager_name=manager_filter)
        out["deals"] = deals[:50]
        pipeline = {s: {"count": 0, "amount": 0.0} for s in db.STAGES}
        for d in deals:
            s = d.get("stage", "lead")
            if s in pipeline:
                pipeline[s]["count"] += 1
                pipeline[s]["amount"] += float(d.get("amount") or 0)
        out["pipeline"] = pipeline
        out["manager_stats"] = db.get_manager_deal_stats(deals) if not is_manager else {}
    except Exception as e:
        out["deals_error"] = str(e)

    sb_url = settings.supabase_url
    sb_key = settings.supabase_service_key or settings.supabase_key
    if sb_url and sb_key:
        hdrs = {"apikey": sb_key, "Authorization": f"Bearer {sb_key}"}
        q = f"tasks?select=*&order=created_at.desc&limit=30"
        if manager_filter:
            q += f"&assignee_name=eq.{manager_filter}"
        async with httpx.AsyncClient(timeout=10) as c:
            try:
                r = await c.get(f"{sb_url}/rest/v1/{q}", headers=hdrs)
                if r.ok:
                    out["tasks"] = r.json()
                    out["tasks_total"] = len(out["tasks"])
            except Exception:
                pass

    if settings.b24_webhook:
        async with httpx.AsyncClient(timeout=10) as c:
            try:
                payload = {"filter": {">=CREATED_DATE": "2026-06-01", "ONLY_MY_TASKS": "N"}, "select": ["ID", "TITLE", "STATUS", "DEADLINE", "CREATED_DATE"]}
                if manager_filter:
                    uid = next((m["b24_user_id"] for m in db.get_all_deals.__globals__.get("_mgr_cache", []) if manager_filter in m.get("name", "")), None)
                r = await c.post(f"{settings.b24_webhook}tasks.task.list.json", json=payload)
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
