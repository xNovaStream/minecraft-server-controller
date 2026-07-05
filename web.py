#!/usr/bin/env python3
from flask import Flask, jsonify, render_template
from config import (
    logger,
    MINECRAFT_SERVER_ID,
    get_server_status,
    wait_server_status,
    try_start_server,
    enable_monitor,
    disable_monitor,
    is_monitor_enabled
)

app = Flask(__name__)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/start-minecraft", methods=["POST"])
def start_minecraft():
    try:
        status = get_server_status(MINECRAFT_SERVER_ID)

        if status in ["REBOOTING", "STARTING", "BUILDING", "ACTIVE"]:
            enable_monitor()
            return jsonify({"message": "Сервер уже запущен"}), 200

        if not try_start_server(MINECRAFT_SERVER_ID):
            return jsonify({"message": "Ошибка при попытке запуска сервера"}), 500

        if not wait_server_status(MINECRAFT_SERVER_ID, "ACTIVE"):
            return jsonify({"message": "Сервер не запустился за отведенное время"}), 500

        logger.info(f"Сервер {MINECRAFT_SERVER_ID} запущен")
        enable_monitor()
        return jsonify({"message": "Сервер запущен"}), 200

    except Exception as e:
        logger.error(f"Ошибка при старте: {e}")
        return jsonify({"message": str(e)}), 500
    
@app.route("/monitoring", methods=["POST"])
def enable_monitoring():
    try:
        enable_monitor()
        return jsonify({"status": "ok", "message": "Мониторинг включён"}), 200
    except Exception as e:
        logger.error(f"Ошибка при включении мониторинга: {e}")
        return jsonify({"message": str(e)}), 500

@app.route("/monitoring", methods=["DELETE"])
def disable_monitoring():
    try:
        disable_monitor()
        return jsonify({"status": "ok", "message": "Мониторинг отключён"}), 200
    except Exception as e:
        logger.error(f"Ошибка при отключении мониторинга: {e}")
        return jsonify({"message": str(e)}), 500

@app.route("/monitoring", methods=["GET"])
def monitoring_status():
    """Возвращает текущее состояние мониторинга (для обновления на странице)"""
    return jsonify({"enabled": is_monitor_enabled()}), 200

@app.route("/server/status", methods=["GET"])
def server_status():
    """Возвращает текущий статус Minecraft-сервера"""
    status = get_server_status(MINECRAFT_SERVER_ID)
    return jsonify({"status": status}), 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=80)