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
            table.add_row(str(idx + 1), p["family_name"], p["variant_name"], p["option_name"])

        console.print(Panel(table, border_style=theme["border_primary"], expand=True))
        console.print(Panel("00. Kembali ke menu utama", border_style=theme["border_info"], padding=(1, 1)))

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
from app.menus.util_helper import print_panel

console = Console()

def show_hot_menu2():
    api_key = AuthInstance.api_key
    tokens = AuthInstance.get_active_tokens()
    theme = get_theme()

    in_menu = True
    while in_menu:
        clear_screen()
        theme = get_theme()

        console.print(Panel(Align.center("🔥 Paket Hot 2 🔥"), border_style=theme["border_info"], padding=(1, 2)))

        try:
            response = requests.get("https://me.mashu.lol/pg-hot2.json", timeout=30)
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
        table.add_column("Nama Paket", style=theme["text_body"])
        table.add_column("Harga", style=theme["text_body"])

        for idx, p in enumerate(hot_packages):
            table.add_row(str(idx + 1), p["name"], f"Rp{p['price']}")

        console.print(Panel(table, border_style=theme["border_primary"], expand=True))
        console.print(Panel("00. Kembali ke menu utama", border_style=theme["border_info"], padding=(1, 1)))

        choice = console.input("Pilih paket (nomor): ").strip()
        if choice == "00":
            return
        if choice.isdigit() and 1 <= int(choice) <= len(hot_packages):
            selected = hot_packages[int(choice) - 1]
            packages = selected.get("packages", [])
            if not packages:
                print_panel("⚠️ Error", "Paket tidak tersedia.")
                pause()
                continue

            payment_items = []
            for pkg in packages:
                detail = get_package_details(api_key, tokens, pkg["family_code"], pkg["variant_code"], pkg["order"], pkg["is_enterprise"])
                if not detail:
                    print_panel("⚠️ Error", f"Gagal mengambil detail untuk {pkg['family_code']}.")
                    return
                payment_items.append(PaymentItem(
                    item_code=detail["package_option"]["package_option_code"],
                    product_type="",
                    item_price=detail["package_option"]["price"],
                    item_name=detail["package_option"]["name"],
                    tax=0,
                    token_confirmation=detail["token_confirmation"]
                ))

            clear_screen()
            console.print(Panel(
                Align.center(
                    f"📦 {selected['name']}\n💰 Harga: Rp{selected['price']}\n📝 Detail: {selected['detail']}"
                ),
                border_style=theme["border_info"],
                padding=(1, 2),
                expand=True
            ))

            payment_for = selected.get("payment_for", "BUY_PACKAGE")
            ask_overwrite = selected.get("ask_overwrite", False)
            overwrite_amount = selected.get("overwrite_amount", -1)
            token_confirmation_idx = selected.get("token_confirmation_idx", 0)
            amount_idx = selected.get("amount_idx", -1)

            in_payment = True
            while in_payment:
                console.print(Panel(
                    "1. Balance\n2. E-Wallet\n3. QRIS\n00. Kembali",
                    title="💳 Metode Pembayaran",
                    border_style=theme["border_info"],
                    padding=(1, 2),
                    expand=True
                ))
                method = console.input("Pilih metode: ").strip()

                if method == "00":
                    in_payment = False
                    continue

                elif method == "1":
                    if overwrite_amount == -1:
                        console.print(Panel(
                            f"⚠️ Pastikan balance KURANG DARI Rp{payment_items[-1]['item_price']}!",
                            border_style=theme["border_warn"]
                        ))
                        confirm = console.input("Lanjutkan pembelian? (y/n): ").strip().lower()
                        if confirm != "y":
                            print_panel("ℹ️ Info", "Pembelian dibatalkan.")
                            pause()
                            in_payment = False
                            continue

                    settlement_balance(
                        api_key, tokens, payment_items, payment_for,
                        ask_overwrite, overwrite_amount,
                        token_confirmation_idx, amount_idx
                    )
                    input("Tekan enter untuk kembali...")
                    return

                elif method == "2":
                    show_multipayment(
                        api_key, tokens, payment_items, payment_for,
                        ask_overwrite, overwrite_amount,
                        token_confirmation_idx, amount_idx
                    )
                    input("Tekan enter untuk kembali...")
                    return

                elif method == "3":
                    show_qris_payment(
                        api_key, tokens, payment_items, payment_for,
                        ask_overwrite, overwrite_amount,
                        token_confirmation_idx, amount_idx
                    )
                    input("Tekan enter untuk kembali...")
                    return

                else:
                    print_panel("⚠️ Error", "Metode tidak valid.")
                    pause()
        else:
            print_panel("⚠️ Error", "Input tidak valid.")
            pause()
