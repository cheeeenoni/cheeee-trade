from flask import Flask, request, jsonify
import datetime

app = Flask(__name__)

# Paper trading log (keeps all alerts sent from TradingView)
trades = []

@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.json  # Get JSON payload from TradingView
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Build trade using real alert data
    trade = {
        "time": data.get("time", timestamp),     # Use TradingView time if available
        "action": data.get("action", "unknown"), # BUY or SELL
        "size": data.get("size", 0.1),           # Default size if not included
        "price": data.get("price", "N/A")        # Real close price from alert
    }

    trades.append(trade)

    print(f"[{timestamp}] Executed {trade['action']} {trade['size']} @ {trade['price']}")
    return jsonify({"status": "ok", "trade": trade})

@app.route('/trades', methods=['GET'])
def get_trades():
    return jsonify(trades)

@app.route('/reset', methods=['POST'])
def reset_trades():
    global trades
    trades = []
    return jsonify({"status": "reset done", "trades": trades})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
