import os
import re
import textwrap
from html.parser import HTMLParser
from datetime import datetime
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.align import Align
from rich import box
from app.config.theme_config import get_theme, get_theme_style
from app.service.auth import AuthInstance
import app.menus.banner as banner

console = Console()
ascii_art = banner.load("https://me.mashu.lol/mebanner890.png", globals())
ascii_art = banner.load("https://d17e22l2uh4h4n.cloudfront.net/corpweb/pub-xlaxiata/2019-03/xl-logo.png", globals())

def clear_screen():
    try:
        os.system('cls' if os.name == 'nt' else 'clear')
    except Exception:
        print("\n" * 100)

    if ascii_art:
        try:
            ascii_art.to_terminal(columns=55)
        except Exception:
            pass

def pause():
    input("\nTekan Enter untuk melanjutkan...")

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
        text = "".join(self.result)
        text = re.sub(r"\n\s*\n\s*\n+", "\n\n", text)
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

def nav_range(label: str, count: int) -> str:
    if count <= 0:
        return f"{label} (tidak tersedia)"
    if count == 1:
        return f"{label} 1"
    return f"{label} 1–{count}"

def live_loading(text: str, theme: dict):
    return console.status(f"[{theme['text_sub']}]{text}[/{theme['text_sub']}]", spinner="dots")

def show_simple_number_panel():
    theme = get_theme()
    active_user = AuthInstance.get_active_user()

    if not active_user:
        text = f"[bold {get_theme_style('text_err')}]Tidak ada akun aktif saat ini.[/]"
    else:
        number = active_user.get("number", "-")
        text = f"[bold {get_theme_style('text_body')}]Akun yang sedang aktif ✨ {number} ✨[/]"

    console.print(Panel(
        Align.center(text),
        border_style=get_theme_style("border_warning"),
        padding=(0, 0),
        expand=True
    ))

def print_panel(title, content, border_style=None):
    style = border_style or get_theme_style("border_info")
    console.print(Panel(content, title=title, title_align="left", border_style=style))

def print_success(title, content):
    console.print(Panel(content, title=title, title_align="left", border_style=get_theme_style("border_success")))

def print_error(title, content):
    console.print(Panel(content, title=title, title_align="left", border_style=get_theme_style("border_error")))

def print_warning(title, content):
    console.print(Panel(content, title=title, title_align="left", border_style=get_theme_style("border_warning")))

def print_title(text):
    console.print(Panel(
        Align.center(f"[bold {get_theme_style('text_title')}]{text}[/{get_theme_style('text_title')}]"),
        border_style=get_theme_style("border_primary"),
        padding=(0, 1),
        expand=True
    ))

def print_key_value(label, value):
    console.print(f"[{get_theme_style('text_key')}]{label}:[/] [{get_theme_style('text_value')}]{value}[/{get_theme_style('text_value')}]")

def print_info(label, value):
    console.print(f"[{get_theme_style('text_sub')}]{label}:[/{get_theme_style('text_sub')}] [{get_theme_style('text_body')}]{value}[/{get_theme_style('text_body')}]")

def print_menu(title, options):
    table = Table(title=title, box=box.SIMPLE, show_header=False)
    for key, label in options.items():
        table.add_row(f"[{get_theme_style('text_key')}]{key}[/{get_theme_style('text_key')}]", f"[{get_theme_style('text_value')}]{label}[/{get_theme_style('text_value')}]")
    console.print(table)
