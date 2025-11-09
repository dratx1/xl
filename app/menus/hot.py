import requests

from app.client.engsel import get_family, get_package_details
from app.menus.package import show_package_details
from app.service.auth import AuthInstance
from app.menus.util import clear_screen, format_quota_byte, pause, display_html, print_panel
from app.client.purchase.ewallet import show_multipayment
from app.client.purchase.qris import show_qris_payment
from app.client.purchase.balance import settlement_balance
from app.type_dict import PaymentItem
from app.config.theme_config import get_theme

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.align import Align
from rich.box import MINIMAL_DOUBLE_HEAD


console = Console()
WIDTH = 55

def show_hot_menu():
    api_key = AuthInstance.api_key
    tokens = AuthInstance.get_active_tokens()
    theme = get_theme()

    clear_screen()
    console.print(Panel(
        Align.center("🔥 Paket Hot Promo 🔥", vertical="middle"),
        border_style=theme["border_info"],
        padding=(1, 2),
        expand=True
    ))

    try:
        response = requests.get("https://me.mashu.lol/pg-hot.json", timeout=30)
        response.raise_for_status()
        hot_packages = response.json()
    except Exception:
        print_panel("⚠️ Error", "Gagal mengambil data hot package.")
        pause()
        return "BACK"

    # Tampilkan tabel hanya sekali
    table = Table(box=MINIMAL_DOUBLE_HEAD, expand=True)
    table.add_column("No", justify="right", style=theme["text_key"], width=4)
    table.add_column("Family", style=theme["text_body"])
    table.add_column("Varian", style=theme["text_body"])
    table.add_column("Opsi", style=theme["text_body"])

    for idx, p in enumerate(hot_packages):
        table.add_row(
            str(idx + 1),
            p["family_name"],
            p["variant_name"],
            p["option_name"]
        )

    console.print(Panel(table, border_style=theme["border_primary"], padding=(0, 0), expand=True))

    nav = Table(show_header=False, box=MINIMAL_DOUBLE_HEAD, expand=True)
    nav.add_column(justify="right", style=theme["text_key"], width=6)
    nav.add_column(style=theme["text_body"])
    nav.add_row("00", f"[{theme['text_sub']}]Kembali ke menu utama[/]")

    console.print(Panel(nav, border_style=theme["border_info"], padding=(0, 1), expand=True))

    # Loop input tanpa clear ulang
    while True:
        choice = console.input(f"[{theme['text_sub']}]Pilih paket (nomor):[/{theme['text_sub']}] ").strip()
        if choice == "00":
            return "MAIN"
        if not choice.isdigit():
            print_panel("⚠️ Error", "Input tidak valid. Masukkan nomor paket.")
            pause()
            continue

        index = int(choice)
        if not (1 <= index <= len(hot_packages)):
            print_panel("⚠️ Error", "Nomor paket tidak ditemukan.")
            pause()
            continue

        selected = hot_packages[index - 1]
        family_code = selected["family_code"]
        is_enterprise = selected["is_enterprise"]

        family_data = get_family(api_key, tokens, family_code, is_enterprise)
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
            result = show_package_details(
                api_key,
                tokens,
                option_code,
                is_enterprise,
                option_order=selected["order"]
            )
            if result == "MAIN":
                return "MAIN"
            elif result == "BACK" or result is True:
                continue
        else:
            print_panel("⚠️ Error", "Paket tidak ditemukan.")
            pause()


