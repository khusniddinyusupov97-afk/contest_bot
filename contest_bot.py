import telebot
from telebot import types
import json
import time
import os  # <-- added this

# ------------------ CONFIG ------------------
TOKEN = os.getenv("TOKEN")   # <-- now it reads from environment variables
bot = telebot.TeleBot(TOKEN)

# Admin IDs
ADMIN_IDS = [1772442968]

# Mandatory channel
MANDATORY_CHANNEL = "@khusniddinyusupov"

# Prizes
PRIZES = {
    1: "💵 1 000 000 so'm",
    2: "🎧 AirPods",
    3: "🎁 Maxfiy Surprise Box"
}

# ------------------ USERS ------------------
try:
    with open("users.json", "r") as f:
        users = json.load(f)
except FileNotFoundError:
    users = {}

def save_users():
    with open("users.json", "w") as f:
        json.dump(users, f)

# ------------------ ADMIN CHECK ------------------
def is_admin(user_id):
    return user_id in ADMIN_IDS

# ------------------ START ------------------
@bot.message_handler(commands=['start'])
def start(message):
    user_id = str(message.from_user.id)
    text = message.text.split()
    first_name = message.from_user.first_name or "Foydalanuvchi"
    username = message.from_user.username

    referrer_id = None
    if len(text) > 1:
        referrer_id = text[1]

    # Yangi foydalanuvchi qo‘shish
    if user_id not in users:
        users[user_id] = {
            "invites": 0,
            "invited_by": referrer_id,
            "first_name": first_name,
            "username": username
        }
        save_users()

        # Referrerga ball qo‘shish
        if referrer_id and referrer_id in users and referrer_id != user_id:
            users[referrer_id]["invites"] += 1
            save_users()
            try:
                bot.send_message(int(referrer_id), "🎉 Sizning havolangiz orqali yangi foydalanuvchi qo‘shildi! +1 ball")
            except:
                pass
    else:
        # update name/username if user already exists
        users[user_id]["first_name"] = first_name
        users[user_id]["username"] = username
        save_users()

    # Salomlashish
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("✅ Ishtirok etish", "🔗 Mening havolam")
    markup.add("📈 Mening natijam", "🏆 Reyting")
    bot.send_message(
        message.chat.id,
        "👋 Assalomu alaykum!\n\n"
        "📣 Konkursga xush kelibsiz!\n"
        "✅ Kanalga obuna bo‘ling\n"
        "🔗 Referral havolangizni oling\n"
        "👥 Do‘stlaringizni taklif qiling va ball to‘plang!\n\n"
        "🏆 Eng ko‘p ball to‘plaganlar sovrinlarni qo‘lga kiritadi!",
        reply_markup=markup
    )

# ------------------ PARTICIPATE ------------------
@bot.message_handler(func=lambda msg: msg.text == "✅ Ishtirok etish")
def participate(message):
    user_id = message.from_user.id
    try:
        member = bot.get_chat_member(MANDATORY_CHANNEL, user_id)
        if member.status in ['member', 'administrator', 'creator']:
            bot.send_message(message.chat.id, "🎉 Tabriklaymiz! Siz konkursda ishtirok etyapsiz!")
        else:
            bot.send_message(message.chat.id, f"❗ Iltimos, {MANDATORY_CHANNEL} kanaliga obuna bo‘ling.")
    except:
        bot.send_message(message.chat.id, f"❗ Iltimos, {MANDATORY_CHANNEL} kanaliga obuna bo‘ling.")

# ------------------ REFERRAL LINK ------------------
@bot.message_handler(func=lambda msg: msg.text == "🔗 Mening havolam")
def referral(message):
    user_id = message.from_user.id
    link = f"https://t.me/{bot.get_me().username}?start={user_id}"
    bot.send_message(message.chat.id, f"🔗 Sizning referral linkingiz:\n{link}")

