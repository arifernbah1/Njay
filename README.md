# 🤖 Arif Signal Trading Bot

**Advanced Signal Generator Bot with Parallel Dual Mode Execution**

## 📊 Overview

Arif Signal Trading Bot adalah sistem signal generator yang canggih dengan fitur:

- **⚡ SCALPING Mode** - Quick momentum trading (15m timeframe)
- **📈 SWING Mode** - Medium-term trend trading (1h timeframe)
- **🔄 Parallel Execution** - Kedua mode jalan bersamaan
- **🎯 Swing Pre-Setup** - Pre-analysis sebelum entry
- **📱 Telegram Integration** - Real-time notifications
- **🏥 Health Monitoring** - Complete system monitoring
- **🛡️ Error Handling** - Comprehensive error management
- **📝 Specialized Logging** - JSON structured logs

## 🚀 Features

### ⚡ SCALPING Mode
- **Timeframe:** 15m candles
- **Cycle:** 15 seconds
- **Patterns:** Sweep, Engulfing
- **Analysis:** RSI, Volume, Basic S/R
- **Strategy:** Quick momentum trades

### 📈 SWING Mode
- **Timeframe:** 1h candles
- **Cycle:** 60 seconds
- **Patterns:** Breakout, Reversal, Continuation
- **Analysis:** Multi-EMA, MACD, Ichimoku, Advanced S/R
- **Pre-Setup:** Comprehensive analysis sebelum entry
- **Strategy:** Medium-term trend trades

### 🎯 Swing Pre-Setup System
- **Setup Creation** - Pre-analysis sebelum entry
- **Setup Types** - BREAKOUT, REVERSAL, CONTINUATION
- **Entry Zone** - Price range untuk entry
- **Risk Management** - Stop Loss + Multiple Take Profits
- **Setup Validation** - Confidence & strength scoring

### 📱 Telegram Notifications
- **Swing Setup Alerts** - Notifikasi setup baru
- **Signal Alerts** - Notifikasi signal generated
- **Setup Triggered Alerts** - Notifikasi setup ter-trigger
- **Health Alerts** - System health notifications
- **Error Alerts** - Critical error notifications

### 🏥 Health Monitoring
- **System Metrics** - CPU, Memory, Disk, Network
- **Bot Metrics** - Performance, Errors, Signals
- **Component Status** - Thread health, Response times
- **Health Alerts** - Warning/Critical notifications
- **Health History** - Performance tracking

## 📦 Installation

### 1. Download & Extract
```bash
# Download dari bashupload
wget https://bashupload.com/6Uo1b/hES7L.zip

# Extract file
unzip hES7L.zip

# Masuk ke directory
cd arif_signal_trading_bot_with_health
```

### 2. Install Dependencies
```bash
# Install Python dependencies
pip install -r requirements.txt

# Atau install manual
pip install requests websocket-client python-dotenv psutil
```

### 3. Configure Environment
Edit file `.env` di dalam folder `arif_signal/`:
```env
# Telegram Configuration
TELEGRAM_BOT_TOKEN=your_bot_token_here
TELEGRAM_CHAT_ID=your_chat_id_here

# Binance API (optional, untuk data)
BINANCE_API_KEY=your_api_key_here
BINANCE_SECRET_KEY=your_secret_key_here

# Trading Pairs
TRADING_PAIRS=BTCUSDT,ETHUSDT,BNBUSDT,ADAUSDT,SOLUSDT
```

