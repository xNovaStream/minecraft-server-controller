#!/usr/bin/env python3
import time
from config import (
    logger,
    MINECRAFT_SERVER_ID,
    MINECRAFT_HOST,
    MINECRAFT_PORT,
    IDLE_TIMEOUT,
    CHECK_INTERVAL_RUNNING,
    CHECK_INTERVAL_STOPPED,
    try_stop_server,
    wait_server_status,
    get_online_players,
    is_monitor_enabled,
    disable_monitor,
    get_server_status
)

def monitor_loop():
    def disable_monitor_internal():
        nonlocal zero_start_time
        disable_monitor()
        zero_start_time = None

    zero_start_time = None

    while True:
        if not is_monitor_enabled():
            time.sleep(CHECK_INTERVAL_STOPPED)
            continue

        try:
            online = get_online_players(f"{MINECRAFT_HOST}:{MINECRAFT_PORT}")
            if online < 0:
                status = get_server_status(MINECRAFT_SERVER_ID)
                if status == "STOPPED":
                    logger.warning("Отключение мониторинга, тк сервер остановлен")
                    disable_monitor_internal()
                time.sleep(CHECK_INTERVAL_RUNNING)
                continue

            if online == 0:
                if zero_start_time is None:
                    zero_start_time = time.time()
                    logger.info("Игроков нет, начинаем отсчёт бездействия")
                else:
                    elapsed = time.time() - zero_start_time
                    if elapsed >= IDLE_TIMEOUT:
                        logger.info(f"Бездействие сервера превысило {IDLE_TIMEOUT} секунд")
                        if try_stop_server(MINECRAFT_SERVER_ID):
                            if wait_server_status(MINECRAFT_SERVER_ID, "STOPPED"):
                                disable_monitor_internal()
            else:
                if zero_start_time is not None:
                    logger.info("Появились игроки, сбрасываем таймер бездействия")
                    zero_start_time = None

        except Exception as e:
            logger.error(f"Необработанная ошибка в цикле мониторинга: {e}")

        time.sleep(CHECK_INTERVAL_RUNNING)

if __name__ == "__main__":
    monitor_loop()