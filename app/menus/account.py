from app.client.ciam import get_otp, submit_otp
from app.menus.util import (
    clear_screen,
    pause,
    print_panel,
    nav_range
)
from app.service.auth import AuthInstance
from app.config.theme_config import get_theme

def login_prompt(api_key: str):
    theme = get_theme()
    clear_screen()
    print_panel("🔐 Login ke MyXL", "Masukkan nomor XL (Contoh: 6281234567890)")
    phone_number = input("Nomor: ").strip()

    if not phone_number.startswith("628") or len(phone_number) < 10 or len(phone_number) > 14:
        print_panel("❌ Error", "Nomor tidak valid. Harus diawali '628' dan panjang sesuai.")
        pause()
        return None, None

    try:
        subscriber_id = get_otp(phone_number)
        if not subscriber_id:
            print_panel("❌ Error", "Gagal mengirim OTP.")
            pause()
            return None, None

        print_panel("✅ Info", "OTP berhasil dikirim ke nomor Anda.")
        try_count = 5
        while try_count > 0:
            otp = input(f"Masukkan OTP (sisa percobaan: {try_count}): ").strip()
            if not otp.isdigit() or len(otp) != 6:
                print_panel("❌ Error", "OTP harus 6 digit angka.")
                continue

            tokens = submit_otp(api_key, "SMS", phone_number, otp)
            if tokens:
                print_panel("✅ Info", "Berhasil login.")
                return phone_number, tokens["refresh_token"]

            print_panel("❌ Error", "OTP salah. Silakan coba lagi.")
            try_count -= 1

        print_panel("❌ Error", "Gagal login setelah beberapa percobaan.")
        pause()
        return None, None

    except Exception as e:
        print_panel("❌ Error", f"Gagal login: {e}")
        pause()
        return None, None

def show_account_menu():
    theme = get_theme()
    clear_screen()
    AuthInstance.load_tokens()
    users = AuthInstance.refresh_tokens
    active_user = AuthInstance.get_active_user()

    in_account_menu = True
    add_user = False
    while in_account_menu:
        clear_screen()

        if active_user is None or add_user:
            number, refresh_token = login_prompt(AuthInstance.api_key)
            if not refresh_token:
                print_panel("❌ Error", "Gagal menambah akun.")
                pause()
                continue

            AuthInstance.add_refresh_token(int(number), refresh_token)
            AuthInstance.load_tokens()
            users = AuthInstance.refresh_tokens
            active_user = AuthInstance.get_active_user()
            add_user = False
            continue

        print_panel("👥 Akun Tersimpan", "Daftar akun yang tersedia:")
        if not users:
            print_panel("ℹ️ Info", "Belum ada akun tersimpan.")
        else:
            for idx, user in enumerate(users):
                is_active = active_user and user["number"] == active_user["number"]
                marker = "✅" if is_active else ""
                number = str(user.get("number", "")).ljust(14)
                sub_type = user.get("subscription_type", "").center(12)
                print(f"{idx + 1}. {number} [{sub_type}] {marker}")

        print("-" * 55)
        print("Command:")
        print("0: Tambah Akun")
        print(nav_range("Nomor", len(users)) + " → Pilih akun")
        print(nav_range("del", len(users)) + " → Hapus akun")
        print("00: Kembali ke menu utama")
        print("-" * 55)

        input_str = input("Pilihan: ").strip()
        if input_str == "00":
            return active_user["number"] if active_user else None
        elif input_str == "0":
            add_user = True
            continue
        elif input_str.isdigit() and 1 <= int(input_str) <= len(users):
            selected_user = users[int(input_str) - 1]
            return selected_user['number']
        elif input_str.startswith("del "):
            parts = input_str.split()
            if len(parts) == 2 and parts[1].isdigit():
                del_index = int(parts[1])
                if 1 <= del_index <= len(users):
                    user_to_delete = users[del_index - 1]
                    if active_user and user_to_delete["number"] == active_user["number"]:
                        print_panel("❌ Error", "Tidak bisa hapus akun aktif. Ganti akun dulu.")
                        pause()
                        continue
                    confirm = input(f"Yakin hapus akun {user_to_delete['number']}? (y/n): ").strip().lower()
                    if confirm == "y":
                        AuthInstance.remove_refresh_token(user_to_delete["number"])
                        users = AuthInstance.refresh_tokens
                        active_user = AuthInstance.get_active_user()
                        print_panel("✅ Info", "Akun berhasil dihapus.")
                    else:
                        print_panel("❎ Info", "Penghapusan dibatalkan.")
                else:
                    print_panel("❌ Error", "Nomor urut tidak valid.")
            else:
                print_panel("❌ Error", "Format perintah tidak valid. Gunakan: del <nomor>")
            pause()
            continue
        else:
            print_panel("❌ Error", "Input tidak valid.")
            pause()
            continue
