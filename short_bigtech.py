import datetime, config, pandas, sys
from alpaca_trade_api.stream import Stream
from alpaca_trade_api.rest import REST, TimeFrame, TimeFrameUnit

pandas.set_option('display.max_rows', None)

api = REST(key_id=config.API_KEY, secret_key=config.SECRET_KEY, base_url=config.BASE_URL)

if not api.get_clock().is_open:
    sys.exit("market is not open")

bars = api.get_bars(config.QQQ_SYMBOLS, TimeFrame.Day, config.START_DATE, config.TODAY).df
bars['previous_close'] = bars['close'].shift(1)
bars['ma'] = bars['previous_close'].rolling(config.MOVING_AVERAGE_DAYS).mean()
filtered = bars[bars.index.strftime('%Y-%m-%d') == config.TODAY.isoformat()].copy()
filtered['percent'] = filtered['open'] / filtered['previous_close']
downgaps = filtered[filtered['percent'] < 0.99]

# filter downgaps below moving average
downgaps_below_ma = downgaps[downgaps['open'] < downgaps['ma']]

market_order_symbols = downgaps_below_ma[downgaps_below_ma['percent'] < 0.985]['symbol'].tolist()
bracket_order_symbols = downgaps_below_ma[downgaps_below_ma['percent'] > 0.985]['symbol'].tolist()

for symbol in market_order_symbols:
    open_price = downgaps[downgaps.symbol == symbol]['open'].iloc[-1]
    quantity = config.ORDER_DOLLAR_SIZE // open_price

    print("{} shorting {} {} at {}".format(datetime.datetime.now().isoformat(), quantity, symbol, open_price))

    try:
        order = api.submit_order(symbol, quantity, 'sell', 'market')
        print("successfully submitted market order with order_id {}".format(order.id))
    except Exception as e:
        print("error executing the above order {}".format(e))

quotes = api.get_latest_quotes(bracket_order_symbols)

for symbol in bracket_order_symbols:
    quantity = config.ORDER_DOLLAR_SIZE // quotes[symbol].bp
    take_profit = round(quotes[symbol].bp * 0.99, 2)
    stop_price = round(quotes[symbol].bp * 1.01, 2)
    stop_limit_price = round(quotes[symbol].bp * 1.02, 2)

    print("{} shorting {} {} at {}".format(datetime.datetime.now().isoformat(), quantity, symbol, quotes[symbol].bp))

    try:
        order = api.submit_order(symbol, quantity, 'sell', 
                                    order_class='bracket', 
                                    take_profit={
                                        'limit_price': take_profit
                                    }, 
                                    stop_loss={
                                        'stop_price': stop_price, 
                                        'limit_price': stop_limit_price
                                    })
        print("successfully submitted bracket order with order_id {}".format(order.id))
    except Exception as e:
        print("error executing the above order {}".format(e))
