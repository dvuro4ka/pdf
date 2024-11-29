from telegram.ext import Updater, CommandHandler, MessageHandler, Filters

from config import TOKEN
from database import init_db, add_user, delete_user
from handlers import send_menu, handle_action, handle_pdf, send_broadcast_message, get_stats
from logging_setup import setup_logging


# Обработчик команды для рассылки
def broadcast(update, context):
    if context.args:
        message = ' '.join(context.args)  # Сообщение, которое будет отправлено
        send_broadcast_message(context, message)
        update.message.reply_text('Сообщение отправлено всем пользователям.')
    else:
        update.message.reply_text('Пожалуйста, введите сообщение для рассылки.')


def start(update, context):
    user_id = update.message.from_user.id
    username = update.message.from_user.username

    # Добавляем пользователя в базу данных при первом запуске бота
    add_user(user_id, username)
    update.message.reply_text(
        'Привет! <b>Я - Бот проверки чеков на валидность</b>\n\n'
        'Проверяем:\n'
        '✅Сбер -> Сбер / СБП\n'
        '✅Т-банк -> Т-банк / СБП\n'
        '✅Втб -> Втб / СБП\n'
        '✅Альфа -> Альфа / СБП\n'
        '✅Яндекс банк -> СБП\n'
        '✅ОТП -> СБП\n'
        '✅Ozon -> СБП\n'
        '✅MTS bank -> СБП\n'
        '✅Росбанк -> СБП\n'
        '✅Ак Барс -> СБП\n'
        'Чтобы проверить чек или группу чеков, просто нажми на кнопку "Проверить чек"\n\n'
        'Если нет вашего банка, можно проверить метаданные, а также через кнопку обратной связи предложить ваш банк.',
        parse_mode='HTML'
    )

    send_menu(update, context)



def main():
    setup_logging()
    init_db()  # Инициализация базы данных
    updater = Updater(TOKEN, use_context=True)
    dp = updater.dispatcher
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("broadcast", broadcast))# Добавляем обработчик команды /broadcast
    dp.add_handler(CommandHandler("stats", get_stats))
    dp.add_handler(CommandHandler("delete_user", delete_user))
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_action))
    dp.add_handler(MessageHandler(Filters.document.mime_type("application/pdf"), handle_pdf))
    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
