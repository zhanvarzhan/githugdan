import asyncio
import os

# ================= 🛑 رفع باگ ناسازگاری پایروگرام با پایتون جدید =================
try:
    asyncio.get_event_loop()
except RuntimeError:
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
# =========================================================================

import requests
from aiohttp import web
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery

# ================= خواندن اطلاعات از سرور =================
API_ID = int(os.environ.get("TG_API_ID", 0))
API_HASH = os.environ.get("TG_API_HASH")
BOT_TOKEN = os.environ.get("TG_BOT_TOKEN")
GITHUB_TOKEN = os.environ.get("GITHUB_PAT")
GITHUB_REPO = os.environ.get("GITHUB_REPO") 
WORKFLOW_FILE = "upload-from-telegram.yml"
# =========================================================

app = Client("smart_ui_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN, in_memory=True)
user_selections = {}

def get_keyboard(chat_id):
    sel = user_selections.get(chat_id, {'GH': True, 'HF': True, 'FTP': True, 'BALE': True})
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton(f"🐙 GitHub: {'✅' if sel['GH'] else '❌'}", callback_data="toggle_GH"),
            InlineKeyboardButton(f"🤗 HuggingFace: {'✅' if sel['HF'] else '❌'}", callback_data="toggle_HF")
        ],
        [
            InlineKeyboardButton(f"🌐 Host: {'✅' if sel['FTP'] else '❌'}", callback_data="toggle_FTP"),
            InlineKeyboardButton(f"🟢 Bale: {'✅' if sel['BALE'] else '❌'}", callback_data="toggle_BALE")
        ],
        [InlineKeyboardButton("🚀 شروع آپلود", callback_data="start_upload")]
    ])

@app.on_message(filters.document | filters.video | filters.audio | filters.photo)
async def handle_file(client, message):
    user_selections[message.chat.id] = {'GH': True, 'HF': True, 'FTP': True, 'BALE': True}
    user_selections[f"msg_{message.chat.id}"] = message.id
    
    await message.reply_text(
        "📍 **مقاصد ذخیره‌سازی این فایل را انتخاب کنید:**",
        reply_markup=get_keyboard(message.chat.id)
    )

@app.on_callback_query()
async def button_handler(client, callback_query: CallbackQuery):
    chat_id = callback_query.message.chat.id
    data = callback_query.data
    
    if data.startswith("toggle_"):
        target = data.split("_")[1]
        user_selections[chat_id][target] = not user_selections[chat_id][target]
        await callback_query.message.edit_reply_markup(reply_markup=get_keyboard(chat_id))
        
    elif data == "start_upload":
        sel = user_selections[chat_id]
        selected_targets = [key for key, value in sel.items() if value]
        
        if not selected_targets:
            await callback_query.answer("❌ حداقل یک مقصد باید انتخاب شود!", show_alert=True)
            return
            
        await callback_query.message.edit_text("⚙️ در حال ارسال دستور به سرورهای گیت‌هاب...")
        
        msg_id = user_selections[f"msg_{chat_id}"]
        dest_str = ",".join(selected_targets)
        
        url = f"https://api.github.com/repos/{GITHUB_REPO}/actions/workflows/{WORKFLOW_FILE}/dispatches"
        headers = {
            "Accept": "application/vnd.github.v3+json",
            "Authorization": f"token {GITHUB_TOKEN}"
        }
        payload = {
            "ref": "main",
            "inputs": {
                "chat_id": str(chat_id),
                "message_id": str(msg_id),
                "destinations": dest_str
            }
        }
        
        response = requests.post(url, headers=headers, json=payload)
        
        if response.status_code == 204:
            await callback_query.message.edit_text(f"✅ دستور با موفقیت ارسال شد.\n\n🎯 مقاصد: {dest_str}\n\nمنتظر دریافت گزارش باشید...")
        else:
            await callback_query.message.edit_text(f"❌ خطا در ارتباط با گیت‌هاب:\n{response.text}")

# ================= سرور وب مصنوعی برای فریب رندر =================
async def web_hello(request):
    return web.Response(text="Bot is running completely free on Render!")

async def start_web_server():
    web_app = web.Application()
    web_app.router.add_get('/', web_hello)
    runner = web.AppRunner(web_app)
    await runner.setup()
    port = int(os.environ.get('PORT', 8080))
    site = web.TCPSite(runner, '0.0.0.0', port)
    await site.start()
    print(f"🌍 Dummy Web Server is alive on port {port}")

async def main():
    await start_web_server()
    await app.start()
    print("🤖 UI Bot is actively listening...")
    await asyncio.Event().wait()

if __name__ == '__main__':
    asyncio.run(main())
