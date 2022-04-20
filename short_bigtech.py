import datetime, config
from alpaca_trade_api.stream import Stream
from alpaca_trade_api.rest import REST, TimeFrame, TimeFrameUnit

api = REST(key_id=config.API_KEY, secret_key=config.SECRET_KEY, base_url=config.BASE_URL)

bars = api.get_bars(config.QQQ_SYMBOLS, TimeFrame.Day, config.yesterday, config.today).df
bars['previous_close'] = bars['close'].shift(1)

filtered = bars[bars.index.strftime('%Y-%m-%d') == config.today.isoformat()].copy()
filtered['percent'] = filtered['open'] / filtered['previous_close']
downgaps = filtered[filtered['percent'] < 0.99]

market_order_symbols = downgaps[downgaps['percent'] < 0.985]['symbol'].tolist()
bracket_order_symbols = downgaps[downgaps['percent'] > 0.985]['symbol'].tolist()

for symbol in market_order_symbols:
    open_price = downgaps[downgaps.symbol == symbol]['open'].iloc[-1]
    quantity = config.ORDER_DOLLAR_SIZE // open_price
    order = api.submit_order(symbol, quantity, 'sell', 'market')

quotes = api.get_latest_quotes(bracket_order_symbols)

for symbol in bracket_order_symbols:
    quantity = config.ORDER_DOLLAR_SIZE // quotes[symbol].bp
    take_profit = round(quotes[symbol].bp * 0.99, 2)
    stop_price = round(quotes[symbol].bp * 1.005, 2)
    stop_limit_price = round(quotes[symbol].bp * 1.01, 2)
    order = api.submit_order(symbol, quantity, 'sell', 
                                order_class='bracket', 
                                take_profit={
                                    'limit_price': take_profit
                                }, 
                                stop_loss={
                                    'stop_price': stop_price, 
                                    'limit_price': stop_limit_price
                                })
