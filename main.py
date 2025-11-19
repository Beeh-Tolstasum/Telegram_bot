import os
import telebot
import tempfile
import time
from PIL import ImageGrab
import subprocess

# ВАЖНО: Модуль pyautogui, команды ввода текста/Enter и их обработчики удалены.

API_TOKEN = '8577346503:AAFR-fUFsh7LGqNYh1BUTiSCPYeotFXD83k'
bot = telebot.TeleBot(API_TOKEN)

# --- Настройки для Запуска/Закрытия Приложений ---
APP_PATHS = {
    'telegram': r'C:\Users\user\Desktop\Telegram.lnk',
    'chrome': r'C:\Users\Public\Desktop\Google Chrome.lnk',
    'steam': r'C:\Users\Public\Desktop\Steam.lnk'
}


# --- Вспомогательная Функция для поиска процесса (ОСТАВЛЕНА, но не используется в close_app) ---
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
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)

    # Основные кнопки
    markup.add("Получить скриншот", "Выключить")

    # Обновленные кнопки
    markup.add("Открыть приложение", "Закрыть приложение")
    # Кнопки "Ввод текста" и "Нажать Enter" удалены.

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


# --- Обновленная функция: Открытие Приложений ---

@bot.message_handler(regexp='открыть приложение')
def request_open_app(message):
    apps = ", ".join(APP_PATHS.keys())
    msg = bot.send_message(message.chat.id, f"Какое приложение открыть? Доступно: **{apps}**", parse_mode='Markdown')
    bot.register_next_step_handler(msg, open_app)


def open_app(message):
    app_key = message.text.lower().strip()

    if app_key in APP_PATHS:
        try:
            app_path = APP_PATHS[app_key]
            # Используем 'start' для надежного открытия .lnk файлов
            subprocess.Popen(f'start "" "{app_path}"', shell=True)

            bot.send_message(message.chat.id, f"Приложение **{app_key}** запущено.", parse_mode='Markdown')
        except Exception as e:
            bot.send_message(message.chat.id, f"Ошибка при запуске: {e}")
    else:
        bot.send_message(message.chat.id, "Неизвестное приложение.")


# --- Функция: Закрытие Приложений (.exe) (Логика не изменена, она верна) ---

@bot.message_handler(regexp='закрыть приложение')
def request_close_app(message):
    msg = bot.send_message(message.chat.id,
                           f"Какое приложение закрыть? Введите имя exe файла (например, **Telegram.exe** или **chrome.exe**)",
                           parse_mode='Markdown')
    bot.register_next_step_handler(msg, close_app)


def close_app(message):
    app_name = message.text.strip().lower()

    try:
        # Принудительное завершение процесса через taskkill
        # Это стандартный и корректный способ. Проблема, скорее всего, в неточном имени процесса.
        subprocess.run(['taskkill', '/IM', app_name, '/F'], check=True, capture_output=True)
        bot.send_message(message.chat.id, f"Приложение **{app_name}** принудительно закрыто.", parse_mode='Markdown')
    except subprocess.CalledProcessError:
        bot.send_message(message.chat.id, f"Ошибка: Приложение **{app_name}** не найдено или не может быть закрыто.",
                         parse_mode='Markdown')
    except Exception as e:
        bot.send_message(message.chat.id, f"Общая ошибка при закрытии: {e}")


bot.infinity_polling()