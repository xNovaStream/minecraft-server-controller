#!/usr/bin/env python3
import threading
from flask import Flask, jsonify, render_template, send_from_directory
from flask_httpauth import HTTPBasicAuth
from werkzeug.security import generate_password_hash, check_password_hash
from config import (
    logger,
    MINECRAFT_SERVER_ID,
    get_server_status,
    wait_server_status,
    try_start_server,
    enable_monitor,
    disable_monitor,
    is_monitor_enabled,
    ADMIN_USERNAME,
    ADMIN_PASSWORD
)

def wait_for_starting_monitor():
    if wait_server_status(MINECRAFT_SERVER_ID, "ACTIVE"):
        logger.info(f"Сервер {MINECRAFT_SERVER_ID} запущен")
        enable_monitor()

app = Flask(__name__)
auth = HTTPBasicAuth()

admins = {
    ADMIN_USERNAME: generate_password_hash(ADMIN_PASSWORD)
}

@auth.verify_password
def verify_password(username, password):
    if username in admins and check_password_hash(admins.get(username), password):
        return username

@app.route("/")
@auth.login_required
def index():
    return render_template("index.html")

@app.route("/start-minecraft", methods=["POST"])
@auth.login_required
def start_minecraft():
    try:
        status = get_server_status(MINECRAFT_SERVER_ID)

        if status in ["REBOOTING", "STARTING", "BUILDING", "ACTIVE"]:
            enable_monitor()
            return jsonify({"message": "Сервер уже запущен"}), 200

        if not try_start_server(MINECRAFT_SERVER_ID):
            return jsonify({"message": "Ошибка при попытке запуска сервера"}), 500

        threading.Thread(target=wait_for_starting_monitor, daemon=True).start()
        return jsonify({"message": "Сервер запускается"}), 202

    except Exception as e:
        logger.error(f"Ошибка при старте: {e}")
        return jsonify({"message": str(e)}), 500
    
@app.route("/monitoring", methods=["POST"])
@auth.login_required
def enable_monitoring():
    try:
        enable_monitor()
        return jsonify({"status": "ok", "message": "Мониторинг включён"}), 200
    except Exception as e:
        logger.error(f"Ошибка при включении мониторинга: {e}")
        return jsonify({"message": str(e)}), 500

@app.route("/monitoring", methods=["DELETE"])
@auth.login_required
def disable_monitoring():
    try:
        disable_monitor()
        return jsonify({"status": "ok", "message": "Мониторинг отключён"}), 200
    except Exception as e:
        logger.error(f"Ошибка при отключении мониторинга: {e}")
        return jsonify({"message": str(e)}), 500

@app.route("/monitoring/status", methods=["GET"])
@auth.login_required
def monitoring_status():
    """Возвращает текущее состояние мониторинга (для обновления на странице)"""
    return jsonify({"enabled": is_monitor_enabled()}), 200

@app.route("/server/status", methods=["GET"])
@auth.login_required
def server_status():
    """Возвращает текущий статус Minecraft-сервера"""
    status = get_server_status(MINECRAFT_SERVER_ID)
    return jsonify({"status": status}), 200

@app.route('/favicon.svg')
def favicon():
    return send_from_directory(app.root_path, 'favicon.svg', mimetype='image/svg+xml')

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)