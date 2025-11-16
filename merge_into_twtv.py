#!/usr/bin/env python3
"""
merge_into_twtv_append.py
-------------------------
僅將新抓取的台灣頻道附加到 TWTV.m3u 末尾，不更動原有頻道。
完整版本包含備份、下載、驗證與 Git 推送。
"""

import os
import requests
import sys
from datetime import datetime

# === 配置設定 ===
GITHUB_TWTV_RAW_URL = "https://raw.githubusercontent.com/15682116618/ML-MO-GOT-IPTV/main/TWTV.m3u"
LOCAL_TWTV_PATH = "TWTV.m3u"
SOURCE_DIR = "m3u-files"
BACKUP_DIR = "backups"


def setup_environment():
    """建立必要的目錄"""
    os.makedirs(BACKUP_DIR, exist_ok=True)
    os.makedirs(SOURCE_DIR, exist_ok=True)


def backup_twtv():
    """備份現有 TWTV.m3u"""
    if os.path.exists(LOCAL_TWTV_PATH):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = os.path.join(BACKUP_DIR, f"TWTV_backup_{timestamp}.m3u")
        with open(LOCAL_TWTV_PATH, "r", encoding="utf-8") as src, \
             open(backup_path, "w", encoding="utf-8") as dst:
            dst.write(src.read())
        print(f"📦 已備份 TWTV.m3u 至 {backup_path}")


def download_twtv():
    """下載最新 TWTV.m3u"""
    print("🌐 正在下載遠程 TWTV.m3u ...")
    try:
        r = requests.get(GITHUB_TWTV_RAW_URL, timeout=20)
        r.raise_for_status()
        with open(LOCAL_TWTV_PATH, "w", encoding="utf-8") as f:
            f.write(r.text)
        print("✅ 已下載最新 TWTV.m3u")
        return True
    except requests.exceptions.RequestException as e:
        print(f"⚠️ 無法下載最新 TWTV.m3u: {e}")
        return False


def collect_taiwan_streams():
    """收集新抓取的台灣頻道"""
    print("📁 正在收集台灣頻道資料...")
    lines = ["#EXTM3U\n"]
    count = 0
    try:
        for file in os.listdir(SOURCE_DIR):
            if file.endswith(".m3u"):
                path = os.path.join(SOURCE_DIR, file)
                with open(path, "r", encoding="utf-8") as f:
                    data = f.read().strip()
                    if "#EXTINF" in data:
                        count += data.count("#EXTINF")
                        lines.append(data)
        lines.append(f"# 台灣頻道更新時間：{datetime.now():%Y-%m-%d %H:%M:%S}\n")
        lines.append(f"# 本次新增頻道數：{count} 個\n")
        print(f"📊 收集到 {count} 個台灣頻道")
        return "\n".join(lines)
    except Exception as e:
        print(f"❌ 收集時出錯: {e}")
        return None


def append_taiwan_to_twtv():
    """將新台灣頻道附加到 TWTV.m3u"""
    print("=" * 60)
    print("🔄 開始附加台灣頻道到 TWTV.m3u")
    print("=" * 60)

    setup_environment()
    backup_twtv()
    download_twtv()

    # 讀取現有內容
    try:
        with open(LOCAL_TWTV_PATH, "r", encoding="utf-8") as f:
            original = f.read().strip()
    except Exception as e:
        print(f"❌ 無法讀取 TWTV.m3u: {e}")
        return False

    new_section = collect_taiwan_streams()
    if not new_section:
        print("⚠️ 沒有找到可附加的台灣頻道")
        return False

    new_text = original + "\n\n" + "#" + "=" * 50 + "\n"
    new_text += "# 自動新增台灣頻道\n"
    new_text += "#" + "=" * 50 + "\n"
    new_text += new_section.strip() + "\n"
    new_text += f"# 合併時間：{datetime.now():%Y-%m-%d %H:%M:%S}\n"

    try:
        with open(LOCAL_TWTV_PATH, "w", encoding="utf-8") as f:
            f.write(new_text)
        print("✅ 已成功附加新台灣頻道至 TWTV.m3u")
        return True
    except Exception as e:
        print(f"❌ 寫入 TWTV.m3u 失敗: {e}")
        return False


def git_push():
    """Git 自動提交推送"""
    print("🚀 正在執行 Git 操作...")
    os.system("git add TWTV.m3u")
    commit_msg = f'🆕 Append 台灣頻道 {datetime.now():%Y-%m-%d %H:%M:%S}'
    os.system(f'git commit -m "{commit_msg}"')
    os.system("git push origin main")
    print("✅ Git 推送完成")



def main():
    start = datetime.now()
    print(f"🕒 開始時間: {start:%Y-%m-%d %H:%M:%S}")

    if append_taiwan_to_twtv():
        git_push()

    end = datetime.now()
    print(f"🏁 結束時間: {end:%Y-%m-%d %H:%M:%S}")
    print(f"⏱️ 耗時: {(end - start).total_seconds():.2f} 秒")


if __name__ == "__main__":
    main()
