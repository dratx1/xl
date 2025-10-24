from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich.box import MINIMAL_DOUBLE_HEAD
from datetime import datetime
from app.config.theme_config import get_theme

console = Console()
theme = get_theme()

def show_main_menu(ctx):
    console.clear()
    expired = datetime.fromtimestamp(ctx["balance_expired_at"]).strftime("%Y-%m-%d")
    quota = ctx["quota"]
    quota_str = f"{quota.get('remaining',0)/1e9:.2f}/{quota.get('total',0)/1e9:.2f} GB" if quota.get("total") else "-"
    if quota.get("has_unlimited"): quota_str += " (Unlimited)"

    info = Text()
    info.append(f"📞 Nomor: {ctx['number']}\n", style=f"bold {theme['text_body']}")
    info.append(f"🧾 Type: {ctx['subscription_type']} ({ctx['subscriber_id']})\n", style=theme["text_body"])
    info.append(f"💰 Pulsa: Rp {ctx['balance']}\n", style=theme["text_money"])
    info.append(f"📊 Kuota: {quota_str}\n", style=theme["text_date"])
    info.append(f"🏅 Points: {ctx['points']} | Tier: {ctx['tier']}\n", style=theme["text_date"])
    info.append(f"⏳ Aktif sampai: {expired}", style=theme["text_date"])

    console.print(Panel(info, title=f"[{theme['text_title']}]✨ Informasi Akun ✨[/]", border_style=theme["border_info"], padding=(1, 2)))

    menu = Table(title=f"[{theme['text_title']}]📋 Menu Utama[/]", box=MINIMAL_DOUBLE_HEAD, show_header=False, expand=True)
    menu.add_column("Kode", justify="right", style=theme["text_key"], width=6)
    menu.add_column("Deskripsi", style=theme["text_body"])

    items = [
        ("1", "🔐 Login/Ganti akun"),
        ("2", "📦 Lihat Paket Saya"),
        ("3", "🔥 Beli Paket HOT"),
        ("4", "🔥 Beli Paket HOT-2"),
        ("5", "📮 Beli via Option Code"),
        ("6", "📁 Beli via Family Code"),
        ("7", "🔁 Loop Pembelian Family Code"),
        ("8", "💾 Simpan/Kelola Family Code"),
        ("9", "👨‍👩‍👧‍👦 Family Plan"),
        ("10", "🧬 Circle [WIP]"),
        ("11", "🏬 Store Segments"),
        ("12", "📚 Store Family List"),
        ("13", "🛍️ Store Packages"),
        ("77", f"[{theme['text_sub']}]💖 Donasi Developer[/]"),
        ("88", f"[{theme['text_sub']}]🎨 Ganti Tema CLI[/]"),
        ("N", "🔔 Notifikasi"),
        ("00", "⭐ Bookmark Paket"),
        ("99", f"[{theme['text_err']}]⛔ Tutup aplikasi[/]"),
    ]
    for code, desc in items:
        menu.add_row(code, desc)

    console.print(Panel(menu, border_style=theme["border_primary"], padding=(1, 2)))
