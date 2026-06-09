# M4: ROP Commander
# Telegram Bot -> Bitrix24 Task Creation + Supabase logging
#
# Usage in Telegram:
#   /task Данадил - позвонить CEO Kaspi до 12.06
#   /help

import httpx
import re
import logging
from datetime import datetime
from app.config import settings

logger = logging.getLogger(__name__)

# Имя/фамилия (любое упоминание) -> B24 user ID
# Источник: extella.bitrix24.kz, Отдел продаж
MANAGER_MAP: dict = {
    # Асылхан Жусупов — РОП (B24 ID: 1)
    "асылхан": 1,
    "жусупов": 1,
    # Данадил Курманжанов — Менеджер по продажам (B24 ID: 24)
    "данадил": 24,
    "курманжанов": 24,
    "дана": 24,
}


async def handle_message(data: dict) -> None:
    message = data.get("message", {})
    text = message.get("text", "").strip()
    chat_id = message.get("chat", {}).get("id")
    if not text or not chat_id:
        return
    logger.info(f"Message from {chat_id}: {text[:80]}")

    await _log_activity(chat_id, text)

    if text == "/start":
        await _send(chat_id, _start_text())
    elif text == "/help":
        await _send(chat_id, _help_text())
    elif text == "/managers":
        await _send(chat_id, _managers_text())
    elif text.lower().startswith(("/task", "задача")):
        await _process_task(text, chat_id)
    else:
        await _send(chat_id, "Неизвестная команда. Напиши /help")


async def _process_task(text: str, chat_id: int) -> None:
    parsed = _parse_task(text)
    if not parsed:
        await _send(chat_id, "Не смог распарсить задачу.\nФормат: /task Данадил - позвонить до 12.06")
        return
    result = await _create_b24_task(parsed)
    if result.get("ok"):
        task_id = result.get("task_id")
        # Логируем задачу в Supabase
        await _log_task(parsed, task_id, chat_id)
        msg = (
            f"✅ Задача создана в Bitrix24\n"
            f"Ответственный: {parsed['assignee']}\n"
            f"Задача: {parsed['title']}\n"
            f"Дедлайн: {parsed.get('deadline', 'не указан')}\n"
            f"ID задачи: {task_id}"
        )
        await _send(chat_id, msg)
    else:
        await _send(chat_id, f"❌ Ошибка: {result.get('error')}")


def _parse_task(text: str) -> dict:
    clean = re.sub(r'^(/task|задача:?)', '', text, flags=re.IGNORECASE).strip()
    if not clean:
        return {}
    deadline = None
    dl = re.search(r'до\s+(\d{1,2}\.\d{1,2}(?:\.\d{2,4})?)', clean, re.IGNORECASE)
    if dl:
        clean = clean[:dl.start()].strip()
        parts = dl.group(1).split('.')
        try:
            day, month = int(parts[0]), int(parts[1])
            year = int(parts[2]) if len(parts) > 2 else datetime.now().year
            if year < 100:
                year += 2000
            deadline = f"{year}-{month:02d}-{day:02d}T18:00:00"
        except Exception:
            pass
    sep = re.search(r'[-—–]', clean)
    if sep:
        assignee = clean[:sep.start()].strip()
        title = clean[sep.end():].strip()
    else:
        parts2 = clean.split(maxsplit=1)
        assignee = parts2[0] if parts2 else 'Менеджер'
        title = parts2[1] if len(parts2) > 1 else clean
    b24_uid = next((uid for k, uid in MANAGER_MAP.items() if k.lower() in assignee.lower()), None)
    return {'assignee': assignee, 'title': title, 'deadline': deadline, 'b24_user_id': b24_uid}


async def _create_b24_task(parsed: dict) -> dict:
    if not settings.b24_webhook:
        return {'ok': False, 'error': 'B24 webhook not configured'}
    fields = {'TITLE': parsed['title'], 'DESCRIPTION': 'Создано через Extella ROP Bot'}
    if parsed.get('b24_user_id'):
        fields['RESPONSIBLE_ID'] = parsed['b24_user_id']
    if parsed.get('deadline'):
        fields['DEADLINE'] = parsed['deadline']
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            r = await client.post(f"{settings.b24_webhook}tasks.task.add.json", json={'fields': fields})
            data = r.json()
        tid = data.get('result', {}).get('task', {}).get('id')
        if tid:
            return {'ok': True, 'task_id': tid}
        return {'ok': False, 'error': str(data.get('error_description', data))}
    except Exception as e:
        return {'ok': False, 'error': str(e)}


async def _log_task(parsed: dict, b24_task_id, chat_id: int) -> None:
    """Логируем созданную задачу в Supabase таблицу tasks."""
    if not settings.supabase_url or not settings.supabase_key:
        return
    try:
        payload = {
            "b24_task_id": int(b24_task_id) if b24_task_id else None,
            "title": parsed.get("title", ""),
            "assignee_name": parsed.get("assignee", ""),
            "b24_user_id": parsed.get("b24_user_id"),
            "deadline": parsed.get("deadline"),
            "created_by": chat_id,
            "status": "created",
        }
        headers = {
            "apikey": settings.supabase_key,
            "Authorization": f"Bearer {settings.supabase_key}",
            "Content-Type": "application/json",
            "Prefer": "return=minimal",
        }
        async with httpx.AsyncClient(timeout=10) as client:
            await client.post(
                f"{settings.supabase_url}/rest/v1/tasks",
                headers=headers,
                json=payload,
            )
    except Exception as e:
        logger.warning(f"Supabase log failed (non-critical): {e}")


async def _log_activity(chat_id: int, text: str) -> None:
    """Логируем каждое взаимодействие в activity_log."""
    if not settings.supabase_url or not settings.supabase_key:
        return
    try:
        command = text.split()[0] if text.startswith("/") else "message"
        payload = {
            "chat_id": chat_id,
            "command": command,
            "raw_text": text[:500],
            "success": True,
        }
        headers = {
            "apikey": settings.supabase_key,
            "Authorization": f"Bearer {settings.supabase_key}",
            "Content-Type": "application/json",
            "Prefer": "return=minimal",
        }
        async with httpx.AsyncClient(timeout=5) as client:
            await client.post(
                f"{settings.supabase_url}/rest/v1/activity_log",
                headers=headers,
                json=payload,
            )
    except Exception as e:
        logger.warning(f"Activity log failed (non-critical): {e}")


async def _send(chat_id: int, text: str) -> None:
    if not settings.telegram_bot_token:
        return
    url = f"https://api.telegram.org/bot{settings.telegram_bot_token}/sendMessage"
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            await client.post(url, json={'chat_id': chat_id, 'text': text})
    except Exception as e:
        logger.error(f"Telegram send error: {e}")


def _start_text() -> str:
    return "Extella Sales Hub — ROP Bot\n\nСоздаю задачи в Bitrix24.\n\nНапиши /help"


def _managers_text() -> str:
    return (
        "👥 Менеджеры в системе:\n\n"
        "• Асылхан Жусупов (РОП)\n"
        "  → /task Асылхан - задача\n\n"
        "• Данадил Курманжанов (Менеджер)\n"
        "  → /task Данадил - задача"
    )


def _help_text() -> str:
    return (
        "Команды:\n\n"
        "/task [менеджер] - [описание] до [дд.мм]\n"
        "Пример: /task Данадил - позвонить CEO Kaspi до 12.06\n\n"
        "/managers — список менеджеров\n"
        "/help — эта справка"
    )
