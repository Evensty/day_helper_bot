from aiogram import Bot, Dispatcher
from aiogram.filters import Command
from aiogram.types import Message
from sqlalchemy import select

from data.config import settings
from data.database import session_factory
from data.models import User

BOT_TOKEN = settings.BOT_TOKEN


# Создаем объекты бота и диспетчера
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# Этот хэндлер будет срабатывать на команду "/start"
@dp.message(Command(commands=['start']))
async def start_command_handler(message: Message):
    await message.answer('Привет!\nМеня зовут day_helper_bot!\nНапиши мне что-нибудь')
    user_id = message.from_user.id
    async with session_factory() as session:
        stmt = select(User).where(User.user_id == user_id)
        result = await session.execute(stmt)
        existing_user = result.scalars().first()

        if not existing_user:
            # Add new user to the database
            new_user = User(user_id=user_id)
            session.add(new_user)
            await session.commit()
            await message.reply("Вы успешно зарегистрированы!")
        else:
            await message.reply("Вы уже зарегистрированы!")


@dp.message(Command(commands=['users']))
async def list_users_handler(message: Message):
    async with session_factory() as session:
        async with session.begin():
            stmt = select(User)
            result = await session.execute(stmt)
            users = result.scalars().all()
            if users:
                users_list = "\n".join([f"ID: {user.id}, User ID: {user.user_id}" for user in users])
                await message.reply(f"Список пользователей:\n{users_list}")
            else:
                await message.reply("В базе данных нет пользователей.")




# # Этот хэндлер будет срабатывать на команду "/help"
# @dp.message(Command(commands=['help']))
# async def process_help_command(message: Message):
#     await message.answer(
#         'help text'
#     )



