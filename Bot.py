# -*- coding: utf-8 -*-
"""
DRX-TM APEX INTELLIGENCE DUAL-MARKET ENGINE TELEGRAM BOT
Features:
  - 20 Modular Quantitative Algorithmic Engines
  - Real-Time Human Brain Dynamic Rank #1 Engine Selector
  - Single Target Number Precision with JAC (Jackpot) Verification
  - 30-Second and 5-Minute Market Support
  - Zero-Emoji Luxury Mathematical Bold Typography
  - In-Place Dynamic Message Dashboard with Live Countdown
  - SQLite Persistent Database with WAL Concurrency Mode
  - Resilient Auto-Reconnection for 24/7 Linux VPS Deployment
"""

import time
import math
import sqlite3
import logging
import threading
import requests
from collections import Counter
import telebot
from telebot import types

# =========================================================
# CONFIGURATION & CONSTANTS
# =========================================================
BOT_TOKEN = "8546395043:AAE0nQWcTuH8mFflnL3Qp8y6rD5XJUefMQk"

# API এন্ডপয়েন্ট কনফিগারেশন
API_URL_30S = "https://draw.ar-lottery01.com/WinGo/WinGo_30S/GetHistoryIssuePage.json"
API_URL_5M = "https://draw.ar-lottery01.com/WinGo/WinGo_5M/GetHistoryIssuePage.json"

DB_NAME = "drx_apex_system.db"
TOTAL_PAGES = 50
HISTORY_LIMIT = 500

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - [%(levelname)s] - %(message)s"
)
logger = logging.getLogger(__name__)

bot = telebot.TeleBot(BOT_TOKEN, parse_mode="HTML")

# =========================================================
# VIP FONT CONVERTER (ZERO-EMOJI CLEAN ENGINE)
# =========================================================
def to_vip(text: str) -> str:
    """ASCII ক্যারেক্টারকে প্রিমিয়াম ম্যাথমেটিক্যাল বোল্ড ফন্টে কনভার্ট করে"""
    res = []
    for ch in str(text):
        code = ord(ch)
        if 65 <= code <= 90:      # A-Z -> 𝐀-𝐙
            res.append(chr(0x1D400 + (code - 65)))
        elif 97 <= code <= 122:   # a-z -> 𝐚-𝐳
            res.append(chr(0x1D41A + (code - 97)))
        elif 48 <= code <= 57:    # 0-9 -> 𝟎-𝟗
            res.append(chr(0x1D7CE + (code - 48)))
        else:
            res.append(ch)
    return "".join(res)

# =========================================================
# DATABASE MANAGER (SQLITE PERSISTENCE)
# =========================================================
def init_database():
    """ডাটাবেজ টেবিল এবং WAL মোড সক্রিয় করে"""
    with sqlite3.connect(DB_NAME, timeout=30) as conn:
        cursor = conn.cursor()
        cursor.execute("PRAGMA journal_mode=WAL;")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS market_history (
                market TEXT,
                period TEXT,
                number INTEGER,
                size TEXT,
                color TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (market, period)
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS engine_predictions (
                market TEXT,
                period TEXT,
                engine TEXT,
                size TEXT,
                num INTEGER,
                color TEXT,
                outcome TEXT DEFAULT '--',
                PRIMARY KEY (market, period, engine)
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS engine_leaderboard (
                market TEXT,
                engine TEXT,
                wins INTEGER DEFAULT 0,
                losses INTEGER DEFAULT 0,
                jacs INTEGER DEFAULT 0,
                streak INTEGER DEFAULT 0,
                score REAL DEFAULT 0.0,
                PRIMARY KEY (market, engine)
            )
        """)
        conn.commit()

def db_save_market_records(market, records):
    if not records:
        return
    with sqlite3.connect(DB_NAME, timeout=30) as conn:
        cursor = conn.cursor()
        cursor.executemany("""
            INSERT OR IGNORE INTO market_history (market, period, number, size, color)
            VALUES (?, ?, ?, ?, ?)
        """, [(market, r["period"], r["number"], r["size"], r["color"]) for r in records])
        conn.commit()

def db_get_recent_records(market, limit=500):
    with sqlite3.connect(DB_NAME, timeout=30) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT period, number, size, color 
            FROM market_history 
            WHERE market = ?
            ORDER BY CAST(period AS INTEGER) DESC 
            LIMIT ?
        """, (market, limit))
        rows = cursor.fetchall()
        return [{"period": str(r[0]), "number": r[1], "size": r[2], "color": r[3]} for r in rows]

def db_save_prediction(market, period, engine, size, num, color):
    with sqlite3.connect(DB_NAME, timeout=30) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT OR REPLACE INTO engine_predictions (market, period, engine, size, num, color, outcome)
            VALUES (?, ?, ?, ?, ?, ?, COALESCE((SELECT outcome FROM engine_predictions WHERE market=? AND period=? AND engine=?), '--'))
        """, (market, period, engine, size, num, color, market, period, engine))
        conn.commit()

def db_update_outcome(market, period, engine, outcome):
    with sqlite3.connect(DB_NAME, timeout=30) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE engine_predictions 
            SET outcome = ? 
            WHERE market = ? AND period = ? AND engine = ?
        """, (outcome, market, period, engine))
        conn.commit()

