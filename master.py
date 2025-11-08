from dotenv import load_dotenv
load_dotenv()

import sys
from datetime import datetime
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.box import MINIMAL_DOUBLE_HEAD
from app.config.theme_config import get_theme_style
from app.menus.util import (
    clear_screen, pause, print_panel, print_error, print_warning, get_rupiah
)
from app.service.auth import AuthInstance
from app.service.git import ensure_git
from app.client.engsel import get_balance, get_tiering_info
from app.client.famplan import validate_msisdn
from app.client.registration import dukcapil
from app.menus.account import show_account_menu
from app.menus.package import show_package_details
from app.menus.package2 import get_packages_by_family, fetch_my_packages
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
from app.menus.info import show_info_menu
from app.menus.family_grup import show_family_grup_menu

console = Console()

def show_main_menu(profile):
    clear_screen()
    expired_at_dt = datetime.fromtimestamp(profile.get("balance_expired_at", 0)).strftime("%Y-%m-%d")
    pulsa_str = get_rupiah(profile.get("balance", 0))

    info_table = Table.grid(padding=(0, 1))
    info_table.add_column(justify="left", style=get_theme_style("text_body"))
    info_table.add_column(justify="left", style=get_theme_style("text_value"))
    info_table.add_row("Nomor", f": {profile.get('number', '-')}")
    info_table.add_row("Tipe", f": {profile.get('subscription_type', '-')}")
    info_table.add_row("Pulsa", f": Rp {pulsa_str}")
    info_table.add_row("Masa Aktif", f": {expired_at_dt}")
    info_table.add_row("Tiering", f": {profile.get('point_info', '-')}")

    console.print(Panel(
        info_table,
        title=f"[{get_theme_style('text_title')}]📱 Informasi Akun[/]",
        border_style=get_theme_style("border_info"),
        expand=True
    ))

    menu_table = Table(show_header=False, box=MINIMAL_DOUBLE_HEAD, expand=True)
    menu_table.add_column("Kode", justify="right", style=get_theme_style("text_key"), width=6)
    menu_table.add_column("Menu", style=get_theme_style("text_body"))

    menu_items = [
        ("1", "🔐 Login/Ganti akun"),
        ("2", "📊 Lihat Paket Saya"),
        ("3", "🔥 Beli Paket Hot Promo"),
        ("4", "🔥 Beli Paket Hot Promo-2"),
        ("5", "💵 Beli Paket via Option Code"),
        ("6", "💶 Beli Paket via Family Code"),
        ("7", "🔁 Beli Semua Paket di Family Code"),
        ("8", "📜 Riwayat Transaksi"),
        ("9", "☕ Family Plan/Akrab Organizer"),
        ("10", "🌀 Circle"),
        ("11", "🏪 Store Segments"),
        ("12", "📚 Store Family List"),
        ("13", "👜 Store Packages"),
        ("14", "🎁 Redeemables"),
        ("R", "📝 Register"),
        ("N", "🔔 Notifikasi"),
        ("V", "✅ Validate MSISDN"),
        ("00", "⭐ Bookmark Paket"),
        ("66", "💾 Simpan/Kelola Family Code"),
        ("77", f"[{get_theme_style('border_warning')}]📢 Info Unlock Code [/]") ,
        ("88", f"[{get_theme_style('text_sub')}]🎨 Ganti Tema CLI [/]"),
        ("99", f"[{get_theme_style('text_err')}]⛔ Tutup Aplikasi [/]"),
    ]

    for kode, label in menu_items:
        menu_table.add_row(kode, label)

    console.print(Panel(
        menu_table,
        title=f"[{get_theme_style('text_title')}]✨ Menu Utama ✨[/]",
        border_style=get_theme_style("border_primary"),
        expand=True
    ))

def main():
    ensure_git()

    while True:
        active_user = AuthInstance.get_active_user()
        if not active_user:
            selected = show_account_menu()
            if selected:
                AuthInstance.set_active_user(selected)
            else:
                print_error("⚠️ Tidak ada akun dipilih", "Silakan login terlebih dahulu.")
                pause()
            continue

        try:
            balance = get_balance(AuthInstance.api_key, active_user["tokens"]["id_token"]) or {}
        except Exception as e:
            print_error("⚠️ Gagal mengambil saldo", str(e))
            balance = {}

        point_info = "Points: N/A | Tier: N/A"
        if active_user.get("subscription_type") == "PREPAID":
            try:
                tiering_data = get_tiering_info(AuthInstance.api_key, active_user["tokens"]) or {}
                point_info = f"Points: {tiering_data.get('current_point', 0)} | Tier: {tiering_data.get('tier', 0)}"
            except Exception as e:
                print_warning("⚠️ Gagal mengambil tiering", str(e))

        profile = {
            "number": active_user.get("number", "-"),
            "subscriber_id": active_user.get("subscriber_id", "-"),
            "subscription_type": active_user.get("subscription_type", "-"),
            "balance": balance.get("remaining", 0),
            "balance_expired_at": balance.get("expired_at", 0),
            "point_info": point_info
        }

        show_main_menu(profile)
        choice = console.input(f"[{get_theme_style('text_sub')}]🎯 Pilih menu:[/{get_theme_style('text_sub')}] ").strip()

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
            case "66": show_family_grup_menu()
            case "77": show_info_menu()
            case "88": show_theme_menu()
            case "99":
                print_panel("👋 Sampai jumpa!", "Aplikasi ditutup", border_style=get_theme_style("border_info"))
                sys.exit(0)
            case "s":
                enter_sentry_mode()
            case _:
                print_warning("⚠️ Pilihan tidak valid", "Silakan pilih menu yang tersedia.")
                pause()

