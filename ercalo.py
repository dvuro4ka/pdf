from telethon import TelegramClient, events
from telethon.tl.types import Document

# Твои данные API
api_id = '26150447'
api_hash = '8f91d54f1ef3e0edfafd3b3125818926'
# Имена ботов
pdf_bot_username = 'pdf4ek_bot'  # Бот, от которого приходит PDF
target_bot_username = 'dvuro4ka'  # Бот, которому отправляем PDF

# Создаём клиент
client = TelegramClient('userbot_session', api_id, api_hash)

# Обработчик для сообщений с PDF от бота @pdf4ek_bot
@client.on(events.NewMessage(from_users=pdf_bot_username))
async def handle_pdf_message(event):
    # Проверяем, есть ли в сообщении PDF-документ
    if event.document and isinstance(event.document, Document):
        # Отправляем PDF в другой бот
        sent_message = await client.send_file(target_bot_username, event.document)
        print(f"PDF отправлен в {target_bot_username}")

        # Ждём ответа от второго бота
        @client.on(events.NewMessage(from_users=target_bot_username))
        async def handle_response(response_event):
            # Пересылаем ответ обратно в @pdf4ek_bot
            await response_event.forward_to(pdf_bot_username)
            print("Ответ отправлен обратно в @pdf4ek_bot")

# Запускаем клиента
with client:
    print("Userbot запущен и ожидает сообщений...")
    client.run_until_disconnected()