import re
import subprocess

from config import ALLOWED_USERS, REFERENCE_METADATA_MAP


# Функция для проверки, разрешён ли пользователь
def is_allowed_user(user_id):
    return user_id in ALLOWED_USERS


# Функция для очистки имени файла
def sanitize_filename(filename):
    return re.sub(r'[<>:"/\\|?*]', '-', filename)


# Функция для извлечения метаданных с помощью ExifTool
def extract_metadata_exiftool(file_path):
    result = subprocess.run(['exiftool', file_path], stdout=subprocess.PIPE)

    try:
        metadata_str = result.stdout.decode('cp1251')
    except UnicodeDecodeError:
        metadata_str = result.stdout.decode('latin-1', errors='ignore')

    metadata = {}
    for line in metadata_str.splitlines():
        if ": " in line:
            key, value = line.split(": ", 1)
            metadata[key.strip()] = value.strip()

    return metadata


# Вспомогательная функция для проверки метаданных
def check_field(metadata, key, reference, error_list, error_msg):
    if metadata.get(key) != reference:
        error_list.append(error_msg)


def get_reference_metadata(producer):
    """Возвращает референсные значения для указанного Producer."""
    return REFERENCE_METADATA_MAP.get(producer, None)


# Функция проверки метаданных на соответствие эталону
def check_metadata(metadata, REFERENCE_METADATA):
    errors = []  # Список для сбора всех ошибок
    # Извлекаем Producer из метаданных
    producer = metadata.get("Producer", "")

    # Получаем референсные значения на основе Producer
    REFERENCE_METADATA = get_reference_metadata(producer)

    if REFERENCE_METADATA is None:
        return False, f"Референсные значения для Producer '{producer}' не найдены."

    # Проверяем соответствие Creator, Producer, ModDate, CreationDate
    if metadata.get("Creator") != REFERENCE_METADATA["Creator"]:
        errors.append("Creator не совпадает.")
    if metadata.get("Producer") != REFERENCE_METADATA["Producer"]:
        errors.append("Producer не совпадает.")
    if metadata.get("ModDate") != metadata.get("CreationDate"):
        errors.append("ModDate и CreationDate не совпадают.")
    if metadata.get("PDF Version") != REFERENCE_METADATA["PDFVersion"]:
        errors.append("PDF Version не совпадает.")


    # Проверяем размер файла
    file_size = int(metadata.get("File Size", "0").split()[0]) * 1024  # Конвертируем в байты
    if not (REFERENCE_METADATA["FileSize"][0] <= file_size <= REFERENCE_METADATA["FileSize"][1]):
        errors.append("Размер файла не в пределах допустимого диапазона.")

    # Проверяем другие параметры
    if metadata.get("File Type") != REFERENCE_METADATA["FileType"]:
        errors.append("FileType не совпадает.")
    if metadata.get("File Type Extension") != REFERENCE_METADATA["FileTypeExtension"]:
        errors.append("FileTypeExtension не совпадает.")
    if metadata.get("MIME Type") != REFERENCE_METADATA["MIMEType"]:
        errors.append("MIMEType не совпадает.")
    if metadata.get("Linearized") != REFERENCE_METADATA["Linearized"]:
        errors.append("Linearized не совпадает.")
    if metadata.get("Tagged PDF") != REFERENCE_METADATA["TaggedPDF"]:
        errors.append("Tagged PDF не совпадает.")
    if int(metadata.get("Page Count", "0")) != REFERENCE_METADATA["PageCount"]:
        errors.append("Количество страниц не совпадает.")

    # Если ошибок нет, чек подлинный
    if not errors:
        return True, "Чек подлинный."
    else:
        # Возвращаем False и список ошибок
        return False, "\n".join(errors)

