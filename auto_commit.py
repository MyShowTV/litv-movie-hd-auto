#!/usr/bin/env python3
"""
update_public_channels.py
-------------------------
自動抓取合法公開直播流（優先選擇高清高碼率）並推送更新到 GitHub。
支援分組，例如：台灣頻道、國際頻道。
"""

import os
import subprocess
import time
from datetime import datetime

import chromedriver_autoinstaller
from apscheduler.schedulers.background import BackgroundScheduler
from seleniumwire import webdriver

# ====== 頻道分組 ======
CHANNEL_GROUPS = {
    "台灣頻道": {
        "龍華戲劇": "https://cdi.ofiii.com/ocean/video/playlist/UW147U4HPU4/litv-longturn21-avc1_336000=1-mp4a_140000=2.m3u8",
        "龍華電影": "https://cdi.ofiii.com/ocean/video/playlist/pKsJnCUdoTU/litv-longturn03-avc1_336000=1-mp4a_114000=2.m3u8"
    },
    "國際頻道": {
        "NASA TV": "https://www.nasa.gov/nasalive/",
        "DW News": "https://www.dw.com/en/live-tv/s-100825",
        "Al Jazeera English": "https://www.aljazeera.com/live/",
        "Bloomberg Global": "https://www.bloomberg.com/live/us"
    }
}

OUTPUT_DIR = "m3u-files"
chromedriver_autoinstaller.install()
os.makedirs(OUTPUT_DIR, exist_ok=True)

# ====== 自動抓取串流 ======
def fetch_stream(group_name, channel_name, url):
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--no-sandbox")
    options.add_argument("--window-size=1280,720")
    options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (HTML, like Gecko) Chrome/121.0.0.0 Safari/537.36")

    driver = webdriver.Chrome(options=options)
    driver.get(url)
    print(f"[{group_name}/{channel_name}] 🌍 正在加载页面...")

    time.sleep(20)

    candidates = []
    for r in driver.requests:
        if r.response and ".m3u8" in r.url:
            if any(k in r.url for k in ["2000000", "2500000", "3000000", "4000000", "hd", "high"]):
                candidates.append(r.url)
                print(f"[{group_name}/{channel_name}] 🎥 檢測到高清流: {r.url}")
            else:
                print(f"[{group_name}/{channel_name}] ⚠️ 檢測到低碼率流: {r.url}")

    driver.quit()

    if candidates:
        stream_url = candidates[-1]
        group_dir = os.path.join(OUTPUT_DIR, group_name)
        os.makedirs(group_dir, exist_ok=True)
        output_file = os.path.join(group_dir, f"{channel_name}.m3u")
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(f"#EXTM3U\n#EXTINF:-1 group-title=\"{group_name}\",{channel_name}\n{stream_url}\n")
        print(f"[{group_name}/{channel_name}] ✅ 已保存高清直播源")
        return stream_url
    else:
        print(f"[{group_name}/{channel_name}] ⚠️ 未检测到高清直播流")
        return None

# ====== 生成總表 ======
def generate_master_playlist():
    lines = ["#EXTM3U\n"]
    for group_name in CHANNEL_GROUPS:
        group_dir = os.path.join(OUTPUT_DIR, group_name)
        if not os.path.exists(group_dir):
            continue
        for filename in os.listdir(group_dir):
            if filename.endswith(".m3u"):
                path = os.path.join(group_dir, filename)
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
        subprocess.run(["git", "push", "--set-upstream", "origin", "main"], check=False)
        print("🚀 已自動推送到 GitHub")
    except Exception as e:
        print(f"⚠️ Git 推送失敗: {e}")

# ====== 全部流程 ======
def update_all_channels():
    print(f"\n🕒 [{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 開始更新...")
    for group_name, channels in CHANNEL_GROUPS.items():
        for name, url in channels.items():
            fetch_stream(group_name, name, url)
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
