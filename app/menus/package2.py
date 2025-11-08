from rich.console import Console, Group
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich.align import Align
from rich.box import MINIMAL_DOUBLE_HEAD
from app.config.theme_config import get_theme
from app.menus.util import clear_screen, pause, print_panel, get_rupiah, format_quota_byte, nav_range
from app.service.auth import AuthInstance
from app.client.engsel import get_family, get_package, send_api_request, unsubscribe
from app.menus.package import show_package_details

console = Console()


def get_packages_by_family(
    family_code: str,
    is_enterprise: bool | None = None,
    migration_type: str | None = None,
    return_package_detail: bool = False
):
    api_key = AuthInstance.api_key
    tokens = AuthInstance.get_active_tokens()
    theme = get_theme()

    if not tokens:
        print_panel("⚠️ Error", "Token pengguna aktif tidak ditemukan.")
        return "BACK"

    data = get_family(api_key, tokens, family_code, is_enterprise, migration_type)
    if not data:
        print_panel("⚠️ Error", "Gagal memuat data paket family.")
        return "BACK"

    price_currency = "Rp"
    if data["package_family"].get("rc_bonus_type") == "MYREWARDS":
        price_currency = "Poin"

    packages = []
    for variant in data["package_variants"]:
        for option in variant["package_options"]:
            packages.append({
                "number": len(packages) + 1,
                "variant_name": variant["name"],
                "option_name": option["name"],
                "price": option["price"],
                "code": option["package_option_code"],
                "option_order": option["order"]
            })

    while True:
        clear_screen()

        info_text = Text()
        info_text.append("Nama: ", style=theme["text_body"])
        info_text.append(f"{data['package_family']['name']}\n", style=theme["text_value"])
        info_text.append("Kode: ", style=theme["text_body"])
        info_text.append(f"{family_code}\n", style=theme["border_warning"])
        info_text.append("Tipe: ", style=theme["text_body"])
        info_text.append(f"{data['package_family']['package_family_type']}\n", style=theme["text_value"])
        info_text.append("Jumlah Varian: ", style=theme["text_body"])
        info_text.append(f"{len(data['package_variants'])}\n", style=theme["text_value"])

        console.print(Panel(
            info_text,
            title=f"[{theme['text_title']}]📦 Info Paket Family[/]",
            border_style=theme["border_info"],
            padding=(0, 2),
            expand=True
        ))

        table = Table(box=MINIMAL_DOUBLE_HEAD, expand=True)
        table.add_column("No", justify="right", style=theme["text_key"], width=4)
        table.add_column("Varian", style=theme["text_body"])
        table.add_column("Nama Paket", style=theme["text_body"])
        table.add_column("Harga", style=theme["text_money"], justify="right")

        for pkg in packages:
            harga_str = get_rupiah(pkg["price"]) if price_currency == "Rp" else f"{pkg['price']} Poin"
            table.add_row(
                str(pkg["number"]),
                pkg["variant_name"],
                pkg["option_name"],
                harga_str
            )

        console.print(Panel(
            table,
            border_style=theme["border_primary"],
            padding=(0, 0),
            expand=True
        ))

        nav = Table(show_header=False, box=MINIMAL_DOUBLE_HEAD, expand=True)
        nav.add_column(justify="right", style=theme["text_key"], width=6)
        nav.add_column(style=theme["text_body"])
        nav.add_row("00", f"[{theme['text_sub']}]Kembali ke menu sebelumnya[/]")

        console.print(Panel(
            nav,
            border_style=theme["border_info"],
            padding=(0, 1),
            expand=True
        ))

        choice = console.input(f"[{theme['text_sub']}]Pilih paket (nomor):[/{theme['text_sub']}] ").strip()
        if choice == "00":
            return "BACK"
        if not choice.isdigit():
            print_panel("⚠️ Error", "Input tidak valid. Masukkan nomor paket.")
            pause()
            continue

        selected = next((p for p in packages if p["number"] == int(choice)), None)
        if not selected:
            print_panel("⚠️ Error", "Nomor paket tidak ditemukan.")
            pause()
            continue

        if return_package_detail:
            variant_code = next((v["package_variant_code"] for v in data["package_variants"] if v["name"] == selected["variant_name"]), None)
            detail = get_package_details(
                api_key, tokens,
                family_code,
                variant_code,
                selected["option_order"],
                is_enterprise
            )
            if detail:
                display_name = f"{data['package_family']['name']} - {selected['variant_name']} - {selected['option_name']}"
                return detail, display_name
            else:
                print_panel("⚠️ Error", "Gagal mengambil detail paket.")
                pause()
                continue
        else:
            result = show_package_details(
                api_key,
                tokens,
                selected["code"],
                is_enterprise,
                option_order=selected["option_order"]
            )
            if result == "MAIN":
                return "MAIN"
            elif result == "BACK":
                continue
            elif result is True:
                continue


