from rich.panel import Panel
from rich.align import Align
from app.theme import _c, console
from app.menus.util import pause, clear_screen
import qrcode
import io

def show_donate_menu():
    clear_screen()
    qris_url = "https://link.dana.id/minta?full_url=https://qr.dana.id/v1/281012012022051849509828"
    
    qr = qrcode.QRCode(border=1)
    qr.add_data(qris_url)
    qr.make(fit=True)
    qr_ascii = io.StringIO()
    qr.print_ascii(out=qr_ascii)
    qr_code_ascii = qr_ascii.getvalue()
    
    donate_text = (
        f"[{_c('text_title')} bold]Dukung Pengembangan MyXL CLI![/]\n\n"
        f"Jika Anda ingin memberikan donasi untuk mendukung pengembangan tool ini, silakan gunakan salah satu metode berikut:\n\n"
        f"[{_c('text_body')}]"
        f"- Dana: 0831-1921-5545\n"
        f"   A/N Joko S\n"
        #f"- QRIS: {qris_url}\n"
        f"Terima kasih atas dukungan Anda![/]"
    )
    panel = Panel(
        Align.center(donate_text),
        title=f"[{_c('text_title')}]💰 Paket Berdonasi Seikhlasnya 🗿[/]",
        border_style=_c("border_success"),
        padding=(1, 1),
        expand=True,
        title_align="center"
    )
    # Print QR code 
    console.print(panel)
    console.print(qr_code_ascii)
    pause()
