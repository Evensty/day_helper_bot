import logging
import types

from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, ForceReply, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery, \
    ReplyKeyboardMarkup, KeyboardButton
from sqlalchemy import select, delete
from sqlalchemy.exc import SQLAlchemyError
from typer.cli import callback

from bot import bot
from data.database import session_factory
from data.models import User, Task, Link
from data.orm import ORM


router = Router()


@router.message(F.data.startswith =='/addtask')
async def add_task_handler(message: Message):
    # Разбор аргументов команды
    command_parts = message.text.split(" ", 1)
    if len(command_parts) < 2 or not command_parts[1].strip():
        await message.reply(escape_md("Введите описание задачи: `/addtask <описание задачи>`"))
        return

    task_text = command_parts[1].strip()
    user_id = message.from_user.id

    async with session_factory() as session:
        try:
            result = await session.execute(select(User).where(User.user_id == user_id))
            user = result.scalars().first()

            if not user:
                await message.reply("Пользователь не найден! Возможно, вам нужно зарегистрироваться.")
                return

            new_task = Task(user_id=user.user_id, task_text=task_text)
            session.add(new_task)
            await session.commit()

            await message.reply("Задача успешно добавлена!")

        except SQLAlchemyError as e:
            logging.error(f"Ошибка базы данных: {e}")
            await message.reply("Произошла ошибка при добавлении задачи. Попробуйте позже.")

@router.message(F.text =='/edittask')
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


# Функция для создания кнопки
def get_tasks_button():
    button = KeyboardButton(text="📋 Показать задачи")
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=False, keyboard=[[button]])
    return keyboard

# Функция для создания кнопок для каждой задачи
def get_task_buttons(tasks):
    inline_buttons = []  # Список для кнопок
    for task in tasks:
        button = InlineKeyboardButton(
            text=f"Удалить задачу ID:{task.task_id}",
            callback_data=f'deltask {task.task_id}')
        inline_buttons.append([button])

    keyboard = InlineKeyboardMarkup(row_width=1, inline_keyboard=inline_buttons)
    return keyboard


@router.message(F.text == '/tasks')
async def get_task_list_handler(message: Message):
    async with session_factory() as session:
        user_id = message.from_user.id
        stmt = select(Task).where(Task.user_id == user_id)
        result = await session.execute(stmt)
        tasks = result.scalars().all()

        if not tasks:
            await message.reply(escape_md("В базе данных нет задач."))
            return
        task_lines = [
            f"**{i}** ID:{task.task_id} {escape_md(task.created_at.strftime('%d.%m.%Y'))} {escape_md(task.task_text)}"
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
            await message.answer(f"Список задач:\n{part}", reply_markup=keyboard, parse_mode="MarkdownV2")
            start_idx += num_lines  # Смещаем индекс начала для следующего блока


@router.callback_query(F.data.startswith("deltask"))
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
            await callback.answer("Задача удалена!", show_alert=True)
            await callback.message.delete()  # Удаляем сообщение с задачами
        else:
            await callback.answer("Задача не найдена или уже удалена.", show_alert=True)





            # args = message.text.split(maxsplit=1)
            # if len(args) < 2:
            #     await message.reply("Пожалуйста, укажите ID задач для удаления, разделяя их пробелами.")
            #     return
            #
            # # Извлекаем часть с ID задач
            # args = args[1]
            #
            # if not args:
            #     await message.reply("Пожалуйста, укажите ID задач для удаления, разделяя их пробелами.")
            #     return
            # # Разделяем аргументы и пытаемся привести их к целым числам
            # try:
            #     user_id = message.from_user.id
            #     task_ids = [int(task_id) for task_id in args.split()]
            # except ValueError:
            #     await message.reply("Все ID должны быть числами. Проверьте ввод и попробуйте снова.")
            #     return
            #
            # stmt = delete(Task).where(Task.task_id.in_(task_ids), Task.user_id == user_id)
            # result = await session.execute(stmt)
            #
            # deleted_count = result.rowcount
            #
            # if deleted_count:
            #     await message.reply(f"Удалено задач: {deleted_count}.")
            # else:
            #     await message.reply("Не найдено задач с указанными ID.")
