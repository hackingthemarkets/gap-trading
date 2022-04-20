import datetime, config
from alpaca_trade_api.stream import Stream
from alpaca_trade_api.rest import REST, TimeFrame, TimeFrameUnit

api = REST(key_id=config.API_KEY, secret_key=config.SECRET_KEY, base_url=config.BASE_URL)

bars = api.get_bars(config.IWM_SYMBOLS, TimeFrame.Day, config.yesterday, config.today).df
bars['previous_close'] = bars['close'].shift(1)

filtered = bars[bars.index.strftime('%Y-%m-%d') == config.today.isoformat()].copy()
filtered['percent'] = filtered['open'] / filtered['previous_close']
downgaps = filtered[filtered['percent'] < 0.99]

market_order_symbols = downgaps[downgaps['percent'] > 0.985]['symbol'].tolist()
trailing_stop_order_symbols = downgaps[downgaps['percent'] < 0.985]['symbol'].tolist()

for symbol in market_order_symbols:
    open_price = downgaps[downgaps.symbol == symbol]['open'].iloc[-1]
    quantity = config.ORDER_DOLLAR_SIZE // open_price
    order = api.submit_order(symbol, quantity, 'buy', 'limit', limit_price=open_price)

quotes = api.get_latest_quotes(trailing_stop_order_symbols)

for symbol in trailing_stop_order_symbols:
    quantity = config.ORDER_DOLLAR_SIZE // quotes[symbol].bp
    take_profit = round(quotes[symbol].bp * 0.99, 2)
    stop_price = round(quotes[symbol].bp * 1.005, 2)
    stop_limit_price = round(quotes[symbol].bp * 1.01, 2)
    order = api.submit_order(symbol, quantity, 'buy', 'trailing_stop', trail_percent=1.0)
