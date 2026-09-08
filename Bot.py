import json
import os
import secrets
import threading
import time
from datetime import datetime, timedelta
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import parse_qs, urlparse

DB_FILE = "panels.json"
HOST = "0.0.0.0"
PORT = 8080


def load_data():
    if not os.path.exists(DB_FILE):
        return {}
    with open(DB_FILE, "r") as f:
        return json.load(f)


def save_data(data):
    with open(DB_FILE, "w") as f:
        json.dump(data, f, indent=4)


# Web Server Handler for Terminal Links
class TerminalHTTPHandler(BaseHTTPRequestHandler):

    def do_GET(self):
        parsed_path = urlparse(self.path)
        path_parts = parsed_path.path.strip("/").split("/")

        if len(path_parts) == 2 and path_parts[0] == "terminal":
            token = path_parts[1]
            panels = load_data()

            if token in panels:
                panel = panels[token]
                expiry_time = datetime.strptime(
                    panel["expiry"], "%Y-%m-%d %H:%M:%S"
                )

                if datetime.now() > expiry_time:
                    self.send_response(403)
                    self.send_header("Content-type", "text/html; charset=utf-8")
                    self.end_headers()
                    self.wfile.write(
                        "<h2>❌ এই লিংকটির মেয়াদ শেষ হয়ে গেছে! (Access Expired)</h2>".encode(
                            "utf-8"
                        )
                    )
                else:
                    self.send_response(200)
                    self.send_header("Content-type", "text/html; charset=utf-8")
                    self.end_headers()
                    html_content = f"""
                    <!DOCTYPE html>
                    <html>
                    <head>
                        <title>Web Terminal Panel</title>
                        <style>
                            body {{ background-color: #1e1e1e; color: #00ff00; font-family: monospace; padding: 20px; }}
                            .info {{ background: #2d2d2d; padding: 15px; border-radius: 5px; color: #fff; margin-bottom: 20px; }}
                        </style>
                    </head>
                    <body>
                        <div class="info">
                            <h3>✅ টার্মিনাল এক্সেস সচল রয়েছে</h3>
                            <p><b>User:</b> {panel['username']}</p>
                            <p><b>Storage Limit:</b> {panel['storage']} GB</p>
                            <p><b>Expires On:</b> {panel['expiry']}</p>
                        </div>
                        <hr>
                        <div id="terminal">
                            <p>Connecting to Web Terminal Session...</p>
                            <p><i>[এখানে আসল Shell/xterm.js ইন্টিগ্রেট করা সম্ভব]</i></p>
                        </div>
                    </body>
                    </html>
                    """
                    self.wfile.write(html_content.encode("utf-8"))
            else:
                self.send_response(404)
                self.send_header("Content-type", "text/html; charset=utf-8")
                self.end_headers()
                self.wfile.write(
                    "<h2>❌ ভুল বা অকার্যকর লিংক! (Invalid Link)</h2>".encode(
                        "utf-8"
                    )
                )
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, format, *args):
        return  # Disable console logging for requests


def start_server():
    server = HTTPServer((HOST, PORT), TerminalHTTPHandler)
    server.serve_forever()


