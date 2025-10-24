from rich.prompt import Prompt
from app.menus.account import show_account_menu
from app.menus.package import fetch_my_packages, get_packages_by_family, show_package_details
from app.menus.hot import show_hot_menu, show_hot_menu2
from app.menus.payment import show_transaction_history
from app.menus.purchase import purchase_by_family
from app.menus.famplan import show_family_info
from app.menus.circle import show_circle_info
from app.menus.notification import show_notification_menu
from app.menus.store.segments import show_store_segments_menu
from app.menus.store.search import show_family_list_menu, show_store_packages_menu
from app.menus.family_grup import show_family_menu
from app.menus.theme import show_theme_menu
from app.menus.donate import show_donate_menu
from app.menus.bookmark import show_bookmark_menu
from app.service.sentry import enter_sentry_mode
from app.service.auth import AuthInstance
from rich.console import Console

console = Console()

def dispatch(choice, ctx):
    match choice:
        case "1":
            selected = show_account_menu()
            if selected: AuthInstance.set_active_user(selected)
        case "2": fetch_my_packages()
        case "3": show_hot_menu()
        case "4": show_hot_menu2()
        case "5":
            code = Prompt.ask("📮 Option code (99 untuk batal)")
            if code != "99": show_package_details(ctx["api_key"], ctx["tokens"], code, False)
        case "6":
            code = Prompt.ask("📁 Family code (99 untuk batal)")
            if code != "99": get_packages_by_family(code)
        case "7":
            code = Prompt.ask("🔁 Family code (99 untuk batal)")
            if code == "99": return
            start = int(Prompt.ask("Mulai dari option ke", default="1"))
            decoy = Prompt.ask("Gunakan decoy? (y/n)", default="n").lower() == "y"
            pause = Prompt.ask("Pause tiap sukses? (y/n)", default="n").lower() == "y"
            delay = int(Prompt.ask("Delay antar pembelian (detik)", default="0"))
            purchase_by_family(code, decoy, pause, delay, start)
        case "8": show_family_menu()
        case "9": show_family_info(ctx["api_key"], ctx["tokens"])
        case "10": show_circle_info(ctx["api_key"], ctx["tokens"])
        case "11":
            ent = Prompt.ask("Enterprise store? (y/n)", default="n").lower() == "y"
            show_store_segments_menu(ent)
        case "12":
            ent = Prompt.ask("Enterprise? (y/n)", default="n").lower() == "y"
            show_family_list_menu(ctx["subscription_type"], ent)
        case "13":
            ent = Prompt.ask("Enterprise? (y/n)", default="n").lower() == "y"
            show_store_packages_menu(ctx["subscription_type"], ent)
        case "77": show_donate_menu()
        case "88": show_theme_menu()
        case "00": show_bookmark_menu()
        case "99":
            console.print("[bold red]⛔ Keluar dari aplikasi.[/bold red]")
            exit()
        case "n": show_notification_menu()
        case "s": enter_sentry_mode()
        case _:
