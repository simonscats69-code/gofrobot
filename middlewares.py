"""
Custom middlewares for the bot
"""
from aiogram import BaseMiddleware
from aiogram.types import Message, CallbackQuery
from typing import Callable, Dict, Any, Awaitable
import logging
import time
from config import RATE_LIMITS

logger = logging.getLogger(__name__)

class ErrorHandlingMiddleware(BaseMiddleware):
    """Global error handling middleware"""

    async def __call__(
        self,
        handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
        event: Message,
        data: Dict[str, Any]
    ) -> Any:
        try:
            return await handler(event, data)
        except Exception as e:
            logger.error(f"Error in handler {handler.__name__}: {str(e)}", exc_info=True)

            # Send error message to user if it's a user-facing error
            if isinstance(event, Message):
                try:
                    await event.answer("❌ Произошла ошибка. Пожалуйста, попробуйте позже.")
                except:
                    pass
            elif isinstance(event, CallbackQuery):
                try:
                    await event.answer("❌ Ошибка. Попробуйте позже.", show_alert=True)
                except:
                    pass

            return None

class RateLimitMiddleware(BaseMiddleware):
    """Rate limiting middleware"""

    def __init__(self):
        self.user_rates: Dict[int, Dict[str, float]] = {}

    async def __call__(
        self,
        handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
        event: Message,
        data: Dict[str, Any]
    ) -> Any:
        user_id = event.from_user.id
        handler_name = handler.__name__

        # Determine rate limit category
        if "davka" in handler_name:
            limit_key = "davka"
        elif "rademka" in handler_name or "fight" in handler_name:
            limit_key = "pvp"
        elif "command" in handler_name or handler_name.startswith("cmd_"):
            limit_key = "commands"
        else:
            limit_key = "default"

        limit = RATE_LIMITS.get(limit_key, RATE_LIMITS["default"])
        window = 60  # 1 minute window

        # Initialize user tracking
        if user_id not in self.user_rates:
            self.user_rates[user_id] = {}

        # Clean up old entries
        current_time = time.time()
        if limit_key in self.user_rates[user_id]:
            last_time = self.user_rates[user_id][limit_key]
            if current_time - last_time > window:
                # Reset counter if window expired
                self.user_rates[user_id][limit_key] = current_time
                return await handler(event, data)

        # Check rate limit
        if limit_key in self.user_rates[user_id]:
            # Already used this limit in current window
            await event.answer(f"🚦 Слишком много запросов. Подождите {window - (current_time - self.user_rates[user_id][limit_key]):.0f} секунд.")
            return None

        # Allow the request
        self.user_rates[user_id][limit_key] = current_time
        return await handler(event, data)

class LoggingMiddleware(BaseMiddleware):
    """Request logging middleware"""

    async def __call__(
        self,
        handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
        event: Message,
        data: Dict[str, Any]
    ) -> Any:
        start_time = time.time()
        handler_name = handler.__name__
        user_id = event.from_user.id
        username = event.from_user.username or "unknown"
        chat_type = event.chat.type if hasattr(event.chat, 'type') else "unknown"

        logger.info(f"📥 Request: {handler_name} | User: {user_id}@{username} | Chat: {chat_type}")

        try:
            result = await handler(event, data)
            duration = time.time() - start_time
            logger.info(f"✅ Success: {handler_name} | Duration: {duration:.3f}s")
            return result
        except Exception as e:
            duration = time.time() - start_time
            logger.error(f"❌ Error: {handler_name} | Duration: {duration:.3f}s | Error: {str(e)}")
            raise

class MaintenanceMiddleware(BaseMiddleware):
    """Maintenance mode middleware"""

    def __init__(self, maintenance_mode: bool = False):
        self.maintenance_mode = maintenance_mode

    async def __call__(
        self,
        handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
        event: Message,
        data: Dict[str, Any]
    ) -> Any:
        if self.maintenance_mode and not await self._is_admin(event.from_user.id):
            await event.answer("🔧 Бот находится в режиме технического обслуживания. Пожалуйста, попробуйте позже.")
            return None

        return await handler(event, data)

    async def _is_admin(self, user_id: int) -> bool:
        """Check if user is admin (can bypass maintenance)"""
        # In real implementation, this would check a list of admin IDs
        return user_id in [123456789]  # Example admin ID