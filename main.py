import os
import telebot
import tempfile
import time
from PIL import ImageGrab
import subprocess
import cv2

# ВАЖНО: Модуль pyautogui, команды ввода текста/Enter и их обработчики удалены.

API_TOKEN = '8577346503:AAFR-fUFsh7LGqNYh1BUTiSCPYeotFXD83k'
bot = telebot.TeleBot(API_TOKEN)

# --- Настройки для Запуска/Закрытия Приложений ---
APP_PATHS = {
    'telegram': r'C:\Users\user\Desktop\Telegram.lnk',
    'chrome': r'C:\Users\Public\Desktop\Google Chrome.lnk',
    'steam': r'C:\Users\Public\Desktop\Steam.lnk'
}

# --- Соответствие имени кнопки имени EXE файла для закрытия ---
APP_EXE_MAP = {
    'Telegram': 'Telegram.exe',
    'Chrome': 'chrome.exe',
    'Steam': 'Steam.exe',
    'Блокнот': 'notepad.exe'
}


# --- Вспомогательная Функция для поиска процесса (ОСТАВЛЕНА) ---
def find_process_pid(app_name):
    """Ищет PID процесса по имени для его закрытия."""
    try:
        result = subprocess.run(
            ['tasklist', '/FI', f'IMAGENAME eq {app_name}'],
            capture_output=True,
            text=True,
            check=True
        )
        if app_name in result.stdout:
            lines = result.stdout.strip().split('\n')
            for line in lines[3:]:
                if line.startswith(app_name):
                    return line.split()[1]
        return None
    except Exception:
        return None


# --- Обработчики Команд ---

@bot.message_handler(commands=['start'])
def send_welcome(message):
    # Основная клавиатура
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add("Получить скриншот", "Выключить")
    markup.add("Открыть приложение", "Закрыть приложение")
    markup.add("Получить фото с камеры")

    bot.send_message(message.chat.id, '👋 Выберите действие:', reply_markup=markup)


@bot.message_handler(regexp='выключить')
def shutdown_pc(message):
    bot.send_message(message.chat.id, 'Выключаю...')
    os.system("shutdown -s -t 0")


@bot.message_handler(regexp='получить скриншот')
def get_screenshot(message):
    try:
        path = tempfile.gettempdir() + os.sep + 'screenshot.png'
        screenshot = ImageGrab.grab()
        screenshot.save(path, 'PNG')

        with open(path, 'rb') as photo:
            bot.send_photo(message.chat.id, photo)

    except Exception as e:
        bot.send_message(message.chat.id, f"Произошла ошибка при получении скриншота: {e}")


@bot.message_handler(regexp='получить фото с камеры')
def get_webcam_photo(message):
    bot.send_message(message.chat.id, 'Попытка получить фото с камеры. Ожидайте...')

    camera = cv2.VideoCapture(0)

    if not camera.isOpened():
        bot.send_message(message.chat.id, "Ошибка: Не удалось открыть веб-камеру. Возможно, она занята.")
        return

    for _ in range(10):
        camera.read()

    ret, frame = camera.read()

    camera.release()

    if ret:
        try:
            path = tempfile.gettempdir() + os.sep + 'webcam_photo.png'
            cv2.imwrite(path, frame)

            with open(path, 'rb') as photo:
                bot.send_photo(message.chat.id, photo)

        except Exception as e:
            bot.send_message(message.chat.id, f"Произошла ошибка при отправке фото: {e}")
    else:
        bot.send_message(message.chat.id, "Не удалось захватить кадр с камеры.")


# --- ОБНОВЛЕННАЯ ФУНКЦИЯ: Открытие Приложений (с кнопками) ---

@bot.message_handler(regexp='открыть приложение')
def request_open_app(message):
    # Создаем клавиатуру для выбора приложений
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True, row_width=2)

    # Добавляем кнопки с именами приложений (ключи словаря APP_PATHS)
    app_buttons = [key.capitalize() for key in APP_PATHS.keys()]
    markup.add(*app_buttons)

    # Добавляем кнопку "Назад"
    markup.add("Назад")

    msg = bot.send_message(message.chat.id,
                           f"Какое приложение открыть? Выберите из списка:",
                           reply_markup=markup)

    bot.register_next_step_handler(msg, open_app)


def open_app(message):
    app_key_capitalize = message.text.strip()
    app_key = app_key_capitalize.lower()

    # Обработка кнопки "Назад"
    if app_key_capitalize == "Назад":
        send_welcome(message)
        return

    # Находим путь к приложению
    if app_key in APP_PATHS:
        # Убираем клавиатуру выбора приложений
        markup_remove = telebot.types.ReplyKeyboardRemove()
        bot.send_message(message.chat.id, f"Попытка запустить **{app_key_capitalize}**...", reply_markup=markup_remove,
                         parse_mode='Markdown')

        try:
            app_path = APP_PATHS[app_key]
            # Используем 'start' для надежного открытия .lnk файлов
            subprocess.Popen(f'start "" "{app_path}"', shell=True)

            # Возвращаем основную клавиатуру после выполнения команды
            send_welcome(message)
            bot.send_message(message.chat.id, f"Приложение **{app_key_capitalize}** запущено.", parse_mode='Markdown')

        except Exception as e:
            # Возвращаем основную клавиатуру
            send_welcome(message)
            bot.send_message(message.chat.id, f"Ошибка при запуске: {e}")

    else:
        # Если пользователь ввел что-то, чего нет в списке
        bot.send_message(message.chat.id,
                         "Неизвестное приложение или некорректный выбор. Пожалуйста, выберите из предложенных кнопок.")
        # Повторяем запрос открытия
        request_open_app(message)


# --- Закрытие Приложений (с кнопками, без изменений) ---

@bot.message_handler(regexp='закрыть приложение')
def request_close_app(message):
    # Создаем клавиатуру с именами приложений из словаря
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True, row_width=2)

    app_buttons = list(APP_EXE_MAP.keys())
    markup.add(*app_buttons)

    markup.add("Отмена")  # Оставим "Отмена", как было в этой функции

    msg = bot.send_message(message.chat.id,
                           f"Какое приложение закрыть? Выберите из списка:",
                           reply_markup=markup)

    bot.register_next_step_handler(msg, close_app)


def close_app(message):
    user_choice = message.text.strip()

    if user_choice == "Отмена":
        send_welcome(message)
        return

    if user_choice in APP_EXE_MAP:
        app_name = APP_EXE_MAP[user_choice]

        markup_remove = telebot.types.ReplyKeyboardRemove()
        bot.send_message(message.chat.id, f"Попытка закрыть **{user_choice}**...", reply_markup=markup_remove,
                         parse_mode='Markdown')

        try:
            subprocess.run(['taskkill', '/IM', app_name, '/F'], check=True, capture_output=True)

            send_welcome(message)
            bot.send_message(message.chat.id, f"Приложение **{user_choice}** ({app_name}) принудительно закрыто.",
                             parse_mode='Markdown')

        except subprocess.CalledProcessError:
            send_welcome(message)
            bot.send_message(message.chat.id,
                             f"Ошибка: Приложение **{user_choice}** не найдено или не может быть закрыто.",
                             parse_mode='Markdown')
        except Exception as e:
            send_welcome(message)
            bot.send_message(message.chat.id, f"Общая ошибка при закрытии: {e}")

    else:
        bot.send_message(message.chat.id,
                         "Неизвестное приложение или некорректный выбор. Пожалуйста, выберите из предложенных кнопок.")
        request_close_app(message)


bot.infinity_polling()