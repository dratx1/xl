from dotenv import load_dotenv
load_dotenv()

import sys, json
from datetime import datetime
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.prompt import Prompt
from rich.text import Text
from rich.align import Align
from rich.box import HEAVY

from app.menus.util import clear_screen, pause
from app.client.engsel import get_balance, get_profile, get_package
from app.client.engsel2 import get_tiering_info
from app.menus.payment import show_transaction_history
from app.service.auth import AuthInstance
from app.menus.bookmark import show_bookmark_menu
from app.menus.account import show_account_menu
from app.menus.package import fetch_my_packages, get_packages_by_family, show_package_details
from app.menus.hot import show_hot_menu, show_hot_menu2
from app.service.sentry import enter_sentry_mode
from app.menus.purchase import purchase_by_family
from app.menus.famplan import show_family_info
from app.menus.circle import show_circle_info
from app.menus.notification import show_notification_menu
from app.menus.store.segments import show_store_segments_menu
from app.menus.store.search import show_family_list_menu, show_store_packages_menu

console = Console()
WIDTH = 60

def show_main_menu(profile):
    clear_screen()
    expired_at_dt = datetime.fromtimestamp(profile["balance_expired_at"]).strftime("%Y-%m-%d")
    
    info = Text()
    info.append(f"📞 Nomor: {profile['number']}\n", style="bold cyan")
    info.append(f"🧾 Type: {profile['subscription_type']} ({profile['subscriber_id']})\n", style="cyan")
    info.append(f"💰 Pulsa: Rp {profile['balance']}\n", style="green")
    info.append(f"🏅 {profile['point_info']}\n", style="magenta")
    info.append(f"⏳ Aktif sampai: {expired_at_dt}", style="yellow")

    console.print(Panel(info, title="✨ Informasi Akun ✨", border_style="bright_blue", padding=(1, 2)))

    menu = Table(title="📋 Menu Utama", box=HEAVY, show_header=False, expand=True)
    menu.add_column("Kode", justify="right", style="bold magenta", width=6)
    menu.add_column("Deskripsi", style="white")

    items = [
        ("1", "🔐 Login/Ganti akun"),
        ("2", "📦 Lihat Paket Saya"),
        ("3", "🔥 Beli Paket HOT"),
        ("4", "🔥 Beli Paket HOT-2"),
        ("5", "📮 Beli Paket via Option Code"),
        ("6", "📁 Beli Paket via Family Code"),
        ("7", "🔁 Beli Semua Paket di Family Code"),
        ("8", "📜 Riwayat Transaksi"),
        ("9", "👨‍👩‍👧‍👦 Family Plan / Akrab Organizer"),
        ("10", "🧬 Circle [WIP]"),
        ("11", "🏬 Store Segments"),
        ("12", "📚 Store Family List"),
        ("13", "🛍️ Store Packages"),
        ("N", "🔔 Notifikasi"),
        ("00", "⭐ Bookmark Paket"),
        ("99", "⛔ Tutup aplikasi"),
    ]

    for code, desc in items:
        menu.add_row(code, desc)

    console.print(Panel(menu, title="✨ Pilih Menu ✨", border_style="bright_magenta", padding=(1, 2)))

def main():
    while True:
        active_user = AuthInstance.get_active_user()

        if active_user is not None:
            balance = get_balance(AuthInstance.api_key, active_user["tokens"]["id_token"])
            profile_data = get_profile(AuthInstance.api_key, active_user["tokens"]["access_token"], active_user["tokens"]["id_token"])
            sub_type = profile_data["profile"]["subscription_type"]

            point_info = "Points: N/A | Tier: N/A"
            if sub_type == "PREPAID":
                tiering_data = get_tiering_info(AuthInstance.api_key, active_user["tokens"])
                tier = tiering_data.get("tier", 0)
                current_point = tiering_data.get("current_point", 0)
                point_info = f"Points: {current_point} | Tier: {tier}"

            profile = {
                "number": active_user["number"],
                "subscriber_id": profile_data["profile"]["subscriber_id"],
                "subscription_type": sub_type,
                "balance": balance.get("remaining"),
                "balance_expired_at": balance.get("expired_at"),
                "point_info": point_info
            }

            show_main_menu(profile)
            choice = Prompt.ask("🎯 Pilih menu").strip().lower()

            if choice == "1":
                selected_user_number = show_account_menu()
                if selected_user_number:
                    AuthInstance.set_active_user(selected_user_number)
                else:
                    console.print("[red]❌ Gagal memilih user.[/red]")
                continue
            elif choice == "2":
                fetch_my_packages()
            elif choice == "3":
                show_hot_menu()
            elif choice == "4":
                show_hot_menu2()
            elif choice == "5":
                option_code = Prompt.ask("📮 Masukkan option code (atau '99' untuk batal)")
                if option_code != "99":
                    show_package_details(AuthInstance.api_key, active_user["tokens"], option_code, False)
            elif choice == "6":
                family_code = Prompt.ask("📁 Masukkan family code (atau '99' untuk batal)")
                if family_code != "99":
                    get_packages_by_family(family_code)
            elif choice == "7":
                family_code = Prompt.ask("🔁 Masukkan family code (atau '99' untuk batal)")
                if family_code == "99":
                    continue
                start_from_option = int(Prompt.ask("Mulai dari option ke", default="1"))
                use_decoy = Prompt.ask("Gunakan decoy package? (y/n)", default="n").lower() == 'y'
                pause_on_success = Prompt.ask("Pause tiap sukses? (y/n)", default="n").lower() == 'y'
                delay_seconds = int(Prompt.ask("Delay antar pembelian (detik)", default="0"))
                purchase_by_family(family_code, use_decoy, pause_on_success, delay_seconds, start_from_option)
            elif choice == "8":
                show_transaction_history(AuthInstance.api_key, active_user["tokens"])
            elif choice == "9":
                show_family_info(AuthInstance.api_key, active_user["tokens"])
            elif choice == "10":
                show_circle_info(AuthInstance.api_key, active_user["tokens"])
            elif choice == "11":
                is_enterprise = Prompt.ask("Enterprise store? (y/n)", default="n").lower() == 'y'
                show_store_segments_menu(is_enterprise)
            elif choice == "12":
                is_enterprise = Prompt.ask("Enterprise? (y/n)", default="n").lower() == 'y'
                show_family_list_menu(profile['subscription_type'], is_enterprise)
            elif choice == "13":
                is_enterprise = Prompt.ask("Enterprise? (y/n)", default="n").lower() == 'y'
                show_store_packages_menu(profile['subscription_type'], is_enterprise)
            elif choice == "00":
                show_bookmark_menu()
            elif choice == "99":
                console.print("[bold red]⛔ Keluar dari aplikasi.[/bold red]")
                sys.exit(0)
            elif choice == "t":
                res = get_package(AuthInstance.api_key, active_user["tokens"], "")
                console.print(json.dumps(res, indent=2))
                input("Tekan Enter untuk lanjut...")
            elif choice == "n":
                show_notification_menu()
            elif choice == "s":
                enter_sentry_mode()
            else:
                console.print("[red]❌ Pilihan tidak valid.[/red]")
                pause()
        else:
            selected_user_number = show_account_menu()
            if selected_user_number:
                AuthInstance.set_active_user(selected_user_number)
            else:
                console.print("[red]❌ Gagal memilih user.[/red]")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        console.print("\n[bold red]⛔ Keluar dari aplikasi.[/bold red]")
