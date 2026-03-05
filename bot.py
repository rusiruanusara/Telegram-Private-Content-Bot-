import datetime
import telebot
import json
import time
import logging
import os
import pytz  # For Sri Lanka time
from dotenv import load_dotenv
import schedule

# Load environment variables
load_dotenv()

# Securely load bot credentials
TOKEN = os.getenv("TOKEN")
PRIVATE_CHANNEL_ID = int(os.getenv("PRIVATE_CHANNEL_ID"))
ADMIN_ID = int(os.getenv("ADMIN_ID"))

# Check if token is missing
if not TOKEN:
    raise ValueError("Bot TOKEN is missing! Set it in .env file.")

# Set Sri Lanka time zone
sri_lanka_tz = pytz.timezone("Asia/Colombo")

# Configure logging
logging.basicConfig(filename="bot_errors.log", level=logging.ERROR, format="%(asctime)s - %(levelname)s - %(message)s")

# Initialize bot
bot = telebot.TeleBot(TOKEN, threaded=True, num_threads=10)

# JSON file for storing message IDs
MESSAGE_FILE = "messages.json"

def load_messages():
    """Loads saved message IDs from JSON file."""
    try:
        with open(MESSAGE_FILE, "r") as file:
            return json.load(file)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}  # No hardcoded fallback


def save_messages(messages):
    """Saves updated message IDs to JSON file."""
    with open(MESSAGE_FILE, "w") as file:
        json.dump(messages, file, indent=4)

# Load message IDs
message_ids = load_messages()

def check_for_new_day():
    """Creates a new user data file at the start of each new day if it doesn't exist."""
    global USER_DATA_FILE, user_data
    
    today_file = get_today_file()
    
    if USER_DATA_FILE != today_file:
        USER_DATA_FILE = today_file
        
        # If today's file doesn't exist, create it without deleting old ones
        if not os.path.exists(USER_DATA_FILE):
            with open(USER_DATA_FILE, "w") as file:
                json.dump({}, file, indent=4)  # Create an empty JSON file
        
        user_data = load_user_data()  # Load new day's user data
        print(f"New day detected! Switched to: {USER_DATA_FILE}")

# Schedule this function to run every minute
schedule.every(1).minutes.do(check_for_new_day)


def get_today_file():
    """Generates today's JSON file name."""
    now = datetime.datetime.now(sri_lanka_tz)
    return f"userdata_{now.year}{now.month:02d}{now.day:02d}.json"

USER_DATA_FILE = get_today_file()

def load_user_data():
    """Loads today's user data file."""
    try:
        with open(USER_DATA_FILE, "r") as file:
            return json.load(file)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}

def save_user_data(data):
    """Saves user data to today's file."""
    with open(USER_DATA_FILE, "w") as file:
        json.dump(data, file, indent=4)

user_data = load_user_data()
valid_users = {
    user_id: datetime.datetime.fromisoformat(info["subscription_time"]).astimezone(sri_lanka_tz)
    for user_id, info in user_data.items()
}


def generate_daily_key():
    """Generates a unique key for today based on Sri Lanka date."""
    now = datetime.datetime.now(sri_lanka_tz)
    seed_str = f"{now.year}{now.month:02d}{now.day:02d}"
    seed = int(seed_str)
    scrambled = seed * 12345 + 67890
    hex_key = hex(scrambled)[2:].upper()[:12]
    return hex_key

@bot.message_handler(commands=['start'])
def start_handler(message):
    try:
        user_id = str(message.from_user.id)
        user_name = message.from_user.first_name
        now = datetime.datetime.now(sri_lanka_tz)

        if user_id not in valid_users:
            bot.reply_to(message, "You need a valid subscription to use this feature. Please enter today's key.\n *How to Get Key -* https://t.me/DonghuaRealm/62",parse_mode="Markdown", disable_web_page_preview=True)
            return

        command_parts = message.text.split()
        if len(command_parts) > 1:
            params = command_parts[1].split("_")  # Split by `_`
            forwarded_messages = []  # Track valid messages to forward

            for param in params:
                message_id = message_ids.get(param)
                if message_id:
                    bot.copy_message(message.chat.id, PRIVATE_CHANNEL_ID, message_id)
                    forwarded_messages.append(message_id)

            if forwarded_messages:
                # Ensure user data is properly initialized
                if user_id not in user_data:
                    user_data[user_id] = {
                        "name": user_name,
                        "subscription_time": str(valid_users[user_id]),
                        "forward_count": 0,
                        "forwarded_messages": []  # Ensure this key always exists
                    }
                else:
                    # If existing user, ensure 'forwarded_messages' key is present
                    if "forwarded_messages" not in user_data[user_id]:
                        user_data[user_id]["forwarded_messages"] = []

                user_data[user_id]["last_used"] = str(now)
                user_data[user_id]["forward_count"] += len(forwarded_messages)  # Increase by number of messages forwarded
                user_data[user_id]["forwarded_messages"].extend(forwarded_messages)  # Store forwarded message IDs
                save_user_data(user_data)

            else:
                bot.reply_to(message, "Invalid parameters. Use valid numbers (1-5).")
        else:
            bot.reply_to(message, "Welcome! You already have access! 😊\n *How to use BOT -* https://t.me",parse_mode="Markdown", disable_web_page_preview=True)

    except Exception as e:
        logging.error(f"Error in /start command: {e}")
        bot.send_message(ADMIN_ID, f"🚨 Bot Error in /start: {e}")
        bot.reply_to(message, "An unexpected error occurred. Please try again later.")


