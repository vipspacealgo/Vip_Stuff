import os

# Market configuration specific to Indian markets
config = {
    # these values are related to the user's environment
    'env': {
        'caching': {
            'driver': 'pickle'
        },

        'logging': {
            'strategy_execution': True,
            'order_submission': True,
            'order_cancellation': True,
            'order_execution': True,
            'position_opened': True,
            'position_increased': True,
            'position_reduced': True,
            'position_closed': True,
            'shorter_period_candles': False,
            'trading_candles': True,
            'balance_update': True,
        },

        # Exchange configuration - NSE is the default exchange for Indian markets
        'exchanges': {
            'NSE': {
                'fee': 0.0003,  # 0.03% standard fee for NSE
                'type': 'spot',  # Indian market is primarily spot trading
                'balance': 100000,  # Default balance in INR
                'market_hours': {
                    'open': '09:15',
                    'close': '15:30',
                    'timezone': 'Asia/Kolkata',
                    'trading_days': [0, 1, 2, 3, 4],  # Monday (0) to Friday (4)
                }
            },
        },

        # Optimization mode settings
        'optimization': {
            'objective_function': 'sharpe',
            'trials': 100,
        },

        # Data settings
        'data': {
            'warmup_candles_num': 210,  # About 3.5 hours of 1-minute candles
            'persistency': True,
            'data_path': os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data'),
        },
    },

    # Application runtime variables
    'app': {
        'considering_symbols': [],
        'trading_symbols': [],
        'considering_timeframes': [],
        'trading_timeframes': [],
        'considering_exchanges': [],
        'trading_exchanges': [],
        'considering_candles': [],
        'trading_mode': '',
        'debug_mode': False,
    },
}

# Timeframe options supported
timeframes = {
    '1m': 60 * 1000,  # 1 minute in milliseconds
    '3m': 3 * 60 * 1000,
    '5m': 5 * 60 * 1000,
    '15m': 15 * 60 * 1000,
    '30m': 30 * 60 * 1000,
    '1h': 60 * 60 * 1000,
    '2h': 2 * 60 * 60 * 1000,
    '4h': 4 * 60 * 60 * 1000,
    '1D': 24 * 60 * 60 * 1000,
    '1W': 7 * 24 * 60 * 60 * 1000,
}
