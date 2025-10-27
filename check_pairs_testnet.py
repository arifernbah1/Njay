#!/usr/bin/env python3

import ccxt
import time

def check_binance_testnet():
    """Check if all trading pairs are available on Binance Testnet"""
    
    # Initialize Binance Testnet
    exchange = ccxt.binance({
        'enableRateLimit': True,
        'options': {'defaultType': 'future'},
        'urls': {
            'api': {
                'public': 'https://testnet.binancefuture.com/fapi/v1',
                'private': 'https://testnet.binancefuture.com/fapi/v1',
            },
        }
    })
    
    # Pairs to check
    pairs = ['BTCUSDT', 'ETHUSDT', 'BNBUSDT', 'SOLUSDT', 'ADAUSDT', 'AVAXUSDT', 'MATICUSDT', 'DOTUSDT']
    symbols = ['BTC/USDT', 'ETH/USDT', 'BNB/USDT', 'SOL/USDT', 'ADA/USDT', 'AVAX/USDT', 'POLYGON/USDT', 'DOT/USDT']
    
    print('🔍 Checking Binance Testnet pairs availability...')
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
    
    return available_pairs, unavailable_pairs

def check_alternative_exchanges():
    """Check pairs on alternative exchanges"""
    
    exchanges = [
        ('Bybit', ccxt.bybit),
        ('OKX', ccxt.okx),
        ('Gate.io', ccxt.gateio)
    ]
    
    pairs = ['BTCUSDT', 'ETHUSDT', 'BNBUSDT', 'SOLUSDT', 'ADAUSDT', 'AVAXUSDT', 'MATICUSDT', 'DOTUSDT']
    
    for exchange_name, exchange_class in exchanges:
        print(f'\n🔍 Checking {exchange_name}...')
        print('=' * 40)
        
        try:
            exchange = exchange_class({'enableRateLimit': True})
            markets = exchange.load_markets()
            
            available_count = 0
            for pair in pairs:
                if pair in markets:
                    print(f'✅ {pair}: Available')
                    available_count += 1
                else:
                    print(f'❌ {pair}: Not available')
            
            print(f'📊 {exchange_name}: {available_count}/{len(pairs)} pairs available')
            
        except Exception as e:
            print(f'❌ {exchange_name}: Error - {str(e)}')

if __name__ == '__main__':
    print('🔍 Checking Binance Testnet first...')
    check_binance_testnet()
    
    print('\n' + '=' * 60)
    print('🔍 Checking alternative exchanges...')
    check_alternative_exchanges()