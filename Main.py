import requests
import time
import random
import threading
from flask import Flask
from datetime import datetime, timedelta, timezone

app = Flask(__name__)
is_bot_running = True
signal_history = []  # হিস্ট্রি টেবিলের জন্য

# --- settings ---
TELEGRAM_TOKEN = "8354111202:AAEqFLMoJ7W7AlwpfHibZbpusiWbnOcl5Xc"
CHAT_ID = "-1003606163349"
SIGNAL_API_URL = "https://mrbeaxt.site/Qx/Qx.php?pair={pair}&count=1&format=json"

pair_wait_until = {}

MARKETS = [
    "AUDNZD_otc", "AXP_otc", "BRLUSD_otc", "BTCUSD_otc", "EURNZD_otc",
    "EURSGD_otc", "INTC_otc", "JNJ_otc", "MCD_otc", "MSFT_otc",
    "NZDCAD_otc", "NZDCHF_otc", "NZDJPY_otc", "NZDUSD_otc", "PFE_otc",
    "USDBDT_otc", "USDCOP_otc", "USDDZD_otc", "USDEGP_otc", "USDIDR_otc",
    "USDINR_otc", "USDMXN_otc", "USDNGN_otc", "USDPKR_otc", "USDTRY_otc",
    "USDZAR_otc", "XAUUSD_otc"
]

def get_bd_time():
    return datetime.now(timezone(timedelta(hours=6)))

def send_notification(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    try: requests.get(url, params={"chat_id": CHAT_ID, "text": message, "parse_mode": "Markdown"}, timeout=10)
    except: pass

def send_msg(pair, action):
    now_bd = get_bd_time()
    signal_time = now_bd.strftime("%H:%M:%S")
    trade_time = (now_bd + timedelta(seconds=12)).replace(second=0).strftime("%H:%M:%S")
    
    # হিস্ট্রিতে ডাটা যোগ করা
    signal_history.append({"time": signal_time, "pair": pair, "action": action})
    
    emoji = "🚀" if "BUY" in action.upper() else "📉"
    full_message = (
        f"{emoji} *API CONFIRMED SIGNAL*\n"
        f"💎 Pair: `{pair}`\n"
        f"📊 Action: *{action}*\n"
        f"⏰ Time: `{signal_time}`\n"
        f"🎯 Trade: `{trade_time}`"
    )
    send_notification(full_message)

def fetch_api_signal(pair):
    try:
        url = SIGNAL_API_URL.format(pair=pair)
        response = requests.get(url, timeout=5).json()
        data = response.get('data', [{}])[0]
        
        if 'signal' in data:
            return data['signal']
        elif 'action' in data:
            return data['action']
            
        close_price = float(data.get('close', 0))
        open_price = float(data.get('open', 0))
        
        if close_price > open_price: return "BUY"
        if close_price < open_price: return "SELL"
        return None
    except:
        return None

def scan_markets():
    global pair_wait_until
    shuffled = MARKETS.copy()
    random.shuffle(shuffled)
    curr_ts = time.time()
    
    for pair in shuffled:
        if pair in pair_wait_until and curr_ts < pair_wait_until[pair]: continue
        action = fetch_api_signal(pair)
        if action and (action.upper() == "BUY" or action.upper() == "SELL"):
            send_msg(pair, action.upper())
            pair_wait_until[pair] = curr_ts + 180 
            return True
    return False

# --- Web UI (Control Panel) ---
@app.route('/')
def home():
    status_text = "RUNNING 🟢" if is_bot_running else "STOPPED 🔴"
    rows = "".join([f"<tr><td>{s['time']}</td><td>{s['pair']}</td><td>{s['action']}</td></tr>" for s in reversed(signal_history[-10:])])
    return f"""
    <html>
        <body style='text-align:center; font-family:sans-serif; background:#f4f4f9; padding:20px;'>
            <h1>DARK SIGNAL BOT</h1>
            <h2>Status: {status_text}</h2>
            <a href='/toggle'><button style='padding:15px 30px; font-size:16px;'>ON/OFF Switch</button></a>
            <h3>Signal History (Last 10)</h3>
            <table border='1' style='margin:auto; width:80%; background:white; border-collapse:collapse;'>
                <tr><th>Time</th><th>Market</th><th>Signal</th></tr>
                {rows if rows else "<tr><td colspan='3'>Waiting for signals...</td></tr>"}
            </table>
        </body>
    </html>
    """

@app.route('/toggle')
def toggle():
    global is_bot_running
    is_bot_running = not is_bot_running
    send_notification(f"{'🟢 BOT STARTED' if is_bot_running else '🔴 BOT STOPPED'}")
    return "<script>location.href='/';</script>"

def bot_loop():
    send_notification("🚀 **FULL API SIGNAL BOT ONLINE**")
    while True:
        if is_bot_running:
            now_bd = get_bd_time()
            if now_bd.second == 48:
                if scan_markets():
                    time.sleep(60)
        time.sleep(1)

if __name__ == "__main__":
    threading.Thread(target=bot_loop, daemon=True).start()
    app.run(host='0.0.0.0', port=10000)
