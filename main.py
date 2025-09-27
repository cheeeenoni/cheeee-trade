from flask import Flask, request, jsonify
import datetime

app = Flask(__name__)

# Simulated paper trading log
trades = []

@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.json
    side = data.get("side", "unknown")
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Simulated trade
    trade = {
        "time": timestamp,
        "action": "BUY" if side == "long" else "SELL",
        "size": 0.1,
        "price": "Simulated"
    }
    trades.append(trade)
    
    print(f"[{timestamp}] Executed {trade['action']} 0.1 BTC (Simulated)")
    return jsonify({"status": "ok", "trade": trade})

@app.route('/trades', methods=['GET'])
def get_trades():
    return jsonify(trades)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
