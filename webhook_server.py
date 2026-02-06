"""
TradingView Webhook Server
Nhận webhook từ TradingView và forward đến Telegram
"""

import os
import logging
import threading
from flask import Flask, request, jsonify
from dotenv import load_dotenv
from telegram_notifier import send_alert
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create Flask app
app = Flask(__name__)

# Configuration from environment
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET", "tradingview_secret_2026")


# ============== TELEGRAM BOT COMMANDS ==============

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler cho lệnh /start"""
    welcome_message = """
🤖 <b>TradingView Alert Bot</b>

Chào mừng bạn! Bot này nhận tín hiệu từ TradingView và gửi thông báo đến đây.

📌 <b>Commands:</b>
/start - Hiển thị tin nhắn chào mừng
/help - Hướng dẫn thiết lập TradingView
/status - Kiểm tra trạng thái bot

⚡ Khi có tín hiệu từ TradingView, bạn sẽ nhận thông báo tự động!
"""
    await update.message.reply_text(welcome_message, parse_mode='HTML')


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler cho lệnh /help"""
    help_message = """
📡 <b>Hướng dẫn thiết lập TradingView Webhook</b>

<b>Bước 1:</b> Mở TradingView và thêm indicator Reversal Pro 3.0

<b>Bước 2:</b> Tạo Alert BULLISH
• Click chuột phải → Add Alert (hoặc Alt+A)
• Condition: Reversal Pro v3.0 → Bullish Reversal
• Trigger: Once per bar close ✅
• Message:
<code>{
  "secret": "tv_alert_secret_2026_xyz",
  "symbol": "{{ticker}}",
  "timeframe": "{{interval}}",
  "indicator": "Reversal Pro 3.0",
  "signal": "BULLISH",
  "price": "{{close}}",
  "time": "{{timenow}}"
}</code>
• Notifications → ✅ Webhook URL
• URL: Webhook server của bạn + /webhook

<b>Bước 3:</b> Tạo Alert BEARISH (tương tự, thay BULLISH → BEARISH)

⚠️ <b>Lưu ý:</b>
• Cần TradingView Pro để dùng Webhook
• Tạo 2 alerts riêng (BULLISH + BEARISH)
• KHÔNG dùng {{strategy.order.action}} với Indicator
"""
    await update.message.reply_text(help_message, parse_mode='HTML')


async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler cho lệnh /status"""
    status_message = """
✅ <b>Bot Status: Online</b>

