from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.align import Align
from rich.box import MINIMAL_DOUBLE_HEAD

from app.menus.util import clear_screen, pause
from app.client.engsel import get_notifications, get_notification_detail
from app.service.auth import AuthInstance
from app.config.theme_config import get_theme
from app.menus.util_helper import print_panel

console = Console()

def show_notification_menu():
    theme = get_theme()
    api_key = AuthInstance.api_key
    tokens = AuthInstance.get_active_tokens()

    if not tokens:
        print_panel("⚠️ Error", "Token tidak tersedia. Silakan login ulang.")
        pause()
        return

    while True:
        clear_screen()
        console.print(Panel(Align.center("📨 Notifikasi"), border_style=theme["border_info"], padding=(1, 2)))

        notifications_res = get_notifications(api_key, tokens)
        if not notifications_res:
            print_panel("Info ℹ️ ", "Tidak ada notifikasi ditemukan.")
            pause()
            return

        notifications = notifications_res.get("data", {}).get("inbox", [])
        if not notifications:
            print_panel("Info ℹ️ ", "Belum ada notifikasi tersedia.")
            pause()
            return

        table = Table(show_header=True, box=MINIMAL_DOUBLE_HEAD, expand=True)
        table.add_column("No", justify="right", style=theme["text_key"], width=4)
        table.add_column("Status", style=theme["text_sub"], width=8)
        table.add_column("Pesan", style=theme["text_body"])
        table.add_column("Waktu", style=theme["text_body"], justify="right")

        unread_count = 0
        for idx, notif in enumerate(notifications):
            status = "✅" if notif.get("is_read") else "📬"
            if not notif.get("is_read"):
                unread_count += 1
            table.add_row(
                str(idx + 1),
                status,
                notif.get("brief_message", "") or notif.get("full_message", ""),
                notif.get("timestamp", "")
            )

        console.print(Panel(table, border_style=theme["border_primary"], padding=(0, 1), expand=True))
        console.print(Panel(
            f"Total: {len(notifications)} | Belum dibaca: {unread_count}",
            border_style=theme["border_info"],
            padding=(0, 1),
            expand=True
        ))

        nav_table = Table(show_header=False, box=MINIMAL_DOUBLE_HEAD, expand=True)
        nav_table.add_column(justify="right", style=theme["text_key"], width=4)
        nav_table.add_column(style=theme["text_body"])
        nav_table.add_row("1", "Tandai semua notifikasi sebagai telah dibaca")
        nav_table.add_row("00", f"[{theme['text_sub']}]Kembali ke menu utama[/]")

        console.print(Panel(nav_table, border_style=theme["border_info"], padding=(0, 1), expand=True))

        choice = console.input(f"[{theme['text_sub']}]Pilih opsi:[/{theme['text_sub']}] ").strip()
        if choice == "00":
            return
        elif choice == "1":
            for notif in notifications:
                if notif.get("is_read"):
                    continue
                notif_id = notif.get("notification_id")
                detail = get_notification_detail(api_key, tokens, notif_id)
                if detail:
                    console.print(f"[{theme['text_sub']}]✔️ Ditandai sebagai dibaca: {notif_id}[/{theme['text_sub']}]")
            console.input(f"[{theme['text_sub']}]Tekan enter untuk kembali...[/{theme['text_sub']}] ")
        else:
            print_panel("⚠️ Error", "Input tidak valid. Silakan coba lagi.")
            pause()
