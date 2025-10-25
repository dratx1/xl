from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.align import Align
from rich.box import MINIMAL_DOUBLE_HEAD

from app.menus.package import show_package_details
from app.service.auth import AuthInstance
from app.menus.util import clear_screen, pause
from app.service.bookmark import BookmarkInstance
from app.client.engsel import get_family
from app.config.theme_config import get_theme
from app.menus.util_helper import print_panel

console = Console()

def show_bookmark_menu():
    api_key = AuthInstance.api_key
    tokens = AuthInstance.get_active_tokens()
    theme = get_theme()

    in_bookmark_menu = True
    while in_bookmark_menu:
        clear_screen()
        theme = get_theme()

        console.print(Panel(Align.center("📌 Bookmark Paket"), border_style=theme["border_info"], padding=(1, 2)))

        bookmarks = BookmarkInstance.get_bookmarks()
        if not bookmarks:
            print_panel("ℹ️ Info", "Tidak ada bookmark tersimpan.")
            pause()
            return None

        table = Table(show_header=True, box=MINIMAL_DOUBLE_HEAD, expand=True)
        table.add_column("No", style=theme["text_key"], justify="right", width=4)
        table.add_column("Family", style=theme["text_body"])
        table.add_column("Variant", style=theme["text_body"])
        table.add_column("Opsi", style=theme["text_body"])

        for idx, bm in enumerate(bookmarks):
            table.add_row(
                str(idx + 1),
                bm["family_name"],
                bm["variant_name"],
                bm["option_name"]
            )

        console.print(Panel(table, border_style=theme["border_primary"], expand=True))

        nav = Table(show_header=False, box=MINIMAL_DOUBLE_HEAD, expand=True)
        nav.add_column(justify="right", style=theme["text_key"], width=6)
        nav.add_column(justify="left", style=theme["text_body"])
        nav.add_row("00", "Kembali ke menu utama")
        nav.add_row("000", f"[{theme['text_err']}]Hapus bookmark tersimpan[/]")

        console.print(Panel(nav, border_style=theme["border_info"], expand=True))
        choice = console.input("Pilih nomor bookmark: ").strip()

        if choice == "00":
            return None

        elif choice == "000":
            del_choice = console.input("Masukkan nomor bookmark yang ingin dihapus: ").strip()
            if del_choice.isdigit() and 1 <= int(del_choice) <= len(bookmarks):
                del_bm = bookmarks[int(del_choice) - 1]
                BookmarkInstance.remove_bookmark(
                    del_bm["family_code"],
                    del_bm["is_enterprise"],
                    del_bm["variant_name"],
                    del_bm["order"],
                )
                print_panel("✅ Info", "Bookmark berhasil dihapus.")
            else:
                print_panel("⚠️ Error", "Input tidak valid.")
            pause()
            continue

        elif choice.isdigit() and 1 <= int(choice) <= len(bookmarks):
            selected_bm = bookmarks[int(choice) - 1]
            family_code = selected_bm["family_code"]
            is_enterprise = selected_bm["is_enterprise"]

            family_data = get_family(api_key, tokens, family_code, is_enterprise)
            if not family_data:
                print_panel("⚠️ Error", "Gagal mengambil data family.")
                pause()
                continue

            option_code = None
            for variant in family_data["package_variants"]:
                if variant["name"] == selected_bm["variant_name"]:
                    for option in variant["package_options"]:
                        if option["order"] == selected_bm["order"]:
                            option_code = option["package_option_code"]
                            break

            if option_code:
                show_package_details(api_key, tokens, option_code, is_enterprise)
            else:
                print_panel("⚠️ Error", "Opsi paket tidak ditemukan.")
                pause()
        else:
            print_panel("⚠️ Error", "Input tidak valid.")
            pause()
