from dotenv import load_dotenv
import app.menus.banner as banner
ascii_art = banner.load("https://me.mashu.lol/mebanner880.png", globals())
ascii_art = banner.load("https://d17e22l2uh4h4n.cloudfront.net/corpweb/pub-xlaxiata/2019-03/xl-logo.png", globals())
import requests
from html.parser import HTMLParser

import os
import textwrap
import re
from datetime import datetime
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.align import Align
from rich import box
from app.config.theme_config import get_theme

console = Console()
load_dotenv()

def print_banner():
    theme = get_theme()
    banner_text = Align.center(
        "[bold]myXL CLI v8.8.0 gen.Z[/]",
        vertical="middle"
    )
    console.print(Panel(
        banner_text,
        border_style=theme["border_primary"],
        style=theme["text_title"],
        padding=(1, 2),
        expand=True,
        box=box.DOUBLE
    ))

def clear_screen():
    print("Clearing screen...")
    os.system('cls' if os.name == 'nt' else 'clear')
    if ascii_art:
        ascii_art.to_terminal(columns=55)

    print_banner()

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
