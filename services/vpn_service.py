import paramiko
import time
import os
from dotenv import load_dotenv
import qrcode
from io import BytesIO
import logging
from qrcode.image.pil import PilImage

logging.basicConfig(level=logging.DEBUG)

base_dir = os.path.dirname(os.path.abspath(__file__))
dotenv_path = os.path.join(base_dir, '..', '.env')

load_dotenv(dotenv_path)
PASSWORD = os.getenv("PASSWORD")
IP = os.getenv("IP")
USERNAME= os.getenv("SSH_USER")

#!!Команды не будут работать без заготовленных скриптов, если у вас выполняются эти действия по другим командам то для работы необходимо изменить их в коде!!


def create_vpn_user(username: str, days: int = 1):
    ssh = paramiko.SSHClient() #создаём SSH-клиент
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy()) #выдаем доверие, чтобы не было ошибки
    ssh.connect(IP, port=22, username=USERNAME, password=PASSWORD, look_for_keys=False,
    allow_agent=False, timeout=10) #подключаемся к серверу
    try:
        logging.info(f"Создаём пользователя {username}...")
        # Добавляем экспорт путей перед запуском скрипта
        command = (
        'bash -lc "'
        'export HOME=/root; '
        'export PATH=$PATH:/usr/local/bin:/usr/sbin:/sbin; '
        f'sudo -E /usr/local/bin/wg_temp.sh {username} {days}'
        '"'
        )
        logging.info(f"Выполняем команду для {username}...")
        stdin, stdout, stderr = ssh.exec_command(command, get_pty=True)

        exit_status = stdout.channel.recv_exit_status()
        output = stdout.read().decode().strip()
        error_output = stderr.read().decode().strip()
        time.sleep(2)
        if exit_status != 0:
            raise Exception(f"Ошибка скрипта (код {exit_status}): {error_output  or output}")
        time.sleep(0.5)

        target_path = f"/root/temp_wg_configs/{username}.conf"
        check_cmd = f"test -f {target_path} && echo EXISTS || echo NOT_EXISTS"

        stdin_c, stdout_c, stderr_c = ssh.exec_command(check_cmd, get_pty=True)
        result = stdout_c.read().decode().strip()
        if result == "EXISTS":
            logging.info(f"✅ Файл успешно создан и подтвержден: {target_path}")
            return True
        else:
            raise Exception(f"Скрипт отработал, но файл {target_path} не появился.")
    except Exception as e:
        logging.error(f"❌ Ошибка создания VPN: {e}")
        raise
    finally:
        ssh.close()

def extend_vpn_user(username: str, days: int = 7):
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        ssh.connect(IP, port=22, username=USERNAME, password=PASSWORD, timeout=10)
        logging.info(f"Продлеваем подписку для {username} на {days} дней...")
        command = f"sudo /usr/local/bin/wg-extend {username} {days}"
        stdin, stdout, stderr = ssh.exec_command(command)
        output = stdout.read().decode().strip()
        error = stderr.read().decode().strip()

        logging.info(f"[EXTEND] output={output}")
        logging.info(f"[EXTEND] error={error}")

        logging.info(f"Подписка для {username} успешно продлена")
        return True
    except Exception as e:
        logging.error(f"Ошибка SSH: {e}")
        return False
    finally:
        ssh.close()

def get_config(username: str, retries: int = 5):
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(IP, username=USERNAME, password=PASSWORD)
    try:
        logging.info('Ждём создание конфига...')
        command = f"sudo cat /root/temp_wg_configs/{username}.conf 2>/dev/null"
        for i in range(retries):
            stdin, stdout, stderr = ssh.exec_command(command)
            error = stderr.read().decode()
            if error:
                logging.error(f"Ошибка SSH: {error}")
            config = stdout.read().decode().strip()
            if config and "Interface" in config:
                logging.info(f"Конфиг найден на попытке {i + 1}")
                return config
            logging.warning(f"Ожидание файла... попытка {i + 1}")
            time.sleep(5)
        raise Exception("Конфиг не найден после ожидания")
    finally:
        ssh.close()

def get_qr(username: str):
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(IP, username=USERNAME, password=PASSWORD)
    try:
        command = f"pivpn -qr {username}"
        stdin, stdout, stderr = ssh.exec_command(command)

        return stdout.read().decode()
    finally:
        ssh.close()

def generate_qr_image(config: str):
    logging.info('Генерируем QR...')
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,)
    qr.add_data(config)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white", image_factory=PilImage)
    buffer = BytesIO()
    img.save(buffer, format="PNG")
    buffer.seek(0)
    return buffer