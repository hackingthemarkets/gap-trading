import datetime, config, sys
from alpaca_trade_api.stream import Stream
from alpaca_trade_api.rest import REST, TimeFrame, TimeFrameUnit

api = REST(key_id=config.API_KEY, secret_key=config.SECRET_KEY, base_url=config.BASE_URL)

if not api.get_clock().is_open:
    sys.exit("market is not open")

bars = api.get_bars(config.IWM_SYMBOLS, TimeFrame.Day, config.START_DATE, config.TODAY).df
bars['previous_close'] = bars['close'].shift(1)
bars['ma'] = bars['previous_close'].rolling(config.MOVING_AVERAGE_DAYS).mean()

filtered = bars[bars.index.strftime('%Y-%m-%d') == config.TODAY.isoformat()].copy()
filtered['percent'] = filtered['open'] / filtered['previous_close']
downgaps = filtered[filtered['percent'] < 0.99]

downgaps_above_ma = downgaps[downgaps['open'] > downgaps['ma']]

market_order_symbols = downgaps_above_ma[downgaps_above_ma['percent'] > 0.985]['symbol'].tolist()
trailing_stop_order_symbols = downgaps_above_ma[downgaps_above_ma['percent'] < 0.985]['symbol'].tolist()

for symbol in market_order_symbols:
    open_price = downgaps[downgaps.symbol == symbol]['open'].iloc[-1]
    quantity = config.ORDER_DOLLAR_SIZE // open_price
    print("{} buying {} {} at {}".format(datetime.datetime.now().isoformat(), quantity, symbol, open_price))

    try:
        order = api.submit_order(symbol, quantity, 'buy', 'limit', limit_price=round(open_price, 2))
        print("successfully submitted limit order with order_id {}".format(order.id))
    except Exception as e:
        print("problem submitting above order - {}".format(e))

quotes = api.get_latest_quotes(trailing_stop_order_symbols)

for symbol in trailing_stop_order_symbols:
    quantity = config.ORDER_DOLLAR_SIZE // quotes[symbol].bp
    print("{} buying {} {} at {}".format(datetime.datetime.now().isoformat(), quantity, symbol, quotes[symbol].bp))

    try:
        order = api.submit_order(symbol, quantity, 'buy', 'trailing_stop', trail_percent=1.0)
        print("successfully submitted trailing stop order with order_id {}".format(order.id))
    except Exception as e:
        print("problem submitting above order - {}".format(e))