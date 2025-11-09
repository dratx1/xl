from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.align import Align
from rich.box import MINIMAL_DOUBLE_HEAD

from app.client.ciam import get_otp, submit_otp
from app.menus.util import clear_screen, pause, print_panel, nav_range
from app.service.auth import AuthInstance
from app.config.theme_config import get_theme
from app.service.service import load_status, save_status

console = Console()

def normalize_number(raw_input: str) -> str:
    raw_input = raw_input.strip()
    if raw_input.startswith("08"):
        return "628" + raw_input[2:]
    elif raw_input.startswith("+628"):
        return "628" + raw_input[4:]
    elif raw_input.startswith("628"):
        return raw_input
    return raw_input

def login_prompt(api_key: str):
    clear_screen()
    theme = get_theme()
    console.print(Panel("🔐 Login ke MyXL", border_style=theme["border_info"], expand=True))
    raw_input = console.input("Masukkan nomor XL (08xx / 628xx / +628xx): ").strip()
    phone_number = normalize_number(raw_input)

    if not phone_number.startswith("628") or len(phone_number) < 10 or len(phone_number) > 14:
        print_panel("⚠️ Error", "Nomor tidak valid. Pastikan input yang sesuai.")
        return None, None

    try:
        print_panel("⏳ Info", "Mengirim OTP...")
        subscriber_id = get_otp(phone_number)
        if not subscriber_id:
            print_panel("⚠️ Error", "Gagal mengirim OTP.")
            return None, None

        print_panel("✅ Info", "OTP berhasil dikirim ke nomor Anda.")

        for attempt in range(1, 6):
            otp = console.input(f"Percobaan {attempt}/5 - Masukkan OTP (6 digit): ").strip()
            if not otp.isdigit() or len(otp) != 6:
                print_panel("⚠️ Error", "OTP tidak valid. Harus 6 digit angka.")
                pause()
                continue

            print_panel("⏳ Info", "Memverifikasi OTP...")
            tokens = submit_otp(api_key, "SMS", phone_number, otp)
            if tokens:
                print_panel("✅ Sukses", f"Berhasil login sebagai {phone_number}")
                return phone_number, tokens["refresh_token"]
            else:
                print_panel("⚠️ Error", "OTP salah atau kadaluarsa.")
                pause()

        print_panel("⛔ Gagal Login", "Percobaan OTP melebihi batas maksimum (5x).")
        return None, None

    except Exception as e:
        print_panel("⚠️ Error", f"Terjadi kesalahan: {e}")
        return None, None

