import io
import qrcode
from rich.console import Console
from rich.panel import Panel
from rich.align import Align
from rich.text import Text
from app.menus.util import clear_screen, pause
from app.menus.util_helper import live_loading
from app.config.theme_config import get_theme

console = Console()


def generate_qr_ascii(data: str) -> str:
    qr = qrcode.QRCode(border=1)
    qr.add_data(data)
    qr.make(fit=True)
    output = io.StringIO()
    qr.print_ascii(out=output, invert=True)
    return output.getvalue()

def show_donate_menu():
    clear_screen()
    theme = get_theme()
    qris_url = (
        "00020101021126570011ID.DANA.WWW011893600915324993094502092499309450303UMI"
        "51440014ID.CO.QRIS.WWW0215ID10254398087220303UMI5204541153033605802ID5908BarbexID"
        "6004011361054646563047A81"
    )

    with live_loading("Menyiapkan QRIS...", theme):
        qr_code_ascii = generate_qr_ascii(qris_url)

    donate_info = Text()
    donate_info.append("Dukung Pengembangan MyXL CLI!\n\n", style=f"{theme['text_title']} bold")
    donate_info.append(
        "Jika Anda butuh Kode Unlock untuk menambahkan lebih banyak akun, hubungi saya di Telegram (@barbex_id), tebus seikhlasnya 😁\n\n",
        style=theme["text_body"]
    )
    donate_info.append(
        "Dan jika ingin memberikan donasi untuk mendukung pengembangan tool ini, silakan gunakan metode berikut:\n\n",
        style=theme["text_body"]
    )
    donate_info.append("- Dana: 0831-1921-5545\n", style=theme["text_body"])
    donate_info.append("  A/N Joko S\n", style=theme["text_body"])
    donate_info.append("- QRIS tersedia di bawah\n\n", style=theme["text_body"])
    donate_info.append("Terima kasih atas dukungan Anda! 🙏", style=theme["text_sub"])

    console.print(Panel(
        Align.left(donate_info),
        title=f"[{theme['text_title']}]💰 Donasi Seikhlasnya[/]",
        border_style=theme["border_success"],
        padding=(1, 2),
        expand=True,
        title_align="center"
    ))

    console.print(Panel(
        Align.center(qr_code_ascii),
        title=f"[{theme['text_title']}]📱 Scan QRIS[/]",
        border_style=theme["border_info"],
        padding=(1, 2),
        expand=True,
        title_align="center"
    ))

    pause()
