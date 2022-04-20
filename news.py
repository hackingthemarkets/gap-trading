import websocket, json, config

def on_message(ws, message):
    print(message)
    msg = json.loads(message)
    try:
        if len(msg) > 0:
            if msg[0] and 'msg' in msg[0] and msg[0]['msg'] == 'authenticated':
                ws.send(json.dumps({"action":"subscribe","news":["*"]}))
    except Exception as e:
        print(e)
        print("error with message")

def on_error(ws, error):
    print(error)

def on_close(ws, close_status_code, close_msg):
    print("### closed ###")

def on_open(ws):
    print("Opened connection")
    ws.send(json.dumps({"action":"auth","key":config.API_KEY,"secret":config.SECRET_KEY}))

    # Specific stock and/or crypto symbols #
    # {"action":"subscribe","news":["AAPL", "TSLA"]}

if __name__ == "__main__":
    websocket.enableTrace(True)
    ws = websocket.WebSocketApp("wss://stream.data.alpaca.markets/v1beta1/news",
                              on_open=on_open,
                              on_message=on_message,
                              on_error=on_error,
                              on_close=on_close)

    ws.run_forever()

