"""
db.py — Supabase database layer for Extella Sales Hub.
Adapted from chocofood-hub/db.py.
"""
import os
import hashlib
import secrets
import requests as _req
from datetime import datetime, timedelta


def _url():
    return os.environ.get("SUPABASE_URL", "")


def _key():
    return os.environ.get("SUPABASE_SERVICE_KEY", "") or os.environ.get("SUPABASE_KEY", "")


def _h():
    k = _key()
    return {
        "apikey": k,
        "Authorization": f"Bearer {k}",
        "Content-Type": "application/json",
        "Prefer": "return=representation",
    }


def _get(table, params=None):
    r = _req.get(f"{_url()}/rest/v1/{table}", headers=_h(), params=params or {}, timeout=15)
    r.raise_for_status()
    return r.json() or []


def _post(table, data, upsert=False):
    h = dict(_h())
    if upsert:
        h["Prefer"] = "resolution=merge-duplicates,return=representation"
    r = _req.post(f"{_url()}/rest/v1/{table}", headers=h, json=data, timeout=15)
    r.raise_for_status()
    res = r.json()
    return res[0] if isinstance(res, list) and res else res


def _patch(table, flt, data):
    r = _req.patch(f"{_url()}/rest/v1/{table}?{flt}", headers=_h(), json=data, timeout=15)
    r.raise_for_status()
    res = r.json()
    return res[0] if isinstance(res, list) and res else {}


def _del(table, flt):
    _req.delete(f"{_url()}/rest/v1/{table}?{flt}", headers=_h(), timeout=15).raise_for_status()


# ── AUTH ──────────────────────────────────────────────────────────

def hash_pw(pw: str) -> str:
    return hashlib.sha256(pw.encode()).hexdigest()


def make_session(uid: int, secret: str) -> str:
    h = hashlib.sha256(f"{uid}:{secret}".encode()).hexdigest()[:20]
    return f"{uid}.{h}"


def parse_session(cookie: str, secret: str):
    """Returns user dict or None."""
    try:
        uid_str, h = cookie.split(".", 1)
        uid = int(uid_str)
        if h == hashlib.sha256(f"{uid}:{secret}".encode()).hexdigest()[:20]:
            return get_user_by_id(uid)
    except Exception:
        pass
    return None


# ── USERS ─────────────────────────────────────────────────────────

ROLE_LABELS = {"admin": "Админ", "office": "Офис", "manager": "Менеджер"}


def get_all_users():
    return _get("users", {"select": "*", "order": "id.asc"}) or []


def get_user_by_email(email: str):
    rows = _get("users", {"select": "*", "email": f"eq.{email.lower().strip()}"})
    return rows[0] if rows else None


def get_user_by_email_and_pass(email: str, pw_hash: str):
    rows = _get("users", {
        "select": "*",
        "email": f"eq.{email.lower().strip()}",
        "password_hash": f"eq.{pw_hash}",
        "active": "eq.1",
    })
    for r in (rows or []):
        if r.get("password_set", 1) == 1:
            return r
    return None


def get_user_by_id(uid: int):
    rows = _get("users", {"select": "*", "id": f"eq.{uid}"})
    return rows[0] if rows else None


def get_user_by_invite(token: str):
    rows = _get("users", {"select": "*", "invite_token": f"eq.{token}"})
    return rows[0] if rows else None


def create_user(email, pw_hash, name, role, active=0, invite_token=None, invite_expires_at=None, password_set=0):
    return _post("users", {
        "email": email.lower().strip(),
        "password_hash": pw_hash,
        "name": name,
        "role": role,
        "active": active,
        "created_at": datetime.now().isoformat(),
        "invite_token": invite_token,
        "invite_expires_at": invite_expires_at,
        "password_set": password_set,
    })


def update_user(uid: int, **fields):
    return _patch("users", f"id=eq.{uid}", fields)


def delete_user(uid: int):
    _del("users", f"id=eq.{uid}")


def generate_invite(email: str, name: str, role: str, base_url: str) -> str:
    """Creates invite user and returns invite URL."""
    token = secrets.token_urlsafe(32)
    expires = (datetime.now() + timedelta(days=7)).isoformat()
    existing = get_user_by_email(email)
    if existing:
        update_user(existing["id"], invite_token=token, invite_expires_at=expires, active=0, name=name, role=role, password_set=0)
    else:
        create_user(email, "", name, role, active=0, invite_token=token, invite_expires_at=expires, password_set=0)
    return f"{base_url}/invite/{token}"


def ensure_admin(email: str, pw_hash: str):
    existing = get_user_by_email(email)
    if existing:
        update_user(existing["id"], password_hash=pw_hash, role="admin", active=1, password_set=1, name="Асылхан Жусупов")
    else:
        create_user(email, pw_hash, "Асылхан Жусупов", "admin", active=1, password_set=1)


# ── DEALS ─────────────────────────────────────────────────────────

STAGES = ["lead", "meeting", "proposal", "partner", "lost"]
STAGE_LABELS = {"lead": "Лид", "meeting": "Встреча", "proposal": "КП", "partner": "Партнёр", "lost": "Отказ"}
STAGE_COLORS = {"lead": "#4a5568", "meeting": "#2b6cb0", "proposal": "#d69e2e", "partner": "#276749", "lost": "#742a2a"}


def get_all_deals(limit=300, manager_name=None, stage=None):
    p = {"select": "*", "order": "created_at.desc", "limit": str(limit)}
    if manager_name:
        p["manager_name"] = f"eq.{manager_name}"
    if stage:
        p["stage"] = f"eq.{stage}"
    return _get("deals", p)


def create_deal(data: dict):
    now = datetime.now().isoformat()
    data.update({"created_at": now, "updated_at": now})
    return _post("deals", data)


def update_deal(deal_id: int, **fields):
    fields["updated_at"] = datetime.now().isoformat()
    return _patch("deals", f"id=eq.{deal_id}", fields)


def get_pipeline_stats():
    deals = get_all_deals(limit=2000)
    stats = {s: {"count": 0, "amount": 0.0} for s in STAGES}
    for d in deals:
        s = d.get("stage", "lead")
        if s in stats:
            stats[s]["count"] += 1
            stats[s]["amount"] += float(d.get("amount") or 0)
    return stats


def get_manager_deal_stats(deals=None):
    """Returns per-manager deal count and revenue."""
    if deals is None:
        deals = get_all_deals(limit=2000)
    stats = {}
    for d in deals:
        m = d.get("manager_name") or "Не назначен"
        if m not in stats:
            stats[m] = {"total": 0, "partners": 0, "revenue": 0.0, "active": 0}
        stats[m]["total"] += 1
        if d.get("stage") == "partner":
            stats[m]["partners"] += 1
            stats[m]["revenue"] += float(d.get("amount") or 0)
        elif d.get("stage") not in ("lost", "partner"):
            stats[m]["active"] += 1
    return stats