@bot.message_handler(commands=['getkey'])
def get_key(message):
    try:
        user_id = message.from_user.id
        if user_id == ADMIN_ID:
            key = generate_daily_key()
            bot.reply_to(message, f"Today's subscription key is: {key}")
        else:
            bot.reply_to(message, "You are not authorized to use this command.")
    except Exception as e:
        logging.error(f"Error in /getkey command: {e}")
        bot.send_message(ADMIN_ID, f"🚨 Bot Error in /getkey: {e}")
        bot.reply_to(message, "An unexpected error occurred. Please try again later.")

@bot.message_handler(commands=['setmsg'])
def set_message_handler(message):
    try:
        if message.from_user.id != ADMIN_ID:
            bot.reply_to(message, "Sorry, you're not authorized to use this command.")
            return

        parts = message.text.split()
        if len(parts) != 3:
            bot.reply_to(message, "Usage: /setmsg <param> <new_message_id>")
            return

        param, new_msg_id = parts[1], parts[2]

        try:
            new_msg_id = int(new_msg_id)
            message_ids[param] = new_msg_id
            save_messages(message_ids)
            bot.reply_to(message, f"✅ Message ID for `{param}` updated to `{new_msg_id}`.", parse_mode="Markdown")
        except ValueError:
            bot.reply_to(message, "The message ID must be a number.")

    except Exception as e:
        logging.error(f"Error in /setmsg command: {e}")
        bot.send_message(ADMIN_ID, f"🚨 Bot Error in /setmsg: {e}")
        bot.reply_to(message, "An unexpected error occurred. Please try again later.")

@bot.message_handler(commands=['allmsgs'])
def show_all_messages(message):
    if message.from_user.id != ADMIN_ID:
        bot.reply_to(message, "You are not authorized to use this command.")
        return

    if not message_ids:
        bot.reply_to(message, "No message IDs have been set yet.")
        return

    response = "📌 All message parameters:\n"
    for param, msg_id in message_ids.items():
        response += f"`{param}` ➜ `{msg_id}`\n"
    bot.reply_to(message, response, parse_mode="Markdown")


@bot.message_handler(commands=['userdata'])
def get_userdata(message):
    try:
        if message.from_user.id != ADMIN_ID:
            bot.reply_to(message, "You are not authorized to use this command.")
            return

        # Load today's user data
        user_data = load_user_data()
        if not user_data:
            bot.reply_to(message, "No user data available for today.")
            return

        # Prepare response message
        response = "📄 Today's User Data:\n"
        for user_id, info in user_data.items():
            user_id_str = str(user_id)
            name = info['name'].replace('[', '').replace(']', '').replace('(', '').replace(')', '')  # Simple escape
            mention = f"[{name}](tg://user?id={user_id_str})"
            response += f"👤 {mention} - 🆔 `{user_id_str}`\n"

        bot.reply_to(message, response, parse_mode="Markdown")

    except Exception as e:
        logging.error(f"Error in /userdata command: {e}")
        bot.send_message(ADMIN_ID, f"🚨 Bot Error in /userdata: {e}")
        bot.reply_to(message, "An unexpected error occurred. Please try again later.")
               
@bot.message_handler(func=lambda m: True)
def check_key(message):
    try:
        user_id = str(message.from_user.id)
        user_name = message.from_user.first_name
        user_input = message.text.strip()
        daily_key = generate_daily_key()
        now = datetime.datetime.now(sri_lanka_tz)

        if user_id in valid_users:
            bot.reply_to(message, "You already have access! 😊")
        else:
            if user_input == daily_key:
                valid_users[user_id] = now
                user_data[user_id] = {
                    "name": user_name,
                    "subscription_time": str(now),
                    "forward_count": 0
                }
                save_user_data(user_data)
                bot.reply_to(message, "Access granted! 🎉 You have until the end of the day.")
            else:
                bot.reply_to(message, "Invalid key. Please try again. ❌")
    
    except Exception as e:
        logging.error(f"Error in check_key function: {e}")
        bot.send_message(ADMIN_ID, f"🚨 Bot Error in check_key: {e}")
        bot.reply_to(message, "An unexpected error occurred. Please try again later.")
        
def run_bot():
    while True:
        try:
            global USER_DATA_FILE, user_data, valid_users
            today_file = get_today_file()
            if USER_DATA_FILE != today_file:
                USER_DATA_FILE = today_file
                user_data = load_user_data()
                valid_users = {}
                print(f"New day detected! Switched to: {USER_DATA_FILE}")

            print("Bot is running...")
            bot.infinity_polling(timeout=120, long_polling_timeout=20)
        except Exception as e:
            logging.error(f"Bot crashed due to error: {e}")
            bot.send_message(ADMIN_ID, f"🚨 Bot crashed! Error: {e}")
            time.sleep(5)

if __name__ == '__main__':
    run_bot()