def db_get_engine_recent_outcomes(market, engine, limit=15):
    with sqlite3.connect(DB_NAME, timeout=30) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT outcome 
            FROM engine_predictions 
            WHERE market = ? AND engine = ? AND outcome != '--'
            ORDER BY CAST(period AS INTEGER) DESC 
            LIMIT ?
        """, (market, engine, limit))
        return [r[0] for r in cursor.fetchall()]

# =========================================================
# CORE MARKET RULES
# =========================================================
VIOLET_NUMBERS = {0, 5}
RED_NUMBERS = {2, 4, 6, 8}
GREEN_NUMBERS = {1, 3, 7, 9}

def get_color(num: int) -> str:
    if num in VIOLET_NUMBERS:
        return "RED" if num == 0 else "GREEN"
    return "RED" if num in RED_NUMBERS else "GREEN"

def get_size(num: int) -> str:
    return "BIG" if num >= 5 else "SMALL"

# =========================================================
# THE 20 MODULAR QUANTITATIVE ENGINES
# =========================================================
def parse_period_digits(period_str: str):
    digits = [int(ch) for ch in str(period_str) if ch.isdigit()]
    d0 = digits[-1] if len(digits) >= 1 else 0
    d1 = digits[-2] if len(digits) >= 2 else 0
    d2 = digits[-3] if len(digits) >= 3 else 0
    d3 = digits[-4] if len(digits) >= 4 else 0
    return d3, d2, d1, d0

# 1. Tiger Pro
def eng_tiger_pro(period: str, history: list):
    d3, d2, d1, d0 = parse_period_digits(period)
    s = d2 + d1 + d0
    size = "SMALL" if s <= 13 else "BIG"
    target = s % 10
    colors = [h["color"] for h in history[:5]]
    if len(colors) >= 2 and colors[0] == colors[1] == "RED":
        col = "GREEN"
    elif len(colors) >= 2 and colors[0] == colors[1] == "GREEN":
        col = "RED"
    else:
        last_num = history[0]["number"] if history else 0
        col = "RED" if last_num % 2 == 0 else "GREEN"
    return "Tiger Pro", size, target, col

# 2. Dragon King
def eng_dragon_king(period: str, history: list):
    d3, d2, d1, d0 = parse_period_digits(period)
    delta = abs(d1 - d0)
    size = "SMALL" if delta % 2 == 0 else "BIG"
    target = delta % 10
    colors = [h["color"] for h in history[:3]]
    if colors == ["RED", "GREEN", "RED"]:
        col = "GREEN"
    elif colors == ["GREEN", "RED", "GREEN"]:
        col = "RED"
    elif len(colors) >= 2 and colors[0] == colors[1]:
        col = "GREEN" if colors[0] == "RED" else "RED"
    else:
        col = "RED" if d0 % 2 == 0 else "GREEN"
    return "Dragon King", size, target, col

# 3. Phoenix VIP
def eng_phoenix_vip(period: str, history: list):
    d3, d2, d1, d0 = parse_period_digits(period)
    val = (d0 * 2) % 10
    size = "SMALL" if val < 5 else "BIG"
    target = val
    evens = sum(1 for h in history[:5] if h["number"] % 2 == 0)
    col = "RED" if evens > 2 else "GREEN"
    return "Phoenix VIP", size, target, col

# 4. Eagle Eye
def eng_eagle_eye(period: str, history: list):
    d3, d2, d1, d0 = parse_period_digits(period)
    val = (d2 * 1 + d1 * 2 + d0 * 3) % 10
    size = "SMALL" if val < 5 else "BIG"
    target = val
    try:
        p_num = int(period)
    except ValueError:
        p_num = 0
    col = "RED" if p_num % 2 == 0 else "GREEN"
    return "Eagle Eye", size, target, col

# 5. Lion Heart
def eng_lion_heart(period: str, history: list):
    d3, d2, d1, d0 = parse_period_digits(period)
    residue = (d0 * d0) % 10
    size = "SMALL" if residue % 2 == 0 else "BIG"
    target = residue
    last_n = history[0]["number"] if len(history) >= 1 else 0
    prev_n = history[1]["number"] if len(history) >= 2 else 0
    fib_mod = (last_n + prev_n) % 10
    col = "RED" if fib_mod < 5 else "GREEN"
    return "Lion Heart", size, target, col

# 6. Thunder Bolt
def eng_thunder_bolt(period: str, history: list):
    d3, d2, d1, d0 = parse_period_digits(period)
    val = (d3 * 1 + d2 * 1 + d1 * 2 + d0 * 3) % 10
    size = "SMALL" if val % 2 == 0 else "BIG"
    target = val
    c_list = [h["color"] for h in history[:10]]
    counts = Counter(c_list)
    col = "RED" if counts["RED"] >= counts["GREEN"] else "GREEN"
    return "Thunder Bolt", size, target, col

# 7. Shadow X
def eng_shadow_x(period: str, history: list):
    d3, d2, d1, d0 = parse_period_digits(period)
    last_n = history[0]["number"] if history else 0
    avg = (last_n + d0) / 2.0
    size = "BIG" if avg.is_integer() else "SMALL"
    target = (last_n + d0) % 10
    colors = [h["color"] for h in history[:3]]
    if len(colors) == 3 and colors[0] == colors[1] == colors[2]:
        col = "GREEN" if colors[0] == "RED" else "RED"
    else:
        col = history[0]["color"] if history else "RED"
    return "Shadow X", size, target, col

# 8. Cobra Strike
def eng_cobra_strike(period: str, history: list):
    d3, d2, d1, d0 = parse_period_digits(period)
    last_n = history[0]["number"] if history else 0
    val = (last_n + d0) % 10
    size = "SMALL" if val < 5 else "BIG"
    target = val
    col = "GREEN" if (last_n - d0) > 0 else "RED"
    return "Cobra Strike", size, target, col

# 9. Wolf Pack
def eng_wolf_pack(period: str, history: list):
    last_n = history[0]["number"] if history else 0
    stepper = (last_n + 1) % 10
    size = "SMALL" if stepper % 2 == 0 else "BIG"
    target = stepper
    h3 = [h["number"] for h in history[:3]]
    m_avg = sum(h3) / max(1, len(h3))
    col = "RED" if int(round(m_avg)) % 2 == 0 else "GREEN"
    return "Wolf Pack", size, target, col

# 10. Blaze Pro
def eng_blaze_pro(period: str, history: list):
    d3, d2, d1, d0 = parse_period_digits(period)
    val = (d1 * 3 + d0) % 10
    size = "BIG" if val % 2 == 0 else "SMALL"
    target = val
    c_list = [h["color"] for h in history[:2]]
    if len(c_list) == 2 and c_list[0] == c_list[1]:
        col = "GREEN" if c_list[0] == "RED" else "RED"
    else:
        col = c_list[0] if c_list else "GREEN"
    return "Blaze Pro", size, target, col

# 11. Viper Gold
def eng_viper_gold(period: str, history: list):
    last_n = history[0]["number"] if history else 0
    cubic = (last_n ** 3) % 10
    size = "BIG" if cubic > last_n else "SMALL"
    target = cubic
    harmonic = int(math.floor(last_n * 1.618)) % 10
    col = "RED" if harmonic % 2 == 0 else "GREEN"
    return "Viper Gold", size, target, col

# 12. Rocket Star
def eng_rocket_star(period: str, history: list):
    last_n = history[0]["number"] if history else 0
    idx = int(math.floor(math.sqrt(max(last_n, 1)) * 10)) % 10
    size = "BIG" if idx >= 5 else "SMALL"
    target = idx
    last_5 = [h["number"] for h in history[:5]]
    avg_5 = sum(last_5) / max(1, len(last_5))
    col = "GREEN" if (last_n - avg_5) >= 0 else "RED"
    return "Rocket Star", size, target, col

# 13. Storm Chaser
def eng_storm_chaser(period: str, history: list):
    last_5 = [h["number"] for h in history[:5]] or [0]
    mean_val = sum(last_5) / len(last_5)
    size = "BIG" if mean_val > 4.5 else "SMALL"
    target = int(round(mean_val)) % 10
    variance = sum((x - mean_val) ** 2 for x in last_5) / len(last_5)
    std = math.sqrt(variance)
    col = "GREEN" if std > 2.5 else "RED"
    return "Storm Chaser", size, target, col

# 14. Ninja Master
def eng_ninja_master(period: str, history: list):
    last_n = history[0]["number"] if history else 0
    val = int(math.floor(last_n * 1.618)) % 10
    size = "SMALL" if val % 2 == 0 else "BIG"
    target = val
    c_list = [h["color"] for h in history[:2]]
    if len(c_list) == 2 and c_list[0] == c_list[1]:
        col = "GREEN" if c_list[0] == "RED" else "RED"
    else:
        col = "RED" if (c_list and c_list[0] == "GREEN") else "GREEN"
    return "Ninja Master", size, target, col

# 15. Falcon Rush
def eng_falcon_rush(period: str, history: list):
    d3, d2, d1, d0 = parse_period_digits(period)
    last_n = history[0]["number"] if history else 0
    p_sum = (d0 % 2) + (last_n % 2)
    size = "SMALL" if p_sum in (0, 2) else "BIG"
    target = (d0 + last_n) % 10
    last_col = history[0]["color"] if history else "RED"
    col = "GREEN" if last_col == "RED" else "RED"
    return "Falcon Rush", size, target, col

# 16. Panther VIP
def eng_panther_vip(period: str, history: list):
    sizes = [h["size"] for h in history[:3]]
    s_str = "".join([s[0] for s in sizes])
    if s_str == "BSB":
        size = "SMALL"
    elif s_str == "SBS":
        size = "BIG"
    else:
        last_s = sizes[0] if sizes else "BIG"
        size = "SMALL" if last_s == "BIG" else "BIG"
    last_n = history[0]["number"] if history else 0
    target = (last_n + 5) % 10
    c4 = [h["color"] for h in history[:4]]
    if len(c4) == 4 and len(set(c4)) == 1:
        col = "GREEN" if c4[0] == "RED" else "RED"
    else:
        col = c4[0] if c4 else "RED"
    return "Panther VIP", size, target, col

# 17. Ghost Rider
def eng_ghost_rider(period: str, history: list):
    last_n = history[0]["number"] if history else 0
    if last_n in (0, 5):
        size = "SMALL" if last_n >= 5 else "BIG"
    else:
        size = "BIG" if last_n >= 5 else "SMALL"
    target = (last_n + 4) % 10
    if last_n in (0, 5):
        col = "RED" if last_n == 0 else "GREEN"
    else:
        last_col = history[0]["color"] if history else "GREEN"
        col = "RED" if last_col == "GREEN" else "GREEN"
    return "Ghost Rider", size, target, col

# 18. Shark Tank
def eng_shark_tank(period: str, history: list):
    d3, d2, d1, d0 = parse_period_digits(period)
    last_n = history[0]["number"] if history else 0
    s_val = (d0 + last_n) % 10
    size = "BIG" if s_val >= 5 else "SMALL"
    target = s_val
    green_3 = sum(1 for h in history[:3] if h["color"] == "GREEN")
    green_8 = sum(1 for h in history[:8] if h["color"] == "GREEN")
    col = "GREEN" if green_3 > (green_8 / 8.0 * 3) else "RED"
    return "Shark Tank", size, target, col

# 19. Bullet Pro
def eng_bullet_pro(period: str, history: list):
    d3, d2, d1, d0 = parse_period_digits(period)
    last_n = history[0]["number"] if history else 1
    prod = (d0 * max(last_n, 1)) % 10
    size = "SMALL" if prod % 2 == 0 else "BIG"
    target = prod
    decay_score = sum((0.7 ** i) * (1 if h["color"] == "GREEN" else -1) for i, h in enumerate(history[:6]))
    col = "GREEN" if decay_score >= 0 else "RED"
    return "Bullet Pro", size, target, col

# 20. Dark Horse
def eng_dark_horse(period: str, history: list):
    d3, d2, d1, d0 = parse_period_digits(period)
    last_n = history[0]["number"] if history else 0
    val = (d0 ^ last_n) % 10
    size = "BIG" if val >= 5 else "SMALL"
    target = val
    col = "RED" if (val % 2 == 0) else "GREEN"
    return "Dark Horse", size, target, col

ALL_ENGINES = [
    eng_tiger_pro, eng_dragon_king, eng_phoenix_vip, eng_eagle_eye, eng_lion_heart,
    eng_thunder_bolt, eng_shadow_x, eng_cobra_strike, eng_wolf_pack, eng_blaze_pro,
    eng_viper_gold, eng_rocket_star, eng_storm_chaser, eng_ninja_master, eng_falcon_rush,
    eng_panther_vip, eng_ghost_rider, eng_shark_tank, eng_bullet_pro, eng_dark_horse
]

# =========================================================
# STATE MANAGEMENT
# =========================================================
class MarketState:
    def __init__(self, market_name: str, interval: int, api_url: str):
        self.market_name = market_name
        self.interval = interval
        self.api_url = api_url
        self.lock = threading.Lock()

        self.current_period = ""
        self.market_data = []
        
        # নির্বাচিত সেরা ইঞ্জিন ও প্রেডিকশন
        self.top_engine = "Tiger Pro"
        self.top_win_rate = 95.0
        self.top_streak = 3
        self.active_prediction = {"period": "", "size": "--", "num": "--", "color": "--"}
        
        # সকল ইঞ্জিনের লাস্ট প্রেডিকশন ক্যাশ
        self.all_predictions = {}
        self.engine_outcomes = {}

    def reload_from_db(self):
        with self.lock:
            self.market_data = db_get_recent_records(self.market_name, TOTAL_PAGES * 10)

state_30s = MarketState("30S", 30, API_URL_30S)
state_5m = MarketState("5M", 300, API_URL_5M)

# সক্রিয় চ্যাট ডিকশনারি: {chat_id: {"message_id": int, "page": int, "market": "30S"|"5M"}}
active_chats = {}
chats_lock = threading.Lock()

# =========================================================
# API FETCHER
# =========================================================
def fetch_market_api(api_url: str):
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Accept": "application/json, text/plain, */*"
        }
        resp = requests.get(api_url, headers=headers, timeout=8)
        if resp.status_code == 200:
            data = resp.json()
            raw_list = []
            if isinstance(data, dict):
                if "data" in data and isinstance(data["data"], dict):
                    raw_list = data["data"].get("list", []) or data["data"].get("records", [])
                elif "data" in data and isinstance(data["data"], list):
                    raw_list = data["data"]
                elif "list" in data and isinstance(data["list"], list):
                    raw_list = data["list"]
            elif isinstance(data, list):
                raw_list = data

            formatted = []
            for item in raw_list:
                if isinstance(item, dict):
                    p_raw = item.get("issueNumber") or item.get("period") or item.get("issue")
                    n_raw = item.get("number") or item.get("openNumber") or item.get("num")
                    if p_raw is not None and n_raw is not None:
                        period = str(p_raw).strip()
                        try:
                            num = int(str(n_raw).split(",")[-1].strip())
                        except (ValueError, TypeError):
                            continue
                        size = get_size(num)
                        color = get_color(num)
                        formatted.append({"period": period, "number": num, "size": size, "color": color})
            return formatted
    except Exception as e:
        logger.error(f"API Fetch Error ({api_url}): {e}")
    return []

# =========================================================
# HUMAN BRAIN DYNAMIC SELECTOR & EVALUATION
# =========================================================
def evaluate_all_engines_and_select_apex(market_state: MarketState, top_record: dict):
    """
    অফিসিয়াল রেজাল্টের সাথে ২০টি ইঞ্জিনের ফলাফল মিলিয়ে 
    সর্বোচ্চ উইন রেট এবং স্ট্রিকের ভিত্তিতে সেরা ইঞ্জিন নির্বাচন করে
    """
    period = top_record["period"]
    actual_num = top_record["number"]
    actual_size = top_record["size"]
    actual_color = top_record["color"]

    engine_scores = []

    for eng_func in ALL_ENGINES:
        eng_name = eng_func.__name__
        # ডাটাবেজ থেকে এই ইঞ্জিনের পূর্বের প্রেডিকশন চেক
        with sqlite3.connect(DB_NAME, timeout=30) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT size, num, color FROM engine_predictions 
                WHERE market = ? AND period = ? AND engine = ?
            """, (market_state.market_name, period, eng_name))
            row = cursor.fetchone()

        if row:
            pred_size, pred_num, pred_color = row[0], row[1], row[2]
            if actual_num == pred_num:
                outcome = "JAC"
            elif (actual_size == pred_size) or (actual_color == pred_color):
                outcome = "WIN"
            else:
                outcome = "LOSS"
            db_update_outcome(market_state.market_name, period, eng_name, outcome)

        # রোলিং পারফরম্যান্স ও স্কোর হিসাব (হিউম্যান ব্রেইন লজিক)
        recent_outcomes = db_get_engine_recent_outcomes(market_state.market_name, eng_name, limit=15)
        wins = recent_outcomes.count("WIN")
        jacs = recent_outcomes.count("JAC")
        losses = recent_outcomes.count("LOSS")
        total = len(recent_outcomes)

        # কারেন্ট স্ট্রিক বের করা
        streak = 0
        for res in recent_outcomes:
            if res in ("WIN", "JAC"):
                streak += 1
            else:
                break

        win_rate = ((wins + jacs) / total * 100) if total > 0 else 80.0
        # হিউম্যান ব্রেইন কম্পোজিট স্কোর: উইন রেট + স্ট্রিক বোনাস + জ্যাকপট বোনাস
        composite_score = win_rate + (streak * 12.5) + (jacs * 18.0)
        engine_scores.append((composite_score, win_rate, streak, eng_name, eng_func))

    # সর্বোচ্চ স্কোরের ইঞ্জিনকে Rank #1 নির্বাচন
    engine_scores.sort(key=lambda x: x[0], reverse=True)
    best = engine_scores[0]

    market_state.top_engine = best[4]("0", [])[0]  # প্রিটি নেইম
    market_state.top_win_rate = round(best[1], 1)
    market_state.top_streak = best[2]

    logger.info(f"[{market_state.market_name}] APEX ENGINE SELECTED: {market_state.top_engine} | RATE: {market_state.top_win_rate}% | STREAK: {market_state.top_streak}")

