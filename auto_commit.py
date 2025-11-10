#!/usr/bin/env python3
"""
update_public_channels.py
-------------------------
自動抓取合法公開直播流並推送更新到 GitHub。
"""

from seleniumwire import webdriver
from apscheduler.schedulers.background import BackgroundScheduler
import chromedriver_autoinstaller
import subprocess
import requests, os, time
from datetime import datetime

# ====== 頻道列表（合法公開流） ======
CHANNELS = {
    "NASA TV": "https://www.nasa.gov/nasalive/",
    "DW News": "https://www.dw.com/en/live-tv/s-100825",
    "Al Jazeera English": "https://www.aljazeera.com/live/",
    "Bloomberg Global": "https://www.bloomberg.com/live/us"
}

OUTPUT_DIR = "m3u-files"
chromedriver_autoinstaller.install()
os.makedirs(OUTPUT_DIR, exist_ok=True)

# ====== 自動抓取串流 ======
def fetch_stream(channel_name, url):
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--no-sandbox")
    options.add_argument("--window-size=1280,720")
    options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36")

    driver = webdriver.Chrome(options=options)
    driver.get(url)
    print(f"[{channel_name}] 🌍 正在加载页面...")

    time.sleep(20)

    candidates = []
    for r in driver.requests:
        if r.response and ".m3u8" in r.url:
            candidates.append(r.url)
            print(f"[{channel_name}] 🎥 檢測到流: {r.url}")

    driver.quit()

    if candidates:
        stream_url = candidates[0]
        output_file = os.path.join(OUTPUT_DIR, f"{channel_name}.m3u")
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(f"#EXTM3U\n#EXTINF:-1,{channel_name}\n{stream_url}\n")
        print(f"[{channel_name}] ✅ 已保存直播源")
        return stream_url
    else:
        print(f"[{channel_name}] ⚠️ 未检测到直播流")
        return None

# ====== 生成總表 ======
def generate_master_playlist():
    lines = ["#EXTM3U\n"]
    for filename in os.listdir(OUTPUT_DIR):
        if filename.endswith(".m3u"):
            path = os.path.join(OUTPUT_DIR, filename)
            with open(path, "r", encoding="utf-8") as f:
                lines.append(f.read().strip())
    all_path = os.path.join(OUTPUT_DIR, "all.m3u")
    with open(all_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print("📄 已生成總表 all.m3u")

# ====== 自動提交到 GitHub ======
def push_to_github():
    try:
        subprocess.run(["git", "add", "."], check=True)
        subprocess.run(["git", "commit", "-m", f"🕒 Auto update {datetime.now():%Y-%m-%d %H:%M:%S}"], check=False)
        subprocess.run(["git", "push"], check=True)
        print("🚀 已自動推送到 GitHub")
    except Exception as e:
        print(f"⚠️ Git 推送失敗: {e}")

# ====== 全部流程 ======
def update_all_channels():
    print(f"\n🕒 [{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 開始更新...")
    for name, url in CHANNELS.items():
        fetch_stream(name, url)
    generate_master_playlist()
    push_to_github()
    print("✅ 所有頻道更新完成\n")

# ====== 啟動排程器 ======
scheduler = BackgroundScheduler()
scheduler.add_job(update_all_channels, 'interval', minutes=15)
scheduler.start()

# 首次執行
update_all_channels()

# 持續運行
try:
    while True:
        time.sleep(60)
except KeyboardInterrupt:
    scheduler.shutdown()
    print("🛑 已手動停止")
