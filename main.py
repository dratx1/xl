from dotenv import load_dotenv
load_dotenv()

import sys, json
from datetime import datetime
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
from app.menus.family_grup import show_family_menu
from app.menus.theme import show_theme_menu
from app.menus.donate import show_donate_menu

WIDTH = 55

def show_main_menu(profile):
    clear_screen()
    print("=" * WIDTH)
    expired_at_dt = datetime.fromtimestamp(profile["balance_expired_at"]).strftime("%Y-%m-%d")
    print(f"Nomor: {profile['number']} | Type: {profile['subscription_type']}".center(WIDTH))
    print(f"Pulsa: Rp {profile['balance']} | Aktif sampai: {expired_at_dt}".center(WIDTH))
    print(f"{profile['point_info']}".center(WIDTH))
    print("=" * WIDTH)
    print("Menu:")
    print("1. Login/Ganti akun")
    print("2. Lihat Paket Saya")
    print("3. Beli Paket 🔥 HOT 🔥")
    print("4. Beli Paket 🔥 HOT-2 🔥")
    print("5. Beli Paket Berdasarkan Option Code")
    print("6. Beli Paket Berdasarkan Family Code")
    print("7. Beli Semua Paket di Family Code (loop)")
    print("8. Simpan/Kelola Family Code")
    print("9. Family Plan/Akrab Organizer")
    print("10. [WIP] Circle")
    print("11. Store Segments")
    print("12. Store Family List")
    print("13. Store Packages")
    print("77. Info Unlock Code")
    print("88. Ganti Tema CLI")
    print("N. Notifikasi")
    print("00. Bookmark Paket")
    print("99. Tutup aplikasi")
    print("-------------------------------------------------------")

def build_profile():
    active_user = AuthInstance.get_active_user()
    if not active_user:
        return None

    balance = get_balance(AuthInstance.api_key, active_user["tokens"]["id_token"])
    profile_data = get_profile(AuthInstance.api_key, active_user["tokens"]["access_token"], active_user["tokens"]["id_token"])
    sub_type = profile_data["profile"]["subscription_type"]

    point_info = "Points: N/A | Tier: N/A"
    if sub_type == "PREPAID":
        tiering_data = get_tiering_info(AuthInstance.api_key, active_user["tokens"])
        tier = tiering_data.get("tier", 0)
        current_point = tiering_data.get("current_point", 0)
        point_info = f"Points: {current_point} | Tier: {tier}"

    return {
        "number": active_user["number"],
        "subscriber_id": profile_data["profile"]["subscriber_id"],
        "subscription_type": sub_type,
        "balance": balance.get("remaining"),
        "balance_expired_at": balance.get("expired_at"),
        "point_info": point_info
    }

def main():
    while True:
        active_user = AuthInstance.get_active_user()
        if not active_user:
            selected_user_number = show_account_menu()
            if selected_user_number:
                AuthInstance.set_active_user(selected_user_number)
            else:
                print("No user selected or failed to load user.")
            continue

        profile = build_profile()
        if not profile:
            print("Gagal membangun profil pengguna.")
            continue

        show_main_menu(profile)
        choice = input("Pilih menu: ").strip().lower()

        if choice == "1":
            selected_user_number = show_account_menu()
            if selected_user_number:
                AuthInstance.set_active_user(selected_user_number)
            else:
                print("No user selected or failed to load user.")

        elif choice == "2":
            fetch_my_packages()

        elif choice == "3":
            show_hot_menu()

        elif choice == "4":
            show_hot_menu2()

        elif choice == "5":
            option_code = input("Masukkan option code (atau '99' untuk batal): ").strip()
            if option_code != "99":
                show_package_details(AuthInstance.api_key, active_user["tokens"], option_code, False)

        elif choice == "6":
            family_code = input("Masukkan family code (atau '99' untuk batal): ").strip()
            if family_code != "99":
                get_packages_by_family(family_code)

        elif choice == "7":
            family_code = input("Masukkan family code (atau '99' untuk batal): ").strip()
            if family_code == "99":
                return
            start_from_option = input("Mulai dari nomor option (default 1): ").strip()
            try:
                start_from_option = int(start_from_option)
            except ValueError:
                start_from_option = 1
            use_decoy = input("Gunakan decoy? (y/n): ").strip().lower() == 'y'
            pause_on_success = input("Pause setiap sukses? (y/n): ").strip().lower() == 'y'
            delay_seconds = input("Delay antar pembelian (detik): ").strip()
            try:
                delay_seconds = int(delay_seconds)
            except ValueError:
                delay_seconds = 0
            purchase_by_family(family_code, use_decoy, pause_on_success, delay_seconds, start_from_option)

        elif choice == "8":
            show_family_menu()

        elif choice == "9":
            show_family_info(AuthInstance.api_key, active_user["tokens"])

        elif choice == "10":
            show_circle_info(AuthInstance.api_key, active_user["tokens"])

        elif choice == "11":
            is_enterprise = input("Enterprise store? (y/n): ").strip().lower() == 'y'
            show_store_segments_menu(is_enterprise)

        elif choice == "12":
            is_enterprise = input("Enterprise? (y/n): ").strip().lower() == 'y'
            show_family_list_menu(profile['subscription_type'], is_enterprise)

        elif choice == "13":
            is_enterprise = input("Enterprise? (y/n): ").strip().lower() == 'y'
            show_store_packages_menu(profile['subscription_type'], is_enterprise)

        elif choice == "77":
            show_donate_menu()

        elif choice == "88":
            show_theme_menu()

        elif choice == "00":
            show_bookmark_menu()

        elif choice == "n":
            show_notification_menu()

        elif choice == "s":
            enter_sentry_mode()

        elif choice == "99":
            print("👋 Sampai jumpa!")
            sys.exit(0)

        else:
            print("Pilihan tidak valid.")
            pause()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nKeluar dari aplikasi.")
