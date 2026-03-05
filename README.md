```
# Telegram Private Content Bot 🔐

A Telegram bot built with **Python** and **PyTelegramBotAPI (telebot)** that provides **controlled access to private channel content using a daily subscription key system**.

Users must enter a **daily key** to unlock access and retrieve messages from a private channel.

---

## ✨ Features

- 🔑 Daily subscription key system
- 📅 Automatic daily user reset
- 📂 JSON based user tracking
- 📤 Forward private channel messages using parameters
- 👑 Admin commands for managing content
- 🕒 Sri Lanka timezone support
- ⚠ Error logging system
- 🔄 Auto restart on crash

---

## 🛠 Technologies Used

- Python 3
- PyTelegramBotAPI (`telebot`)
- dotenv
- JSON database
- pytz
- schedule

---

## 📁 Project Structure

```

project/
│
├── bot.py
├── messages.json
├── userdata_YYYYMMDD.json
├── .env
├── bot_errors.log
└── README.md





⚙️ Installation

2️⃣ Install dependencies

```

pip install pyTelegramBotAPI python-dotenv pytz schedule

```

---

## 🔐 Environment Variables

Create a `.env` file:

```

TOKEN=YOUR_BOT_TOKEN
PRIVATE_CHANNEL_ID=-100XXXXXXXXXX
ADMIN_ID=YOUR_TELEGRAM_USER_ID

```

---

## ▶️ Run the Bot

```

python bot.py

```

---

## 🤖 User Commands

### `/start`
Start the bot and access content.

Example:

```

/start 1
/start 1_2_3

```

This forwards specific messages from the private channel.

---

## 👑 Admin Commands

### Get today's key

```

/getkey

```

---

### Set message parameter

```

/setmsg <param> <message_id>

```

Example

```

/setmsg 1 12345

```

---

### View all message parameters

```

/allmsgs

```

---

### View today's users

```

/userdata

```

---

## 🔑 Daily Key System

- Admin generates the key using `/getkey`
- Users send the key to the bot
- Access is valid **until the end of the day**
- New user data file is created daily

Example:

```

userdata_20260305.json

```

---

## 📊 User Data Stored

```

{
"user_id": {
"name": "username",
"subscription_time": "timestamp",
"forward_count": 3,
"forwarded_messages": [12345, 12346]
}
}

```

---

## ⚠ Error Logging

Errors are stored in:

```

bot_errors.log

```

Admin also receives bot error notifications.

---

## 📌 Notes

- The bot must be **admin in the private channel**.
- Message IDs must exist in the channel.
- Daily key resets every day automatically.

---

## 📜 License

This project is open-source and available under the MIT License.

```

---
