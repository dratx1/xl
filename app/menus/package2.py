from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from rich.console import Console
from rich.box import MINIMAL_DOUBLE_HEAD
from app.config.theme_config import get_theme
from app.menus.util import clear_screen, pause, print_panel, get_rupiah
from app.service.auth import AuthInstance
from app.client.engsel import get_family, get_package_details
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

        # Panel info family
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

        # Tabel daftar paket
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
            padding=(0, 1),
            expand=True
        ))

        # Navigasi
        nav = Table(show_header=False, box=MINIMAL_DOUBLE_HEAD, expand=True)
        nav.add_column(justify="right", style=theme["text_key"], width=6)
        nav.add_column(style=theme["text_body"])
        nav.add_row("00", f"[{theme['text_sub']}]Kembali ke menu utama[/]")

        console.print(Panel(
            nav,
            border_style=theme["border_info"],
            padding=(0, 1),
            expand=True
        ))

        # Input
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
