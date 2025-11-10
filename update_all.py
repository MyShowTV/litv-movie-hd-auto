import os
import subprocess
import requests
import shutil
from datetime import datetime

# === 配置 ===
REPO_DIR = r"D:\MyProjects\PythonProject1"
OUTPUT_DIR = os.path.join(REPO_DIR, "m3u-files")
BACKUP_DIR = os.path.join(REPO_DIR, "m3u-backup", datetime.now().strftime("%Y-%m-%d"))
GIT_USER_NAME = "github-actions[bot]"
GIT_USER_EMAIL = "github-actions[bot]@users.noreply.github.com"

CHANNELS = {
    "LITV電影": "https://cdi.ofiii.com/ocean/video/playlist/ynpCU-j6j94/litv-longturn03-avc1_2936000=4-mp4a_114000=2.m3u8",
    "龍華電影": "https://cdi.ofiii.com/ocean/video/playlist/5B_0z92_TBE/litv-longturn03-avc1_2936000=4-mp4a_114000=2.m3u8"
}

def is_valid_m3u8(url: str) -> bool:
    try:
        r = requests.head(url, timeout=5)
        return r.status_code == 200
    except Exception:
        return False

def backup_m3u_files():
    os.makedirs(BACKUP_DIR, exist_ok=True)
    for file in os.listdir(OUTPUT_DIR):
        if file.endswith(".m3u"):
            shutil.copy2(os.path.join(OUTPUT_DIR, file), os.path.join(BACKUP_DIR, file))
    print(f"🗂 已備份到 {BACKUP_DIR}")

def update_all():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    valid_channels = []

    for name, url in CHANNELS.items():
        if not is_valid_m3u8(url):
            print(f"❌ {name} 串流失效或無法連線")
            continue

        content = f"""#EXTM3U
#EXTINF:-1 group-title="自定义频道",{name}
{url}
# 更新时间：{datetime.now():%Y-%m-%d %H:%M:%S}
"""
        path = os.path.join(OUTPUT_DIR, f"{name}.m3u")
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"✅ 已更新 {path}")
        valid_channels.append(name)

    generate_master_playlist(valid_channels)

def generate_master_playlist(names: list[str]):
    lines = ["#EXTM3U\n"]
    for name in names:
        lines.append(f"#EXTINF:-1 group-title='自定义频道',{name}")
        lines.append(f"{CHANNELS[name]}\n")

    with open(os.path.join(OUTPUT_DIR, "all.m3u"), "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print("📄 已生成总表 all.m3u")

def run(cmd):
    return subprocess.run(cmd, shell=True, cwd=REPO_DIR)

def git_push():
    print("🔄 檢查變更中...")
    run(f'git config --local user.name "{GIT_USER_NAME}"')
    run(f'git config --local user.email "{GIT_USER_EMAIL}"')
    run("git add m3u-files/")

    diff = subprocess.run("git diff --staged --quiet", shell=True, cwd=REPO_DIR)
    if diff.returncode == 0:
        print("✅ 沒有變更，跳過提交")
        return

    msg = f"Auto update M3U files at {datetime.now():%Y-%m-%d %H:%M:%S}"
    run(f'git commit -m "{msg}"')
    print("🚀 正在推送到 GitHub...")
    run("git stash")
    run("git pull --rebase origin main")
    run("git stash pop")
    run("git push origin main")
    print("✅ 推送完成！")

if __name__ == "__main__":
    backup_m3u_files()
    update_all()
    git_push()