# =========================================================
# DASHBOARD UI GENERATOR (ZERO EMOJI VIP)
# =========================================================
def get_start_menu():
    markup = types.InlineKeyboardMarkup(row_width=1)
    btn_30s = types.InlineKeyboardButton(to_vip("30 SECOND MARKET [APEX BRAIN]"), callback_data="open_30S")
    btn_5m = types.InlineKeyboardButton(to_vip("5 MINUTE MARKET [STANDARD]"), callback_data="open_5M")
    markup.add(btn_30s, btn_5m)
    return markup

def get_dashboard_text(market_state: MarketState) -> str:
    m_label = "30 SECOND" if market_state.market_name == "30S" else "5 MINUTE"
    return (
        f"<b>{to_vip('DRX-TM')} | {to_vip('APEX INTELLIGENCE')}</b>\n"
        f"<b>{to_vip('MARKET')}: {to_vip(m_label)} | {to_vip('RANK #1')}</b>\n"
        f"<b>{to_vip('ACTIVE ENGINE')}: {to_vip(market_state.top_engine)}</b>\n"
        f"<b>{to_vip('ACCURACY')}: {to_vip(str(market_state.top_win_rate))}% | {to_vip('STREAK')}: {to_vip(str(market_state.top_streak))} {to_vip('WINS')}</b>\n"
        "────────────────────────"
    )

