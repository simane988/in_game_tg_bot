import os
import re
import time
import asyncio

import requests
import telegram.constants
from telegram import Bot
from telegram.error import TelegramError

# Конфигурация
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
TARGET_CHAT_ID = os.getenv('TARGET_CHAT_ID')
STEAM_API_KEY = os.getenv('STEAM_API_KEY')

# Список отслеживаемых пользователей steam
STEAM_IDS = {
    'Семён': '76561198409472880',
    'Илья': '76561198192926761',
    'Эмиль': '76561198157888681'
}

# Последние известные игры
LAST_KNOWN_STEAM_GAMES = {
    'Семён': None,
    'Илья':None,
    'Эмиль': None
}

# Кеш запросов в стим
steam_requests_delay = 5
steam_cache_len = int(60 / steam_requests_delay * 5)
steam_cache_threshold = 0.75
CACHE_STEAM_GAMES = {
    'Семён': [None] * steam_cache_len,
    'Илья': [None] * steam_cache_len,
    'Эмиль': [None] * steam_cache_len
}

# Соответствие имени и тега в telegram
TELEGRAM_IDS = {
    'Семён': '396770433',
    'Илья': '1380077865',
    'Эмиль': '704174263'
}


def get_steam_user_games(steam_id):
    url = f'https://api.steampowered.com/ISteamUser/GetPlayerSummaries/v0002/?key={STEAM_API_KEY}&steamids={steam_id}'
    try:
        response = requests.get(url, timeout=10).json()
        if 'gameextrainfo' in response['response']['players'][0]:
            return response['response']['players'][0]['gameextrainfo']
        else:
            return None
    except Exception as e:
        print(f"Ошибка запроса {url} Steam API: {e}")
        return None


def send_telegram_message(message):
    """Отправить сообщение в Telegram чат"""
    try:
        bot = Bot(token=TELEGRAM_BOT_TOKEN)
        asyncio.run(bot.send_message(chat_id=TARGET_CHAT_ID, text=message, parse_mode=telegram.constants.ParseMode.MARKDOWN))
    except TelegramError as e:
        print(f"Ошибка отправки в Telegram: {e}")


def check_activities():
    """Проверить активность всех пользователей"""
    for name, steam_id in STEAM_IDS.items():

        current_game = get_steam_user_games(steam_id)
        print(f"{name} steam_id: {steam_id}, game: {current_game}")
        CACHE_STEAM_GAMES[name].pop(0)
        CACHE_STEAM_GAMES[name].append(current_game)

        previous_game = LAST_KNOWN_STEAM_GAMES[name]

        if ((current_game != previous_game) and
                (CACHE_STEAM_GAMES[name].count(current_game) / len(CACHE_STEAM_GAMES[name]) >= steam_cache_threshold)):
            if current_game:
                send_telegram_message(
                    f"🎮 [{name}](tg://user?id={TELEGRAM_IDS[name]}) начал играть в _{current_game}_",
                )
            elif previous_game:
                send_telegram_message(
                    f"❌ [{name}](tg://user?id={TELEGRAM_IDS[name]}) вышел из игры _{previous_game}_"
                )

            LAST_KNOWN_STEAM_GAMES[name] = current_game

        time.sleep(steam_requests_delay)  # Задержка между запросами к API


if __name__ == '__main__':
    print("Бот запущен...")
    while True:
        check_activities()
        time.sleep(30)