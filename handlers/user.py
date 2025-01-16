from aiogram import Bot, Dispatcher
from aiogram.filters import Command
from aiogram.types import Message
from sqlalchemy import select, delete

from data.config import settings
from data.database import session_factory
from data.models import User, Task, Link
from data.orm import AsyncORM

BOT_TOKEN = settings.BOT_TOKEN


# Создаем объекты бота и диспетчера
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# Этот хэндлер будет срабатывать на команду "/start"
@dp.message(Command(commands=['start']))
async def start_command_handler(message: Message):
    await message.answer('Привет!\nМеня зовут day_helper_bot!\nЯ могу создавать список задач')
    user_id = message.from_user.id
    username = message.from_user.username
    async with session_factory() as session:
        stmt = select(User).where(User.user_id == user_id)
        result = await session.execute(stmt)
        existing_user = result.scalars().first()

        if not existing_user:
            await AsyncORM.insert_users(User, user_id, username)
            await message.reply("Вы успешно зарегистрированы!")
        else:
            await message.reply("Вы уже зарегистрированы!")


@dp.message(Command(commands=['users']))
async def get_user_list_handler(message: Message):
    async with session_factory() as session:
        async with session.begin():
            stmt = select(User)
            result = await session.execute(stmt)
            users = result.scalars().all()
            if users:
                # users_list = "\n".join([f"User ID: {user.user_id}" for user in users])
                users_list = "\n".join([f"{user.user_id} - {user.username}" for user in users])
                # task_list = "\n".join([f"{task.task_id}. {task.task_text}" for task in tasks])
                await message.reply(f"Список пользователей:\n{users_list}")
            else:
                await message.reply("В базе данных нет пользователей.")


@dp.message(Command(commands=['add_task']))
async def add_task_handler(message: Message):
    async with session_factory() as session:
        async with session.begin():
            # Extract task description
            new_task = message.text[len("/add_task "):].strip()
            if not new_task:
                await message.reply("Введите описание задачи, используя: /add_task <описание задачи>")
                return
            # Add task to the database
            username = message.from_user.username
            result = await session.execute(select(User).where(User.username == username))
            user = result.scalars().first()
            if user:
                new_task = Task(user_id=user.user_id, task_text=new_task)
                session.add(new_task)
                await session.commit()
            else:
                await message.reply("Пользователь не найден!")


@dp.message(Command(commands=['tasks']))
async def get_task_list_handler(message: Message):
    async with session_factory() as session:
        async with session.begin():
            stmt = select(Task)
            result = await session.execute(stmt)
            tasks = result.scalars().all()
            if tasks:
                task_list = "\n".join([f"{task.task_id}. {task.task_text}" for task in tasks])
                await message.reply(f"Список задач:\n{task_list}")
            else:
                await message.reply("В базе данных нет задач.")


@dp.message(Command(commands=['delete_task']))
async def delete_task_handler(message: Message):
    async with session_factory() as session:
        async with session.begin():
            args = message.text.split(maxsplit=1)
            if len(args) < 2:
                await message.reply("Пожалуйста, укажите ID задач для удаления, разделяя их пробелами.")
                return

            # Извлекаем часть с ID задач
            args = args[1]

            if not args:
                await message.reply("Пожалуйста, укажите ID задач для удаления, разделяя их пробелами.")
                return
            # Разделяем аргументы и пытаемся привести их к целым числам
            try:
                task_ids = [int(task_id) for task_id in args.split()]
            except ValueError:
                await message.reply("Все ID должны быть числами. Проверьте ввод и попробуйте снова.")
                return

            stmt = delete(Task).where(Task.task_id.in_(task_ids))
            result = await session.execute(stmt)

            deleted_count = result.rowcount

            if deleted_count:
                await message.reply(f"Удалено задач: {deleted_count}.")
            else:
                await message.reply("Не найдено задач с указанными ID.")


@dp.message(Command(commands=['add_link']))
async def add_link_handler(message: Message):
    # Extract task description
    new_link = message.text[len("/add_link "):].strip()

    if not new_link:
        await message.reply("Please provide a task description. Usage: /add_task <task description>")
        return

    # Add task to the database
    async with session_factory() as session:
        link = Link(link=new_link)
        session.add(link)
        await session.commit()

@dp.message(Command(commands=['links']))
async def get_link_list_handler(message: Message):
    async with session_factory() as session:
        async with session.begin():
            stmt = select(Link)
            result = await session.execute(stmt)
            links = result.scalars().all()
            if links:
                link_list = "\n".join([f"{link.link_id}. {link.link}" for link in links])
                await message.reply(f"Ссылки:\n{link_list}")
            else:
                await message.reply("В базе данных нет ссылок.")


@dp.message(Command(commands=['delete_link']))
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
# @dp.message(Command(commands=['help']))
# async def process_help_command(message: Message):
#     await message.answer(
#         'help text'
#     )