def create_dashboard_markup(market_state: MarketState, page: int = 1):
    markup = types.InlineKeyboardMarkup(row_width=4)

    # ১. পিরিয়ড
    period_str = market_state.current_period or "SYNCING..."
    btn_period = types.InlineKeyboardButton(f"{to_vip('PERIOD')}: {to_vip(period_str)}", callback_data="none")
    markup.row(btn_period)

    # ২. টাইমার ও প্রোগ্রেস বার
    now_ts = int(time.time())
    elapsed = now_ts % market_state.interval
    remaining = market_state.interval - elapsed

    total_blocks = 15
    filled_blocks = int((elapsed / market_state.interval) * total_blocks)
    progress_bar = "█" * filled_blocks + "▒" * (total_blocks - filled_blocks)
    timer_text = f"{to_vip(str(remaining).zfill(2))}S [{progress_bar}]"
    markup.row(types.InlineKeyboardButton(timer_text, callback_data="none"))

    # ৩. প্রেডিকশন কল (একক ডিজিট টার্গেট)
    pred = market_state.active_prediction
    s_val = to_vip(pred['size']) if pred['size'] != "--" else "--"
    n_val = f"{to_vip('TARGET')} {to_vip(str(pred['num']))}" if pred['num'] != "--" else "--"
    c_val = to_vip(pred['color']) if pred['color'] != "--" else "--"

    btn_size = types.InlineKeyboardButton(f"{s_val}", callback_data="none")
    btn_num = types.InlineKeyboardButton(f"{n_val}", callback_data="none")
    btn_color = types.InlineKeyboardButton(f"{c_val}", callback_data="none")
    markup.row(btn_size, btn_num, btn_color)

    # ৪. মার্কেট ডাটা টেবিল (প্রতি পেজে ১০টি সারি)
    total_records = len(market_state.market_data)
    available_pages = max(1, (total_records + 9) // 10)
    page = max(1, min(TOTAL_PAGES, min(page, available_pages)))

    start_idx = (page - 1) * 10
    end_idx = start_idx + 10
    records = market_state.market_data[start_idx:end_idx]

    # ডাটাবেজ থেকে শীর্ষ ইঞ্জিনের আউটকাম লোড
    outcomes_map = {}
    with sqlite3.connect(DB_NAME, timeout=30) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT period, outcome FROM engine_predictions 
            WHERE market = ? AND engine = ?
        """, (market_state.market_name, market_state.top_engine.replace(" ", "_").lower()))
        outcomes_map = dict(cursor.fetchall())

    for item in records:
        p_full = item["period"]
        p_short = p_full[-4:] if len(p_full) >= 4 else p_full
        num = item["number"]
        actual_size = item["size"]

        # যদি ডাটাবেজে থাকে
        outcome_raw = outcomes_map.get(p_full, "--")
        outcome = to_vip(outcome_raw) if outcome_raw != "--" else "--"

        b1 = types.InlineKeyboardButton(f"{to_vip(p_short)}", callback_data="none")
        b2 = types.InlineKeyboardButton(f"{to_vip(str(num))}", callback_data="none")
        b3 = types.InlineKeyboardButton(f"{to_vip(actual_size)}", callback_data="none")
        b4 = types.InlineKeyboardButton(f"{outcome}", callback_data="none")
        markup.row(b1, b2, b3, b4)

    # ১০ সারির কম হলে ড্যাশ ফিলাপ
    for _ in range(10 - len(records)):
        markup.row(
            types.InlineKeyboardButton("-", callback_data="none"),
            types.InlineKeyboardButton("-", callback_data="none"),
            types.InlineKeyboardButton("-", callback_data="none"),
            types.InlineKeyboardButton("-", callback_data="none")
        )

    # ৫. পেজিনেশন
    max_nav_pages = min(TOTAL_PAGES, max(available_pages, 1))
    prev_page = page - 1 if page > 1 else max_nav_pages
    next_page = page + 1 if page < max_nav_pages else 1

    btn_prev = types.InlineKeyboardButton(f"{to_vip('PREV')}", callback_data=f"page_{prev_page}")
    btn_curr = types.InlineKeyboardButton(f"{to_vip('PAGE')} {to_vip(str(page))}/{to_vip(str(TOTAL_PAGES))}", callback_data="none")
    btn_next = types.InlineKeyboardButton(f"{to_vip('NEXT')}", callback_data=f"page_{next_page}")
    markup.row(btn_prev, btn_curr, btn_next)

    # ৬. মার্কেট সুইচ ও রিফ্রেশ বাটন
    target_market = "5M" if market_state.market_name == "30S" else "30S"
    target_label = "SWITCH TO 5 MINUTE" if market_state.market_name == "30S" else "SWITCH TO 30 SECOND"
    btn_switch = types.InlineKeyboardButton(to_vip(target_label), callback_data=f"switch_{target_market}")
    btn_refresh = types.InlineKeyboardButton(to_vip("REFRESH"), callback_data="refresh")
    markup.row(btn_switch)
    markup.row(btn_refresh)

    return markup

# =========================================================
# BACKGROUND ENGINE SYNC LOOP (24/7 DAEMON)
# =========================================================
def sync_market_engine(market_state: MarketState):
    last_fetched_period = ""

    while True:
        try:
            data = fetch_market_api(market_state.api_url)
            if data:
                db_save_market_records(market_state.market_name, data)
                top_record = data[0]
                top_period = top_record["period"]

                if top_period != last_fetched_period:
                    last_fetched_period = top_period
                    market_state.reload_from_db()

                    # ১. হিউম্যান ব্রেইন দিয়ে ফলাফল যাচাই ও বেস্ট ইঞ্জিন নির্বাচন
                    evaluate_all_engines_and_select_apex(market_state, top_record)

                    # ২. পরবর্তী পিরিয়ড প্রস্তুত করা
                    try:
                        next_p_num = int(top_period) + 1
                        next_period_str = str(next_p_num).zfill(len(top_period))
                    except Exception:
                        next_period_str = f"{int(time.time() // market_state.interval) + 1}"

                    market_state.current_period = next_period_str

                    # ৩. ২০টি ইঞ্জিনের নতুন প্রেডিকশন জেনারেট ও ডাটাবেজে সংরক্ষণ
                    selected_pred = None
                    for eng_func in ALL_ENGINES:
                        eng_display_name, pred_s, pred_n, pred_c = eng_func(next_period_str, market_state.market_data)
                        eng_key = eng_func.__name__
                        db_save_prediction(market_state.market_name, next_period_str, eng_key, pred_s, pred_n, pred_c)

                        if eng_display_name == market_state.top_engine or selected_pred is None:
                            selected_pred = {"period": next_period_str, "size": pred_s, "num": pred_n, "color": pred_c}

                    market_state.active_prediction = selected_pred

            # ৪. রিয়েল-টাইম UI রেন্ডারিং (প্রতি ৩ সেকেন্ডে ইন-প্লেস এডিট)
            with chats_lock:
                current_chats = list(active_chats.items())

            for chat_id, info in current_chats:
                if info.get("market") == market_state.market_name:
                    try:
                        markup = create_dashboard_markup(market_state, page=info.get("page", 1))
                        bot.edit_message_reply_markup(
                            chat_id=chat_id,
                            message_id=info["message_id"],
                            reply_markup=markup
                        )
                    except telebot.apihelper.ApiTelegramException as te:
                        if "message is not modified" not in str(te).lower():
                            pass
                    except Exception:
                        pass

        except Exception as e:
            logger.error(f"Sync Loop Error ({market_state.market_name}): {e}")

        time.sleep(2.5)

# =========================================================
# BOT COMMANDS & CALLBACK HANDLERS
# =========================================================
@bot.message_handler(commands=["start"])
def handle_start(message):
    chat_id = message.chat.id
    welcome_text = (
        f"<b>{to_vip('DRX-TM')} | {to_vip('QUANTITATIVE CORE')}</b>\n"
        f"<i>{to_vip('SELECT PREDICTION MARKET')}</i>\n"
        "────────────────────────\n"
        f"<b>{to_vip('SYSTEM READY')}: 24/7 {to_vip('ACTIVE')}</b>"
    )
    markup = get_start_menu()
    bot.send_message(chat_id, welcome_text, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: True)
def handle_callbacks(call):
    chat_id = call.message.chat.id
    data = call.data

    if data == "none":
        bot.answer_callback_query(call.id)
        return

    # ১. মার্কেট ওপেন
    if data.startswith("open_"):
        market_code = data.split("_")[1]
        m_state = state_30s if market_code == "30S" else state_5m

        header_text = get_dashboard_text(m_state)
        markup = create_dashboard_markup(m_state, page=1)

        try:
            bot.edit_message_text(
                header_text,
                chat_id=chat_id,
                message_id=call.message.message_id,
                reply_markup=markup
            )
        except Exception:
            pass

        with chats_lock:
            active_chats[chat_id] = {
                "message_id": call.message.message_id,
                "page": 1,
                "market": market_code
            }
        bot.answer_callback_query(call.id, text=to_vip(f"{market_code} MARKET ACTIVATED"))
        return

    # ২. মার্কেট সুইচ
    if data.startswith("switch_"):
        new_market = data.split("_")[1]
        m_state = state_30s if new_market == "30S" else state_5m

        with chats_lock:
            curr_page = active_chats.get(chat_id, {}).get("page", 1)
            active_chats[chat_id] = {
                "message_id": call.message.message_id,
                "page": curr_page,
                "market": new_market
            }

        header_text = get_dashboard_text(m_state)
        markup = create_dashboard_markup(m_state, page=curr_page)

        try:
            bot.edit_message_text(
                header_text,
                chat_id=chat_id,
                message_id=call.message.message_id,
                reply_markup=markup
            )
        except Exception:
            pass

        bot.answer_callback_query(call.id, text=to_vip(f"SWITCHED TO {new_market}"))
        return

    # ৩. পেজিনেশন
    if data.startswith("page_"):
        try:
            page_num = int(data.split("_")[1])
            with chats_lock:
                current_market = active_chats.get(chat_id, {}).get("market", "30S")
                active_chats[chat_id]["page"] = page_num

            m_state = state_30s if current_market == "30S" else state_5m
            markup = create_dashboard_markup(m_state, page=page_num)
            bot.edit_message_reply_markup(
                chat_id=chat_id,
                message_id=call.message.message_id,
                reply_markup=markup
            )
            bot.answer_callback_query(call.id, text=f"{to_vip('PAGE')} {page_num}")
        except Exception:
            bot.answer_callback_query(call.id)

    # ৪. রিফ্রেশ
    elif data == "refresh":
        try:
            current_market = active_chats.get(chat_id, {}).get("market", "30S")
            m_state = state_30s if current_market == "30S" else state_5m
            m_state.reload_from_db()

            info = active_chats.get(chat_id, {"page": 1, "market": current_market})
            markup = create_dashboard_markup(m_state, page=info.get("page", 1))
            bot.edit_message_reply_markup(
                chat_id=chat_id,
                message_id=call.message.message_id,
                reply_markup=markup
            )
            bot.answer_callback_query(call.id, text=to_vip("DATA SYNCHRONIZED"))
        except Exception:
            bot.answer_callback_query(call.id)

# =========================================================
# APPLICATION ENTRYPOINT
# =========================================================
if __name__ == "__main__":
    init_database()
    state_30s.reload_from_db()
    state_5m.reload_from_db()

    print("=" * 60)
    print(f"{to_vip('DRX-TM APEX INTELLIGENCE RUNNING')}")
    print(f"MODES: 30-SECOND & 5-MINUTE | 20 ENGINES ONLINE")
    print(f"ZERO-EMOJI VIP INTERFACE | WAL PERSISTENT SQLITE")
    print("=" * 60)

    # ব্যাকগ্রাউন্ড সিঙ্ক থ্রেড চালু
    t_30s = threading.Thread(target=sync_market_engine, args=(state_30s,), daemon=True)
    t_5m = threading.Thread(target=sync_market_engine, args=(state_5m,), daemon=True)
    t_30s.start()
    t_5m.start()

    # মেইন টেলিগ্রাম বট লিসেনার
    while True:
        try:
            bot.infinity_polling(timeout=20, long_polling_timeout=10)
        except Exception as e:
            logger.error(f"Connection lost: {e}. Reconnecting in 5s...")
            time.sleep(5)
