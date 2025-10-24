import os
import json
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.align import Align
from rich.text import Text
from rich.box import MINIMAL_DOUBLE_HEAD

from app.menus.package import get_packages_by_family
from app.menus.util import clear_screen, pause
from app.menus.util_helper import print_panel, live_loading
from app.config.theme_config import get_theme

console = Console()
FAMILY_FILE = os.path.abspath("family_codes.json")


def ensure_family_file():
    default_data = {"codes": []}
    if not os.path.exists(FAMILY_FILE):
        with open(FAMILY_FILE, "w") as f:
            json.dump(default_data, f, indent=2)
        return default_data

    try:
        with open(FAMILY_FILE, "r") as f:
            data = json.load(f)
        if not isinstance(data, dict) or "codes" not in data or not isinstance(data["codes"], list):
            raise ValueError("Struktur tidak valid")
        return data
    except (json.JSONDecodeError, ValueError):
        with open(FAMILY_FILE, "w") as f:
            json.dump(default_data, f, indent=2)
        return default_data

def list_family_codes():
    return ensure_family_file()["codes"]

def add_family_code(code, name):
    if not code.strip() or not name.strip():
        return False
    data = ensure_family_file()
    if any(item["code"] == code for item in data["codes"]):
        return False
    data["codes"].append({"code": code.strip(), "name": name.strip()})
    with open(FAMILY_FILE, "w") as f:
        json.dump(data, f, indent=2)
    return True

def remove_family_code(index):
    data = ensure_family_file()
    if 0 <= index < len(data["codes"]):
        removed = data["codes"].pop(index)
        with open(FAMILY_FILE, "w") as f:
            json.dump(data, f, indent=2)
        return removed["code"]
    return None

def edit_family_name(index, new_name):
    if not new_name.strip():
        return False
    data = ensure_family_file()
    if 0 <= index < len(data["codes"]):
        data["codes"][index]["name"] = new_name.strip()
        with open(FAMILY_FILE, "w") as f:
            json.dump(data, f, indent=2)
        return True
    return False

def show_family_menu(return_package_detail: bool = False):
    while True:
        clear_screen()
        semua_kode = list_family_codes()
        theme = get_theme()

        console.print(Panel(
            Align.center("📋 Family Kode Yang Terdaftar", vertical="middle"),
            border_style=theme["border_info"],
            padding=(1, 2),
            expand=True
        ))

        packages = []
        if semua_kode:
            table = Table(box=MINIMAL_DOUBLE_HEAD, expand=True)
            table.add_column("No", justify="right", style=theme["text_key"], width=3)
            table.add_column("Nama FC", style=theme["text_body"])
            table.add_column("Family Code", style=theme["text_sub"])

            for i, item in enumerate(semua_kode, start=1):
                table.add_row(str(i), item["name"], item["code"])
                packages.append({
                    "number": i,
                    "code": item["code"],
                    "name": item["name"]
                })

            console.print(Panel(table, border_style=theme["border_primary"], padding=(0, 0), expand=True))
        else:
            console.print(Panel(
                "[italic]Belum ada family code yang terdaftar.[/italic]",
                border_style=theme["border_warning"],
                padding=(1, 2),
                expand=True
            ))

        nav_table = Table(show_header=False, box=MINIMAL_DOUBLE_HEAD, expand=True)
        nav_table.add_column(justify="right", style=theme["text_key"], width=6)
        nav_table.add_column(style=theme["text_body"])
        nav_table.add_row("T", "Tambah family code")
        nav_table.add_row("E", "Edit nama family code")
        nav_table.add_row("H", f"[{theme['text_err']}]Hapus family code[/]")
        nav_table.add_row("00", f"[{theme['text_sub']}]Kembali ke menu awal[/]")

        console.print(Panel(nav_table, border_style=theme["border_info"], padding=(0, 1), expand=True))

        aksi = console.input(f"[{theme['text_sub']}]Pilih aksi atau nomor kode:[/{theme['text_sub']}] ").strip().lower()

        if aksi == "t":
            code = console.input("Masukkan family code: ").strip()
            name = console.input("Masukkan nama family: ").strip()
            success = add_family_code(code, name)
            print_panel("✅ Info" if success else "❌ Error", "Berhasil menambahkan." if success else "Gagal menambahkan, family code sudah ada di daftar.")
            pause()

        elif aksi == "h":
            if not semua_kode:
                print_panel("Info", "Tidak ada kode untuk dihapus.")
                pause()
                continue
            idx = console.input("Masukkan nomor kode yang ingin dihapus: ").strip()
            if idx.isdigit() and 1 <= int(idx) <= len(semua_kode):
                index = int(idx) - 1
                nama = semua_kode[index]["name"]
                kode = semua_kode[index]["code"]
                konfirmasi = console.input(f"Yakin ingin menghapus '{nama}' ({kode})? (y/n): ").strip().lower()
                if konfirmasi == "y":
                    removed = remove_family_code(index)
                    print_panel("✅ Info" if removed else "❌ Error", f"Berhasil menghapus {removed}." if removed else "Gagal menghapus.")
                else:
                    print_panel("❎ Info", "Penghapusan dibatalkan.")
            else:
                print_panel("❌ Error", "Nomor tidak valid.")
            pause()

        elif aksi == "e":
            if not semua_kode:
                print_panel("Info", "Tidak ada kode untuk diedit.")
                pause()
                continue
            idx = console.input("Masukkan nomor kode yang ingin diubah namanya: ").strip()
            if idx.isdigit() and 1 <= int(idx) <= len(semua_kode):
                new_name = console.input("Masukkan nama baru: ").strip()
                success = edit_family_name(int(idx) - 1, new_name)
                print_panel("✅ Info" if success else "❌ Error", "Nama berhasil diperbarui." if success else "Gagal memperbarui nama.")
            else:
                print_panel("❌ Error", "Nomor tidak valid.")
            pause()

        elif aksi == "00":
            return None, None if return_package_detail else None

        elif aksi.isdigit():
            nomor = int(aksi)
            selected = next((p for p in packages if p["number"] == nomor), None)
            if selected:
                try:
                    result = get_packages_by_family(selected["code"], return_package_detail=return_package_detail)
                    if return_package_detail:
                        if isinstance(result, tuple):
                            return result
                        elif result == "MAIN":
                            return "MAIN"
                        else:
                            return None, None
                    if result == "MAIN":
                        return None
                    elif result == "BACK":
                        continue
                    pause()
                except Exception as e:
                    print_panel("❌ Error", f"Gagal menampilkan paket: {e}")
            else:
                print_panel("❌ Error", "Nomor tidak valid.")
            pause()
