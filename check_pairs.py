#!/usr/bin/env python3

import ccxt
import time

def check_binance_pairs():
    """Check if all trading pairs are available on Binance Futures"""
    
    # Initialize Binance Futures exchange
    exchange = ccxt.binance({
        'enableRateLimit': True,
        'options': {'defaultType': 'future'}
    })
    
    # Pairs to check
    pairs = ['BTCUSDT', 'ETHUSDT', 'BNBUSDT', 'SOLUSDT', 'ADAUSDT', 'AVAXUSDT', 'MATICUSDT', 'DOTUSDT']
    symbols = ['BTC/USDT', 'ETH/USDT', 'BNB/USDT', 'SOL/USDT', 'ADA/USDT', 'AVAX/USDT', 'POLYGON/USDT', 'DOT/USDT']
    
    print('🔍 Checking Binance Futures pairs availability...')
    print('=' * 60)
    
    available_pairs = []
    unavailable_pairs = []
    
    for pair, symbol in zip(pairs, symbols):
        try:
            # Load markets first
            markets = exchange.load_markets()
            
            if symbol in markets:
                # Get ticker data
                ticker = exchange.fetch_ticker(symbol)
                price = ticker['last']
                volume_24h = ticker['quoteVolume']
                
                print(f'✅ {pair} ({symbol}): Available')
                print(f'   💰 Price: ${price:,.4f}')
                print(f'   📊 24h Volume: ${volume_24h:,.0f}')
                
                available_pairs.append(pair)
            else:
                print(f'❌ {pair} ({symbol}): NOT AVAILABLE')
                unavailable_pairs.append(pair)
                
        except Exception as e:
            print(f'❌ {pair} ({symbol}): ERROR - {str(e)}')
            unavailable_pairs.append(pair)
        
        # Rate limiting
        time.sleep(0.5)
    
    print('\n' + '=' * 60)
    print('📊 SUMMARY:')
    print(f'✅ Available: {len(available_pairs)} pairs')
    print(f'❌ Unavailable: {len(unavailable_pairs)} pairs')
    
    if available_pairs:
        print(f'\n✅ Available pairs: {", ".join(available_pairs)}')
    
    if unavailable_pairs:
        print(f'\n❌ Unavailable pairs: {", ".join(unavailable_pairs)}')
    
    # Recommendations
    print('\n💡 RECOMMENDATIONS:')
    if len(available_pairs) >= 6:
        print('✅ Most pairs are available - Bot should work well!')
    elif len(available_pairs) >= 4:
        print('⚠️  Some pairs unavailable - Consider removing problematic pairs')
    else:
        print('❌ Many pairs unavailable - Check Binance API or use different pairs')
    
    return available_pairs, unavailable_pairs

if __name__ == '__main__':
    check_binance_pairs()