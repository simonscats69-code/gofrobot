#!/usr/bin/env python3
"""
Тест для проверки работы декоратора @ignore_not_modified_error
"""

from aiogram.exceptions import TelegramBadRequest

def ignore_not_modified_error(func):
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except TelegramBadRequest as e:
            if "message is not modified" in str(e):
                if args and hasattr(args[0], 'callback_query'):
                    await args[0].callback_query.answer()
                return
            raise
    return wrapper

class MockCallbackQuery:
    def __init__(self):
        self.answered = False

    async def answer(self):
        self.answered = True
        print("Callback answered successfully")

@ignore_not_modified_error
async def test_function(callback):
    # Имитация ошибки "message is not modified"
    # TelegramBadRequest требует аргумент message
    error = TelegramBadRequest(message="Bad Request: message is not modified: specified new message content and reply markup are exactly the same as a current content and reply markup of the message")
    raise error

async def main():
    print("Testing @ignore_not_modified_error decorator...")

    # Создаем mock объект callback_query
    callback = MockCallbackQuery()

    try:
        # Вызываем функцию, которая должна вызвать ошибку
        result = await test_function(callback)
        print(f"Function returned: {result}")

        # Проверяем, что callback был отвечен
        if callback.answered:
            print("✅ SUCCESS: Callback was answered correctly")
        else:
            print("❌ FAIL: Callback was not answered")

    except TelegramBadRequest as e:
        print(f"❌ FAIL: TelegramBadRequest was not caught: {e}")
    except Exception as e:
        print(f"❌ FAIL: Unexpected exception: {e}")

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())