import types

from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.types import Message, ForceReply, InlineKeyboardMarkup, InlineKeyboardButton
from sqlalchemy import select, delete
from sqlalchemy.exc import SQLAlchemyError
from bot import bot
from data.database import session_factory
from data.models import User, Task, Link
from data.orm import ORM
from handlers.tasks import escape_md

router = Router()

@router.message(F.text == '/users')
async def get_user_list_handler(message: Message):
    async with session_factory() as session:
        async with session.begin():
            stmt = select(User)
            result = await session.execute(stmt)
            users = result.scalars().all()
            if users:
                users_list = "\n".join([f"{user.user_id} - @{user.username}" for user in users])
                await message.reply(escape_md(f"Список пользователей:\n{users_list}"))
            else:
                await message.reply("В базе данных нет пользователей.")



@router.message(Command(commands=['addlink']))
async def add_link_handler(message: Message):
    async with session_factory() as session:
        async with session.begin():
            # Extract link
            new_link = message.text[len("/add_link "):].strip()
            if not new_link:
                await message.reply("Добавьте ссылку, используя: /add_link <ссылка>")
                return
            # Add link to the database
            username = message.from_user.username
            result = await session.execute(select(User).where(User.username == username))
            user = result.scalars().first()
            if user:
                link = Link(user_id=user.user_id, link=new_link)
                session.add(link)
                await session.commit()
            else:
                await message.reply("Пользователь не найден!")


@router.message(Command(commands=['links']))
async def get_link_list_handler(message: Message):
    async with session_factory() as session:
        async with session.begin():
            user_id = message.from_user.id
            stmt = select(Link).where(Link.user_id == user_id)
            result = await session.execute(stmt)
            links = result.scalars().all()
            if links:
                link_list = "\n".join([f"{link.link_id}. {link.link}" for link in links])
                await message.reply(f"Ссылки:\n{link_list}")
            else:
                await message.reply("В базе данных нет ссылок.")


@router.message(Command(commands=['dellink']))
async def delete_link_handler(message: Message):
    async with session_factory() as session:
        async with session.begin():
            args = message.text.split(maxsplit=1)
            if len(args) < 2:
                await message.reply("Пожалуйста, укажите ID ссылок для удаления, разделяя их пробелами.")
                return

            # Извлекаем часть с ID задач
            args = args[1]

            if not args:
                await message.reply("Пожалуйста, укажите ID ссылок для удаления, разделяя их пробелами.")
                return
            # Разделяем аргументы и пытаемся привести их к целым числам
            try:
                link_ids = [int(task_id) for task_id in args.split()]
            except ValueError:
                await message.reply("Все ID должны быть числами. Проверьте ввод и попробуйте снова.")
                return

            stmt = delete(Link).where(Link.link_id.in_(link_ids))
            result = await session.execute(stmt)

            deleted_count = result.rowcount

            if deleted_count:
                await message.reply(f"Удалено ссылок: {deleted_count}.")
            else:
                await message.reply("Не найдено ссылок с указанными ID.")


# # Этот хэндлер будет срабатывать на команду "/help"
# @router.message(Command(commands=['help']))
# async def process_help_command(message: Message):
#     await message.answer(
#         'help text'
#     )




