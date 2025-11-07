from dotenv import load_dotenv
load_dotenv()

import sys
from datetime import datetime
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich.box import MINIMAL_DOUBLE_HEAD
from app.config.theme_config import get_theme
from app.menus.util import clear_screen, pause
from app.service.auth import AuthInstance
from app.service.git import check_for_updates
from app.client.engsel import get_balance, get_tiering_info
from app.client.famplan import validate_msisdn
from app.client.registration import dukcapil
from app.menus.account import show_account_menu
from app.menus.package import fetch_my_packages, get_packages_by_family, show_package_details
from app.menus.hot import show_hot_menu, show_hot_menu2
from app.menus.purchase import purchase_by_family
from app.menus.payment import show_transaction_history
from app.menus.bookmark import show_bookmark_menu
from app.menus.famplan import show_family_info
from app.menus.circle import show_circle_info
from app.menus.notification import show_notification_menu
from app.menus.theme import show_theme_menu
from app.menus.store.segments import show_store_segments_menu
from app.menus.store.search import show_family_list_menu, show_store_packages_menu
from app.menus.store.redemables import show_redeemables_menu
from app.service.sentry import enter_sentry_mode

console = Console()
theme = get_theme()

def show_main_menu(profile):
    clear_screen()
    expired_at_dt = datetime.fromtimestamp(profile["balance_expired_at"]).strftime("%Y-%m-%d")
    pulsa_str = f"Rp {profile['balance']:,}".replace(",", ".")

    info_table = Table.grid(padding=(0, 1))
    info_table.add_column(justify="left", style=theme["text_body"])
    info_table.add_column(justify="left", style=theme["text_value"])
    info_table.add_row("Nomor", f": {profile['number']}")
    info_table.add_row("Tipe", f": {profile['subscription_type']}")
    info_table.add_row("Pulsa", f": {pulsa_str}")
    info_table.add_row("Masa Aktif", f": {expired_at_dt}")
    info_table.add_row("Tiering", f": {profile['point_info']}")

    console.print(Panel(info_table, title="📱 Informasi Akun", border_style=theme["border_info"], expand=True))

    menu_table = Table(show_header=False, box=MINIMAL_DOUBLE_HEAD, expand=True)
    menu_table.add_column("Kode", justify="right", style=theme["text_key"], width=6)
    menu_table.add_column("Menu", style=theme["text_body"])

    menu_items = [
        ("1", "🔐 Login/Ganti akun"),
        ("2", "📦 Lihat Paket Saya"),
        ("3", "🔥 Beli Paket HOT"),
        ("4", "🔥 Beli Paket HOT-2"),
        ("5", "🧾 Beli Paket via Option Code"),
        ("6", "📁 Beli Paket via Family Code"),
        ("7", "🔁 Beli Semua Paket di Family Code"),
        ("8", "📜 Riwayat Transaksi"),
        ("9", "👨‍👩‍👧‍👦 Family Plan/Akrab Organizer"),
        ("10", "🌀 Circle"),
        ("11", "🏪 Store Segments"),
        ("12", "📚 Store Family List"),
        ("13", "🛍️ Store Packages"),
        ("14", "🎁 Redeemables"),
        ("R", "📝 Register"),
        ("N", "🔔 Notifikasi"),
        ("V", "✅ Validate MSISDN"),
        ("00", "⭐ Bookmark Paket"),
        ("88", f"[{theme['text_sub']}]🎨 Ganti Tema CLI [/]"),
        ("99", f"[{theme['text_err']}]⛔ Tutup Aplikasi [/]"),
    ]

    for kode, label in menu_items:
        menu_table.add_row(kode, label)

    console.print(Panel(menu_table, title="📋 Menu Utama", border_style=theme["border_primary"], expand=True))


