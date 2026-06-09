from fastapi import APIRouter, Request, HTTPException
from app.modules.m4_rop_commander import handle_message
import logging

logger = logging.getLogger(__name__)
router = APIRouter(tags=["Telegram"])


@router.post("/telegram")
async def telegram_webhook(request: Request):
    try:
        data = await request.json()
        await handle_message(data)
        return {"ok": True}
    except Exception as e:
        logger.error(f"Telegram webhook error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
