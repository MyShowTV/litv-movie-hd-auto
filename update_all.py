#!/usr/bin/env python3
"""
update_hd_movie.py
------------------
定时更新直播源，生成 .m3u 文件并推送到 GitHub。
"""

import os
import subprocess
import requests
from datetime import datetime

# ====== 频道配置 ======
CHANNELS = {
    "LITV電影": "https://cdi.ofiii.com/ocean/video/playlist/ynpCU-j6j94/litv-longturn03-avc1_2936000=4-mp4a_114000=2.m3u8",
    "龍華電影": "https://cdi.ofiii.com/ocean/video/playlist/5B_0z92_TBE/litv-longturn03-avc1_2936000=4-mp4a_114000=2.m3u8"
}

# ====== 串流有效性檢查 ======
def is_valid_m3u8(url: str) -> bool:
    try:
        r = requests.head(url, timeout=5)
        return r.status_code == 200
    except Exception:
        return False

# ====== 抓取逻辑 ======
def fetch_url(channel_code: str) -> str | None:
    if channel_code.startswith("http") and is_valid_m3u8(channel_code):
        return channel_code
    return None

# ====== 更新所有频道 ======
def update_all():
    os.makedirs("m3u-files", exist_ok=True)
    valid_channels = []

    for name, code in CHANNELS.items():
        m3u_url = fetch_url(code)
        if not m3u_url:
            print(f"❌ {name} 串流失效或未抓取到链接")
            continue

        content = f"""#EXTM3U
#EXTINF:-1 group-title="自定义频道",{name}
{m3u_url}
# 更新时间：{datetime.now():%Y-%m-%d %H:%M:%S}
"""
        path = f"m3u-files/{name}.m3u"
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"✅ 已更新 {path}")
        valid_channels.append(name)

    generate_master_playlist(valid_channels)

# ====== 汇总总表 ======
def generate_master_playlist(names: list[str]):
    lines = ["#EXTM3U\n"]
    for n in names:
        m3u_url = CHANNELS[n]
        lines.append(f"#EXTINF:-1 group-title='自定义频道',{n}")
        lines.append(f"{m3u_url}\n")

    with open("m3u-files/all.m3u", "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    print("📄 已生成总表 all.m3u")

# ====== 推送到 GitHub ======
def push_to_github():
    try:
        subprocess.run(["git", "add", "."], cwd="D:/MyProjects/PythonProject1")
        subprocess.run(["git", "commit", "-m", f"更新串流清單 {datetime.now():%Y-%m-%d %H:%M:%S}"], cwd="D:/MyProjects/PythonProject1")
        subprocess.run(["git", "pull", "--rebase", "origin", "main"], cwd="D:/MyProjects/PythonProject1")
        subprocess.run(["git", "push", "origin", "main"], cwd="D:/MyProjects/PythonProject1")
        print("🚀 已推送更新到 GitHub")
    except Exception as e:
        print(f"❌ 推送失敗：{e}")

# ====== 主流程 ======
if __name__ == "__main__":
    update_all()
    push_to_github()
