import logging

def setup_logging():
    logging.basicConfig(
        filename='bot_log.log',  # Запись логов в файл
        level=logging.INFO,  # Уровень логирования (INFO, WARNING, ERROR)
        format='%(asctime)s - %(levelname)s - %(message)s'  # Формат логов\
    )
    logging.getLogger('easyocr').setLevel(logging.ERROR)
