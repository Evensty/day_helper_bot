import logging
import types
from aiogram import Router, types, F, Bot
from aiogram.types import Message, ForceReply, InlineKeyboardMarkup, InlineKeyboardButton
from sqlalchemy import select

from data.database import session_factory
from data.models import User
from data.orm import ORM
from handlers.tasks import escape_md, get_main_keyboard, get_task_list_handler

router = Router()

# Этот хэндлер будет срабатывать на команду "/start"
@router.message(F.text == "/start")
async def start_handler(message: Message):
    keyboard = get_main_keyboard()  # Получаем клавиатуру с кнопкой
    await message.answer(escape_md('Привет!\nМеня зовут day_helper_bot!\nЯ могу создавать список задач'), reply_markup=keyboard)
    # Отправляем сообщение с кнопкой
    user_id = message.from_user.id
    username = message.from_user.username
    async with session_factory() as session:
        stmt = select(User).where(User.user_id == user_id)
        result = await session.execute(stmt)
        existing_user = result.scalars().first()
        if not existing_user:
            await ORM.insert_users(User, user_id, username)
            await message.answer(escape_md("Вы успешно зарегистрированы!"))
        else:
            await message.answer(escape_md("Вы уже зарегистрированы!"))