### 4. Setup Telegram Bot
1. Buat bot di [@BotFather](https://t.me/botfather)
2. Dapatkan bot token
3. Chat dengan bot dan dapatkan chat ID
4. Update `.env` file

## 🚀 Usage

### Run Bot
```bash
# Cara 1: Menggunakan run.py (recommended)
python run.py

# Cara 2: Langsung dari arif_signal directory
cd arif_signal
python main.py
```

### Bot Output
```
🚀 Starting Arif Signal Trading System...
============================================================
📊 Signal Generator Bot
⚡ SCALPING Mode: Active (15s cycle)
📈 SWING Mode: Active (60s cycle)
🔄 Both modes running simultaneously!
🏥 Health Monitoring: Active (5min cycle)
📱 Telegram Notifications: Enabled
🛡️ Error Handling: Comprehensive
📝 Logging: Specialized Trading Logger
============================================================
```

## 📱 Telegram Messages

### Signal Alert Example
```
⚡ SCALPING SIGNAL

🟢 Direction: BUY
💎 Pair: BTCUSDT
📊 Pattern: Sweep/Engulfing
🕐 Time: 22:30:15 WIB

💰 Entry Price: $43,250.00
🛑 Stop Loss: $43,000.00
🎯 Take Profit: $43,600.00

💪 Strength: 4.2/5.0
📊 Risk/Reward: 1:3.0

🚀 Signal ready for execution!
```

### Swing Setup Alert Example
```
🎯 SWING SETUP CREATED

💎 Pair: BTCUSDT
📊 Type: BREAKOUT
⏰ Timeframe: 1h
🕐 Created: 22:15:30 WIB

📈 Market Structure: BULLISH
🎯 Confidence: 85.0%
💪 Strength: 4.2/5.0
📊 Risk/Reward: 1:3.0

💰 Entry Zone: $43,200.00 - $43,300.00
🛑 Stop Loss: $43,000.00

🎯 Take Profit Targets:
   TP1: $43,600.00
   TP2: $43,900.00
   TP3: $44,500.00

⚠️ Setup is ACTIVE - Waiting for price to enter entry zone...
```

### Health Alert Example
```
🏥 BOT HEALTH ALERT

🟢 Status: EXCELLENT
🕐 Time: 22:15:30 WIB
⏱️ Uptime: 2h 15m

💻 System Metrics:
• CPU: 25.3%
• Memory: 45.2% (2048MB)
• Disk: 65.8%

🤖 Bot Metrics:
• Signals: 15 (S: 8, W: 7)
• Errors: 2
• Telegram: 20 sent, 0 failed
• Processing: 150ms avg

🔧 Component Status:
• SCALPING_THREAD: 🟢 RUNNING
• SWING_THREAD: 🟢 RUNNING
• DATA_MANAGER: 🟢 RUNNING
• SIGNAL_PROCESSOR: 🟢 RUNNING
• TELEGRAM_SERVICE: 🟢 RUNNING
• ERROR_HANDLER: 🟢 RUNNING
• SWING_SETUP_MANAGER: 🟢 RUNNING
```

## 📁 File Structure

```
arif_signal_trading_bot_with_health/
├── run.py                          # Main entry point
├── requirements.txt                # Python dependencies
├── README.md                       # This file
└── arif_signal/                    # Main bot directory
    ├── main.py                     # Main application
    ├── health_monitor.py           # Health monitoring system
    ├── trading_logger.py           # Specialized trading logger
    ├── error_handler.py            # Error handling system
    ├── notifications.py            # Telegram integration
    ├── swing_setup.py              # Swing pre-setup system
    ├── processor.py                # Signal processing
    ├── analysis.py                 # Technical analysis
    ├── data_ws.py                  # Data management
    ├── config.py                   # Configuration management
    ├── models.py                   # Data models
    ├── utils.py                    # Utility functions
    ├── logger.py                   # Legacy logger
    ├── __init__.py                 # Package initialization
    └── .env                        # Environment configuration
```

## 📝 Logging

Bot menggunakan **Specialized Trading Logger** dengan output JSON:

```
trading_logs/
├── signals.json          # Trading signals
├── patterns.json         # Pattern detections
├── performance.json      # Performance metrics
├── risk_management.json  # Entry/exit logs
├── market_analysis.json  # Technical analysis
├── alerts.json          # System alerts
├── backtest.json        # Backtest results
├── live_trading.json    # Live trading logs
└── errors.json          # Error logs
```

## 🛡️ Error Handling

Bot memiliki **Comprehensive Error Handling** dengan:

- **8 Error Categories** - Data, Network, API, Config, Processing, Telegram, System, Validation
- **4 Severity Levels** - Low, Medium, High, Critical
- **Auto Recovery** - Retry logic & fallback mechanisms
- **Error Statistics** - Tracking & analytics
- **Safe Execution** - Protected function calls

## 🏥 Health Monitoring

Bot memonitor kesehatan sistem secara real-time:

- **System Metrics** - CPU, Memory, Disk, Network usage
- **Bot Metrics** - Performance, Errors, Signals generated
- **Component Status** - Thread health, Response times
- **Health Alerts** - Warning/Critical notifications
- **Health History** - Performance tracking & trends

## ⚠️ Important Notes

### Signal Generator, Bukan Auto Trading
- **Bot ini adalah SIGNAL GENERATOR** - Memberikan rekomendasi trading
- **TIDAK execute trades otomatis** - Anda yang manual entry/exit
- **Perfect untuk learning** - Study patterns & market structure
- **Risk management** - Anda yang control SL/TP

### System Requirements
- **Python 3.7+** - Required
- **Internet Connection** - Untuk data & Telegram
- **Minimal 2GB RAM** - Recommended
- **Linux/Windows/Mac** - Supported

### Telegram Setup
1. **Bot Token** - Dapatkan dari @BotFather
2. **Chat ID** - Chat dengan bot untuk dapat ID
3. **Permissions** - Bot harus bisa send messages
4. **Testing** - Test notification sebelum live

## 🔧 Troubleshooting

### Common Issues

#### Import Error
```bash
# Error: No module named 'arif_signal'
# Solution: Run dari root directory
python run.py
```

#### Telegram Error
```bash
# Error: Telegram notification failed
# Solution: Check bot token & chat ID di .env
```

#### Health Monitor Error
```bash
# Error: psutil not found
# Solution: Install psutil
pip install psutil
```

#### Permission Error
```bash
# Error: Cannot create log files
# Solution: Check directory permissions
chmod 755 arif_signal/
```

## 📞 Support

Untuk bantuan dan support:
- **Documentation** - Lihat file ini
- **Logs** - Check `trading_logs/` directory
- **Health Monitor** - Monitor system health
- **Error Handler** - Check error logs

## 📄 License

Bot ini dibuat untuk educational purposes. Gunakan dengan risiko sendiri.

---

**🚀 Happy Trading! 📊**