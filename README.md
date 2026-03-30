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

+ aiogram (FSM)
+ MySQL
+ модульной структуры
  
Структура проекта:

routers/
states/
keyboards/
database/
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
2. Установить зависимости:
```
pip install -r requirements.txt
```
3. Создать .env файл:
```
BOT_TOKEN=your_token
PAYMENT_TOKEN_1=your_payment_token
```
4. Запустить бота:
```
python main.py
```

## 📌 В планах
+ 🔔 Уведомления об окончании подписки
+ 🖥️ Интеграция с WireGuard сервером
+ 🐳 Docker деплой
  
## 👩‍💻 Автор

**Алина** - начинающий backend-разработчик
