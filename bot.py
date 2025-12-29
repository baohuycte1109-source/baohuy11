import requests
from telegram import Bot
import schedule
import time
from keep_alive import keep_alive
import json
from datetime import datetime, date

# ---------------- CẤU HÌNH ----------------
TOKEN = "6320148381:AAEZbi1TogQwXJ0gkyV9mqW1rpINeVRbeIg"
CHAT_ID = "5736655322"
API_URL = "https://abcdxyz310107.x10.mx/apifl.php"
USERNAME = "baohuydz158"
TIMEOUT = 36  # giây
HISTORY_FILE = "history.log"
# ------------------------------------------

bot = Bot(TOKEN)
last_data = None
keep_alive()

def fetch_api(username):
    """Gọi API với timeout và xử lý lỗi"""
    try:
        resp = requests.get(API_URL, params={"username": username}, timeout=TIMEOUT)
        resp.raise_for_status()
        return resp.json()
    except requests.exceptions.Timeout:
        return {"error": "API timeout"}
    except requests.exceptions.RequestException as e:
        return {"error": str(e)}
    except ValueError:
        return {"error": "Invalid JSON response"}

def log_history(data):
    """Ghi log với timestamp"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(HISTORY_FILE, "a", encoding="utf-8") as f:
        f.write(f"[{timestamp}] {json.dumps(data, ensure_ascii=False)}\n")

def format_message(data):
    """Tạo message khi follow thay đổi"""
    if "error" in data:
        return f"❌ Lỗi khi gọi API:\n{data['error']}"
    
    nickname = data.get("nickname", "Không có")
    follow_before = data.get("follow_before", 0)
    follow_increase = data.get("follow_increase", 0)
    follow_current = data.get("follow_current", 0)
    
    # Emoji tăng follow
    emoji = "🚀" if follow_increase >= 10 else ("✨" if follow_increase > 0 else "⚠️")
    
    return (
        f"✅ BUFF THÀNH CÔNG {emoji}\n\n"
        f"👤 @{USERNAME}\n"
        f"Nickname: {nickname}\n"
        f"Follow trước: {follow_before}\n"
        f"Follow tăng: +{follow_increase}\n"
        f"Follow hiện tại: {follow_current}"
    )

def send_result():
    global last_data
    data = fetch_api(USERNAME)
    
    if data != last_data:
        message = format_message(data)
        bot.send_message(chat_id=CHAT_ID, text=message)
        log_history(data)
        last_data = data
        print("✅ Gửi dữ liệu mới")
    else:
        print("ℹ️ Dữ liệu không thay đổi, không gửi")

def send_daily_summary():
    """Tính tổng follow tăng trong ngày và gửi báo cáo"""
    today = date.today().strftime("%Y-%m-%d")
    total_increase = 0

    try:
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            for line in f:
                if line.startswith(f"[{today}"):
                    entry = json.loads(line.strip().split("] ")[1])
                    total_increase += entry.get("follow_increase", 0)
    except FileNotFoundError:
        pass

    if total_increase > 0:
        message = f"📊 Tổng follow tăng trong ngày hôm nay ({today}): +{total_increase}"
    else:
        message = f"⚠️ Không có follow tăng trong ngày hôm nay ({today})"
    
    bot.send_message(chat_id=CHAT_ID, text=message)
    print(f"✅ Báo cáo tổng follow hôm nay: {total_increase}")

# Lịch gửi mỗi 15 phút
schedule.every(15).minutes.do(send_result)

# Lịch gửi tổng follow tăng vào 23:59 mỗi ngày
schedule.every().day.at("23:59").do(send_daily_summary)

print("Bot đang chạy 24/7… Bắt đầu gửi kết quả mỗi 15 phút và tổng follow mỗi ngày")
send_result()  # gửi lần đầu

while True:
    try:
        schedule.run_pending()
        time.sleep(1)
    except Exception as e:
        print("❌ Lỗi trong loop:", e)
        time.sleep(5)
