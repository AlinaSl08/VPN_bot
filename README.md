# VPN Telegram Bot

Telegram-бот для продажи и автоматической выдачи VPN-доступа (**WireGuard**).

## 🚀 Функционал

+ 💳 Покупка подписки через Telegram Payments
+ 🎁 Пробный период (7 дней)
+ 🔄 Продление подписки
+ 📅 Отслеживание срока действия
+ 👤 Профиль пользователя
+ ⚙️ Админ-панель (изменение тарифов)
+ 🔐 Выдача доступа (QR / конфиг)
  
## 🧠 Архитектура

Проект построен с использованием:

+ Python (aiogram 3.x)
+ MySQL
+ модульной структуры
  
Структура проекта:

commands/
database/
keyboards/
routers/
services/
states/
utils/


## 💾 База данных

Основные таблицы:

+ users
+ tariffs
+ subscriptions
+ profile

## 💳 Оплата

Реализована через Telegram Payments API:

+ создание invoice
+ обработка оплаты
+ активация подписки

## 🔧 Технологии

+ Python 3.11+
+ aiogram 3.x
+ MySQL
+ dotenv
  
## ⚙️ Установка

1. Клонировать репозиторий:
```
git clone https://github.com/AlinaSl08/VPN_bot.git
```
2. Создать .env файл.
Скопировать .env.example и заполнить:

3. Запуск проекта:
```
docker compose up -d --build
```
4. Проверка работы:
```
docker ps
```
или открыть Telegram бот и написать /start

5. Обновление проекта
```
git pull
docker compose up -d --build
```
⚙️ Локальный запуск (без Docker)
```
pip install -r requirements.txt
python src/main.py
```

## 👩‍💻 Автор

**Алина** - начинающий backend-разработчик
