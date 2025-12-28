import asyncio
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters
import aiohttp

from keep_alive import keep_alive

BOT_TOKEN = "8080338995:AAHitAzhTUUb1XL0LB44BiJmOCgulA4fx38"
ADMINS = [5736655322]  # Thay bằng user_id admin thật

AUTO_JOBS = {}

# ================= Keep Alive =================
keep_alive()  # Giữ bot online

# ================= /start =================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🤖 Bot Buff Telegram\n\n"
        "📌 Lệnh:\n"
        "/buff <username> – Buff 1 lần (delay 20s) (chỉ admin)\n"
        "/autobuff <username> <time> – Auto buff (giây) (chỉ admin)\n"
        "/stopbuff – Dừng auto buff\n"
        "/adm – Thông tin admin\n"
        "/addadmin <user_id> – Thêm admin mới"
    )

# ================= Kiểm tra admin =================
def is_admin(user_id):
    return user_id in ADMINS

# ================= /adm =================
async def adm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if is_admin(user_id):
        await update.message.reply_text(
            f"✅ Bạn là admin\n"
            f"User ID: {user_id}\n"
            f"Admins hiện tại: {ADMINS}"
        )
    else:
        await update.message.reply_text("❌ Bạn không có quyền dùng lệnh này.")

# ================= /addadmin =================
async def addadmin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_admin(user_id):
        await update.message.reply_text("❌ Bạn không có quyền dùng lệnh này.")
        return

    if not context.args:
        await update.message.reply_text("❌ Dùng: /addadmin <user_id>")
        return

    try:
        new_admin = int(context.args[0])
    except ValueError:
        await update.message.reply_text("❌ user_id phải là số.")
        return

    if new_admin in ADMINS:
        await update.message.reply_text(f"⚠️ User {new_admin} đã là admin.")
        return

    ADMINS.append(new_admin)
    await update.message.reply_text(f"✅ Đã thêm admin mới: {new_admin}\nADMINS hiện tại: {ADMINS}")

# ================= Gọi API =================
async def call_buff_api(username: str):
    url = f"https://abcdxyz310107.x10.mx/apifl.php?username={username}"
    async with aiohttp.ClientSession() as session:
        async with session.get(url, timeout=15) as response:
            data = await response.json()  # API trả JSON
            return data

# ================= Format kết quả đẹp =================
def format_result(data: dict):
    return (
        f"✅ Tăng follow thành công\n"
        f"👤 @{data.get('username')}\n\n"
        f"UID: {data.get('uid')}\n"
        f"Nickname: {data.get('nickname')}\n\n"
        f"FOLLOW BAN ĐẦU: {data.get('follow_base')}\n"
        f"FOLLOW ĐÃ TĂNG: +{data.get('follow_added')}\n"
        f"FOLLOW HIỆN TẠI: {data.get('follow_current')}"
    )

# ================= /buff (chỉ admin) =================
async def buff(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_admin(user_id):
        await update.message.reply_text("❌ Bạn không có quyền dùng lệnh này. Chỉ admin mới có thể buff.")
        return

    if not context.args:
        await update.message.reply_text("❌ Dùng: /buff <username>")
        return

    username = context.args[0]
    await update.message.reply_text("⏳ Chờ 20 giây để buff...")
    await asyncio.sleep(20)

    try:
        data = await call_buff_api(username)
        await update.message.reply_text(format_result(data))
    except Exception as e:
        await update.message.reply_text(f"❌ Lỗi: {e}")

# ================= AUTO BUFF JOB =================
async def auto_buff_job(context: ContextTypes.DEFAULT_TYPE):
    job_data = context.job.data
    username = job_data["username"]
    chat_id = job_data["chat_id"]

    try:
        data = await call_buff_api(username)
        await context.bot.send_message(chat_id=chat_id, text=format_result(data))
    except Exception as e:
        await context.bot.send_message(chat_id=chat_id, text=f"❌ Lỗi auto buff: {e}")

# ================= /autobuff (chỉ admin) =================
async def autobuff(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_admin(user_id):
        await update.message.reply_text("❌ Bạn không có quyền dùng lệnh này. Chỉ admin mới có thể auto buff.")
        return

    if len(context.args) < 2:
        await update.message.reply_text(
            "❌ Dùng: /autobuff <username> <time_giây>\nVí dụ: /autobuff phuongju_8 900"
        )
        return

    chat_id = update.effective_chat.id
    username = context.args[0]

    try:
        interval = int(context.args[1])
    except ValueError:
        await update.message.reply_text("❌ Thời gian phải là số (giây)")
        return

    if user_id in AUTO_JOBS:
        await update.message.reply_text("⚠️ Bạn đã bật auto buff rồi. Dùng /stopbuff trước.")
        return

    job = context.job_queue.run_repeating(
        auto_buff_job,
        interval=interval,
        first=20,
        data={"username": username, "chat_id": chat_id},
        name=str(user_id)
    )

    AUTO_JOBS[user_id] = job
    await update.message.reply_text(
        f"✅ Đã bật AUTO BUFF\n"
        f"👤 Username: {username}\n"
        f"⏱️ Mỗi {interval} giây"
    )

# ================= /stopbuff =================
async def stopbuff(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    job = AUTO_JOBS.pop(user_id, None)
    if job:
        job.schedule_removal()
        await update.message.reply_text("🛑 Đã dừng auto buff.")
    else:
        await update.message.reply_text("⚠️ Bạn chưa bật auto buff.")

# ================= MAIN =================
def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("buff", buff))
    app.add_handler(CommandHandler("autobuff", autobuff))
    app.add_handler(CommandHandler("stopbuff", stopbuff))
    app.add_handler(CommandHandler("adm", adm))
    app.add_handler(CommandHandler("addadmin", addadmin))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, lambda u, c: None))

    print("🤖 Bot đang chạy...")
    app.run_polling()

if __name__ == "__main__":
    main()
