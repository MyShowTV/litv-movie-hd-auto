import subprocess
from datetime import datetime
import os

# ✅ 設定輸出資料夾
OUTPUT_DIR = "D:/MyProjects/PythonProject1/m3u-files"
CHANNEL_NAME = "台灣龍華頻道"
M3U_FILENAME = f"{CHANNEL_NAME}.m3u"

# ✅ 模擬抓取串流（你可以換成 selenium-wire 或 Playwright）
def fetch_latest_m3u8():
    # 假設這是你抓到的最新串流地址（請替換成真實抓取邏輯）
    return "https://cdi.ofiii.com/live/litv_donghwa_hd/playlist.m3u8"

# ✅ 寫入 .m3u 清單
def update_streams():
    m3u8_url = fetch_latest_m3u8()
    m3u_content = f"#EXTM3U\n#EXTINF:-1,{CHANNEL_NAME}\n{m3u8_url}\n"

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    with open(os.path.join(OUTPUT_DIR, M3U_FILENAME), "w", encoding="utf-8") as f:
        f.write(m3u_content)

    print(f"✅ 已更新 {M3U_FILENAME}")

# ✅ 推送到 GitHub
def push_to_github():
    try:
        subprocess.run(["git", "add", "."], cwd="D:/MyProjects/PythonProject1")
        subprocess.run(["git", "commit", "-m", f"更新串流清單 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"], cwd="D:/MyProjects/PythonProject1")
        subprocess.run(["git", "push", "origin", "main"], cwd="D:/MyProjects/PythonProject1")
        print("🚀 已推送更新到 GitHub")
    except Exception as e:
        print(f"❌ 推送失敗：{e}")

# ✅ 主流程
if __name__ == "__main__":
    update_streams()
    push_to_github()
