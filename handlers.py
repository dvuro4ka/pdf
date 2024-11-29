import logging
import os
import shutil

from telegram import Update, KeyboardButton, ReplyKeyboardMarkup
from telegram.ext import CallbackContext

from check_scaner import visual_check
from config import producers, REFERENCE_METADATA_MAP
from database import update_user_checks, get_user_without_zero, \
    get_id_users, get_active_users_today, get_active_users_yesterday, get_active_users_week, calculate_all_user
from utils import sanitize_filename, extract_metadata_exiftool, check_metadata


# Обработчик для отправки клавиатуры пользователю
def send_menu(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id

    # Выводим информацию о пользователе user_info = get_user_info(user_id) update.message.reply_text( f"ID: {
    # user_info[0]}\nUsername: {user_info[1]}\nКоличество проверок: {user_info[2]}\nДата первого запуска: {user_info[
    # 3]}\nДата последней проверки: {user_info[4]}")

    # Создаём клавиатуру
    keyboard = [
        [KeyboardButton("Проверить чек"), KeyboardButton("Узнать метаданные")],
        [KeyboardButton("Обратиться в поддержку")], [KeyboardButton("Использовать зеркало")]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)
    update.message.reply_text("Выбери действие:", reply_markup=reply_markup)
    logging.info(f"Пользователь {user_id} открыл меню.")


def get_stats(update: Update, context: CallbackContext):
    keyboard = [
        [KeyboardButton("За сегодня"), KeyboardButton("За Вчера")],
        [KeyboardButton("Все пользователи")],
        [KeyboardButton("Назад")]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)
    username = update.message.from_user.username
    update.message.reply_text(
        f"Выбери действие: \n\nЗа сегодня - выгружает статистику использования бота за сегодня\n\nЗа Вчера - "
        f"выгружает статистику бота за вчерашний день\n\nВсе пользователи - показывает всех пользователей, "
        f"кто хотя бы раз проверил чек",
        reply_markup=reply_markup)
    json_dump = get_user_without_zero()
    result_string = "\n".join(item.strip("' \n") for item in json_dump)
    today = get_active_users_today()
    yesterday = get_active_users_yesterday()
    week = get_active_users_week()
    all = calculate_all_user()
    update.message.reply_text(f"За сегодня - {today}")
    update.message.reply_text(f"За вчера - {yesterday}")
    update.message.reply_text(f"За неделю - {week}")
    update.message.reply_text(f"Всего пользователей в боте - {all}")
    # print(result_string)
    logging.info(f"Пользователь {username} Выгрузил стату.")


# Функция для рассылки сообщений всем пользователям
def send_broadcast_message(context: CallbackContext, message: str):
    users = get_id_users()
    for user_id in users:
        print(user_id)
        try:
            context.bot.send_message(chat_id=user_id, text=message)
            logging.info(f"Сообщение отправлено пользователю {user_id}")
        except Exception as e:
            logging.error(f"Ошибка при отправке сообщения пользователю {user_id}: {e}")


# Обработчик выбора действия пользователем
def handle_action(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    user_name = update.message.from_user
    text = update.message.text

    if text == "Проверить чек":
        context.user_data['action'] = 'check'
        keyboard = [
            [KeyboardButton("Назад")],
            [KeyboardButton("Обратиться в поддержку")]
        ]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)
        update.message.reply_text("Отправьте PDF-чек для проверки.", reply_markup=reply_markup)
        logging.info(f"Пользователь {user_id} выбрал проверку чека.")

    elif text == "Узнать метаданные":
        keyboard = [
            [KeyboardButton("Назад")],
            [KeyboardButton("Обратиться в поддержку")]
        ]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)
        update.message.reply_text("Отправьте PDF-файл для извлечения метаданных.", reply_markup=reply_markup)
        context.user_data['action'] = 'get_metadata'
        logging.info(f"Пользователь {user_id} выбрал получение метаданных.")

    elif text == "Назад":
        # Создаём клавиатуру
        keyboard = [
            [KeyboardButton("Проверить чек"), KeyboardButton("Узнать метаданные")],
            [KeyboardButton("Обратиться в поддержку")], [KeyboardButton("Использовать зеркало")]
        ]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)
        update.message.reply_text("Выбери действие:", reply_markup=reply_markup)
        # Сбрасываем флаг поддержки, если он был установлен
        context.user_data['support_mode'] = False
        logging.info(f"Пользователь {user_id} вернулся в меню.")

    elif text == "Обратиться в поддержку":
        keyboard = [
            [KeyboardButton("Назад")]
        ]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)
        update.message.reply_text(
            "Готов выслушать ваше предложение / проблему.\nНапишите прямо тут и получите ответ в ближайшее время!",
            reply_markup=reply_markup
        )
        # Устанавливаем флаг, что пользователь находится в режиме поддержки
        context.user_data['support_mode'] = True
        logging.info(f"Пользователь {user_id} выбрал меню поддержка.")

    elif context.user_data.get('support_mode', False):
        # Если пользователь в режиме поддержки
        if text == "Назад":
            # Возврат в главное меню
            keyboard = [
                [KeyboardButton("Проверить чек"), KeyboardButton("Узнать метаданные")],
                [KeyboardButton("Обратиться в поддержку")], [KeyboardButton("Использовать зеркало")]
            ]
            reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)
            update.message.reply_text("Вы вернулись в главное меню.", reply_markup=reply_markup)
            context.user_data['support_mode'] = False
            logging.info(f"Пользователь {user_id} вышел из режима поддержки.")
        else:
            # Отправка сообщения администратору
            admin_id = 6015351108
            try:
                context.bot.send_message(
                    chat_id=admin_id,
                    text=f"Сообщение от пользователя {user_id} c @{user_name['username']}:\n{text}"
                )
                keyboard = [
                    [KeyboardButton("Проверить чек"), KeyboardButton("Узнать метаданные")],
                    [KeyboardButton("Обратиться в поддержку")], [KeyboardButton("Использовать зеркало")]
                ]
                reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)
                update.message.reply_text("Ваше сообщение отправлено. Мы ответим вам в ближайшее время!",
                                          reply_markup=reply_markup)

                logging.info(f"Сообщение от пользователя {user_id} отправлено администратору: {text}")
            except Exception as e:
                keyboard = [
                    [KeyboardButton("Проверить чек"), KeyboardButton("Узнать метаданные")],
                    [KeyboardButton("Обратиться в поддержку")], [KeyboardButton("Использовать зеркало")]
                ]
                reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)
                update.message.reply_text(f"Кажется, произошла ошибка:\n\n{e}\n\n Напишите напрямую мне: @midtownbas",
                                          reply_markup=reply_markup)

    elif text == "Пришли статистику всех пользователей":
        get_stats(update, context)

    elif text == "Использовать зеркало":
        context.user_data['action'] = 'glasses'
        keyboard = [
            [KeyboardButton("Назад")],
            [KeyboardButton("Обратиться в поддержку")]
        ]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)
        update.message.reply_text("Отправьте PDF-чек для проверки.", reply_markup=reply_markup)
        logging.info(f"Пользователь {user_id} выбрал проверку чека через зеркало.")