# Main CLI Management System
def create_panel():
    print("\n--- 🆕 নতুন প্যানেল তৈরি করুন ---")
    username = input("ইউজারনেম দিন: ").strip()
    password = input("পাসওয়ার্ড দিন: ").strip()

    print("\nমেয়াদ নির্বাচন করুন:")
    print("1. ১ দিন")
    print("2. ৭ দিন (১ সপ্তাহ)")
    print("3. ৩০ দিন (১ মাস)")
    print("4. ৩৬৫ দিন (১ বছর)")
    print("5. কাস্টম দিন")

    choice = input("অপশন সিলেক্ট করুন (1-5): ").strip()
    days_map = {"1": 1, "2": 7, "3": 30, "4": 365}

    if choice in days_map:
        days = days_map[choice]
    elif choice == "5":
        days = int(input("কত দিন চালাতে চান লিখে দিন: ").strip())
    else:
        days = 1

    storage = input("স্টোরেজ লিমিট দিন (GB): ").strip()

    token = secrets.token_hex(8)
    created_at = datetime.now()
    expiry_date = created_at + timedelta(days=days)

    panel_info = {
        "username": username,
        "password": password,
        "storage": storage,
        "created_at": created_at.strftime("%Y-%m-%d %H:%M:%S"),
        "expiry": expiry_date.strftime("%Y-%m-%d %H:%M:%S"),
    }

    panels = load_data()
    panels[token] = panel_info
    save_data(panels)

    link = f"http://localhost:{PORT}/terminal/{token}"
    print("\n✅ প্যানেল সফলভাবে তৈরি হয়েছে!")
    print(f"🔗 টার্মিনাল লিংক: {link}")
    print(f"⏳ মেয়াদের শেষ তারিখ: {panel_info['expiry']}\n")


def view_old_panels():
    panels = load_data()
    if not panels:
        print("\n❌ কোনো সংরক্ষিত প্যানেল পাওয়া যায়নি।\n")
        return

    print("\n--- 📂 সংরক্ষিত প্যানেলের তালিকা ---")
    tokens = list(panels.keys())
    for idx, token in enumerate(tokens, 1):
        info = panels[token]
        expiry = datetime.strptime(info["expiry"], "%Y-%m-%d %H:%M:%S")
        status = (
            "✅ Active" if datetime.now() < expiry else "❌ Expired"
        )
        print(
            f"{idx}. User: {info['username']} | Storage: {info['storage']}GB | Expiry: {info['expiry']} [{status}]"
        )

    print("\n1. প্যানেলের মেয়াদ বাড়ান")
    print("2. প্যানেল মুছে ফেলুন (Delete)")
    print("3. মূল মেনুতে ফিরে যান")

    action = input("অপশন বেছে নিন: ").strip()

    if action in ["1", "2"]:
        selected = int(input("প্যানেল নম্বরটি নির্বাচন করুন: ")) - 1
        if 0 <= selected < len(tokens):
            target_token = tokens[selected]

            if action == "1":
                add_days = int(
                    input("কত দিন মেয়াদ বাড়াতে চান?: ").strip()
                )
                curr_expiry = datetime.strptime(
                    panels[target_token]["expiry"], "%Y-%m-%d %H:%M:%S"
                )
                new_expiry = (
                    curr_expiry
                    if curr_expiry > datetime.now()
                    else datetime.now()
                ) + timedelta(days=add_days)
                panels[target_token]["expiry"] = new_expiry.strftime(
                    "%Y-%m-%d %H:%M:%S"
                )
                save_data(panels)
                print("✅ প্যানেলের মেয়াদ আপডেট করা হয়েছে!")

            elif action == "2":
                del panels[target_token]
                save_data(panels)
                print("🗑️ প্যানেল মুছে ফেলা হয়েছে!")


def main_menu():
    threading.Thread(target=start_server, daemon=True).start()
    print(
        f"🚀 সিস্টেম ব্যাকগ্রাউন্ড সার্ভার চালু হয়েছে (Port: {PORT})...\n"
    )

    while True:
        print("=============================")
        print("    PANEL MANAGEMENT SYSTEM  ")
        print("=============================")
        print("1. New Panel Create")
        print("2. Old Data / Old Panel")
        print("3. Exit")

        choice = input("\nপছন্দমত অপশন বেছে নিন (1-3): ").strip()

        if choice == "1":
            create_panel()
        elif choice == "2":
            view_old_panels()
        elif choice == "3":
            print("প্রোগ্রামটি বন্ধ করা হচ্ছে...")
            break
        else:
            print("❌ ভুল ইনপুট, আবার চেষ্টা করুন।\n")


if __name__ == "__main__":
    main_menu()
