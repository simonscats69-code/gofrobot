from .commands import router as commands_router
from .callbacks import router as callbacks_router
from .daily import router as daily_router
from .nickname_and_rademka import router as nickname_router
from .shop import router as shop_router
from .top import router as top_router
from .atm_handlers import router as atm_router
from aiogram import Router

router = Router()

__all__ = ['router']
