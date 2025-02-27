# 🚀 Steam Telegram-Bot Project v0.3.4  

## 🔥 About the Project  
Steam Bot is a **Telegram bot** designed to automate interactions with a Steam account.  
It utilizes **Playwright** for **automatic login**, capturing login page screenshots, and sending messages to friends.  

Thanks to **session persistence**, the bot **restores authentication** on launch, eliminating the need for repeated logins.  

---

## ⚙️ Features  

### 🔑 **Login via QR Code**  
- `/loginsteam` opens the Steam login page.  
- Takes screenshots **every 2 seconds** while waiting for the user to log in.  
- Once logged in, the session is **saved**, so future logins aren't required.  

### 🛡 **Session Status Check**  
- `/checkstatus` verifies if the session is active (i.e., user is logged in).  

### 💬 **Send Message to a Random Friend**  
- `/sendrandomfriendmsgadvanced <text>` selects a **random friend**, opens a chat, and sends the provided message.  

### 🧹 **Clear Chat**  
- `/clearchat` removes all messages sent by the bot to **keep the chat clean**.  

### 🔄 **Automatic Session Recovery**  
- If the bot detects that it's on the login page, it will automaticly recover the session. 

---

## 🛠 Installation & Setup  

### 1️⃣ Clone the Repository  
```bash
git clone https://github.com/yourusername/steam_bot_project.git
cd steam_bot_project
```
### 2️⃣ Install Dependencies
Make sure you have Python 3.10+ installed, then run:

```bash
pip install -r requirements.txt
```
Next, install Playwright browsers:
```bash
playwright install
```
### 3️⃣ Configure the Bot
The utils folder contains configuration files (e.g., Telegram bot token).
For security reasons, utils is excluded from Git.
Create a **utils/config.py** file based on **utils/config.example.py** and fill in the required variables (e.g., TELEGRAM_BOT_TOKEN).
### 4️⃣ Run the Bot
```bash
python main.py
```
---
### 📜 License
This project is licensed under the Apache License 2.0.