def show_hot_menu2():
    api_key = AuthInstance.api_key
    tokens = AuthInstance.get_active_tokens()
    
    in_bookmark_menu = True
    while in_bookmark_menu:
        clear_screen()
        main_package_detail = {}
        print("=" * WIDTH)
        print("🔥 Paket  Hot 2 🔥".center(WIDTH))
        print("=" * WIDTH)
        
        url = "https://me.mashu.lol/pg-hot2.json"
        response = requests.get(url, timeout=30)
        if response.status_code != 200:
            print("Gagal mengambil data hot package.")
            pause()
            return None

        hot_packages = response.json()

        for idx, p in enumerate(hot_packages):
            print(f"{idx + 1}. {p['name']}\n   Harga: {p['price']}")
            print("-" * WIDTH)
        
        print("00. Kembali ke menu utama")
        print("-" * WIDTH)
        choice = input("Pilih paket (nomor): ")
        if choice == "00":
            in_bookmark_menu = False
            return None
        if choice.isdigit() and 1 <= int(choice) <= len(hot_packages):
            selected_package = hot_packages[int(choice) - 1]
            packages = selected_package.get("packages", [])
            if len(packages) == 0:
                print("Paket tidak tersedia.")
                pause()
                continue
            
            payment_items = []
            for package in packages:
                package_detail = get_package_details(
                    api_key,
                    tokens,
                    package["family_code"],
                    package["variant_code"],
                    package["order"],
                    package["is_enterprise"],
                    package["migration_type"],
                )
                
                if package == packages[0]:
                    main_package_detail = package_detail
                
                # Force failed when one of the package detail is None
                if not package_detail:
                    print(f"Gagal mengambil detail paket untuk {package['family_code']}.")
                    return None
                
                payment_items.append(
                    PaymentItem(
                        item_code=package_detail["package_option"]["package_option_code"],
                        product_type="",
                        item_price=package_detail["package_option"]["price"],
                        item_name=package_detail["package_option"]["name"],
                        tax=0,
                        token_confirmation=package_detail["token_confirmation"],
                    )
                )
            
            clear_screen()
            print("=" * WIDTH)
            print(f"Name: {selected_package['name']}")
            print(f"Price: {selected_package['price']}")
            print(f"Detail: {selected_package['detail']}")
            print("=" * WIDTH)
            print("Main Package Details:".center(WIDTH))
            print("-" * WIDTH)
            # Show package 0 details
            
            price = main_package_detail["package_option"]["price"]
            detail = display_html(main_package_detail["package_option"]["tnc"])
            validity = main_package_detail["package_option"]["validity"]

            option_name = main_package_detail.get("package_option", {}).get("name","") #Vidio
            family_name = main_package_detail.get("package_family", {}).get("name","") #Unlimited Turbo
            variant_name = main_package_detail.get("package_detail_variant", "").get("name","") #For Xtra Combo
            option_name = main_package_detail.get("package_option", {}).get("name","") #Vidio
            
            title = f"{family_name} - {variant_name} - {option_name}".strip()
            
            family_code = main_package_detail.get("package_family", {}).get("package_family_code","")
            parent_code = main_package_detail.get("package_addon", {}).get("parent_code","")
            if parent_code == "":
                parent_code = "N/A"
            
            payment_for = main_package_detail["package_family"]["payment_for"]
                
            print(f"Nama: {title}")
            print(f"Harga: Rp {price}")
            print(f"Payment For: {payment_for}")
            print(f"Masa Aktif: {validity}")
            print(f"Point: {main_package_detail['package_option']['point']}")
            print(f"Plan Type: {main_package_detail['package_family']['plan_type']}")
            print("-" * WIDTH)
            print(f"Family Code: {family_code}")
            print(f"Parent Code (for addon/dummy): {parent_code}")
            print("-" * WIDTH)
            benefits = main_package_detail["package_option"]["benefits"]
            if benefits and isinstance(benefits, list):
                print("Benefits:")
                for benefit in benefits:
                    print("-" * WIDTH)
                    print(f" Name: {benefit['name']}")
                    print(f"  Item id: {benefit['item_id']}")
                    data_type = benefit['data_type']
                    if data_type == "VOICE" and benefit['total'] > 0:
                        print(f"  Total: {benefit['total']/60} menit")
                    elif data_type == "TEXT" and benefit['total'] > 0:
                        print(f"  Total: {benefit['total']} SMS")
                    elif data_type == "DATA" and benefit['total'] > 0:
                        if benefit['total'] > 0:
                            quota = int(benefit['total'])
                            quota_formatted = format_quota_byte(quota)
                            print(f"  Total: {quota_formatted} ({data_type})")
                    elif data_type not in ["DATA", "VOICE", "TEXT"]:
                        print(f"  Total: {benefit['total']} ({data_type})")
                    
                    if benefit["is_unlimited"]:
                        print("  Unlimited: Yes")

            print("-" * WIDTH)
            print(f"SnK MyXL:\n{detail}")
            print("-" * WIDTH)
                
            print("=" * WIDTH)
            
            payment_for = selected_package.get("payment_for", "BUY_PACKAGE")
            ask_overwrite = selected_package.get("ask_overwrite", False)
            overwrite_amount = selected_package.get("overwrite_amount", -1)
            token_confirmation_idx = selected_package.get("token_confirmation_idx", 0)
            amount_idx = selected_package.get("amount_idx", -1)

            in_payment_menu = True
            while in_payment_menu:
                print("Pilih Metode Pembelian:")
                print("1. Balance")
                print("2. E-Wallet")
                print("3. QRIS")
                print("00. Kembali ke menu sebelumnya")
                
                input_method = input("Pilih metode (nomor): ")
                if input_method == "1":
                    if overwrite_amount == -1:
                        print(f"Pastikan sisa balance KURANG DARI Rp{payment_items[-1]['item_price']}!!!")
                        balance_answer = input("Apakah anda yakin ingin melanjutkan pembelian? (y/n): ")
                        if balance_answer.lower() != "y":
                            print("Pembelian dibatalkan oleh user.")
                            pause()
                            in_payment_menu = False
                            continue

                    settlement_balance(
                        api_key,
                        tokens,
                        payment_items,
                        payment_for,
                        ask_overwrite,
                        overwrite_amount=overwrite_amount,
                        token_confirmation_idx=token_confirmation_idx,
                        amount_idx=amount_idx,
                    )
                    input("Tekan enter untuk kembali...")
                    in_payment_menu = False
                    in_bookmark_menu = False
                elif input_method == "2":
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
                    input("Tekan enter untuk kembali...")
                    in_payment_menu = False
                    in_bookmark_menu = False
                elif input_method == "3":
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

                    input("Tekan enter untuk kembali...")
                    in_payment_menu = False
                    in_bookmark_menu = False
                elif input_method == "00":
                    in_payment_menu = False
                    continue
                else:
                    print("Metode tidak valid. Silahkan coba lagi.")
                    pause()
                    continue
        else:
            print("Input tidak valid. Silahkan coba lagi.")
            pause()
            continue
