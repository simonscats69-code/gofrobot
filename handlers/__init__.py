from aiogram import Router
from .commands import router as commands_router
from .callbacks import router as callbacks_router
from .nickname_and_rademka import router as nickname_router
from .top import router as top_router
from .atm_handlers import router as atm_router
from .group_handlers import router as group_router
from .chat_handlers import router as chat_router

router = Router()

router.include_router(commands_router)
router.include_router(callbacks_router)
router.include_router(nickname_router)
router.include_router(top_router)
router.include_router(atm_router)
router.include_router(group_router)
router.include_router(chat_router)

__all__ = ['router']