# Обработчик сообщений с PDF
def handle_pdf(update: Update, context: CallbackContext):
    global safe_file_name
    user_id = update.message.from_user.id
    user_name = update.message.from_user
    file = update.message.document
    if file.mime_type == 'application/pdf':
        try:
            file_obj = file.get_file()
            safe_file_name = sanitize_filename(file.file_name)
            file_path = f"./check/{safe_file_name}"
            file_obj.download(file_path)
            logging.info(f"Получен файл: {safe_file_name} от пользователя {user_id}")
            exiftool_metadata = extract_metadata_exiftool(file_path)
            producer = exiftool_metadata.get("Producer", "")
            creator = exiftool_metadata.get("Creator", "")
            diversion = exiftool_metadata.get("PDF Version", "")
            create_date = exiftool_metadata.get("Create Date", "")
            mod_date = exiftool_metadata.get("Modify Date", "")
            page_count = exiftool_metadata.get("Page Count", "")
            file_size = exiftool_metadata.get("File Size", "")
            action = context.user_data.get('action')

            if action == 'get_metadata':
                metadata_str = "\n".join([f"{key}: {value}" for key, value in exiftool_metadata.items()])
                update.message.reply_text(f"Метаданные PDF:\n{metadata_str}")

                logging.info(f"Отправлены метаданные для файла: {safe_file_name}")

            elif action == 'check':
                logging.info(f"будем чекать")
                if producer in producers:
                    logging.info(f"Producer '{producer}' найден в списке разрешённых., работаем дальше")
                    # print(f"cr - {creator}\npr - {producer}\npdfv - {diversion}")
                    if (creator == "JasperReports Library version 6.5.1" and producer == "iText 2.1.7 by 1T3XT" and
                            (diversion == "1.3" or diversion == "1.5")):
                        print(f'зашли проверять по визуалу @{user_name["username"]}')
                        update.message.reply_text(
                            f'зашли проверять по визуалу, сейчас проверки занимают больше 2 минут')
                        # Укажите путь к исходному файлу и путь к дубликату с новым именем
                        source_file = f'{file_path}'
                        duplicate_file = f'./check/sber_{user_id}.pdf'
                        # Скопируйте файл
                        shutil.copy(source_file, duplicate_file)
                        delta, timer = visual_check(duplicate_file)
                        #delta, timer = [0.99,0]
                        #print(delta)
                        if delta != 0:
                            new_file_path = os.path.splitext(duplicate_file)[0] + '.png'
                            # print(new_file_path)
                            try:
                                context.bot.send_document(chat_id=user_id, document=open(new_file_path, 'rb'),
                                                          caption=f"Братик, присмотрись, по визуалу чек отличается в этих местах. Время проверки заняло: {timer} секунд")
                                update.message.reply_text(
                                    f"Будь осторожен, чек схож с оригиналом на {delta:.2f}.")

                            except Exception as e:
                                update.message.reply_text(f"Ошибка при отправке документа: {e}, но его коэф схожести такой: {delta}")

                        else:
                            update.message.reply_text(f"Чек {safe_file_name} по визуалу прошёл проверку. за {timer} секунд")
                    # print(f"сломался сразу после проверки на визуальную составляющую")
                    if producer in REFERENCE_METADATA_MAP:
                        reference_metadata = REFERENCE_METADATA_MAP[producer]
                        print(creator, producer, diversion, int(file_size.split()[0]))
                        if (creator == "JasperReports Library version 6.5.1" and producer == "iText 2.1.7 by 1T3XT" and
                                diversion == "1.3" and (50*1024 <= int(file_size.split()[0])*1024 <= 53*1024 or 108*1024 <= int(file_size.split()[0])*1024 <= 112*1024)):
                            print("Зашли")
                            is_valid, message = [True, ""]

                        else:
                            is_valid, message = check_metadata(exiftool_metadata, reference_metadata)
                        # print(f"сломался сразу после проверки на валидность")
                        logging.info(f"valid? - {is_valid}, msg = {message}")
                        if is_valid:
                            update.message.reply_text(f"Чек {safe_file_name} по метаданным выглядит хорошо.\n\n"
                                                      f"Producer = {producer}\nCreator = {creator}\nCreate Date = "
                                                      f"{create_date}\nModify Date = {mod_date}\n"
                                                      f"PDF Version = {diversion}\nВес = {file_size}\n"
                                                      f"Page Count = {page_count}")
                            # update.message.reply_text(f"Producer '{producer}' найден в списке разрешённых. и на первый взгляд Чек {safe_file_name} подлинный.")
                            logging.info(f"Чек {safe_file_name} по метаданным выглядит хорошо.")
                        else:
                            update.message.reply_text(f"Чек {safe_file_name} поддельный. Причины:\n{message}")
                            logging.warning(f"Чек поддельный: {safe_file_name}. Причины: {message}")
                else:
                    update.message.reply_text(f"Чек {safe_file_name} поддельный. Причины: Слишком плохо сделан")
                    logging.warning(
                        f"Чек поддельный: {safe_file_name}. Причины: Producer '{producer}' не найден в списке разрешённых.")
                # Обновляем количество проверок пользователя
                update_user_checks(user_id)

            elif action == 'glasses':
                logging.info(f"Используется зеркало")
        except Exception as e:
            update.message.reply_text("Произошла ошибка при обработке файла.")
            logging.error(f"Ошибка при обработке файла {safe_file_name}: {e}")
    else:
        update.message.reply_text("Пожалуйста, отправьте PDF-файл.")
        logging.warning(f"Получен файл неподходящего формата от пользователя {user_id}")
