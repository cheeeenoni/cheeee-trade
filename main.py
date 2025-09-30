from flask import Flask, request, jsonify
import datetime, sqlite3, os
import alpaca_trade_api as tradeapi

# === CONFIG: Alpaca Paper Trading ===
API_KEY = os.getenv("APCA_API_KEY_ID", "PKQZQZE8L2H38RU3CC4P")
API_SECRET = os.getenv("APCA_API_SECRET_KEY", "fe2WyZgPc60b4HcfWCU8DVIBlBVX4qjljuua0OEO")
BASE_URL = "https://paper-api.alpaca.markets"

api = tradeapi.REST(API_KEY, API_SECRET, BASE_URL)

app = Flask(__name__)

# === SQLite DB ===
DB_FILE = "trades.db"
conn = sqlite3.connect(DB_FILE, check_same_thread=False)
c = conn.cursor()
c.execute("""CREATE TABLE IF NOT EXISTS trades (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    time TEXT, symbol TEXT, action TEXT, size REAL, price REAL, stop REAL, tp REAL
)""")
conn.commit()


# === Webhook: receives TradingView alerts ===
@app.route('/webhook', methods=['POST'])
def webhook():
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    try:
        data = request.get_json(force=True)

        symbol = data.get("symbol", "BTCUSD")
        action = data.get("action")  # "BUY" or "SELL"
        size   = float(data.get("size", 0.001))
        price  = float(data.get("price", 0.0))
        stop   = float(data.get("stop", 0.0))
        tp     = float(data.get("tp", 0.0))

        side = "buy" if action == "BUY" else "sell"

        # === MAIN ENTRY ORDER ===
        entry_order = api.submit_order(
            symbol=symbol,
            qty=size,
            side=side,
            type="market",
            time_in_force="gtc"
        )

        # === TAKE PROFIT + STOP LOSS (separate orders for crypto) ===
        tp_order, sl_order = None, None
        if side == "buy":
            if tp > 0:
                tp_order = api.submit_order(
                    symbol=symbol,
                    qty=size,
                    side="sell",
                    type="limit",
                    limit_price=str(tp),
                    time_in_force="gtc"
                )
            if stop > 0:
                sl_order = api.submit_order(
                    symbol=symbol,
                    qty=size,
                    side="sell",
                    type="stop",
                    stop_price=str(stop),
                    time_in_force="gtc"
                )
        else:  # short
            if tp > 0:
                tp_order = api.submit_order(
                    symbol=symbol,
                    qty=size,
                    side="buy",
                    type="limit",
                    limit_price=str(tp),
                    time_in_force="gtc"
                )
            if stop > 0:
                sl_order = api.submit_order(
                    symbol=symbol,
                    qty=size,
                    side="buy",
                    type="stop",
                    stop_price=str(stop),
                    time_in_force="gtc"
                )

        # === Save to DB ===
        c.execute("INSERT INTO trades (time, symbol, action, size, price, stop, tp) VALUES (?,?,?,?,?,?,?)",
                  (timestamp, symbol, action, size, price, stop, tp))
        conn.commit()

        return jsonify({
            "status": "ok",
            "symbol": symbol,
            "entry_order": str(entry_order),
            "take_profit_order": str(tp_order) if tp_order else None,
            "stop_loss_order": str(sl_order) if sl_order else None
        }), 200

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 400


# === Trades log ===
@app.route('/trades', methods=['GET'])
def get_trades():
    c.execute("SELECT * FROM trades")
    rows = c.fetchall()
    return jsonify(rows)


# === Status check (health + positions) ===
@app.route('/status', methods=['GET'])
def status():
    try:
        account = api.get_account()
        positions = api.list_positions()

        summary = {}
        for pos in positions:
            summary[pos.symbol] = {
                "side": pos.side,
                "qty": pos.qty,
                "avg_entry_price": pos.avg_entry_price,
                "market_price": pos.current_price,
                "unrealized_pl": pos.unrealized_pl,
                "unrealized_plpc": pos.unrealized_plpc
            }

        return jsonify({
            "status": "alive",
            "equity": account.equity,
            "buying_power": account.buying_power,
            "positions": summary
        }), 200

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)

