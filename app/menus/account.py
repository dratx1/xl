from app.client.engsel import get_otp, submit_otp
from app.service.auth import AuthInstance
from app.menus.util_helper import clear_screen, print_panel
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from app.config.theme_config import get_theme

console = Console()
theme = get_theme()

def normalize_xl_number(raw: str) -> str | None:
    raw = raw.strip().replace(" ", "").replace("-", "")
    if raw.startswith("+62"):
        normalized = "62" + raw[3:]
    elif raw.startswith("62"):
        normalized = raw
    elif raw.startswith("08"):
        normalized = "62" + raw[1:]
    else:
        return None

    if normalized.startswith("628") and 10 <= len(normalized) <= 14 and normalized.isdigit():
        return normalized
    return None

def login_prompt(api_key: str):
    clear_screen()
    console.print(Panel("🔐 Login ke MyXL", border_style=theme["border_primary"], padding=(1, 2)))
    raw_input = console.input(f"[{theme['text_sub']}]Masukkan nomor XL (08xx / 628xx / +628xx):[/{theme['text_sub']}] ").strip()
    phone_number = normalize_xl_number(raw_input)
    if not phone_number:
        print_panel("⚠️ Error", "Nomor tidak valid. Format harus 08xx, 628xx, atau +628xx.")
        return None, None

    try:
        subscriber_id = get_otp(phone_number)
        if not subscriber_id:
            print_panel("⚠️ Error", "Gagal mengirim OTP.")
            return None, None

        print_panel("✅ Info", "OTP berhasil dikirim ke nomor Anda.")
        try_count = 5
        while try_count > 0:
            otp = console.input(f"[{theme['text_sub']}]Masukkan OTP (6 digit):[/{theme['text_sub']}] ").strip()
            if not otp.isdigit() or len(otp) != 6:
                print_panel("⚠️ Error", "OTP tidak valid. Harus 6 digit angka.")
                continue

            tokens = submit_otp(api_key, phone_number, otp)
            if not tokens:
                try_count -= 1
                print_panel("⚠️ Error", f"OTP salah. Sisa percobaan: {try_count}")
                continue

            print_panel("✅ Sukses", "Berhasil login!")
            return phone_number, tokens["refresh_token"]

        print_panel("⛔ Gagal", "Login gagal setelah beberapa percobaan.")
        return None, None
    except Exception as e:
        print_panel("⚠️ Error", f"Gagal login: {e}")
        return None, None

def show_account_menu():
    clear_screen()
    AuthInstance.load_tokens()
    users = AuthInstance.refresh_tokens
    active_user = AuthInstance.get_active_user()

    in_account_menu = True
    add_user = False

    while in_account_menu:
        clear_screen()

        if AuthInstance.get_active_user() is None or add_user:
            number, refresh_token = login_prompt(AuthInstance.api_key)
            if not refresh_token:
                print_panel("⚠️ Error", "Gagal menambah akun.")
                continue

            AuthInstance.add_refresh_token(int(number), refresh_token)
            AuthInstance.load_tokens()
            users = AuthInstance.refresh_tokens
            active_user = AuthInstance.get_active_user()
            add_user = False
            continue

        console.print(Panel("👥 Akun Tersimpan", border_style=theme["border_info"], padding=(1, 2)))
        if not users:
            print_panel("ℹ️ Info", "Belum ada akun tersimpan.")

        table = Table(show_header=False, box=None)
        table.add_column("No", style=theme["text_key"], justify="right", width=4)
        table.add_column("Nomor", style=theme["text_body"])
        for idx, user in enumerate(users):
            is_active = active_user and user["number"] == active_user["number"]
            marker = " [bold green](Aktif)[/]" if is_active else ""
            table.add_row(str(idx + 1), f"{user['number']}{marker}")
        console.print(table)

        nav = Table(show_header=False, box=None)
        nav.add_column("Kode", style=theme["text_key"], justify="right", width=6)
        nav.add_column("Aksi", style=theme["text_body"])
        nav.add_row("0", "➕ Tambah Akun")
        nav.add_row("del <n>", "🗑️ Hapus akun ke-n")
        nav.add_row("00", "⬅️ Kembali ke menu utama")
        console.print(Panel(nav, title="📋 Navigasi", border_style=theme["border_primary"], padding=(0, 1)))

        input_str = console.input(f"[{theme['text_sub']}]Pilihan:[/{theme['text_sub']}] ").strip().lower()

        if input_str == "00":
            in_account_menu = False
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
                        print_panel("⚠️ Error", "Tidak bisa hapus akun aktif. Ganti dulu.")
                        continue
                    confirm = console.input(f"[{theme['text_sub']}]Yakin hapus {user_to_delete['number']}? (y/n):[/{theme['text_sub']}] ").strip().lower()
                    if confirm == "y":
                        AuthInstance.remove_refresh_token(user_to_delete["number"])
                        users = AuthInstance.refresh_tokens
                        active_user = AuthInstance.get_active_user()
                        print_panel("✅ Info", "Akun berhasil dihapus.")
                    else:
                        print_panel("ℹ️ Info", "Penghapusan dibatalkan.")
                else:
                    print_panel("⚠️ Error", "Nomor urut tidak valid.")
            else:
                print_panel("⚠️ Error", "Format salah. Gunakan: del <nomor>")
            continue

        else:
            print_panel("⚠️ Error", "Input tidak valid.")
            continue
