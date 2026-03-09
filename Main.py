import requests
import time
import random
import threading
from flask import Flask
from datetime import datetime, timedelta, timezone

app = Flask(__name__)
is_bot_running = True
signal_history = []

# --- Settings ---
TELEGRAM_TOKEN = "8354111202:AAEqFLMoJ7W7AlwpfHibZbpusiWbnOcl5Xc"
CHAT_ID = "-1003606163349"
SIGNAL_API_URL = "https://mrbeaxt.site/Qx/Qx.php?pair={pair}&count=1&format=json"

MARKETS = [
    "AUDNZD_otc", "AXP_otc", "BRLUSD_otc", "BTCUSD_otc", "EURNZD_otc", 
    "EURSGD_otc", "INTC_otc", "JNJ_otc", "MCD_otc", "MSFT_otc", 
    "NZDCAD_otc", "NZDCHF_otc", "NZDJPY_otc", "NZDUSD_otc", "PFE_otc", 
    "USDBDT_otc", "USDCOP_otc", "USDDZD_otc", "USDEGP_otc", "USDIDR_otc", 
    "USDINR_otc", "USDMXN_otc", "USDNGN_otc", "USDPKR_otc", "USDTRY_otc", 
    "USDZAR_otc", "XAUUSD_otc"
]

pair_wait_until = {}

def send_telegram_msg(message):
    try:
        requests.get(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage", 
                     params={"chat_id": CHAT_ID, "text": message, "parse_mode": "Markdown"})
    except: pass

# --- Web UI Logic ---
@app.route('/')
def home():
    status_color = "green" if is_bot_running else "red"
    status_text = "RUNNING 🟢" if is_bot_running else "STOPPED 🔴"
    
    history_rows = ""
    for s in reversed(signal_history[-10:]):
        action_color = "blue" if "BUY" in s['action'] else "orange"
        history_rows += f"<tr><td>{s['time']}</td><td><b>{s['pair']}</b></td><td style='color:{action_color}'><b>{s['action']}</b></td></tr>"

    return f"""
    <html>
        <head>
            <title>DARK SIGNAL BOT PANEL</title>
            <meta name="viewport" content="width=device-width, initial-scale=1">
            <style>
                body {{ font-family: sans-serif; text-align: center; background: #f4f4f9; padding: 20px; }}
                .card {{ background: white; padding: 20px; border-radius: 15px; box-shadow: 0 4px 8px rgba(0,0,0,0.1); max-width: 500px; margin: auto; }}
                button {{ padding: 15px 30px; font-size: 18px; cursor: pointer; border-radius: 10px; border: none; background: #007bff; color: white; }}
                table {{ width: 100%; margin-top: 20px; border-collapse: collapse; background: white; }}
                th, td {{ padding: 12px; border: 1px solid #ddd; text-align: center; }}
                th {{ background: #eee; }}
            </style>
        </head>
        <body>
            <div class="card">
                <h1>DARK SIGNAL BOT</h1>
                <h2 style="color:{status_color}">Status: {status_text}</h2>
                <a href="/toggle"><button>ON/OFF Switch</button></a>
            </div>
            <h3>Recent Signal History</h3>
            <table>
                <tr><th>Time (BD)</th><th>Market</th><th>Signal</th></tr>
                {history_rows if history_rows else "<tr><td colspan='3'>No signals yet</td></tr>"}
            </table>
        </body>
    </html>
    """

@app.route('/toggle')
def toggle():
    global is_bot_running
    is_bot_running = not is_bot_running
    # বাটন টিপে অন করলে মেসেজ যাবে
    if is_bot_running:
        send_telegram_msg("🟢 *BOT STARTED*")
    else:
        send_telegram_msg("🔴 *BOT STOPPED*")
    return "<script>window.location.href='/';</script>"

# --- Bot Core Logic ---
def get_bd_time():
    return datetime.now(timezone(timedelta(hours=6)))

def bot_loop():
    global signal_history
    # প্রথমবার রান হওয়ার সময় মেসেজ পাঠানো
    send_telegram_msg("🚀 *BOT SYSTEM ONLINE*")
    
    while True:
        if is_bot_running:
            now_bd = get_bd_time()
            if now_bd.second == 48:
                shuffled = MARKETS.copy()
                random.shuffle(shuffled)
                curr_ts = time.time()
                
                for pair in shuffled:
                    if pair in pair_wait_until and curr_ts < pair_wait_until[pair]: continue
                    try:
                        res = requests.get(SIGNAL_API_URL.format(pair=pair), timeout=5).json()
                        data = res.get('data', [{}])[0]
                        action = data.get('signal') or data.get('action')
                        
                        if action:
                            action = action.upper()
                            time_now = now_bd.strftime('%H:%M:%S')
                            signal_history.append({"time": time_now, "pair": pair, "action": action})
                            
                            trade_t = (now_bd + timedelta(seconds=12)).replace(second=0).strftime("%H:%M:%S")
                            emoji = "🚀" if "BUY" in action else "📉"
                            msg = f"{emoji} *API SIGNAL*\n💎 Pair: `{pair}`\n📊 Action: *{action}*\n⏰ Time: `{time_now}`\n🎯 Trade: `{trade_t}`"
                            send_telegram_msg(msg)
                            
                            pair_wait_until[pair] = curr_ts + 180
                            break 
                    except: continue
                time.sleep(60)
        time.sleep(1)

if __name__ == "__main__":
    threading.Thread(target=bot_loop, daemon=True).start()
    app.run(host='0.0.0.0', port=10000)
