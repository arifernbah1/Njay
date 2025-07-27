#!/bin/bash

echo "🚀 Arif Signal Trading Bot - Installation Script"
echo "================================================"

# Check if Python 3 is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3.7+ first."
    exit 1
fi

# Check Python version
python_version=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
echo "✅ Python version: $python_version"

# Install dependencies
echo "📦 Installing Python dependencies..."
pip3 install -r requirements.txt

if [ $? -eq 0 ]; then
    echo "✅ Dependencies installed successfully"
else
    echo "❌ Failed to install dependencies"
    exit 1
fi

# Check if .env file exists
if [ ! -f "arif_signal/.env" ]; then
    echo "⚠️  .env file not found. Creating template..."
    cat > arif_signal/.env << EOF
# Telegram Configuration
TELEGRAM_BOT_TOKEN=your_bot_token_here
TELEGRAM_CHAT_ID=your_chat_id_here

# Binance API (optional, untuk data)
BINANCE_API_KEY=your_api_key_here
BINANCE_SECRET_KEY=your_secret_key_here

# Trading Pairs
TRADING_PAIRS=BTCUSDT,ETHUSDT,BNBUSDT,ADAUSDT,SOLUSDT
EOF
    echo "📝 Created .env template. Please edit arif_signal/.env with your configuration."
else
    echo "✅ .env file found"
fi

# Make scripts executable
chmod +x run.py
chmod +x arif_signal/start.py

echo ""
echo "🎉 Installation completed successfully!"
echo ""
echo "📋 Next steps:"
echo "1. Edit arif_signal/.env with your Telegram bot token and chat ID"
echo "2. Run the bot using one of these methods:"
echo "   - From root directory: python3 run.py"
echo "   - From arif_signal directory: python3 start.py"
echo ""
echo "📚 For more information, see README.md"
echo ""
echo "🚀 Happy Trading! 📊"