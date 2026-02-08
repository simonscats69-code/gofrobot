from aiogram import Router
from .commands import router as commands_router
from .callbacks import router as callbacks_router
from .timing_commands import router as timing_router

router = Router()

router.include_router(commands_router)
router.include_router(callbacks_router)
router.include_router(timing_router)

__all__ = ['router']