🔗 Webhook đang hoạt động
📡 Sẵn sàng nhận tín hiệu từ TradingView
"""
    await update.message.reply_text(status_message, parse_mode='HTML')


def run_telegram_bot():
    """Chạy Telegram bot trong thread riêng"""
    import asyncio
    
    if not TELEGRAM_BOT_TOKEN:
        logger.warning("TELEGRAM_BOT_TOKEN not set, bot commands disabled")
        return
    
    try:
        # Create new event loop for this thread
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
        
        # Add handlers
        application.add_handler(CommandHandler("start", start_command))
        application.add_handler(CommandHandler("help", help_command))
        application.add_handler(CommandHandler("status", status_command))
        
        logger.info("Starting Telegram bot polling...")
        application.run_polling(drop_pending_updates=True)
    except Exception as e:
        logger.error(f"Failed to start Telegram bot: {e}")


# ============== AUTO-START BOT WHEN MODULE IS IMPORTED ==============
# This runs when gunicorn imports the module
def start_bot_thread():
    """Start bot in background thread - works with gunicorn"""
    bot_thread = threading.Thread(target=run_telegram_bot, daemon=True)
    bot_thread.start()
    logger.info("Telegram bot thread started (gunicorn compatible)")

# Start bot when module is loaded (for Railway/gunicorn)
start_bot_thread()


@app.route("/", methods=["GET"])
def home():
    """Health check endpoint"""
    return jsonify({
        "status": "online",
        "service": "TradingView Alert Bot",
        "endpoints": {
            "webhook": "POST /webhook"
        }
    })


@app.route("/webhook", methods=["POST"])
def webhook():
    """
    Nhận webhook từ TradingView
    
    Expected JSON payload:
    {
        "secret": "your_secret_token",
        "symbol": "BTCUSDT",
        "timeframe": "1H",
        "indicator": "Reversal Pro 3.0",
        "signal": "BULLISH",
        "price": "42150.00",
        "time": "2026-02-02 21:00"
    }
    """
    try:
        # Parse JSON data
        data = request.get_json(force=True)
        
        if not data:
            logger.warning("Received empty webhook payload")
            return jsonify({"error": "Empty payload"}), 400
        
        logger.info(f"Received webhook: {data}")
        
        # Validate secret token
        received_secret = data.get("secret", "")
        if received_secret != WEBHOOK_SECRET:
            logger.warning(f"Invalid secret token received")
            return jsonify({"error": "Invalid secret"}), 401
        
        # Check required config
        if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
            logger.error("Telegram configuration missing")
            return jsonify({"error": "Server configuration error"}), 500
        
        # Send alert to Telegram
        success = send_alert(TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, data)
        
        if success:
            logger.info("Alert sent successfully")
            return jsonify({"status": "success", "message": "Alert sent to Telegram"}), 200
        else:
            logger.error("Failed to send alert")
            return jsonify({"error": "Failed to send Telegram message"}), 500
            
    except Exception as e:
        logger.error(f"Webhook error: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/help", methods=["GET"])
def help_page():
    """
    Hướng dẫn setup TradingView Webhook
    Truy cập: GET /help
    """
    help_text = """
    <html>
    <head>
        <title>TradingView Webhook Setup Guide</title>
        <meta charset="UTF-8">
        <style>
            body { font-family: Arial, sans-serif; max-width: 800px; margin: 50px auto; padding: 20px; background: #1a1a2e; color: #eee; }
            h1 { color: #00d4ff; }
            h2 { color: #ff6b6b; margin-top: 30px; }
            code { background: #16213e; padding: 2px 8px; border-radius: 4px; color: #00ff88; }
            pre { background: #16213e; padding: 15px; border-radius: 8px; overflow-x: auto; color: #00ff88; }
            .step { background: #16213e; padding: 15px; margin: 10px 0; border-radius: 8px; border-left: 4px solid #00d4ff; }
            .warning { background: #3d1a1a; border-left-color: #ff6b6b; }
            a { color: #00d4ff; }
        </style>
    </head>
    <body>
        <h1>📡 TradingView Webhook Setup Guide</h1>
        
        <h2>🔧 Bước 1: Mở Chart và thêm Indicator</h2>
        <div class="step">
            <p>1. Mở <a href="https://www.tradingview.com" target="_blank">TradingView</a></p>
            <p>2. Chọn symbol bạn muốn theo dõi (VD: BTCUSDT, ETHUSD...)</p>
            <p>3. Thêm indicator <strong>Reversal Pro 3.0</strong> vào chart</p>
        </div>
        
        <h2>⚡ Bước 2: Tạo Alert BULLISH</h2>
        <div class="step">
            <p>1. Click chuột phải trên chart → <strong>Add Alert</strong> (hoặc nhấn Alt+A)</p>
            <p>2. Trong tab <strong>Settings</strong>:</p>
            <ul>
                <li><strong>Condition:</strong> Reversal Pro v3.0 → Bullish Reversal</li>
                <li><strong>Trigger:</strong> Once per bar close</li>
            </ul>
            <p>3. Trong tab <strong>Message</strong>, paste:</p>
            <pre>{
  "secret": "tv_alert_secret_2026_xyz",
  "symbol": "{{ticker}}",
  "timeframe": "{{interval}}",
  "indicator": "Reversal Pro 3.0",
  "signal": "BULLISH",
  "price": "{{close}}",
  "time": "{{timenow}}"
}</pre>
            <p>4. Trong tab <strong>Notifications</strong>:</p>
            <ul>
                <li>✅ Tick chọn <strong>Webhook URL</strong></li>
                <li>Nhập URL: <code>https://web-production-79fba.up.railway.app/webhook</code></li>
            </ul>
            <p>5. Click <strong>Save</strong></p>
        </div>
        
        <h2>⚡ Bước 3: Tạo Alert BEARISH</h2>
        <div class="step">
            <p>Lặp lại bước 2 với các thay đổi:</p>
            <ul>
                <li><strong>Condition:</strong> Reversal Pro v3.0 → Bearish Reversal</li>
            </ul>
            <p>Trong tab <strong>Message</strong>:</p>
            <pre>{
  "secret": "tv_alert_secret_2026_xyz",
  "symbol": "{{ticker}}",
  "timeframe": "{{interval}}",
  "indicator": "Reversal Pro 3.0",
  "signal": "BEARISH",
  "price": "{{close}}",
  "time": "{{timenow}}"
}</pre>
        </div>
        
        <h2 style="color: #ffd93d;">⚠️ Lưu ý quan trọng</h2>
        <div class="step warning">
            <ul>
                <li>Cần tạo <strong>2 alerts riêng</strong> cho mỗi symbol (1 BULLISH + 1 BEARISH)</li>
                <li>KHÔNG dùng <code>{{strategy.order.action}}</code> - chỉ hoạt động với Strategy, không hoạt động với Indicator</li>
                <li>URL phải kết thúc bằng <code>/webhook</code></li>
            </ul>
        </div>
        
        <h2>✅ Hoàn tất!</h2>
        <div class="step">
            <p>Mỗi khi có tín hiệu, bạn sẽ nhận thông báo trên Telegram! 🎉</p>
        </div>
    </body>
    </html>
    """
    return help_text, 200, {'Content-Type': 'text/html; charset=utf-8'}


@app.route("/test", methods=["GET"])
def test_alert():
    """
    Test endpoint để kiểm tra Telegram connection
    Truy cập: GET /test
    """
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        return jsonify({"error": "Telegram configuration missing"}), 500
    
    test_data = {
        "symbol": "BTCUSDT",
        "timeframe": "H1",
        "indicator": "Test Alert",
        "signal": "BULLISH",
        "price": "42150.00",
        "time": "Test Time"
    }
    
    success = send_alert(TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, test_data)
    
    if success:
        return jsonify({"status": "success", "message": "Test alert sent!"}), 200
    else:
        return jsonify({"error": "Failed to send test alert"}), 500


if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    # Bot already started when module loaded (see start_bot_thread())
    logger.info(f"Starting webhook server on port {port}")
    app.run(host="0.0.0.0", port=port, debug=False)

