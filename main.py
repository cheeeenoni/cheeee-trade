from flask import Flask, request, jsonify
import datetime
import json

app = Flask(__name__)

# Store trades in memory
trades = []

@app.route('/webhook', methods=['POST'])
def webhook():
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    trade = None

    try:
        # Try to parse JSON body
        data = request.get_json(force=True, silent=True)
        if data:
            trade = {
                "time": data.get("time", timestamp),
                "action": data.get("action", "unknown"),
                "size": data.get("size", 0.1),
                "price": data.get("price", "N/A")
            }
        else:
            # Fallback: if TradingView sent plain text, log raw message
            raw_message = request.data.decode("utf-8")
            trade = {
                "time": timestamp,
                "action": "RAW",
                "size": "N/A",
                "price": "N/A",
                "message": raw_message
            }

        trades.append(trade)
        print(f"[{timestamp}] Logged trade: {trade}")
        return jsonify({"status": "ok", "trade": trade}), 200

    except Exception as e:
        print(f"[{timestamp}] Error processing alert: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 400

@app.route('/trades', methods=['GET'])
def get_trades():
    return jsonify(trades)

@app.route('/reset', methods=['POST'])
def reset_trades():
    trades.clear()
    print("[RESET] Trades list cleared.")
    return jsonify({"status": "ok", "message": "Trades cleared"})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
