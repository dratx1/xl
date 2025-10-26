import requests, time
from random import randint
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.align import Align
from rich.box import MINIMAL_DOUBLE_HEAD

from app.client.engsel import get_family, get_package_details
from app.menus.util import pause, clear_screen
from app.service.auth import AuthInstance
from app.type_dict import PaymentItem
from app.client.balance import settlement_balance
from app.config.theme_config import get_theme
from app.menus.util_helper import print_panel, get_rupiah

console = Console()

def purchase_by_family(
    family_code: str,
    use_decoy: bool,
    pause_on_success: bool = True,
    delay_seconds: int = 0,
    start_from_option: int = 1,
):
    theme = get_theme()
    api_key = AuthInstance.api_key
    tokens = AuthInstance.get_active_tokens() or {}

    if use_decoy:
        try:
            response = requests.get("https://me.mashu.lol/pg-decoy-xcp.json", timeout=30)
            response.raise_for_status()
            decoy_data = response.json()
            decoy_detail = get_package_details(
                api_key, tokens,
                decoy_data["family_code"],
                decoy_data["variant_code"],
                decoy_data["order"],
                decoy_data["is_enterprise"],
                decoy_data["migration_type"]
            )
            threshold = decoy_detail["package_option"]["price"]
            console.print(Panel(
                f"⚠️ Pastikan sisa balance KURANG DARI Rp{get_rupiah(threshold)}!",
                border_style=theme["border_warning"]
            ))
            confirm = console.input("Lanjutkan pembelian? (y/n): ").strip().lower()
            if confirm != "y":
                print_panel("ℹ️ Info", "Pembelian dibatalkan oleh pengguna.")
                pause()
                return
        except Exception as e:
            print_panel("⚠️ Error", f"Gagal mengambil data decoy: {e}")
            pause()
            return

    family_data = get_family(api_key, tokens, family_code)
    if not family_data:
        print_panel("⚠️ Error", f"Gagal mengambil data family: {family_code}")
        pause()
        return

    family_name = family_data["package_family"]["name"]
    variants = family_data["package_variants"]

    successful = []
    total_options = sum(len(v["package_options"]) for v in variants)
    purchase_count = 0
    start_buying = start_from_option <= 1

    for variant in variants:
        variant_name = variant["name"]
        for option in variant["package_options"]:
            tokens = AuthInstance.get_active_tokens()
            order = option["order"]
            if not start_buying and order == start_from_option:
                start_buying = True
            if not start_buying:
                console.print(f"[{theme['text_sub']}]Lewati opsi {order}: {option['name']}[/{theme['text_sub']}]")
                continue

            purchase_count += 1
            console.print(Panel(
                f"🛒 Pembelian {purchase_count} dari {total_options}\n"
                f"{variant_name} - {order}. {option['name']} - Rp{get_rupiah(option['price'])}",
                border_style=theme["border_info"]
            ))

            try:
                if use_decoy:
                    decoy_detail = get_package_details(
                        api_key, tokens,
                        decoy_data["family_code"],
                        decoy_data["variant_code"],
                        decoy_data["order"],
                        decoy_data["is_enterprise"],
                        decoy_data["migration_type"]
                    )

                target_detail = get_package_details(
                    api_key, tokens,
                    family_code,
                    variant["package_variant_code"],
                    order,
                    None, None
                )
            except Exception as e:
                print_panel("⚠️ Error", f"Gagal mengambil detail paket: {e}")
                continue

            payment_items = [
                PaymentItem(
                    item_code=target_detail["package_option"]["package_option_code"],
                    product_type="",
                    item_price=target_detail["package_option"]["price"],
                    item_name=f"{randint(1000,9999)} {target_detail['package_option']['name']}",
                    tax=0,
                    token_confirmation=target_detail["token_confirmation"]
                )
            ]

            if use_decoy:
                payment_items.append(PaymentItem(
                    item_code=decoy_detail["package_option"]["package_option_code"],
                    product_type="",
                    item_price=decoy_detail["package_option"]["price"],
                    item_name=f"{randint(1000,9999)} {decoy_detail['package_option']['name']}",
                    tax=0,
                    token_confirmation=decoy_detail["token_confirmation"]
                ))

            overwrite_amount = target_detail["package_option"]["price"]
            if use_decoy or overwrite_amount == 0:
                overwrite_amount += decoy_detail["package_option"]["price"]

            try:
                res = settlement_balance(
                    api_key, tokens, payment_items,
                    "🤑", False,
                    overwrite_amount=overwrite_amount,
                    token_confirmation_idx=1
                )

                if res and res.get("status") != "SUCCESS":
                    msg = res.get("message", "")
                    if "Bizz-err.Amount.Total" in msg:
                        try:
                            valid_amount = int(msg.split("=")[1].strip())
                            console.print(f"[{theme['text_sub']}]Menyesuaikan jumlah ke: Rp{get_rupiah(valid_amount)}[/{theme['text_sub']}]")
                            res = settlement_balance(
                                api_key, tokens, payment_items,
                                "SHARE_PACKAGE", False,
                                overwrite_amount=valid_amount,
                                token_confirmation_idx=-1
                            )
                        except:
                            print_panel("⚠️ Error", "Gagal parsing jumlah dari pesan error.")
                            continue

                if res and res.get("status") == "SUCCESS":
                    successful.append(f"{variant_name}|{order}. {option['name']} - Rp{get_rupiah(option['price'])}")
                    print_panel("✅ Sukses", "Pembelian berhasil.")
                    if pause_on_success:
                        pause()
                else:
                    print_panel("⚠️ Gagal", res.get("message", "Transaksi gagal."))
            except Exception as e:
                print_panel("⚠️ Error", f"Exception saat pembelian: {e}")

            if delay_seconds > 0:
                console.print(f"[{theme['text_sub']}]Menunggu {delay_seconds} detik sebelum lanjut...[/{theme['text_sub']}]")
                time.sleep(delay_seconds)

    console.print(Panel(
        f"📦 Family: [bold]{family_name}[/]\n"
        f"✅ Berhasil: {len(successful)} dari {total_options}",
        border_style=theme["border_success"],
        padding=(1, 2),
        expand=True
    ))

    if successful:
        result_table = Table(title="Daftar Pembelian Berhasil", box=MINIMAL_DOUBLE_HEAD, expand=True)
        result_table.add_column("No", justify="right", style=theme["text_key"], width=4)
        result_table.add_column("Paket", style=theme["text_body"])
        for idx, item in enumerate(successful, start=1):
            result_table.add_row(str(idx), item)
        console.print(result_table)

    pause()


