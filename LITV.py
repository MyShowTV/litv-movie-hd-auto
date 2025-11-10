from seleniumwire import webdriver
from apscheduler.schedulers.background import BackgroundScheduler
import chromedriver_autoinstaller
import requests, os, time
from datetime import datetime

CHANNELS = {
    "龍華電影": "https://www.ofiii.com/channel/watch/litv-longturn03",
    "龍華偶像": "https://www.ofiii.com/channel/watch/litv-longturn12",
    "龍華戲劇": "https://www.ofiii.com/channel/watch/litv-longturn18",
    "龍華經典": "https://www.ofiii.com/channel/watch/litv-longturn21"
}

OUTPUT_DIR = "m3u-files"
chromedriver_autoinstaller.install()
os.makedirs(OUTPUT_DIR, exist_ok=True)

def fetch_hd_stream(channel_name, url):
    options = webdriver.ChromeOptions()
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--user-agent=Mozilla/5.0 (iPhone; CPU iPhone OS 15_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148")
    options.add_argument("--window-size=375,667")

    driver = webdriver.Chrome(options=options)
    driver.get(url)
    print(f"[{channel_name}] 🐉 網頁已載入")

    try:
        driver.find_element("tag name", "button").click()
        print(f"[{channel_name}] 🖱️ 已模擬點擊播放")
    except:
        print(f"[{channel_name}] ⚠️ 未找到播放按鈕")

    time.sleep(120)

    # 攔截所有 avc1 串流
    candidates = []
    for r in driver.requests:
        if r.response and ".m3u8" in r.url and "avc1_" in r.url:
            try:
                bitrate = int(r.url.split("avc1_")[1].split("=")[0])
                candidates.append((bitrate, r.url))
                print(f"[{channel_name}] 🔍 偵測到串流：{r.url}")
            except:
                continue
    driver.quit()

    if candidates:
        candidates.sort(reverse=True)
        best_stream = candidates[0][1]
        output_file = os.path.join(OUTPUT_DIR, f"{channel_name}.m3u")
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(f"#EXTM3U\n#EXTINF:-1,{channel_name}（高清）\n{best_stream}\n")
        print(f"[{channel_name}] ✅ 已保存最高碼率串流：{best_stream}")
    else:
        print(f"[{channel_name}] ❌ 沒有偵測到任何 avc1 串流")

def update_all_channels():
    print(f"\n🕒 [{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] ⏱️ 開始逐頻道更新（即時保存）")
    for name, url in CHANNELS.items():
        fetch_hd_stream(name, url)

# 啟動排程器
scheduler = BackgroundScheduler()
scheduler.add_job(update_all_channels, 'interval', minutes=15)
scheduler.start()

# 首次執行
update_all_channels()

# 持續運行直到手動停止
try:
    while True:
        time.sleep(60)
except KeyboardInterrupt:
    print("🛑 已手動停止")
    scheduler.shutdown()
