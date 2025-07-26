# 🤖 Arif Signal Trading Bot

Bot trading otomatis yang mendeteksi pola sweep dan engulfing untuk menghasilkan sinyal trading berkualitas tinggi.

## 🚀 Fitur Utama

- **Pattern Detection**: Sweep + Engulfing patterns
- **Real-time Data**: WebSocket connection ke Binance Futures
- **Technical Analysis**: RSI, Support/Resistance levels
- **Signal Filtering**: Multi-layer filtering system
- **Telegram Notifications**: Sinyal otomatis via Telegram
- **Advanced Logging**: Colored console + file logging

## 📋 Requirements

- Python 3.8+
- Telegram Bot Token
- Telegram Chat ID

## 🛠️ Installation

1. **Clone repository**
```bash
git clone <repository-url>
cd arif_signal
```

2. **Install dependencies**
```bash
pip install -r requirements.txt
```

3. **Setup Telegram Bot**
   - Buat bot di [@BotFather](https://t.me/botfather)
   - Dapatkan token bot
   - Dapatkan chat ID dari [@userinfobot](https://t.me/userinfobot)

4. **Configure bot**
   - Edit `arif_signal/utils.py`
   - Ganti `TELEGRAM_TOKEN` dan `TELEGRAM_CHAT_ID`

## ⚙️ Configuration

### Trading Pairs
```python
TIER1_PAIRS = [
    'BTCUSDT', 'ETHUSDT', 'BNBUSDT', 'SOLUSDT',
    'ADAUSDT', 'AVAXUSDT', 'MATICUSDT', 'DOTUSDT'
]
```

### Trading Parameters
```python
TIMEFRAME = '15m'
MIN_VOLUME_USDT = 500000  # $500k minimum
SIGNAL_COOLDOWN_MINUTES = 30
```

### Pair-specific Config
```python
'BTCUSDT': TradingConfig(
    min_strength=4.0,      # Minimum signal strength
    volume_multiplier=2.0, # Volume confirmation
    rsi_oversold=25,       # RSI oversold level
    rsi_overbought=75,     # RSI overbought level
    min_risk_reward=2.0,   # Minimum R:R ratio
    priority=1,            # Priority level
    max_daily_signals=4    # Max signals per day
)
```

## 🚀 Usage

### Run Bot
```bash
cd arif_signal
python main.py
```

### Stop Bot
```bash
Ctrl+C
```

## 📊 Signal Quality

Bot menggunakan sistem rating 1-6.5★:

- **🔥🔥🔥 PREMIUM** (5.0+★): Sinyal berkualitas sangat tinggi
- **🔥🔥 HIGH** (4.0+★): Sinyal berkualitas tinggi
- **🔥 GOOD** (3.5+★): Sinyal berkualitas baik
- **⚡ STANDARD** (<3.5★): Sinyal standar

## 🕐 Trading Sessions

Bot aktif di jam optimal (WIB):
- **PAGI** (08:00-12:00): Asian + EU Prep
- **SORE** (15:00-19:00): London Active
- **MALAM** (20:00-23:00): NY Prime

## 📁 File Structure

```
arif_signal/
├── main.py              # Entry point
├── models.py            # Data structures
├── utils.py             # Config & time utilities
├── analysis.py          # Technical analysis
├── processor.py         # Signal processing
├── notifications.py     # Telegram notifications
├── data_ws.py           # WebSocket & data management
└── trading_logger.py    # Advanced logging
```

## 🔧 Troubleshooting

### Common Issues

1. **Import Errors**
   - Pastikan semua dependencies terinstall
   - Jalankan `pip install -r requirements.txt`

2. **WebSocket Connection Failed**
   - Cek koneksi internet
   - Pastikan firewall tidak memblokir

3. **Telegram Notifications Failed**
   - Cek token bot dan chat ID
   - Pastikan bot sudah di-start

4. **No Signals Generated**
   - Cek jam trading (WIB)
   - Pastikan volume pair mencukupi
   - Cek daily signal limit

## ⚠️ Disclaimer

**RISK WARNING**: Trading cryptocurrency memiliki risiko tinggi. Bot ini hanya untuk edukasi dan tidak menjamin profit. Gunakan dengan tanggung jawab dan sesuai kemampuan finansial Anda.

## 📝 License

MIT License - Gunakan dengan bijak!

## 🤝 Support

Untuk pertanyaan atau support, silakan buat issue di repository ini.