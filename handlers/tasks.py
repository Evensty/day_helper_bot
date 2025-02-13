import logging
import types

from aiogram import Router, types, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import Message, ForceReply, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery, \
    ReplyKeyboardMarkup, KeyboardButton
from sqlalchemy import select, delete
from sqlalchemy.exc import SQLAlchemyError

from bot import bot
from data.database import session_factory
from data.models import User, Task, Link


router = Router()


# Определяем состояние для ввода задачи
class TaskState(StatesGroup):
    waiting_for_task = State()

@router.callback_query(F.data == "add_task")
async def ask_for_task(callback: CallbackQuery, state: FSMContext):
    await callback.message.delete()
    """Запрашиваем у пользователя текст задачи"""
    await callback.message.answer("✏ Введите описание задачи:")
    await state.set_state(TaskState.waiting_for_task)

@router.message(TaskState.waiting_for_task)
async def add_task_handler(message: Message, state: FSMContext):
    async with session_factory() as session:
        # Extract task description
        new_task_text = message.text.strip()
        if not new_task_text:
            await message.answer(escape_md("⚠ Описание задачи не может быть пустым!"))
            return
        # Add task to the database
        user_id = message.from_user.id
        result = await session.execute(select(User).where(User.user_id == user_id))
        user = result.scalars().first()
        if not user:
            await message.answer(escape_md("Пользователь не найден!"))
            return
        new_task = Task(user_id=user.user_id, task_text=new_task_text)
        session.add(new_task)
        await session.commit()
        await message.answer(escape_md("Задача успешно добавлена!"), reply_markup=get_main_keyboard())
        await state.clear()  # Выходим из состояния


@router.message(F.text.startswith('/edittask'))
async def edit_task_handler(message: Message):
    async with session_factory() as session:
        async with session.begin():
            try:
                # Извлечение ID задачи
                args = message.text[len("/edittask "):].strip()
                if not args.isdigit():
                    await message.reply("Используйте: /edittask <ID задачи>, где ID задачи — число.")
                    return

                task_id = int(args)
                user_id = message.from_user.id

                # Поиск задачи в базе данных
                result = await session.execute(
                    select(Task).where(Task.task_id == task_id, Task.user_id == user_id)
                )
                task = result.scalars().first()

                if not task:
                    await message.reply("Задача с указанным ID не найдена или она вам не принадлежит.")
                    return

                # Отправка сообщения с кнопкой ForceReply, подставляя старое описание задачи
                await message.reply(
                    f"Редактирование задачи #{task_id}:\n"
                    f"Старый текст: \"{task.task_text}\"\n\n"
                    f"Введите новый текст задачи:",
                    reply_markup = ForceReply(input_field_placeholder="Введите новый текст задачи...")
                )

            except SQLAlchemyError as e:
                # Обработка ошибок базы данных
                await message.reply("Произошла ошибка при подготовке к редактированию задачи. Попробуйте позже.")
                print(f"Ошибка базы данных: {e}")


@router.message(lambda message: message.reply_to_message and "Редактирование задачи" in message.reply_to_message.text)
async def save_edited_task_handler(message: Message):
    async with session_factory() as session:
        async with session.begin():
            try:
                # Извлечение ID задачи из текста оригинального сообщения
                original_text = message.reply_to_message.text
                task_id_start = original_text.find("#") + 1
                task_id_end = original_text.find(":", task_id_start)
                task_id_str = original_text[task_id_start:task_id_end].strip()

                if not task_id_str.isdigit():
                    await message.reply("Ошибка при обработке ID задачи.")
                    return

                task_id = int(task_id_str)
                user_id = message.from_user.id

                # Поиск задачи в базе данных
                result = await session.execute(
                    select(Task).where(Task.task_id == task_id, Task.user_id == user_id)
                )
                task = result.scalars().first()

                if not task:
                    await message.reply("Задача не найдена или она вам не принадлежит.")
                    return

                # Обновление задачи
                new_task_text = message.text.strip()
                if not new_task_text:
                    await message.reply("Описание задачи не может быть пустым.")
                    return

                task.task_text = new_task_text
                await session.commit()
                await message.reply(f"Задача #{task_id} успешно обновлена: {new_task_text}")

            except SQLAlchemyError as e:
                # Обработка ошибок базы данных
                await message.reply("Произошла ошибка при редактировании задачи. Попробуйте позже.")
                print(f"Ошибка базы данных: {e}")

