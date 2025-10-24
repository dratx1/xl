from dotenv import load_dotenv
load_dotenv()

import sys
from rich.console import Console
from rich.prompt import Prompt
from app.service.auth import AuthInstance
from cli.context import get_user_context
from cli.menu import show_main_menu
from cli.dispatcher import dispatch

console = Console()

def main():
    while True:
        user = AuthInstance.get_active_user()
        if not user:
            selected = Prompt.ask("🔐 Masukkan nomor akun (atau kosong untuk keluar)")
            if selected:
                AuthInstance.set_active_user(selected)
            else:
                console.print("[bold red]⛔ Tidak ada akun aktif. Keluar.[/bold red]")
                sys.exit(0)
            continue

        ctx = get_user_context()
        if not ctx:
            console.print("[bold red]⚠️ Gagal mengambil data akun.[/bold red]")
            continue

        show_main_menu(ctx)
        choice = Prompt.ask("🎯 Pilih menu").strip().lower()
        dispatch(choice, ctx)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        console.print("\n[bold red]⛔ Keluar dari aplikasi.[/bold red]")
        sys.exit(0)
