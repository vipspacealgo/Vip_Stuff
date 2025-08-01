from dataclasses import dataclass

@dataclass
class sides:
    BUY = 'buy'
    SELL = 'sell'


@dataclass
class trade_types:
    LONG = 'long'
    SHORT = 'short'


@dataclass
class order_statuses:
    ACTIVE = 'ACTIVE'
    CANCELED = 'CANCELED'
    EXECUTED = 'EXECUTED'
    PARTIALLY_FILLED = 'PARTIALLY FILLED'
    QUEUED = 'QUEUED'
    LIQUIDATED = 'LIQUIDATED'
    REJECTED = 'REJECTED'


@dataclass
class timeframes:
    MINUTE_1 = '1m'
    MINUTE_3 = '3m'
    MINUTE_5 = '5m'
    MINUTE_15 = '15m'
    MINUTE_30 = '30m'
    MINUTE_45 = '45m'
    HOUR_1 = '1h'
    HOUR_2 = '2h'
    HOUR_3 = '3h'
    HOUR_4 = '4h'
    HOUR_6 = '6h'
    HOUR_8 = '8h'
    HOUR_12 = '12h'
    DAY_1 = '1D'
    DAY_3 = '3D'
    WEEK_1 = '1W'
    MONTH_1 = '1M'


@dataclass
class colors:
    GREEN = 'green'
    YELLOW = 'yellow'
    RED = 'red'
    MAGENTA = 'magenta'
    BLACK = 'black'


@dataclass
class order_types:
    MARKET = 'MARKET'
    LIMIT = 'LIMIT'
    STOP = 'STOP'
    FOK = 'FOK'
    STOP_LIMIT = 'STOP LIMIT'


@dataclass
class exchanges:
    SANDBOX = 'Sandbox'
    COINBASE_SPOT = 'Coinbase Spot'
    BITFINEX_SPOT = 'Bitfinex Spot'
    BINANCE_SPOT = 'Binance Spot'
    BINANCE_US_SPOT = 'Binance US Spot'
    BINANCE_PERPETUAL_FUTURES = 'Binance Perpetual Futures'
    BINANCE_PERPETUAL_FUTURES_TESTNET = 'Binance Perpetual Futures Testnet'
    BYBIT_USDT_PERPETUAL = 'Bybit USDT Perpetual'
    BYBIT_USDC_PERPETUAL = 'Bybit USDC Perpetual'
    BYBIT_USDT_PERPETUAL_TESTNET = 'Bybit USDT Perpetual Testnet'
    BYBIT_USDC_PERPETUAL_TESTNET = 'Bybit USDC Perpetual Testnet'
    BYBIT_SPOT = 'Bybit Spot'
    BYBIT_SPOT_TESTNET = 'Bybit Spot Testnet'
    FTX_PERPETUAL_FUTURES = 'FTX Perpetual Futures'
    FTX_SPOT = 'FTX Spot'
    FTX_US_SPOT = 'FTX US Spot'
    BITGET_SPOT = 'Bitget Spot'
    BITGET_USDT_PERPETUAL = 'Bitget USDT Perpetual'
    BITGET_USDT_PERPETUAL_TESTNET = 'Bitget USDT Perpetual Testnet'
    DYDX_PERPETUAL = "Dydx Perpetual"
    DYDX_PERPETUAL_TESTNET = "Dydx Perpetual Testnet"
    APEX_PRO_PERPETUAL_TESTNET = 'Apex Pro Perpetual Testnet'
    APEX_PRO_PERPETUAL = 'Apex Pro Perpetual'
    APEX_OMNI_PERPETUAL_TESTNET = 'Apex Omni Perpetual Testnet'
    APEX_OMNI_PERPETUAL = 'Apex Omni Perpetual'
    GATE_USDT_PERPETUAL = 'Gate USDT Perpetual'
    GATE_SPOT = 'Gate Spot'
    HYPERLIQUID_PERPETUAL = 'Hyperliquid Perpetual'
    HYPERLIQUID_PERPETUAL_TESTNET = 'Hyperliquid Perpetual Testnet'


@dataclass
class migration_actions:
    ADD = 'add'
    DROP = 'drop'
    RENAME = 'rename'
    MODIFY_TYPE = 'modify_type'
    ALLOW_NULL = 'allow_null'
    DENY_NULL = 'deny_null'
    ADD_INDEX = 'add_index'
    DROP_INDEX = 'drop_index'


@dataclass
class order_submitted_via:
    STOP_LOSS = 'stop-loss'
    TAKE_PROFIT = 'take-profit'
