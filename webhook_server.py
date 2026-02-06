"""
TradingView Webhook Server
Nhận webhook từ TradingView và forward đến Telegram
"""

import os
import logging
from flask import Flask, request, jsonify
from dotenv import load_dotenv
from telegram_notifier import send_alert

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
    logger.info(f"Starting webhook server on port {port}")
    app.run(host="0.0.0.0", port=port, debug=False)
