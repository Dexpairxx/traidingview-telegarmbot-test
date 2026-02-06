"""
Telegram Notifier Module
Gửi thông báo từ TradingView alerts đến Telegram
"""

import asyncio
from telegram import Bot
from telegram.constants import ParseMode
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


def detect_signal_from_data(data: dict) -> str:
    """
    Detect signal type từ các field trong data
    Xử lý trường hợp {{strategy.order.action}} không hoạt động với indicators
    """
    signal = data.get("signal", "").upper()
    
    # Nếu signal là placeholder chưa được thay thế
    placeholder_patterns = ["{{", "}}", "STRATEGY", "ORDER", "ACTION"]
    is_placeholder = any(p in signal for p in placeholder_patterns)
    
    if not is_placeholder and signal:
        return signal
    
    # Fallback: trả về REVERSAL nếu không detect được
    return "REVERSAL"


def format_alert_message(data: dict) -> str:
    """
    Format webhook data thành message đẹp cho Telegram
    
    Args:
        data: Dict chứa thông tin từ TradingView webhook
        
    Returns:
        Formatted string message
    """
    signal = detect_signal_from_data(data)
    
    # Emoji theo loại tín hiệu
    if signal in ["BULLISH", "BUY", "LONG", "GREEN"]:
        signal_emoji = "🟢"
        signal_text = "BULLISH"
    elif signal in ["BEARISH", "SELL", "SHORT", "RED"]:
        signal_emoji = "🔴"
        signal_text = "BEARISH"
    elif signal in ["REVERSAL"]:
        signal_emoji = "🔄"
        signal_text = "REVERSAL"
    elif signal in ["OVERSOLD"]:
        signal_emoji = "🟢"
        signal_text = "RSI OVERSOLD (Có thể đảo chiều lên)"
    elif signal in ["OVERBOUGHT"]:
        signal_emoji = "🔴"
        signal_text = "RSI OVERBOUGHT (Có thể đảo chiều xuống)"
    else:
        signal_emoji = "⚪"
        signal_text = signal
    
    # Lấy thông tin từ data
    symbol = data.get("symbol", "N/A")
    timeframe = data.get("timeframe", "N/A")
    indicator = data.get("indicator", "N/A")
    price = data.get("price", "N/A")
    time_str = data.get("time", "")
    
    # Format thời gian sang múi giờ Việt Nam (GMT+7)
    try:
        from datetime import timezone, timedelta
        # Parse ISO format từ TradingView (2026-02-06T13:25:00Z)
        if time_str and "T" in time_str:
            # Remove 'Z' and parse
            clean_time = time_str.replace("Z", "")
            utc_time = datetime.fromisoformat(clean_time)
            # Convert to Vietnam timezone (UTC+7)
            vietnam_tz = timezone(timedelta(hours=7))
            vietnam_time = utc_time.replace(tzinfo=timezone.utc).astimezone(vietnam_tz)
            time_str = vietnam_time.strftime("%d/%m/%Y %H:%M (GMT+7)")
        elif not time_str:
            # Fallback: sử dụng thời gian hiện tại
            from datetime import timezone, timedelta
            vietnam_tz = timezone(timedelta(hours=7))
            now = datetime.now(vietnam_tz)
            time_str = now.strftime("%d/%m/%Y %H:%M (GMT+7)")
    except Exception:
        # Giữ nguyên nếu không parse được
        pass
    
    # Format giá nếu là số
    try:
        price_float = float(price)
        if price_float >= 1000:
            price = f"${price_float:,.2f}"
        else:
            price = f"${price_float:.4f}"
    except (ValueError, TypeError):
        pass
    
    # Map timeframe
    timeframe_map = {
        "1": "1m", "5": "5m", "15": "15m", "30": "30m",
        "60": "H1", "240": "H4", "D": "Daily", "1D": "Daily",
        "W": "Weekly", "1W": "Weekly", "M": "Monthly", "1M": "Monthly",
        "1H": "H1", "4H": "H4"
    }
    timeframe_display = timeframe_map.get(timeframe, timeframe)
    
    message = f"""
{signal_emoji} <b>{signal_text}</b>

📊 <b>Crypto:</b> {symbol}
⏱️ <b>Timeframe:</b> {timeframe_display}
📈 <b>Indicator:</b> {indicator}
💰 <b>Price:</b> {price}
🕐 <b>Time:</b> {time_str}
"""
    
    return message.strip()


async def send_telegram_message_async(bot_token: str, chat_id: str, message: str) -> bool:
    """
    Gửi message đến Telegram (async version)
    
    Args:
        bot_token: Telegram Bot API token
        chat_id: Chat ID để gửi message
        message: Nội dung message
        
    Returns:
        True nếu gửi thành công, False nếu thất bại
    """
    try:
        bot = Bot(token=bot_token)
        await bot.send_message(
            chat_id=chat_id,
            text=message,
            parse_mode=ParseMode.HTML
        )
        logger.info(f"Telegram message sent successfully to chat_id: {chat_id}")
        return True
    except Exception as e:
        logger.error(f"Failed to send Telegram message: {e}")
        return False


def send_telegram_message(bot_token: str, chat_id: str, message: str) -> bool:
    """
    Gửi message đến Telegram (sync wrapper)
    
    Args:
        bot_token: Telegram Bot API token
        chat_id: Chat ID để gửi message
        message: Nội dung message
        
    Returns:
        True nếu gửi thành công, False nếu thất bại
    """
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(
            send_telegram_message_async(bot_token, chat_id, message)
        )
        loop.close()
        return result
    except Exception as e:
        logger.error(f"Error in sync wrapper: {e}")
        return False


def send_alert(bot_token: str, chat_id: str, alert_data: dict) -> bool:
    """
    Main function: Format và gửi alert đến Telegram
    
    Args:
        bot_token: Telegram Bot API token
        chat_id: Chat ID để gửi message
        alert_data: Dict chứa thông tin alert từ TradingView
        
    Returns:
        True nếu gửi thành công, False nếu thất bại
    """
    message = format_alert_message(alert_data)
    return send_telegram_message(bot_token, chat_id, message)