def show_account_menu():
    clear_screen()
    theme = get_theme()
    AuthInstance.load_tokens()
    users = AuthInstance.refresh_tokens
    active_user = AuthInstance.get_active_user()

    sumit_otp = 2
    verif_otp = "6969"
    status_id = load_status()
    is_verif = status_id.get("is_verif", False)

    in_account_menu = True
    add_user = False

    while in_account_menu:
        clear_screen()

        if active_user is None or add_user:
            if not is_verif and len(users) >= sumit_otp:
                print_panel("🚫 Batas akun tercapai", "Masukkan kode unlock untuk menambah akun.")
                verif_input = console.input("Kode Unlock: ").strip()
                if verif_input != verif_otp:
                    print_panel("⚠️ Gagal", "Kode unlock salah. Tidak bisa menambah akun.")
                    pause()
                    add_user = False
                    continue
                save_status(True)
                is_verif = True
                print_panel("✅ Berhasil", "Akses akun tambahan telah dibuka.")
                pause()

            number, refresh_token = login_prompt(AuthInstance.api_key)
            if not refresh_token:
                print_panel("⚠️ Error", "Gagal menambah akun. Silakan coba lagi.")
                pause()
                add_user = False
                continue

            AuthInstance.add_refresh_token(int(number), refresh_token)
            AuthInstance.load_tokens()
            users = AuthInstance.refresh_tokens
            active_user = AuthInstance.get_active_user()
            add_user = False
            continue

        console.print(Panel(
            Align.center("👥 Akun Tersimpan", vertical="middle"),
            border_style=theme["border_info"],
            padding=(1, 2),
            expand=True
        ))

        account_table = Table(box=MINIMAL_DOUBLE_HEAD, expand=True)
        account_table.add_column("No", style=theme["text_key"], justify="right", width=3)
        account_table.add_column("Nama", style=theme["text_body"])
        account_table.add_column("Nomor XL", style=theme["text_body"])
        account_table.add_column("Tipe", style=theme["text_body"])
        account_table.add_column("Status", style=theme["text_sub"], justify="center")

        for idx, user in enumerate(users):
            is_active = active_user and user["number"] == active_user["number"]
            status = "✅ Aktif" if is_active else "-"
            account_table.add_row(
                str(idx + 1),
                user.get("name", "-"),
                str(user["number"]),
                user.get("subscription_type", "-"),
                status
            )

        console.print(Panel(account_table, border_style=theme["border_primary"], padding=(0, 1), expand=True))

        nav_table = Table(show_header=False, box=MINIMAL_DOUBLE_HEAD, expand=True)
        nav_table.add_column(justify="right", style=theme["text_key"], width=6)
        nav_table.add_column(justify="left", style=theme["text_body"])
        nav_table.add_row("T", "Tambah akun")
        nav_table.add_row("E", "Edit nama akun")
        nav_table.add_row("H", f"[{theme['text_err']}]Hapus akun tersimpan[/]")
        nav_table.add_row("00", f"[{theme['text_sub']}]Kembali ke menu utama[/]")
        
        console.print(Panel(nav_table, border_style=theme["border_info"], padding=(0, 1), expand=True))
        console.print(f"Masukkan nomor akun (1 - {len(users)}) untuk berganti.")
        
        input_str = console.input("Pilihan: ").strip()
        
        if input_str == "00":
            return active_user["number"] if active_user else None
        
        elif input_str.upper() == "T":
            add_user = True
            continue
        
        elif input_str.upper() == "E":
            if not users:
                print_panel("⚠️ Error", "Tidak ada akun untuk diedit.")
                pause()
                continue
        
            nomor_input = console.input(f"Nomor akun yang ingin diedit (1 - {len(users)}): ").strip()
            if nomor_input.isdigit():
                nomor = int(nomor_input)
                if 1 <= nomor <= len(users):
                    selected_user = users[nomor - 1]
                    new_name = console.input(f"Masukkan nama baru untuk akun {selected_user['number']}: ").strip()
                    if new_name:
                        AuthInstance.edit_account_name(selected_user["number"], new_name)
                        AuthInstance.load_tokens()
                        users = AuthInstance.refresh_tokens
                        active_user = AuthInstance.get_active_user()
                        print_panel("✅ Berhasil", f"Nama akun diubah menjadi '{new_name}'.")
                    else:
                        print_panel("⚠️ Error", "Nama tidak boleh kosong.")
                    pause()
                else:
                    print_panel("⚠️ Error", "Nomor akun di luar jangkauan.")
                    pause()
            else:
                print_panel("⚠️ Error", "Input tidak valid.")
                pause()
        
        elif input_str.upper() == "H":
            if not users:
                print_panel("⚠️ Error", "Tidak ada akun untuk dihapus.")
                pause()
                continue
        
            nomor_input = console.input(f"Nomor akun yang ingin dihapus (1 - {len(users)}): ").strip()
            if nomor_input.isdigit():
                nomor = int(nomor_input)
                if 1 <= nomor <= len(users):
                    selected_user = users[nomor - 1]
                    confirm = console.input(f"Yakin ingin menghapus akun {selected_user['number']}? (y/n): ").strip().lower()
                    if confirm == "y":
                        print_panel("⏳ Info", f"Menghapus akun {selected_user['number']}...")
                        AuthInstance.remove_refresh_token(selected_user["number"])
                        AuthInstance.load_tokens()
                        users = AuthInstance.refresh_tokens
                        active_user = AuthInstance.get_active_user()
                        print_panel("✅ Info", f"Akun {selected_user['number']} berhasil dihapus.")
                    else:
                        print_panel("ℹ️ Info", "Penghapusan akun dibatalkan.")
                    pause()
                else:
                    print_panel("⚠️ Error", "Nomor akun di luar jangkauan.")
                    pause()
            else:
                print_panel("⚠️ Error", "Input tidak valid.")
                pause()
        
        elif input_str.isdigit() and 1 <= int(input_str) <= len(users):
            selected_user = users[int(input_str) - 1]
            return selected_user["number"]
        
        else:
            print_panel("⚠️ Error", "Input tidak valid. Silakan coba lagi.")
            pause()
