import mysql.connector
import os
from dotenv import load_dotenv
import logging

load_dotenv('../.env')
PASSWORD = os.getenv("PASSWORD_DB")
DB_HOST = os.getenv("DB_HOST")
DB_USER = os.getenv("DB_USER")


class Database:
    def __init__(self, db_host, db_user, password, port):
        self.__conn = None
        self.connect_db(db_host, db_user, password, port)
        self.init_db()

    def connect_db(self, db_host, db_user, password, port):
        try:
            self.__conn = mysql.connector.connect(
                host=db_host,
                user=db_user,
                password=password,
                port=port)
            print("Подключение успешно!")
        except Exception as e:
            print("Подключение не удалось! Ошибка:", e)

    def init_db(self):
        with self.__conn.cursor() as cursor:
            cursor.execute("CREATE DATABASE IF NOT EXISTS clearnet_vpn_db;")
            cursor.execute("USE clearnet_vpn_db;")
            #на случай сброса бд(УДАЛЯЕТ ВСЮ БД БЕЗВОЗВРАТНО)
            #cursor.execute("DROP TABLE IF EXISTS users, tariffs, profile, subscriptions;")
            cursor.execute('''CREATE TABLE IF NOT EXISTS users(
                            id INT PRIMARY KEY AUTO_INCREMENT,
                            tg_id BIGINT NOT NULL UNIQUE);''')
            cursor.execute('''CREATE TABLE IF NOT EXISTS admins(
                                        id INT PRIMARY KEY AUTO_INCREMENT,
                                        tg_id BIGINT NOT NULL UNIQUE);''')
            #вынести в отдельную функцию после настройки админки logging.info('Админ успешно добавлен в БД')
            cursor.execute('''INSERT IGNORE INTO admins(tg_id)
                                        VALUES (967760347), (1926843289)''')

            cursor.execute('''CREATE TABLE IF NOT EXISTS profile(
                            id INT PRIMARY KEY AUTO_INCREMENT,
                            user_id INT NOT NULL,
                            trial_used BOOL DEFAULT TRUE,
                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE);''')
            cursor.execute('''CREATE TABLE IF NOT EXISTS tariffs(
                            id INT PRIMARY KEY AUTO_INCREMENT,
                            name VARCHAR(150) NOT NULL UNIQUE,
                            price INT NOT NULL,
                            duration_days INT NOT NULL,
                            is_active BOOL DEFAULT TRUE);''')
            cursor.execute('''INSERT IGNORE INTO tariffs(name, price, duration_days)
                            VALUES ('7 дней', 99, 7), ('30 дней', 149, 30), ('6 месяцев', 540, 182),
                            ('12 месяцев', 1020, 365);''')
            cursor.execute('''CREATE TABLE IF NOT EXISTS subscriptions(
                            id INT PRIMARY KEY AUTO_INCREMENT,
                            user_id INT NOT NULL,
                            start_date DATETIME NOT NULL,
                            end_date DATETIME NOT NULL,
                            tariff_id INT NULL,
                            is_active BOOL DEFAULT TRUE,
                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                            FOREIGN KEY (tariff_id) REFERENCES tariffs(id));''')
            cursor.execute('''CREATE TABLE IF NOT EXISTS payments_method(
                            id INT PRIMARY KEY AUTO_INCREMENT,
                            name VARCHAR(200) NOT NULL UNIQUE,
                            is_active BOOL DEFAULT TRUE);''')
        self.__conn.commit()

    # --ПРОВЕРКА--
    # есть ли юзер в системе
    def is_exist_user(self, tg_id):
        with self.__conn.cursor() as cursor:
            cursor.execute("SELECT * FROM users WHERE tg_id = %s", (tg_id,))
            rows = cursor.fetchall()
            return bool(rows)

    # пользовался ли юзер пробной подпиской
    def is_exist_trial(self, user_id):
        with self.__conn.cursor() as cursor:
            cursor.execute("SELECT trial_used FROM profile WHERE user_id = %s", (user_id,))
            row = cursor.fetchone()
            if row:
                return bool(row[0])
            return False

    # --ДОБАВЛЕНИЕ--
    # добавляем нового пользователя
    def add_new_user(self, tg_id):
        with self.__conn.cursor() as cursor:
            cursor.execute("INSERT IGNORE INTO users(tg_id) VALUES (%s)", (tg_id,))
        self.__conn.commit()
        logging.info('Пользователь успешно добавлен в БД')

    # добавляем нового админа
    def add_new_admin(self, tg_id):
        with self.__conn.cursor() as cursor:
            cursor.execute("INSERT IGNORE INTO admins(tg_id) VALUES (%s)", (tg_id,))
        self.__conn.commit()
        logging.info('Админ успешно добавлен в БД')

    # создаем профиль
    def create_profile(self, user_id):
        with self.__conn.cursor() as cursor:
            cursor.execute("INSERT IGNORE INTO profile(user_id) VALUES (%s)", (user_id,))
        self.__conn.commit()
        logging.info('Профиль успешно создан в БД')

    # оформляем платную подписку
    def making_subscription(self, user_id, start_date, end_date, tariff_id):
        with self.__conn.cursor() as cursor:
            cursor.execute("INSERT IGNORE INTO subscriptions(user_id, start_date, end_date, tariff_id) VALUES (%s, %s, %s, %s)", (user_id,  start_date, end_date, tariff_id,))
        self.__conn.commit()
        logging.info('Запись о подписке успешно создана в БД')

    # добавление нового тарифа(админка)
    def add_tariff(self, name, price, duration_days):
        with self.__conn.cursor() as cursor:
            cursor.execute(
                '''INSERT IGNORE INTO tariffs(name, price, duration_days)
                   VALUES (%s, %s, %s);''',
                (name, price, duration_days,))
        self.__conn.commit()
        logging.info('Новый тариф добавлен в БД')

    # добавление нового тарифа(админка)
    def add_method(self, name):
        with self.__conn.cursor() as cursor:
            cursor.execute(
                '''INSERT IGNORE INTO payments_method(name)
                    VALUES (%s);''',
                (name,))
        self.__conn.commit()
        logging.info('Новый метод добавлен в БД')


    #--ОБНОВЛЕНИЕ--
    # активация пробной подписки
    def update_profile_trial(self, user_id):
        with self.__conn.cursor() as cursor:
            cursor.execute('''UPDATE profile 
                            SET trial_used  = 0
                            WHERE user_id = %s ''', (user_id, ))
        self.__conn.commit()
        logging.info('Пробная подписка активирована')

    # включение тарифа
    def tariff_activation(self, tariff_id):
        with self.__conn.cursor() as cursor:
            cursor.execute('''UPDATE tariffs 
                            SET is_active = 1
                            WHERE id = %s ''', (tariff_id,))
        self.__conn.commit()
        logging.info('Тариф включен')

    # включение метода
    def method_activation(self, method_id):
        with self.__conn.cursor() as cursor:
            cursor.execute('''UPDATE payments_method 
                            SET is_active = 1
                            WHERE id = %s ''', (method_id,))
        self.__conn.commit()
        logging.info('Метод включен')

    # выключение тарифа
    def tariff_deactivation(self, tariff_id):
        with self.__conn.cursor() as cursor:
            cursor.execute('''UPDATE tariffs 
                            SET is_active = 0
                            WHERE id = %s ''', (tariff_id,))
        self.__conn.commit()
        logging.info('Тариф выключен')

    # выключение метода
    def method_deactivation(self, method_id):
        with self.__conn.cursor() as cursor:
            cursor.execute('''UPDATE payments_method 
                            SET is_active = 0
                            WHERE id = %s ''', (method_id,))
        self.__conn.commit()
        logging.info('Метод выключен')

    # продление подписки
    def update_subscription(self, user_id, end_date):
        with self.__conn.cursor() as cursor:
            cursor.execute('''UPDATE subscriptions 
                            SET end_date = %s
                            WHERE user_id = %s ''', (end_date, user_id,))
        self.__conn.commit()
        logging.info('Подписка продлена')

    # --УДАЛЕНИЕ--
    #удаление тарифа по айди
    def delete_tariff(self, tariff_id):
        with self.__conn.cursor() as cursor:
            cursor.execute('''DELETE FROM tariffs 
                        WHERE id = %s''', (tariff_id,))
        self.__conn.commit()
        logging.info('Тариф удален из БД')

    # удаление метода по айди
    def delete_method(self, method_id):
        with self.__conn.cursor() as cursor:
            cursor.execute('''DELETE FROM payments_method 
                            WHERE id = %s''', (method_id,))
        self.__conn.commit()
        logging.info('Метод удален из БД')

    # удаление админа
    def delete_admin(self, admin_id):
        with self.__conn.cursor() as cursor:
            cursor.execute('''DELETE FROM admins 
                            WHERE tg_id = %s''', (admin_id,))
        self.__conn.commit()
        logging.info('Админ удален из БД')

    # удаление юзера
    def delete_user(self, user_id):
        with self.__conn.cursor() as cursor:
            cursor.execute('''DELETE FROM users
                            WHERE tg_id = %s''', (user_id,))
        self.__conn.commit()
        logging.info('Пользователь удален из БД')

    #--ВЫВОДЫ--
    # получаем айди юзера
    def get_user_id(self, user_id):
        with self.__conn.cursor() as cursor:
            cursor.execute("SELECT id FROM users WHERE tg_id = %s", (user_id,))
            row = cursor.fetchone()
            return row[0] if row else None

    # выводим всех пользователей
    def get_all_user(self):
        with self.__conn.cursor() as cursor:
            cursor.execute("SELECT * FROM users")
            return cursor.fetchall()

    # выводим всех пользователей
    def get_all_admins(self):
        with self.__conn.cursor() as cursor:
            cursor.execute("SELECT * FROM admins")
            return cursor.fetchall()

    # выводим все включенные тарифы
    def get_all_tariffs(self):
        with self.__conn.cursor() as cursor:
            cursor.execute("SELECT * FROM tariffs WHERE is_active = 1 ORDER BY duration_days ASC;")
            return cursor.fetchall()

    # выводим все выключенные тарифы
    def get_all_tariffs_off(self):
        with self.__conn.cursor() as cursor:
            cursor.execute("SELECT * FROM tariffs WHERE is_active = 0 ORDER BY duration_days ASC;")
            return cursor.fetchall()

    # выводим все включенные методы оплат
    def get_payments_method(self):
        with self.__conn.cursor() as cursor:
            cursor.execute("SELECT * FROM payments_method WHERE is_active = 1")
            return cursor.fetchall()

    # выводим все включенные методы оплат
    def get_payments_method_off(self):
        with self.__conn.cursor() as cursor:
            cursor.execute("SELECT * FROM payments_method WHERE is_active = 0")
            return cursor.fetchall()

    # выводим дату активной подписке по юзеру
    def get_subscription_date(self, user_id):
        with self.__conn.cursor() as cursor:
            cursor.execute("SELECT start_date, end_date FROM subscriptions WHERE user_id = %s AND is_active = 1", (user_id,))
            return cursor.fetchall()

database = Database(DB_HOST, DB_USER, PASSWORD,3306)