def fetch_my_packages():
    theme = get_theme()
    api_key = AuthInstance.api_key
    tokens = AuthInstance.get_active_tokens()
    if not tokens:
        print_panel("❌ Error", "Token pengguna aktif tidak ditemukan.")
        pause()
        return "BACK"

    id_token = tokens.get("id_token")
    path = "api/v8/packages/quota-details"
    payload = {
        "is_enterprise": False,
        "lang": "en",
        "family_member_id": ""
    }

    with console.status("🔄 Mengambil paket aktif..."):
        res = send_api_request(api_key, path, payload, id_token, "POST")

    if res.get("status") != "SUCCESS":
        print_panel("❌ Error", "Gagal mengambil paket aktif.")
        pause()
        return "BACK"

    quotas = res["data"]["quotas"]
    if not quotas:
        print_panel("ℹ️ Info", "Tidak ada paket aktif ditemukan.")
        pause()
        return "BACK"

    while True:
        clear_screen()
        console.print(Panel(
            Align.center("📦 Paket Aktif Saya", vertical="middle"),
            border_style=theme["border_info"],
            padding=(1, 2),
            expand=True
        ))

        my_packages = []
        for num, quota in enumerate(quotas, start=1):
            quota_code = quota["quota_code"]
            group_code = quota["group_code"]
            group_name = quota["group_name"]
            quota_name = quota["name"]
            family_code = "N/A"

            product_subscription_type = quota.get("product_subscription_type", "")
            product_domain = quota.get("product_domain", "")

            benefits = quota.get("benefits", [])
            benefit_table = None
            if benefits:
                benefit_table = Table(box=MINIMAL_DOUBLE_HEAD, expand=True)
                benefit_table.add_column("Nama", style=theme["text_body"])
                benefit_table.add_column("Jenis", style=theme["text_body"])
                benefit_table.add_column("Kuota", style=theme["text_body"], justify="right")

                for b in benefits:
                    name = b.get("name", "")
                    dt = b.get("data_type", "N/A")
                    r = b.get("remaining", 0)
                    t = b.get("total", 0)

                    if dt == "DATA":
                        r_str = format_quota_byte(r)
                        t_str = format_quota_byte(t)
                    elif dt == "VOICE":
                        r_str = f"{r / 60:.2f} menit"
                        t_str = f"{t / 60:.2f} menit"
                    elif dt == "TEXT":
                        r_str = f"{r} SMS"
                        t_str = f"{t} SMS"
                    else:
                        r_str = str(r)
                        t_str = str(t)

                    benefit_table.add_row(name, dt, f"{r_str} / {t_str}")

            with console.status(f"🔍 Memuat detail paket #{num}..."):
                package_details = get_package(api_key, tokens, quota_code)
            if package_details:
                family_code = package_details["package_family"]["package_family_code"]

            package_text = Text()
            package_text.append(f"📦 Paket {num}\n", style="bold")
            package_text.append("Nama: ", style=theme["border_info"])
            package_text.append(f"{quota_name}\n", style=theme["text_sub"])
            package_text.append("Quota Code: ", style=theme["border_info"])
            package_text.append(f"{quota_code}\n", style=theme["text_body"])
            package_text.append("Family Code: ", style=theme["border_info"])
            package_text.append(f"{family_code}\n", style=theme["border_warning"])
            package_text.append("Group Code: ", style=theme["border_info"])
            package_text.append(f"{group_code}\n", style=theme["text_body"])

            panel_content = [package_text]
            if benefit_table:
                panel_content.append(benefit_table)

            console.print(Panel(
                Group(*panel_content),
                border_style=theme["border_primary"],
                padding=(0, 1),
                expand=True
            ))

            my_packages.append({
                "number": num,
                "name": quota_name,
                "quota_code": quota_code,
                "product_subscription_type": product_subscription_type,
                "product_domain": product_domain,
            })

        nav_table = Table(show_header=False, box=MINIMAL_DOUBLE_HEAD, expand=True)
        nav_table.add_column(justify="right", style=theme["text_key"], width=6)
        nav_table.add_column(style=theme["text_body"])
        nav_table.add_row("00", f"[{theme['text_sub']}]Kembali ke menu utama[/]")
        nav_table.add_row(nav_range("", len(my_packages)), "Lihat detail paket")
        nav_table.add_row(nav_range("del", len(my_packages)), f"[{theme['text_err']}]Unsubscribe dari paket[/]")

        console.print(Panel(
            nav_table,
            border_style=theme["border_info"],
            padding=(0, 1),
            expand=True
        ))

        choice = console.input(f"[{theme['text_sub']}]Pilihan:[/{theme['text_sub']}] ").strip()
        if choice == "00":
            return "BACK"

        if choice.isdigit():
            nomor = int(choice)
            selected = next((p for p in my_packages if p["number"] == nomor), None)
            if not selected:
                print_panel("❌ Error", "Nomor paket tidak ditemukan.")
                pause()
                continue
            show_package_details(api_key, tokens, selected["quota_code"], False)
            continue

        elif choice.startswith("del "):
            parts = choice.split(" ")
            if len(parts) != 2 or not parts[1].isdigit():
                print_panel("❌ Error", "Format perintah hapus tidak valid.")
                pause()
                continue

            nomor = int(parts[1])
            selected = next((p for p in my_packages if p["number"] == nomor), None)
            if not selected:
                print_panel("❌ Error", "Nomor paket tidak ditemukan.")
                pause()
                continue

            confirm = console.input(f"[{theme['text_sub']}]Yakin ingin unsubscribe dari paket {nomor}. {selected['name']}? (y/n):[/{theme['text_sub']}] ").strip().lower()
            if confirm == "y":
                with console.status("🔄 Menghapus paket..."):
                    success = unsubscribe(
                        api_key,
                        tokens,
                        selected["quota_code"],
                        selected["product_subscription_type"],
                        selected["product_domain"]
                    )
                print_panel("✅ Info" if success else "❌ Error", "Berhasil unsubscribe." if success else "Gagal unsubscribe.")
            else:
                print_panel("❎ Info", "Unsubscribe dibatalkan.")
            pause()
