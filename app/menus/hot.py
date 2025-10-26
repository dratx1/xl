from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.align import Align
from rich.box import MINIMAL_DOUBLE_HEAD

import requests
from app.client.engsel import get_family
from app.menus.package import show_package_details
from app.service.auth import AuthInstance
from app.menus.util import clear_screen, pause
from app.config.theme_config import get_theme
from app.menus.util_helper import print_panel

console = Console()

def show_hot_menu():
    api_key = AuthInstance.api_key
    tokens = AuthInstance.get_active_tokens()
    theme = get_theme()

    in_menu = True
    while in_menu:
        clear_screen()
        theme = get_theme()

        console.print(Panel(Align.center("🔥 Paket Hot 🔥"), border_style=theme["border_info"], padding=(1, 2)))

        try:
            response = requests.get("https://me.mashu.lol/pg-hot.json", timeout=30)
            if response.status_code != 200:
                print_panel("⚠️ Error", "Gagal mengambil data hot package.")
                pause()
                return
            hot_packages = response.json()
        except Exception as e:
            print_panel("⚠️ Error", f"Gagal koneksi: {e}")
            pause()
            return

        table = Table(show_header=True, box=MINIMAL_DOUBLE_HEAD, expand=True)
        table.add_column("No", style=theme["text_key"], justify="right", width=4)
        table.add_column("Family", style=theme["text_body"])
        table.add_column("Variant", style=theme["text_body"])
        table.add_column("Opsi", style=theme["text_body"])

        for idx, p in enumerate(hot_packages):
            table.add_row(str(idx + 1), p["family_name"], p["variant_name"], p["option_name"], padding=(0, 0))

        console.print(Panel(table, border_style=theme["border_primary"], expand=True))
        
        nav_table = Table(show_header=False, box=MINIMAL_DOUBLE_HEAD, expand=True)
        nav_table.add_column(justify="right", style=theme["text_key"], width=4)
        nav_table.add_column(style=theme["text_body"])
        nav_table.add_row("00", f"[{theme['text_sub']}]Kembali ke menu utama[/]")

        console.print(Panel(nav_table, border_style=theme["border_info"], padding=(0, 1), expand=True))

        choice = console.input("Pilih paket (nomor): ").strip()
        if choice == "00":
            return
        if choice.isdigit() and 1 <= int(choice) <= len(hot_packages):
            selected = hot_packages[int(choice) - 1]
            family_data = get_family(api_key, tokens, selected["family_code"], selected["is_enterprise"])
            if not family_data:
                print_panel("⚠️ Error", "Gagal mengambil data family.")
                pause()
                continue

            option_code = None
            for variant in family_data["package_variants"]:
                if variant["name"] == selected["variant_name"]:
                    for option in variant["package_options"]:
                        if option["order"] == selected["order"]:
                            option_code = option["package_option_code"]
                            break

            if option_code:
                show_package_details(api_key, tokens, option_code, selected["is_enterprise"])
            else:
                print_panel("⚠️ Error", "Opsi paket tidak ditemukan.")
                pause()
        else:
            print_panel("⚠️ Error", "Input tidak valid.")
            pause()

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.align import Align
from rich.box import MINIMAL_DOUBLE_HEAD

import requests
from app.client.engsel import get_package_details
from app.service.auth import AuthInstance
from app.menus.util import clear_screen, pause
from app.client.ewallet import show_multipayment
from app.client.qris import show_qris_payment
from app.client.balance import settlement_balance
from app.type_dict import PaymentItem
from app.config.theme_config import get_theme
from app.menus.util_helper import print_panel, get_rupiah

console = Console()

