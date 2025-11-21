#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LITV_TWTV_AutoUpdate_Optimized.py
--------------------------------------------
Windows + PyCharm 版本 (優化版)
自動抓取 LITV (ofiii) 串流，智能等待，自動合併並推送 GitHub。
"""

import os
import time
import glob
import subprocess
import requests
import chromedriver_autoinstaller
from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler

# Selenium 相關模組
from seleniumwire import webdriver  # 需安裝 selenium-wire
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

# ====== 配置設定 ======
CHANNEL_GROUPS = {
    "台灣頻道": {
        "龍華電影": "https://www.ofiii.com/channel/watch/litv-longturn03",
        "龍華偶像": "https://www.ofiii.com/channel/watch/litv-longturn12",
        "龙华洋片": "https://www.ofiii.com/channel/watch/litv-longturn02",
        "龙华日韩": "https://www.ofiii.com/channel/watch/litv-longturn11",
        "龙华卡通": "https://www.ofiii.com/channel/watch/litv-longturn01",
        "龍華戲劇": "https://www.ofiii.com/channel/watch/litv-longturn18",
        "龍華經典": "https://www.ofiii.com/channel/watch/litv-longturn21"
    }
}

GITHUB_TWTV_RAW_URL = "https://raw.githubusercontent.com/15682116618/ML-MO-GOT-IPTV/main/TWTV.m3u"
LOCAL_TWTV_PATH = "TWTV.m3u"
OUTPUT_DIR = "m3u-files"
BACKUP_DIR = "backups"
GIT_BRANCH = "main"  # 請確認你的 GitHub 分支名稱

# ====== 初始化環境 ======
print("🔧 正在檢查 ChromeDriver...")
chromedriver_autoinstaller.install()
os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(BACKUP_DIR, exist_ok=True)


def click_if_exists(driver, text, timeout=3):
    """嘗試點擊按鈕，若不存在則忽略"""
    try:
        xpath = f"//*[contains(text(), '{text}')]"
        btn = WebDriverWait(driver, timeout).until(EC.element_to_be_clickable((By.XPATH, xpath)))
        btn.click()
        print(f"    🖱️ 點擊：{text}")
        time.sleep(1)
        return True
    except TimeoutException:
        return False
    except Exception as e:
        print(f"    ⚠️ 點擊 {text} 異常: {e}")
        return False


def fetch_stream(group_name, channel_name, url):
    """使用 SeleniumWire 抓取 .m3u8"""
    print(f"[{channel_name}] 🚀 啟動瀏覽器抓取中...")

    options = webdriver.ChromeOptions()
    # 隱匿模式與效能設定
    options.add_argument("--headless=new")  # 新版無頭模式
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--mute-audio")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--ignore-certificate-errors")  # 忽略 SSL 錯誤 (重要)
    options.add_argument("--allow-running-insecure-content")

    # 偽裝 User-Agent
    options.add_argument(
        "--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")

    driver = None
    try:
        # Selenium Wire 特定設定：排除圖片與不必要的請求以加速
        seleniumwire_options = {
            'exclude_hosts': ['google-analytics.com', 'facebook.com', 'doubleclick.net'],
            'disable_capture': False  # 確保開啟抓包
        }

        driver = webdriver.Chrome(options=options, seleniumwire_options=seleniumwire_options)
        driver.set_page_load_timeout(30)

        driver.get(url)

        # 自動化點擊流程
        click_if_exists(driver, "我同意", timeout=5)
        click_if_exists(driver, "確定", timeout=3)

        # 嘗試尋找並點擊播放 (處理不同的 HTML 結構)
        try:
            play_btn = WebDriverWait(driver, 10).until(
                EC.any_of(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, "button.vjs-big-play-button")),
                    EC.element_to_be_clickable((By.CSS_SELECTOR, ".play-icon")),
                    EC.element_to_be_clickable((By.XPATH, "//button[contains(@class, 'play')]"))
                )
            )
            play_btn.click()
            print(f"    ▶️ 觸發播放按鈕")
        except TimeoutException:
            print(f"    ℹ️ 無需點擊播放或自動播放中")

        # 智能等待 m3u8
        target_m3u8 = None
        start_time = time.time()
        print(f"    ⏳ 等待串流封包...")

        while time.time() - start_time < 45:  # 最多等待 45 秒
            # 檢查 requests
            for request in list(driver.requests):  # 轉 list 避免迭代時變動
                if request.response and ".m3u8" in request.url:
                    # 過濾掉廣告或非主要串流 (簡單過濾)
                    if "litv" in request.url or "hls" in request.url or "manifest" in request.url:
                        target_m3u8 = request.url
                        print(f"    ✅ 捕捉到串流！")
                        break
            if target_m3u8:
                break
            time.sleep(1)

        if target_m3u8:
            # 再多等 3 秒收集其他可能的畫質選項
            time.sleep(3)
            candidates = [
                r.url for r in driver.requests
                if r.response and ".m3u8" in r.url
            ]
            # 去重並排序 (高畫質優先邏輯：通常 URL 越長或包含特定關鍵字越精細，這裡簡單用 set 去重)
            candidates = sorted(list(set(candidates)), key=len, reverse=True)

            # 寫入檔案
            group_dir = os.path.join(OUTPUT_DIR, group_name)
            os.makedirs(group_dir, exist_ok=True)
            output_file = os.path.join(group_dir, f"{channel_name}.m3u")

            with open(output_file, "w", encoding="utf-8") as f:
                f.write("#EXTM3U\n")
                for i, u in enumerate(candidates):
                    # 簡單標記
                    tag = "主線路" if i == 0 else f"備用線路{i}"
                    f.write(
                        f"#EXTINF:-1 group-title=\"{group_name}\" tvg-name=\"{channel_name}\",{channel_name} [{tag}]\n{u}\n")
                f.write(f"# Updated: {datetime.now():%Y-%m-%d %H:%M:%S}\n")

            print(f"    💾 已儲存 {len(candidates)} 條線路 -> {channel_name}.m3u")
            return True
        else:
            print(f"    ❌ 逾時：未偵測到有效 m3u8")
            return False

    except Exception as e:
        print(f"    ❌ 發生錯誤: {e}")
        return False
    finally:
        if driver:
            driver.quit()


def git_operations():
    """執行 Git 推送流程"""
    print("\n📡 正在執行 Git 同步...")

    # 檢查是否為 Git 倉庫
    if not os.path.exists(".git"):
        print("⚠️ 當前目錄不是 Git 倉庫，跳過 Git 操作")
        return

    cmds = [
        ["git", "pull", "origin", GIT_BRANCH, "--no-rebase"],  # 先拉取避免衝突
        ["git", "add", "."],
        ["git", "commit", "-m", f"📺 Auto Update {datetime.now():%Y-%m-%d %H:%M}"],
        ["git", "push", "origin", GIT_BRANCH]
    ]

    for cmd in cmds:
        try:
            # capture_output=True 讓它不要把 git 的廢話都印出來，除非出錯
            subprocess.run(cmd, check=True, capture_output=True, text=True)
        except subprocess.CalledProcessError as e:
            # 允許 commit 失敗 (例如沒有檔案變更時)
            if "nothing to commit" in e.stderr:
                print("    ℹ️ 沒有變更需要提交")
            elif "non-fast-forward" in e.stderr:
                print("    ⚠️ Git Push 衝突，嘗試強制拉取...")
                # 簡單的衝突解決策略：再次 pull
                subprocess.run(["git", "pull", "origin", GIT_BRANCH, "--rebase"], check=False)
                subprocess.run(["git", "push", "origin", GIT_BRANCH], check=False)
            else:
                print(f"    ❌ Git 指令錯誤 [{cmd[1]}]: {e.stderr}")

    print("✅ Git 操作完成")


def merge_m3u():
    """合併邏輯"""
    print("\n📑 開始合併列表...")

    # 1. 下載最新 TWTV
    try:
        r = requests.get(GITHUB_TWTV_RAW_URL, timeout=15)
        if r.status_code != 200:
            print("    ❌ 無法下載遠端 TWTV.m3u")
            return
        original_content = r.text
    except Exception as e:
        print(f"    ❌ 下載失敗: {e}")
        return

    # 2. 備份
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    if os.path.exists(LOCAL_TWTV_PATH):
        os.rename(LOCAL_TWTV_PATH, os.path.join(BACKUP_DIR, f"TWTV_backup_{ts}.m3u"))

    # 3. 清理舊備份 (保留最近 5 個)
    backups = sorted(glob.glob(os.path.join(BACKUP_DIR, "*.m3u")), key=os.path.getmtime)
    for b in backups[:-5]:
        os.remove(b)

    # 4. 過濾掉舊的「台灣頻道」
    lines = original_content.splitlines()
    clean_lines = []
    skip = False
    for line in lines:
        # 假設我們的台灣頻道都有這個 group-title
        if 'group-title="台灣頻道"' in line:
            skip = True
            continue
        if skip and (line.startswith("http") or line.strip() == ""):
            skip = False  # 網址行結束後，下一行恢復
            continue
        if not skip:
            clean_lines.append(line)

    # 5. 讀取新抓取的頻道
    new_channels = []
    m3u_files = glob.glob(os.path.join(OUTPUT_DIR, "**", "*.m3u"), recursive=True)

    for f in m3u_files:
        with open(f, "r", encoding="utf-8") as mfile:
            c_lines = mfile.readlines()
            # 跳過 #EXTM3U 頭部，只抓內容
            for cl in c_lines:
                if cl.startswith("#EXTINF") or cl.startswith("http"):
                    new_channels.append(cl.strip())

    # 6. 組合
    final_content = "#EXTM3U\n"
    # 加入原始內容 (去掉第一行 #EXTM3U 避免重複)
    for l in clean_lines:
        if "#EXTM3U" not in l:
            final_content += l + "\n"

    final_content += f"\n\n# ========== 自動更新台灣頻道 ==========\n"
    final_content += f"# 更新時間: {datetime.now():%Y-%m-%d %H:%M:%S}\n"
    final_content += "\n".join(new_channels)

    with open(LOCAL_TWTV_PATH, "w", encoding="utf-8") as f:
        f.write(final_content)

    print(f"✅ 合併完成！新增了 {len(m3u_files)} 個頻道資訊")


def job_wrapper():
    """排程任務主入口"""
    print(f"\n⏰ 排程啟動: {datetime.now():%Y-%m-%d %H:%M:%S}")

    total_tasks = sum(len(v) for v in CHANNEL_GROUPS.values())
    current = 0

    for group, channels in CHANNEL_GROUPS.items():
        for name, url in channels.items():
            current += 1
            print(f"--- 進度 {current}/{total_tasks} ---")
            fetch_stream(group, name, url)
            time.sleep(2)  # 稍微休息避免被網站封鎖

    merge_m3u()
    git_operations()
    print(f"🏁 排程結束: {datetime.now():%Y-%m-%d %H:%M:%S}\n")
    print("⏳ 等待下次排程 (15分鐘後)...")


# ====== 主程式 ======
if __name__ == "__main__":
    print("🚀 LITV 自動更新系統 (Enhanced) 啟動")

    # 啟動時先執行一次
    job_wrapper()

    # 設定排程
    scheduler = BackgroundScheduler()
    scheduler.add_job(job_wrapper, 'interval', minutes=15)
    scheduler.start()

    try:
        while True:
            time.sleep(2)
    except KeyboardInterrupt:
        print("\n🛑 程式已停止")
        scheduler.shutdown()