# ------------------ MY STATS ------------------
@bot.message_handler(func=lambda msg: msg.text == "📈 Mening natijam")
def my_stats(message):
    user_id = str(message.from_user.id)
    invites = users[user_id].get("invites", 0)

    ranking = sorted(users.items(), key=lambda x: x[1].get("invites", 0), reverse=True)
    place = [u[0] for u in ranking].index(user_id) + 1

    # Display name
    name = users[user_id].get("first_name", "Foydalanuvchi")
    username = users[user_id].get("username")
    display_name = f"@{username}" if username else name

    # Top-10 motivatsiya
    top10 = ranking[:10]
    if user_id in [u[0] for u in top10]:
        motivation = "🔥 Siz hozir TOP-10 ichidasiz! Sovrinlarga juda yaqin turibsiz!"
    else:
        if len(top10) >= 10:
            tenth_place_points = top10[-1][1].get("invites", 0)
            needed = max(0, tenth_place_points - invites + 1)
            motivation = f"💡 TOP-10 ga kirish uchun yana {needed} ta do‘st chaqirishingiz kerak."
        else:
            motivation = "💡 Hali TOP-10 to‘lmagan. Imkoniyatdan foydalaning!"

    bot.send_message(
        message.chat.id,
        f"📊 Sizning natijangiz:\n\n"
        f"👤 Ism: {display_name}\n"
        f"🔢 Taklif qilgan do'stlaringiz: {invites}\n"
        f"🏆 Reytingdagi o‘rningiz: {place}\n\n"
        f"{motivation}"
    )

# ------------------ LEADERBOARD ------------------
@bot.message_handler(func=lambda msg: msg.text == "🏆 Reyting")
def leaderboard(message):
    sorted_users = sorted(users.items(), key=lambda x: x[1].get("invites", 0), reverse=True)
    text = "🏆 Reyting:\n\n"
    for i, (uid, data) in enumerate(sorted_users[:10], start=1):
        username = data.get("username")
        first_name = data.get("first_name", "Foydalanuvchi")
        display_name = f"@{username}" if username else first_name
        text += f"{i}. {display_name} — {data.get('invites', 0)} ball\n"
    bot.send_message(message.chat.id, text)

# ------------------ ADMIN COMMANDS ------------------
@bot.message_handler(commands=['statistika'])
def send_statistics(message):
    if not is_admin(message.from_user.id):
        return
    bot.send_message(message.chat.id, f"📊 Jami foydalanuvchilar: {len(users)}")

@bot.message_handler(commands=['top'])
def send_top(message):
    if not is_admin(message.from_user.id):
        return
    sorted_users = sorted(users.items(), key=lambda x: x[1].get("invites", 0), reverse=True)
    text = "🏆 TOP foydalanuvchilar:\n\n"
    for i, (uid, data) in enumerate(sorted_users[:10], start=1):
        username = data.get("username")
        first_name = data.get("first_name", "Foydalanuvchi")
        display_name = f"@{username}" if username else first_name
        text += f"{i}. {display_name} — {data.get('invites', 0)} ball\n"
    bot.send_message(message.chat.id, text)

@bot.message_handler(commands=['msg'])
def broadcast_message(message):
    if not is_admin(message.from_user.id):
        return
    text = message.text.split(" ", 1)
    if len(text) < 2:
        bot.send_message(message.chat.id, "❗ Xabar matnini kiriting.")
        return
    for uid in users.keys():
        try:
            bot.send_message(int(uid), text[1])
        except:
            pass
    bot.send_message(message.chat.id, "✅ Xabar barcha foydalanuvchilarga yuborildi.")

@bot.message_handler(commands=['stop'])
def stop_contest(message):
    if not is_admin(message.from_user.id):
        return
    sorted_users = sorted(users.items(), key=lambda x: x[1].get("invites", 0), reverse=True)
    winners = sorted_users[:3]
    for i, (uid, data) in enumerate(winners, start=1):
        prize = PRIZES.get(i, "🎁 Maxfiy sovrin")
        username = data.get("username")
        first_name = data.get("first_name", "Foydalanuvchi")
        display_name = f"@{username}" if username else first_name
        try:
            bot.send_message(int(uid), f"🏆 Tabriklaymiz {display_name}! Siz {i}-o‘rinni oldingiz va sovrinni qo‘lga kiritdingiz: {prize}")
        except:
            pass
    bot.send_message(message.chat.id, "🏁 Konkurs tugadi! Sovrinlar taqsimlandi.")

# ------------------ START BOT ------------------
print("🤖 Bot ishga tushdi...")
bot.infinity_polling()