def show_hot_menu2():
    api_key = AuthInstance.api_key
    tokens = AuthInstance.get_active_tokens()
    theme = get_theme()

    if not tokens:
        print_panel("⚠️ Error", "Token tidak tersedia. Silakan login ulang.")
        pause()
        return

    while True:
        clear_screen()
        console.print(Panel(
            Align.center("🔥 Paket Hot Promo-2 🔥", vertical="middle"),
            border_style=theme["border_info"],
            padding=(1, 2),
            expand=True
        ))

        try:
            response = requests.get("https://me.mashu.lol/pg-hot2.json", timeout=30)
            response.raise_for_status()
            hot_packages = response.json()
        except Exception as e:
            print_panel("⚠️ Error", f"Gagal mengambil data Hot promo-2 Package.\n{e}")
            pause()
            return

        if not hot_packages:
            print_panel("⚠️ Error", "Tidak ada data paket tersedia.")
            pause()
            return

        table = Table(box=MINIMAL_DOUBLE_HEAD, expand=True)
        table.add_column("No", justify="right", style=theme["text_key"], width=6)
        table.add_column("Nama Paket", style=theme["text_body"])
        table.add_column("Harga", justify="right", style=theme["text_money"], width=12)

        for idx, p in enumerate(hot_packages):
            table.add_row(str(idx + 1), p["name"], get_rupiah(p["price"]))

        console.print(Panel(table, border_style=theme["border_primary"], padding=(0, 0), expand=True))

        nav_table = Table(show_header=False, box=MINIMAL_DOUBLE_HEAD, expand=True)
        nav_table.add_column(justify="right", style=theme["text_key"], width=4)
        nav_table.add_column(style=theme["text_body"])
        nav_table.add_row("00", f"[{theme['text_sub']}]Kembali ke menu utama[/]")

        console.print(Panel(nav_table, border_style=theme["border_info"], padding=(0, 1), expand=True))

        choice = console.input(f"[{theme['text_sub']}]Pilih paket:[/{theme['text_sub']}] ").strip()
        if choice == "00":
            return

        if not choice.isdigit() or not (1 <= int(choice) <= len(hot_packages)):
            print_panel("⚠️ Error", "Input tidak valid. Silakan coba lagi.")
            pause()
            continue

        selected_package = hot_packages[int(choice) - 1]
        packages = selected_package.get("packages", [])
        if not packages:
            print_panel("⚠️ Error", "Paket tidak tersedia.")
            pause()
            continue

        payment_items = []
        for package in packages:
            detail = get_package_details(
                api_key,
                tokens,
                package["family_code"],
                package["variant_code"],
                package["order"],
                package["is_enterprise"],
            )
            if not detail:
                print_panel("⚠️ Error", f"Gagal mengambil detail paket untuk {package['family_code']}.")
                pause()
                return

            payment_items.append(PaymentItem(
                item_code=detail["package_option"]["package_option_code"],
                product_type="",
                item_price=detail["package_option"]["price"],
                item_name=detail["package_option"]["name"],
                tax=0,
                token_confirmation=detail["token_confirmation"],
            ))

        detail_lines = [
            f"[{theme['text_body']}]• {line.strip()}[/{theme['text_body']}]"
            for line in selected_package.get("detail", "").split("\n")
            if line.strip()
        ]

        clear_screen()
        console.print(Panel(
            f"[bold]{selected_package['name']}[/]\n\n"
            f"Harga: Rp [bold {theme['text_money']}]{get_rupiah(selected_package['price'])}[/]\n\n"
            f"[{theme['text_sub']}]Detail:[/]\n" + "\n".join(detail_lines),
            title=f"[{theme['text_title']}]📦 Detail Paket[/]",
            border_style=theme["border_info"],
            padding=(1, 2),
            expand=True
        ))

        payment_for = selected_package.get("payment_for", "BUY_PACKAGE")
        ask_overwrite = selected_package.get("ask_overwrite", False)
        overwrite_amount = selected_package.get("overwrite_amount", -1)
        token_confirmation_idx = selected_package.get("token_confirmation_idx", 0)
        amount_idx = selected_package.get("amount_idx", -1)

        method_table = Table(show_header=False, box=MINIMAL_DOUBLE_HEAD, expand=True)
        method_table.add_column(justify="right", style=theme["text_key"], width=6)
        method_table.add_column(style=theme["text_body"])
        method_table.add_row("1", "💰 Balance")
        method_table.add_row("2", "📱 E-Wallet")
        method_table.add_row("3", "🏧 QRIS")
        method_table.add_row("00", f"[{theme['text_sub']}]Kembali ke daftar paket[/]")

        console.print(Panel(
            method_table,
            title=f"[{theme['text_title']}]💳 Pilih Metode Pembayaran[/]",
            border_style=theme["border_primary"],
            padding=(0, 1),
            expand=True
        ))

        method = console.input(f"[{theme['text_sub']}]Pilih metode:[/{theme['text_sub']}] ").strip()
        if method == "00":
            continue

        if method == "1":
            if overwrite_amount == -1:
                console.print(Panel(
                    f"⚠️ Pastikan sisa balance KURANG DARI Rp{get_rupiah(payment_items[-1]['item_price'])}\n"
                    f"Lanjutkan pembelian?",
                    border_style=theme["border_warning"],
                    padding=(1, 2)
                ))
                confirm = console.input(f"[{theme['text_sub']}]Lanjutkan? (y/n):[/{theme['text_sub']}] ").strip().lower()
                if confirm != "y":
                    print_panel("ℹ️ Info", "Pembelian dibatalkan oleh pengguna.")
                    pause()
                    continue

            settlement_balance(
                api_key,
                tokens,
                payment_items,
                payment_for,
                ask_overwrite,
                overwrite_amount,
                token_confirmation_idx,
                amount_idx,
            )
        elif method == "2":
            show_multipayment(
                api_key,
                tokens,
                payment_items,
                payment_for,
                ask_overwrite,
                overwrite_amount,
                token_confirmation_idx,
                amount_idx,
            )
        elif method == "3":
            show_qris_payment(
                api_key,
                tokens,
                payment_items,
                payment_for,
                ask_overwrite,
                overwrite_amount,
                token_confirmation_idx,
                amount_idx,
            )
        else:
            print_panel("⚠️ Error", "Metode tidak valid. Silakan coba lagi.")
            pause()
            continue

        console.input(f"[{theme['text_sub']}]Tekan enter untuk kembali...[/{theme['text_sub']}] ")
        return