def main():
    while True:
        active_user = AuthInstance.get_active_user()

        if active_user:
            balance = get_balance(AuthInstance.api_key, active_user["tokens"]["id_token"])
            point_info = "Points: N/A | Tier: N/A"

            if active_user["subscription_type"] == "PREPAID":
                tiering_data = get_tiering_info(AuthInstance.api_key, active_user["tokens"])
                point_info = f"Points: {tiering_data.get('current_point', 0)} | Tier: {tiering_data.get('tier', 0)}"

            profile = {
                "number": active_user["number"],
                "subscriber_id": active_user["subscriber_id"],
                "subscription_type": active_user["subscription_type"],
                "balance": balance.get("remaining"),
                "balance_expired_at": balance.get("expired_at"),
                "point_info": point_info
            }

            show_main_menu(profile)
            choice = console.input(f"[{theme['text_sub']}]Pilih menu:[/{theme['text_sub']}] ").strip()

            match choice.lower():
                case "1": selected = show_account_menu(); AuthInstance.set_active_user(selected) if selected else pause()
                case "2": fetch_my_packages()
                case "3": show_hot_menu()
                case "4": show_hot_menu2()
                case "5":
                    code = console.input("Masukkan Option Code: ").strip()
                    if code != "99": show_package_details(AuthInstance.api_key, active_user["tokens"], code, False)
                case "6":
                    code = console.input("Masukkan Family Code: ").strip()
                    if code != "99": get_packages_by_family(code)
                case "7":
                    code = console.input("Family Code: ").strip()
                    if code == "99": return
                    start = console.input("Mulai dari urutan ke- (default 1): ").strip()
                    delay = console.input("Delay antar pembelian (detik): ").strip()
                    use_decoy = console.input("Gunakan decoy? (y/n): ").strip().lower() == "y"
                    pause_each = console.input("Pause tiap sukses? (y/n): ").strip().lower() == "y"
                    purchase_by_family(code, use_decoy, pause_each, int(delay or 0), int(start or 1))
                case "8": show_transaction_history(AuthInstance.api_key, active_user["tokens"])
                case "9": show_family_info(AuthInstance.api_key, active_user["tokens"])
                case "10": show_circle_info(AuthInstance.api_key, active_user["tokens"])
                case "11": show_store_segments_menu(console.input("Enterprise? (y/n): ").strip().lower() == "y")
                case "12": show_family_list_menu(profile["subscription_type"], console.input("Enterprise? (y/n): ").strip().lower() == "y")
                case "13": show_store_packages_menu(profile["subscription_type"], console.input("Enterprise? (y/n): ").strip().lower() == "y")
                case "14": show_redeemables_menu(console.input("Enterprise? (y/n): ").strip().lower() == "y")
                case "r":
                    msisdn = console.input("MSISDN: ")
                    nik = console.input("NIK: ")
                    kk = console.input("KK: ")
                    res = dukcapil(AuthInstance.api_key, msisdn, kk, nik)
                    console.print(res)
                    pause()
                case "v":
                    msisdn = console.input("MSISDN: ")
                    res = validate_msisdn(AuthInstance.api_key, active_user["tokens"], msisdn)
                    console.print(res)
                    pause()
                case "n": show_notification_menu()
                case "00": show_bookmark_menu()
                case "88": show_theme_menu()
                case "99":
                    console.print(Panel("👋 Sampai jumpa!", border_style=theme["border_err"]))
                    sys.exit(0)
                case _: console.print(Panel("⚠️ Pilihan tidak valid.", border_style=theme["border_warning"])); pause()
        else:
            selected = show_account_menu()
            if selected: AuthInstance.set_active_user(selected)
            else: console.print("⚠️ Tidak ada akun dipilih."); pause()


if __name__ == "__main__":
    try:
        console.print("🔍 [bold]Checking for updates...[/]")
        if check_for_updates(): pause()
        main()
    except KeyboardInterrupt:
        console.print("\n👋 Aplikasi dihentikan oleh pengguna.")
    except Exception as e:
        console.print(f"\n⚠️ [bold red]Error:[/] {type(e).__name__} - {e}")
        pause()
