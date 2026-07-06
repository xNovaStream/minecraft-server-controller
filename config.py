import time
import os
import requests
import logging
from dotenv import load_dotenv
from mcstatus import JavaServer

# Configs
load_dotenv()

ADMIN_USERNAME = os.getenv("ADMIN_USERNAME")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD")

CLOUD_API_TOKEN = os.getenv("CLOUD_API_TOKEN")
MINECRAFT_SERVER_ID = os.getenv("MINECRAFT_SERVER_ID")

MINECRAFT_HOST = os.getenv("MINECRAFT_HOST")
MINECRAFT_PORT = 25565
IDLE_TIMEOUT = 3600
CHECK_INTERVAL_RUNNING = 60
CHECK_INTERVAL_STOPPED = 30

MONITOR_DISABLE_FILE = "/tmp/minecraft_monitor_disabled"

# Logger
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

# API
HEADERS = {
    "Authorization": f"Bearer {CLOUD_API_TOKEN}",
    "Content-Type": "application/json"
}
BASE_API_URL = "https://api.clo.ru/v2"

def get_server_status(server_id):
    try:
        resp = requests.get(f"{BASE_API_URL}/servers/{server_id}/detail", headers=HEADERS)
        resp.raise_for_status()
        return resp.json()["result"]["status"]
    except Exception as e:
        logger.error(f"Ошибка при получении статуса сервера: {e}")
        return "UNKNOWN"

def wait_server_status(server_id, waiting_status, timeout = 300, request_frequency = 10):
    logger.info(f"Ожидаем статус {waiting_status} от сервера {server_id}")
    start_wait = time.time()
    while time.time() - start_wait < timeout:
        current_status = get_server_status(server_id)
        if current_status == waiting_status:
            return True
        time.sleep(request_frequency)
    else:
        logger.warning(f"Таймаут ожидания статуса {waiting_status} от сервера {server_id}")
        return False

def try_stop_server(server_id):
    try:
        logger.info(f"Остановка сервера {server_id}")
        requests.post(f"{BASE_API_URL}/servers/{server_id}/stop", headers=HEADERS).raise_for_status()
        return True
    except Exception as e:
        logger.error(f"Ошибка при попытке остановки сервера: {e}")
        return False

def try_start_server(server_id):
    try:
        logger.info(f"Запуск сервера {server_id}")
        requests.post(f"{BASE_API_URL}/servers/{server_id}/start", headers=HEADERS).raise_for_status()
        return True
    except Exception as e:
        logger.error(f"Ошибка при попытке запуска сервера: {e}")
        return False

def get_online_players(minecraft_ip_address):
    try:
        server = JavaServer.lookup(minecraft_ip_address)
        status = server.status()
        return status.players.online
    except Exception as e:
        logger.warning(f"Ошибка при получении онлайна: {e}")
        return -1

# Monitoring Control
def is_monitor_enabled():
    return not os.path.exists(MONITOR_DISABLE_FILE)

def disable_monitor():
    with open(MONITOR_DISABLE_FILE, "w") as f:
        f.write("disabled")
    logger.info("Мониторинг отключён")

def enable_monitor():
    logger.info("Мониторинг включен")
    if os.path.exists(MONITOR_DISABLE_FILE):
        os.remove(MONITOR_DISABLE_FILE)