import requests, time
from random import randint
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.align import Align
from rich.box import MINIMAL_DOUBLE_HEAD

from app.client.engsel import get_family, get_package_details
from app.menus.util import pause
from app.service.auth import AuthInstance
from app.type_dict import PaymentItem
from app.client.balance import settlement_balance
from app.config.theme_config import get_theme
from app.menus.util_helper import print_panel, get_rupiah

console = Console()

def purchase_n_times(
    n: int,
    family_code: str,
    variant_code: str,
    option_order: int,
    use_decoy: bool,
    delay_seconds: int = 0,
    pause_on_success: bool = False,
    token_confirmation_idx: int = 0,
):
    theme = get_theme()
    api_key = AuthInstance.api_key
    tokens = AuthInstance.get_active_tokens() or {}

    decoy_detail = None
    if use_decoy:
        try:
            response = requests.get("https://me.mashu.lol/pg-decoy-xcp.json", timeout=30)
            response.raise_for_status()
            decoy_data = response.json()
            decoy_detail = get_package_details(
                api_key, tokens,
                decoy_data["family_code"],
                decoy_data["variant_code"],
                decoy_data["order"],
                decoy_data["is_enterprise"],
                decoy_data["migration_type"]
            )
            threshold = decoy_detail["package_option"]["price"]
            console.print(Panel(
                f"⚠️ Pastikan sisa balance KURANG DARI Rp{get_rupiah(threshold)}!",
                border_style=theme["border_warning"]
            ))
            confirm = console.input("Lanjutkan pembelian? (y/n): ").strip().lower()
            if confirm != "y":
                print_panel("ℹ️ Info", "Pembelian dibatalkan oleh pengguna.")
                pause()
                return
        except Exception as e:
            print_panel("⚠️ Error", f"Gagal mengambil data decoy: {e}")
            pause()
            return

    family_data = get_family(api_key, tokens, family_code)
    if not family_data:
        print_panel("⚠️ Error", f"Gagal mengambil data family: {family_code}")
        pause()
        return

    family_name = family_data["package_family"]["name"]
    variants = family_data["package_variants"]
    target_variant = next((v for v in variants if v["package_variant_code"] == variant_code), None)
    if not target_variant:
        print_panel("⚠️ Error", f"Variant {variant_code} tidak ditemukan di family {family_name}")
        pause()
        return

    target_option = next((o for o in target_variant["package_options"] if o["order"] == option_order), None)
    if not target_option:
        print_panel("⚠️ Error", f"Opsi {option_order} tidak ditemukan di variant {target_variant['name']}")
        pause()
        return

    option_name = target_option["name"]
    option_price = target_option["price"]
    successful = []

    for i in range(n):
        console.print(Panel(
            f"🛒 Pembelian {i + 1} dari {n}\n"
            f"{target_variant['name']} - {option_order}. {option_name} - Rp{get_rupiah(option_price)}",
            border_style=theme["border_info"]
        ))

        tokens = AuthInstance.get_active_tokens() or {}
        try:
            target_detail = get_package_details(
                api_key, tokens,
                family_code,
                target_variant["package_variant_code"],
                target_option["order"],
                None, None
            )
        except Exception as e:
            print_panel("⚠️ Error", f"Gagal mengambil detail paket: {e}")
            continue

        payment_items = [
            PaymentItem(
                item_code=target_detail["package_option"]["package_option_code"],
                product_type="",
                item_price=target_detail["package_option"]["price"],
                item_name=f"{randint(1000,9999)} {target_detail['package_option']['name']}",
                tax=0,
                token_confirmation=target_detail["token_confirmation"]
            )
        ]

        if use_decoy and decoy_detail:
            payment_items.append(PaymentItem(
                item_code=decoy_detail["package_option"]["package_option_code"],
                product_type="",
                item_price=decoy_detail["package_option"]["price"],
                item_name=f"{randint(1000,9999)} {decoy_detail['package_option']['name']}",
                tax=0,
                token_confirmation=decoy_detail["token_confirmation"]
            ))

        overwrite_amount = target_detail["package_option"]["price"]
        if use_decoy:
            overwrite_amount += decoy_detail["package_option"]["price"]

        try:
            res = settlement_balance(
                api_key, tokens, payment_items,
                "🤫", False,
                overwrite_amount=overwrite_amount,
                token_confirmation_idx=token_confirmation_idx
            )

            if res and res.get("status") != "SUCCESS":
                msg = res.get("message", "")
                if "Bizz-err.Amount.Total" in msg:
                    try:
                        valid_amount = int(msg.split("=")[1].strip())
                        console.print(f"[{theme['text_sub']}]Menyesuaikan jumlah ke: Rp{get_rupiah(valid_amount)}[/{theme['text_sub']}]")
                        res = settlement_balance(
                            api_key, tokens, payment_items,
                            "🤫", False,
                            overwrite_amount=valid_amount,
                            token_confirmation_idx=token_confirmation_idx
                        )
                    except:
                        print_panel("⚠️ Error", "Gagal parsing jumlah dari pesan error.")
                        continue

            if res and res.get("status") == "SUCCESS":
                successful.append(f"{target_variant['name']}|{option_order}. {option_name} - Rp{get_rupiah(option_price)}")
                print_panel("✅ Sukses", "Pembelian berhasil.")
                if pause_on_success:
                    pause()
            else:
                print_panel("⚠️ Gagal", res.get("message", "Transaksi gagal."))
        except Exception as e:
            print_panel("⚠️ Error", f"Exception saat pembelian: {e}")

        if delay_seconds > 0 and i < n - 1:
            console.print(f"[{theme['text_sub']}]Menunggu {delay_seconds} detik sebelum lanjut...[/{theme['text_sub']}]")
            time.sleep(delay_seconds)

    console.print(Panel(
        f"📦 Family: [bold]{family_name}[/]\n"
        f"✅ Berhasil: {len(successful)} dari {n}",
        border_style=theme["border_success"],
        padding=(1, 2),
        expand=True
    ))

    if successful:
        result_table = Table(title="Daftar Pembelian Berhasil", box=MINIMAL_DOUBLE_HEAD, expand=True)
        result_table.add_column("No", justify="right", style=theme["text_key"], width=4)
        result_table.add_column("Paket", style=theme["text_body"])
        for idx, item in enumerate(successful, start=1):
            result_table.add_row(str(idx), item)
        console.print(result_table)

    pause()
    return True
