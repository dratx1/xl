import os
import sys
import subprocess
import requests
import configparser
import xml.etree.ElementTree as ET
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from app.config.theme_config import get_theme_style

console = Console()

OWNER = "dratx1"
REPO = "xl"
BRANCH = "main"
EXPECTED_URL = f"https://github.com/{OWNER}/{REPO}"

def get_repo_root():
    try:
        return subprocess.check_output(["git", "rev-parse", "--show-toplevel"]).decode().strip()
    except Exception:
        return os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

def ensure_git(strict=True):
    root_path = get_repo_root()
    git_config = os.path.join(root_path, ".git", "config")

    if not os.path.exists(git_config):
        show_panel(
            "❌ Script ini hanya bisa dijalankan dari hasil git clone.",
            f"Pastikan Anda meng-clone dari repository resmi:\n  git clone {EXPECTED_URL}",
            style="info"
        )
        if strict: sys.exit(1)
        return False

    config = configparser.RawConfigParser(strict=False)
    config.read(git_config)

    origin_url = config.get('remote "origin"', 'url', fallback="").strip()
    if origin_url != EXPECTED_URL:
        show_panel(
            "⚠️ Repo ini tidak berasal dari sumber resmi.",
            f"URL saat ini: {origin_url}\nSilakan clone ulang dari:\n  git clone {EXPECTED_URL}",
            style="info"
        )
        if strict: sys.exit(1)
        return False

    return True

def get_local_commit():
    try:
        return subprocess.check_output(["git", "rev-parse", "HEAD"], stderr=subprocess.DEVNULL).decode().strip()
    except Exception:
        return None

def get_latest_commit_atom():
    url = f"https://github.com/{OWNER}/{REPO}/commits/{BRANCH}.atom"
    r = requests.get(url, timeout=5)
    r.raise_for_status()
    root = ET.fromstring(r.text)
    ns = {"a": "http://www.w3.org/2005/Atom"}
    entry = root.find("a:entry", ns)
    entry_id = entry.find("a:id", ns) if entry is not None else None
    return entry_id.text.rsplit("/", 1)[-1] if entry_id is not None else None

def check_for_updates():
    local = get_local_commit()
    try:
        remote = get_latest_commit_atom()
    except Exception:
        remote = None

    if not remote or not local:
        return False

    if local != remote:
        console.print(f"[bold yellow]⚠️ Versi terbaru tersedia[/] [dim](local {local[:7]} vs remote {remote[:7]})[/]")
        console.print("[green]Jalankan:[/] [bold]git pull --rebase[/] untuk update.")
        return True

    return False

def show_panel(title, body, style="info"):
    border = get_theme_style(f"border_{style}")
    text = Text()
    for line in body.split("\n"):
        line_style = get_theme_style("text_link") if "http" in line else get_theme_style("text_body")
        text.append(line + "\n", style=line_style)
    console.print(Panel(text, title=title, border_style=border, expand=True))
