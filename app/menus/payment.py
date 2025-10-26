from datetime import datetime, timedelta
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.align import Align
from rich.box import MINIMAL_DOUBLE_HEAD

from app.client.engsel2 import get_transaction_history
from app.menus.util import clear_screen, pause
from app.config.theme_config import get_theme
from app.menus.util_helper import print_panel, get_rupiah

console = Console()

def show_transaction_history(api_key, tokens):
    theme = get_theme()
    in_transaction_menu = True

    while in_transaction_menu:
        clear_screen()
        theme = get_theme()

        console.print(Panel(
            Align.center("📜 Riwayat Transaksi", vertical="middle"),
            border_style=theme["border_info"],
            padding=(1, 2),
            expand=True
        ))

        try:
            data = get_transaction_history(api_key, tokens)
            history = data.get("list", [])
        except Exception as e:
            print_panel("⚠️ Error", f"Gagal mengambil riwayat transaksi:\n{e}")
            pause()
            return

        if not history:
            print_panel("ℹ️ Info", "Tidak ada riwayat transaksi.")
            pause()
            return

        table = Table(show_header=True, box=MINIMAL_DOUBLE_HEAD, expand=True)
        table.add_column("No", justify="right", style=theme["text_key"], width=4)
        table.add_column("Judul", style=theme["text_body"])
        table.add_column("Harga", justify="right", style=theme["text_money"], width=12)
        table.add_column("Waktu", style=theme["text_sub"], justify="right")
        table.add_column("Metode", style=theme["text_body"])
        table.add_column("Status", style=theme["text_sub"])
        table.add_column("Bayar", style=theme["text_sub"])

        for idx, tx in enumerate(history, start=1):
            ts = tx.get("timestamp", 0)
            dt = datetime.fromtimestamp(ts) - timedelta(hours=7)
            formatted_time = dt.strftime("%d %b %Y %H:%M WIB")

            table.add_row(
                str(idx),
                tx.get("title", "-"),
                get_rupiah(tx.get("price", 0)),
                formatted_time,
                tx.get("payment_method_label", "-"),
                tx.get("status", "-"),
                tx.get("payment_status", "-")
            )

        console.print(Panel(table, border_style=theme["border_primary"], padding=(0, 1), expand=True))

        nav_table = Table(show_header=False, box=MINIMAL_DOUBLE_HEAD, expand=True)
        nav_table.add_column(justify="right", style=theme["text_key"], width=4)
        nav_table.add_column(style=theme["text_body"])
        nav_table.add_row("0", "🔄 Refresh")
        nav_table.add_row("00", f"[{theme['text_sub']}]Kembali ke menu utama[/]")

        console.print(Panel(nav_table, border_style=theme["border_info"], padding=(0, 1), expand=True))

        choice = console.input(f"[{theme['text_sub']}]Pilih opsi:[/{theme['text_sub']}] ").strip()
        if choice == "0":
            continue
        elif choice == "00":
            in_transaction_menu = False
        else:
            print_panel("⚠️ Error", "Opsi tidak valid. Silakan coba lagi.")
            pause()
