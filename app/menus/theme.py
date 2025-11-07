from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.align import Align
from rich.box import MINIMAL_DOUBLE_HEAD

from app.config.theme_config import get_theme, get_all_presets, set_theme
from app.menus.util import clear_screen, pause, print_panel

console = Console()

def show_theme_menu():
    while True:
        clear_screen()
        theme = get_theme()
        presets = get_all_presets()
        theme_names = list(presets.keys())

        # Header panel
        console.print(Panel(
            Align.center("🎨 Pilih Tema CLI", vertical="middle"),
            style=theme["text_title"],
            border_style=theme["border_info"],
            padding=(1, 2),
            expand=True,
        ))

        # Tabel daftar tema
        table = Table(box=MINIMAL_DOUBLE_HEAD, expand=True)
        table.add_column("No", justify="right", style=theme["text_number"], width=6)
        table.add_column("Nama Tema", style=theme["text_body"])
        table.add_column("Preview", justify="left")

        for idx, name in enumerate(theme_names, start=1):
            preset = presets[name]
            preview = (
                f"[{preset['border_primary']}]■[/] "
                f"[{preset['border_info']}]■[/] "
                f"[{preset['border_success']}]■[/] "
                f"[{preset['border_warning']}]■[/] "
                f"[{preset['border_error']}]■[/]"
            )
            table.add_row(str(idx), name.replace("_", " ").title(), preview)

        console.print(Panel(table, border_style=theme["border_primary"], padding=(0, 0), expand=True))

        # Navigasi
        nav_table = Table(show_header=False, box=MINIMAL_DOUBLE_HEAD, expand=True)
        nav_table.add_column(justify="right", style=theme["text_key"], width=4)
        nav_table.add_column(style=theme["text_body"])
        nav_table.add_row("00", f"[{theme['text_sub']}]Kembali ke menu utama[/]")

        console.print(Panel(nav_table, border_style=theme["border_info"], padding=(0, 1), expand=True))

        # Input pilihan
        choice = console.input(f"[{theme['text_sub']}]Pilih nomor tema:[/{theme['text_sub']}] ").strip()

        if choice == "00":
            return

        if choice.isdigit() and 1 <= int(choice) <= len(theme_names):
            selected_theme = theme_names[int(choice) - 1]
            selected_preset = presets[selected_theme]

            # Preview tema sebelum konfirmasi
            preview_panel = Panel(
                Align.center(f"Preview Tema: {selected_theme.replace('_', ' ').title()}"),
                border_style=selected_preset["border_primary"],
                style=selected_preset["text_title"],
                padding=(1, 2),
                expand=True
            )
            console.print(preview_panel)

            confirm = console.input(
                f"[{theme['text_sub']}]Gunakan tema '{selected_theme.replace('_', ' ').title()}'? (y/n):[/{theme['text_sub']}] "
            ).strip().lower()

            if confirm == "y":
                set_theme(selected_theme)
                theme = get_theme(force_reload=True)
                print_theme_changed(selected_theme)
                pause()
                return
        else:
            print_panel("⚠️ Error", "Pilihan tidak valid.")
            pause()

def print_theme_changed(theme_name):
    theme = get_theme()
    terminal_width = console.size.width
    message_text = (
        f"[{theme['text_ok']}]✅ Tema Diubah[/]\n"
        f"[{theme['text_sub']}]Tema sekarang: {theme_name.replace('_', ' ').title()}[/]"
    )
    panel = Panel(
        Align.left(message_text),
        title="",
        title_align="left",
        style=theme["border_success"],
        width=terminal_width
    )
    console.print(panel)
