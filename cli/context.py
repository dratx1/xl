import time
from datetime import datetime
from app.service.auth import AuthInstance
from app.client.engsel import get_balance, get_quota, get_profile
from app.client.engsel2 import get_tiering_info, segments
from rich.console import Console

console = Console()
_cached = None
_last_fetch = 0

def get_user_context(force=False):
    global _cached, _last_fetch
    now = time.time()
    if not force and _cached and now - _last_fetch < 60:
        return _cached

    user = AuthInstance.get_active_user()
    if not user:
        console.print("[bold red]❌ Tidak ada user aktif.[/bold red]")
        return None

    api_key = AuthInstance.api_key
    tokens = user["tokens"]
    id_token = tokens.get("id_token")
    access_token = tokens.get("access_token")

    console.print("Fetching balance...")
    try:
        balance = get_balance(api_key, id_token)
    except Exception as e:
        console.print(f"[bold red]Error getting balance: {e}[/bold red]")
        return None

    console.print("Fetching profile...")
    try:
        profile = get_profile(api_key, access_token, id_token)
        if not profile or "profile" not in profile:
            console.print("[bold red]❌ Gagal mengambil profil pengguna.[/bold red]")
            return None
    except Exception as e:
        console.print(f"[bold red]Error getting profile: {e}[/bold red]")
        return None

    quota = get_quota(api_key, id_token) or {}
    tiering = {}
    sub_type = profile["profile"].get("subscription_type", "-")
    if sub_type == "PREPAID":
        try:
            tiering = get_tiering_info(api_key, tokens)
        except Exception as e:
            console.print(f"[bold yellow]⚠️ Gagal mengambil tiering: {e}[/bold yellow]")

    try:
        seg = segments(api_key, id_token, access_token, balance.get("remaining", 0)) or {}
    except Exception as e:
        console.print(f"[bold yellow]⚠️ Gagal mengambil segments: {e}[/bold yellow]")
        seg = {}

    _cached = {
        "api_key": api_key,
        "tokens": tokens,
        "number": user["number"],
        "subscriber_id": profile["profile"].get("subscriber_id", "-"),
        "subscription_type": sub_type,
        "balance": balance.get("remaining", 0),
        "balance_expired_at": balance.get("expired_at", 0),
        "quota": quota,
        "tier": tiering.get("tier", 0),
        "points": tiering.get("current_point", 0),
        "segments": seg
    }
    _last_fetch = now
    return _cached
