import paramiko
import time
import os
from dotenv import load_dotenv
import qrcode
from io import BytesIO
import logging

logging.basicConfig(level=logging.DEBUG)

base_dir = os.path.dirname(os.path.abspath(__file__))
dotenv_path = os.path.join(base_dir, '..', '.env')

load_dotenv(dotenv_path)
PASSWORD = os.getenv("PASSWORD")
IP = os.getenv("IP")
USERNAME= os.getenv("SSH_USER")

print(f"DEBUG: Host='{IP}'")
print(f"DEBUG: User='{USERNAME}'")
print(f"DEBUG: Pass='{PASSWORD}'")

def create_vpn_user(username: str, days: int = 1):
    ssh = paramiko.SSHClient() #создаём SSH-клиент
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy()) #выдаем доверие, чтобы не было ошибки
    ssh.connect(IP, port=22, username=USERNAME, password=PASSWORD, look_for_keys=False,
    allow_agent=False) #подключаемся к серверу
    print(f"Trying to login as: '{USERNAME}' with password: '{PASSWORD}'")
    try:
        # создаём пользователя
        command = f"sudo pivpn-temp {username} {days}"
        stdin, stdout, stderr = ssh.exec_command(command) #получаем ввод\результат\ошибки
        error = stderr.read().decode()  #читаем ошибки и переводим в строку
        if error:
            raise Exception(error)
        return True
    finally:
        ssh.close()


def get_config(username: str, retries: int = 5):
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(IP, username=USERNAME, password=PASSWORD)
    try:
        command = f"cat /root/temp_wg_configs/{username}.conf"
        for _ in range(retries):
            stdin, stdout, stderr = ssh.exec_command(command)
            error = stderr.read().decode()
            config = stdout.read().decode()
            if config:
                return config
            if error:
                raise Exception(error)
            time.sleep(1)
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
    qr = qrcode.make(config)
    buffer = BytesIO()
    qr.save(buffer, format="PNG")
    buffer.seek(0)
    return buffer