def escape_md(text: str) -> str:
    """
    Экранирует специальные символы для Markdown.
    """
    escape_chars = r"_*[]()~`>#+-=|{}.!"
    return "".join(f"\\{char}" if char in escape_chars else char for char in text)

async def split_message(text, limit=4000):
    parts, current = [], ""
    for line in text.split("\n"):
        if len(current) + len(line) + 1 > limit:
            parts.append(current)
            current = line
        else:
            current += "\n" + line if current else line
    if current:
        parts.append(current)
    return parts

# Словарь для хранения последних сообщений с задачами
user_last_messages = {}

def get_main_keyboard():
    inline_buttons = [
        [InlineKeyboardButton(text="➕ Добавить задачу", callback_data="add_task")],
        [InlineKeyboardButton(text="📋 Показать задачи", callback_data="show_tasks")]
    ]
    keyboard = InlineKeyboardMarkup(inline_keyboard=inline_buttons)
    return keyboard

# Функция для создания кнопок для каждой задачи
def get_task_buttons(tasks):
    inline_buttons = []  # Список для кнопок
    for i, task in enumerate(tasks):
        button = InlineKeyboardButton(
            text=f"Удалить задачу {i+1}",
            callback_data=f'delete_task {task.task_id}')
        inline_buttons.append([button])

    keyboard = InlineKeyboardMarkup(inline_keyboard=inline_buttons)
    return keyboard


@router.callback_query(F.data.startswith('remove_keyboard'))
async def remove_keyboard(callback: CallbackQuery):
    await callback.message.edit_text('Клавиатура удалена', reply_markup=None)
    await callback.answer()

@router.callback_query(F.data.startswith('show_tasks'))
async def get_task_list_handler(callback: CallbackQuery, state: FSMContext):
    await callback.message.delete()
    async with session_factory() as session:
        user_id = callback.from_user.id
        stmt = select(Task).where(Task.user_id == user_id)
        result = await session.execute(stmt)
        tasks = result.scalars().all()

        # Удаляем старые сообщения
        if user_id in user_last_messages:
            for msg_id in user_last_messages[user_id]:
                try:
                    await callback.message.bot.delete_message(chat_id=user_id, message_id=msg_id)
                except Exception:
                    pass  # Если сообщение уже удалено, игнорируем ошибку

                # Очищаем список сообщений пользователя
                user_last_messages[user_id] = []

        if not tasks:
            await callback.answer("У вас пока нет задач", show_alert=False)
            new_msg = await callback.message.answer("Выбери действие", reply_markup=get_main_keyboard())
            user_last_messages[user_id] = [new_msg.message_id]

            return
        task_lines = [
            f"*{i}* {escape_md(task.created_at.strftime('%d.%m.%Y'))} {escape_md(task.task_text)}"
            for i, task in enumerate(tasks, start=1)
        ]
        # Разбиваем список задач на части
        task_parts = await split_message("\n".join(task_lines))

        # Генерируем сообщения и кнопки для каждой части
        start_idx = 0
        for part in task_parts:
            # Определяем, какие задачи входят в этот кусок текста
            num_lines = part.count("\n") + 1  # Количество задач в этой части
            tasks_in_part = tasks[start_idx:start_idx + num_lines]  # Выбираем соответствующие задачи
            keyboard = get_task_buttons(tasks_in_part)  # Создаем кнопки только для этих задач

            # Отправка сообщения с задачами и клавиатурой
            new_msg = await callback.message.answer(f"Список задач:\n{part}", reply_markup=keyboard, parse_mode="MarkdownV2")
            start_idx += num_lines  # Смещаем индекс начала для следующего блока

        # Сохраняем ID нового сообщения
        user_last_messages[user_id] = [new_msg.message_id]
        await callback.message.answer('Выбери действие', reply_markup=get_main_keyboard())


@router.callback_query(F.data.startswith("delete_task"))
async def delete_task_handler(callback: CallbackQuery, state: FSMContext):
    task_id = int(callback.data.split()[1])  # Получаем ID задачи из callback_data
    user_id = callback.from_user.id

    async with session_factory() as session:
        stmt = select(Task).where(Task.task_id == task_id, Task.user_id == user_id)
        result = await session.execute(stmt)
        task = result.scalar()

        if task:
            await session.delete(task)
            await session.commit()
            await callback.answer("Задача удалена!", show_alert=False)
            await callback.message.delete()  # Удаляем сообщение с задачами
        else:
            await callback.answer("Задача не найдена или уже удалена.", show_alert=False)

