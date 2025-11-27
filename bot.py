import os
import re
import time
import asyncio

import requests
import telegram.constants
from telegram import Bot
from telegram.error import TelegramError

# Конфигурация
TELEGRAM_BOT_TOKEN = os.getenv('TARGET_BOT_TOKEN')
CHAT_ID = os.getenv('TARGET_CHAT_ID')

# Список отслеживаемых пользователей steam
STEAM_IDS = {
    'Семён': '76561198409472880',
    'Илья': '76561198192926761',
    'Эмиль': '76561198157888681'
}

# Последние известные игры
last_known_games = {
    'Семён': None,
    'Илья':None,
    'Эмиль': None
}

# Соответствие имени и тега в telegram
telegram_ids = {
    'Семён': '396770433',
    'Илья': '1380077865',
    'Эмиль': '704174263'
}


def get_steam_user_games(steam_id):
    url = f'https://steamcommunity.com/profiles/{steam_id}?xml=1'
    try:
        response = requests.get(url, timeout=10, headers={'Cache-Control': 'no-cache'})
        cur_game = re.search(r'(?<=In-Game<br\/>).*(?=\]\])', response.text)
        if cur_game:
            return cur_game.group(0)
        else:
            return None
    except Exception as e:
        print(f"Ошибка запроса {url} Steam API: {e}")
        return None


def send_telegram_message(message):
    """Отправить сообщение в Telegram чат"""
    try:
        bot = Bot(token=TELEGRAM_BOT_TOKEN)
        asyncio.run(bot.send_message(chat_id=CHAT_ID, text=message, parse_mode=telegram.constants.ParseMode.MARKDOWN))
    except TelegramError as e:
        print(f"Ошибка отправки в Telegram: {e}")


def check_activities():
    """Проверить активность всех пользователей"""
    for name, steam_id in STEAM_IDS.items():
        current_game = get_steam_user_games(steam_id)
        print(f"{name} steam_id: {steam_id}, game: {current_game}")
        previous_game = last_known_games[name]

        if current_game != previous_game:
            if current_game:
                send_telegram_message(
                    f"🎮 [{name}](tg://user?id={telegram_ids[name]}) начал играть в _{current_game}_",
                )
            elif previous_game:
                send_telegram_message(
                    f"❌ [{name}](tg://user?id={telegram_ids[name]}) вышел из игры _{previous_game}_"
                )

            last_known_games[name] = current_game

        time.sleep(1)  # Задержка между запросами к API


if __name__ == '__main__':
    print("Бот запущен...")
    while True:
        check_activities()
        time.sleep(30)