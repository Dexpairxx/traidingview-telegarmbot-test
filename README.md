# TradingView Alert → Telegram Bot

Bot nhận webhook từ TradingView và gửi thông báo đến Telegram khi indicator phát tín hiệu.

## 🎯 Tính năng

- Nhận alert từ **Reversal Pro 3.0** (bullish/bearish signals)
- Nhận alert từ **RSI** (overbought/oversold)
- Hỗ trợ timeframe: **H1, H4, Daily**
- Thông báo đẹp với emoji 🟢🔴

---

## 🚀 Thiết lập

### Bước 1: Tạo Telegram Bot

1. Mở Telegram, tìm **@BotFather**
2. Gửi `/newbot`
3. Đặt tên bot (ví dụ: `TradingView Alert Bot`)
4. Đặt username (ví dụ: `tv_alert_yourname_bot`)
5. **Lưu lại Bot Token** (dạng: `1234567890:ABCdefGHIjklMNOpqrsTUVwxyz`)

### Bước 2: Lấy Chat ID

1. Gửi tin nhắn bất kỳ cho bot bạn vừa tạo
2. Truy cập: `https://api.telegram.org/bot<BOT_TOKEN>/getUpdates`
3. Tìm `"chat":{"id": 123456789}` → đó là Chat ID của bạn

### Bước 3: Deploy lên Railway

1. Đăng nhập [Railway](https://railway.app)
2. New Project → Deploy from GitHub repo
3. Thêm Environment Variables:
   - `TELEGRAM_BOT_TOKEN` = Bot token từ bước 1
   - `TELEGRAM_CHAT_ID` = Chat ID từ bước 2
   - `WEBHOOK_SECRET` = `tv_alert_secret_2026_xyz`
4. Deploy và lấy URL (dạng: `https://your-app.up.railway.app`)

### Bước 4: Test Bot

Truy cập `https://your-app.up.railway.app/test` để gửi test alert.

---

## 📊 Cấu hình Alert trên TradingView

### Alert cho Reversal Pro 3.0

1. Mở chart **BTCUSDT** trên TradingView
2. Thêm indicator **"Reversal Detection v3.0"**
3. Chọn timeframe **H1** (hoặc H4, D)
4. Click biểu tượng 🔔 **Alert** trên toolbar
5. Cấu hình:
   - **Condition**: Reversal Detection v3.0
   - **Alert type**: Chọn loại bạn muốn (Bullish Reversal, Bearish Reversal, etc.)
   - **Once Per Bar Close**: ✅ Bật
   - **Alert name**: `Reversal Pro - H1 - BTCUSDT`

6. Tab **Notifications** → Bật **Webhook URL**:

   ```
   https://your-app.up.railway.app/webhook
   ```

7. **Message** (copy nguyên văn):

   ```json
   {
     "secret": "tv_alert_secret_2026_xyz",
     "symbol": "{{ticker}}",
     "timeframe": "{{interval}}",
     "indicator": "Reversal Pro 3.0",
     "signal": "{{strategy.order.action}}",
     "price": "{{close}}",
     "time": "{{timenow}}"
   }
   ```

8. Click **Create**

### Alert cho RSI

1. Thêm indicator **RSI** (built-in)
2. Click 🔔 **Alert**
3. Cấu hình:
   - **Condition**: RSI → Crossing Down → 70 (cho overbought)
   - **Condition**: RSI → Crossing Up → 30 (cho oversold)
   - **Once Per Bar Close**: ✅ Bật

4. **Webhook URL**: `https://your-app.up.railway.app/webhook`

5. **Message cho Overbought** (RSI > 70):

   ```json
   {
     "secret": "tv_alert_secret_2026_xyz",
     "symbol": "{{ticker}}",
     "timeframe": "{{interval}}",
     "indicator": "RSI",
     "signal": "OVERBOUGHT",
     "price": "{{close}}",
     "time": "{{timenow}}"
   }
   ```

6. **Message cho Oversold** (RSI < 30):
   ```json
   {
     "secret": "tv_alert_secret_2026_xyz",
     "symbol": "{{ticker}}",
     "timeframe": "{{interval}}",
     "indicator": "RSI",
     "signal": "OVERSOLD",
     "price": "{{close}}",
     "time": "{{timenow}}"
   }
   ```

---

## 📱 Ví dụ thông báo Telegram

```
🟢 BULLISH

📊 Symbol: BTCUSDT
⏱️ Timeframe: H1
📈 Indicator: Reversal Pro 3.0
💰 Price: $42,150.00
🕐 Time: 2026-02-02 21:00
```

---

## 🔧 Chạy Local (Development)

```bash
# Tạo virtual environment
python -m venv venv
venv\Scripts\activate  # Windows

# Cài dependencies
pip install -r requirements.txt

# Copy và sửa file .env
copy .env.example .env
# Sửa TELEGRAM_BOT_TOKEN và TELEGRAM_CHAT_ID

# Chạy server
python webhook_server.py
```

Test với ngrok:

```bash
ngrok http 5000
```

---

## 📁 Cấu trúc Project

```
telegram-bot-test02/
├── webhook_server.py    # Flask server nhận webhook
├── telegram_notifier.py # Module gửi Telegram
├── requirements.txt     # Dependencies
├── Procfile            # Railway config
├── .env.example        # Template env vars
├── .gitignore
└── README.md
```

---

## ⚠️ Lưu ý quan trọng

1. **TradingView Pro** cần thiết để dùng Webhook
2. **Giữ bí mật** `WEBHOOK_SECRET` - không share public
3. Tạo **alert riêng** cho mỗi timeframe (H1, H4, D)
4. Sử dụng **Once Per Bar Close** để tránh tín hiệu giả
