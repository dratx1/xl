import os
import subprocess
import requests
import xml.etree.ElementTree as ET

from rich.text import Text

OWNER = "dratx1"
REPO  = "xl"
BRANCH = "main"


def ensure_git():
    root_path = os.path.dirname(os.path.abspath(__file__))
    git_folder = os.path.join(root_path, ".git")
    git_config = os.path.join(git_folder, "config")
    expected_url = "https://github.com/dratx1/xl"

    if not os.path.exists(git_folder):
        text = Text()
        text.append("❌ Script ini hanya bisa dijalankan dari hasil git clone.\n", style="bold red")
        text.append("Pastikan Anda meng-clone dari repository resmi.\n", style="yellow")
        text.append(f"  git clone {expected_url}", style="bold green")
        console.print(Panel(text, title="Validasi", border_style="red"))
        sys.exit(1)

    if not os.path.exists(git_config):
        text = Text()
        text.append("❌ Script ini tidak memiliki konfigurasi git yang valid.\n", style="bold red")
        text.append("File .git/config tidak ditemukan.", style="yellow")
        console.print(Panel(text, title="Validasi", border_style="red"))
        sys.exit(1)

    config = configparser.RawConfigParser(strict=False)
    config.read(git_config)

    if not config.sections():
        text = Text()
        text.append("❌ Gagal membaca konfigurasi git.\n", style="bold red")
        text.append("File .git/config mungkin rusak atau tidak valid.", style="yellow")
        console.print(Panel(text, title="Validasi", border_style="red"))
        sys.exit(1)

    if 'remote "origin"' not in config:
        text = Text()
        text.append("❌ Repo ini tidak memiliki remote origin.\n", style="bold red")
        text.append("Pastikan Anda meng-clone dari repository resmi.", style="yellow")
        console.print(Panel(text, title="Validasi", border_style="red"))
        sys.exit(1)

    origin_url = config['remote "origin"'].get("url", "").strip()

    if origin_url != expected_url:
        text = Text()
        text.append("⚠️ Repo ini tidak berasal dari sumber resmi.\n", style="bold yellow")
        text.append(f"URL saat ini: {origin_url}\n", style="yellow")
        text.append("Silakan clone ulang dari:\n", style="yellow")
        text.append(f"  git clone {expected_url}", style="bold green")
        console.print(Panel(text, title="Validasi", border_style="yellow"))
        sys.exit(1)

def get_local_commit():
    """Return current local commit hash, or None if not in a git repo."""
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "HEAD"],
            stderr=subprocess.DEVNULL
        ).decode().strip()
    except Exception:
        return None

def get_latest_commit_atom():
    """Return the latest commit SHA from GitHub via the Atom feed (no auth)."""
    url = f"https://github.com/{OWNER}/{REPO}/commits/{BRANCH}.atom"
    r = requests.get(url, timeout=5)
    r.raise_for_status()
    root = ET.fromstring(r.text)
    ns = {"a": "http://www.w3.org/2005/Atom"}
    entry = root.find("a:entry", ns)
    if entry is None:
        return None
    entry_id = entry.find("a:id", ns)
    if entry_id is None or not entry_id.text:
        return None
    # The SHA is the last path segment of the <id> URL
    return entry_id.text.rsplit("/", 1)[-1]

def check_for_updates():
    local = get_local_commit()
    try:
        remote = get_latest_commit_atom()
    except Exception:
        remote = None

    if not remote:
        # Could not fetch remote commit
        return False

    if not local:
        # Not a git repo
        return False

    if local != remote:
        print(f"⚠️  A newer version is available (remote {remote[:7]} vs local {local[:7]}).")
        print("   Run: git pull --rebase to update.")
        return True
    else:
        # Up to date
        return False
