from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties

from data.config import settings

BOT_TOKEN = settings.BOT_TOKEN


# Создаем объекты бота и диспетчера
bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode='MarkdownV2'))
dp = Dispatcher()