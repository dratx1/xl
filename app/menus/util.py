import app.menus.banner as banner
ascii_art = banner.load("https://me.mashu.lol/mebanner890.png", globals())
ascii_art = banner.load("https://d17e22l2uh4h4n.cloudfront.net/corpweb/pub-xlaxiata/2019-03/xl-logo.png", globals())
from html.parser import HTMLParser
import os
import re
import textwrap
from datetime import datetime
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.align import Align
from rich import box
from app.config.theme_config import get_theme

console = Console()

def clear_screen():
    print("Clearing screen...")
    # user_info = get_user_info(load_api_key())
    os.system('cls' if os.name == 'nt' else 'clear')
    if ascii_art:
        ascii_art.to_terminal(columns=55)

    # if user_info:
    #     credit = user_info.get("credit", 0)
    #     premium_credit = user_info.get("premium_credit", 0)
        
    #     width = 55 
    #     print("=" * width)
    #     print(f" Credit: {credit} | Premium Credit: {premium_credit} ".center(width))
    #     print("=" * width)
    #     print("")
        

def pause():
    input("\nPress enter to continue...")

class HTMLToText(HTMLParser):
    def __init__(self, width=80):
        super().__init__()
        self.width = width
        self.result = []
        self.in_li = False

    def handle_starttag(self, tag, attrs):
        if tag == "li":
            self.in_li = True
        elif tag == "br":
            self.result.append("\n")

    def handle_endtag(self, tag):
        if tag == "li":
            self.in_li = False
            self.result.append("\n")

    def handle_data(self, data):
        text = data.strip()
        if text:
            if self.in_li:
                self.result.append(f"- {text}")
            else:
                self.result.append(text)

    def get_text(self):
        # Join and clean multiple newlines
        text = "".join(self.result)
        text = re.sub(r"\n\s*\n\s*\n+", "\n\n", text)
        # Wrap lines nicely
        return "\n".join(textwrap.wrap(text, width=self.width, replace_whitespace=False))

def display_html(html_text, width=80):
    parser = HTMLToText(width=width)
    parser.feed(html_text)
    return parser.get_text()

def format_quota_byte(quota_byte: int) -> str:
    GB = 1024 ** 3 
    MB = 1024 ** 2
    KB = 1024

    if quota_byte >= GB:
        return f"{quota_byte / GB:.2f} GB"
    elif quota_byte >= MB:
        return f"{quota_byte / MB:.2f} MB"
    elif quota_byte >= KB:
        return f"{quota_byte / KB:.2f} KB"
    else:
        return f"{quota_byte} B"

def get_rupiah(value) -> str:
    value_str = str(value).strip()
    value_str = re.sub(r"^Rp\s?", "", value_str)
    match = re.match(r"([\d,]+)(.*)", value_str)
    if not match:
        return value_str

    raw_number = match.group(1).replace(",", "")
    suffix = match.group(2).strip()

    try:
        number = int(raw_number)
    except ValueError:
        return value_str

    formatted_number = f"{number:,}".replace(",", ".")
    formatted = f"{formatted_number},-"
    return f"{formatted} {suffix}" if suffix else formatted

def live_loading(text: str, theme: dict):
    return console.status(f"[{theme['text_sub']}]{text}[/{theme['text_sub']}]", spinner="dots")

def show_simple_number_panel():
    theme = get_theme()
    active_user = AuthInstance.get_active_user()

    if not active_user:
        text = f"[bold {theme['text_err']}]Tidak ada akun aktif saat ini.[/]"
    else:
        number = active_user.get("number", "-")
        text = f"[bold {theme['text_body']}]Akun yang sedang aktif ✨ {number} ✨[/]"

    console.print(Panel(
        Align.center(text),
        border_style=theme["border_warning"],
        padding=(0, 0),
        expand=True
    ))

def print_panel(title, content, border_style=None):
    theme = get_theme()
    console = Console()
    style = border_style or theme["border_info"]
    console.print(Panel(content, title=title, title_align="left", border_style=style))


def print_menu(title, options):
    theme = get_theme()
    table = Table(title=title, box=box.SIMPLE, show_header=False)
    for key, label in options.items():
        table.add_row(f"[{theme['text_key']}]{key}[/{theme['text_key']}]", f"[{theme['text_value']}]{label}[/{theme['text_value']}]")
    console.print(table)

def print_info(label, value):
    theme = get_theme()
    console.print(f"[{theme['text_sub']}]{label}:[/{theme['text_sub']}] [{theme['text_body']}]{value}[/{theme['text_body']}]")
