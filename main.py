from dotenv import load_dotenv
load_dotenv()

import subprocess
import os
import sys
from rich.panel import Panel
from rich.text import Text
from rich.console import Console
from app.service.git import ensure_git
from app.menus.util import pause, live_loading, print_panel, print_error
from app.config.theme_config import get_theme, get_theme_style

console = Console()

def is_rebase_in_progress():
    return os.path.exists(".git/rebase-apply") or os.path.exists(".git/rebase-merge")

def git_pull_rebase():
    theme = get_theme()
    result = {"status": None, "error": None, "output": ""}

    if is_rebase_in_progress():
        text = Text.from_markup(
            "[bold yellow]⚠️ Rebase sebelumnya belum selesai[/]\n\n"
            f"[{get_theme_style('text_warning')}]Selesaikan dengan `git rebase --continue` atau batalkan dengan `git rebase --abort`[/]"
        )
        console.print(Panel(
            text,
            title=f"[{get_theme_style('text_title')}]📥 Update CLI[/]",
            border_style=get_theme_style("border_warning"),
            padding=(1, 2),
            expand=True
        ))
        pause()
        sys.exit(1)

    def run_git_pull():
        try:
            subprocess.run(['git', 'rev-parse', '--is-inside-work-tree'], check=True, stdout=subprocess.DEVNULL)
            output = subprocess.run(
                ['git', 'pull', '--rebase'],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                check=True
            )
            result["status"] = "success"
            result["output"] = output.stdout.strip()
        except subprocess.CalledProcessError as e:
            result["status"] = "fail"
            result["error"] = e.stderr.strip()
        except Exception as e:
            result["status"] = "error"
            result["error"] = str(e)

    def run_git_reset():
        try:
            branch = subprocess.check_output(['git', 'rev-parse', '--abbrev-ref', 'HEAD'], text=True).strip()
            subprocess.run(['git', 'fetch'], check=True, stdout=subprocess.DEVNULL)
            reset_output = subprocess.run(
                ['git', 'reset', '--hard', f'origin/{branch}'],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                check=True
            )
            result["status"] = "reset"
            result["output"] = reset_output.stdout.strip()
        except Exception as e:
            result["status"] = "reset_fail"
            result["error"] = str(e)

    with live_loading("🔄 Menarik update dari repository...", theme):
        run_git_pull()

    if result["status"] == "success":
        text = Text.from_markup(
            f"[bold {get_theme_style('text_date')}]✅ Git pull berhasil[/]\n\n[{get_theme_style('text_body')}]{result['output']}[/]"
        )
        console.print(Panel(
            text,
            title=f"[{get_theme_style('text_title')}]📥 Update CLI[/]",
            border_style=get_theme_style("border_info"),
            padding=(1, 2),
            expand=True
        ))

    elif result["status"] == "fail":
        text = Text.from_markup(
            f"[bold {get_theme_style('text_error')}]❌ Git pull gagal[/]\n\n[{get_theme_style('text_error')}]{result['error']}[/]\n\n[{get_theme_style('text_warning')}]Mencoba reset paksa...[/]"
        )
        console.print(Panel(
            text,
            title=f"[{get_theme_style('text_title')}]📥 Update CLI[/]",
            border_style=get_theme_style("border_error"),
            padding=(1, 2),
            expand=True
        ))

        with live_loading("🧹 Menjalankan git reset --hard...", theme):
            run_git_reset()

        if result["status"] == "reset":
            text = Text.from_markup(
                f"[bold {get_theme_style('text_success')}]✅ Reset berhasil, CLI disinkronkan ke origin[/]\n\n[{get_theme_style('text_body')}]{result['output']}[/]"
            )
            console.print(Panel(
                text,
                title=f"[{get_theme_style('text_title')}]📥 Update CLI[/]",
                border_style=get_theme_style("border_success"),
                padding=(1, 2),
                expand=True
            ))
        else:
            text = Text.from_markup(
                f"[bold {get_theme_style('text_error')}]❌ Reset gagal[/]\n\n[{get_theme_style('text_error')}]{result['error']}[/]"
            )
            console.print(Panel(
                text,
                title=f"[{get_theme_style('text_title')}]📥 Update CLI[/]",
                border_style=get_theme_style("border_error"),
                padding=(1, 2),
                expand=True
            ))
            pause()
            sys.exit(1)

    else:
        text = Text.from_markup(
            f"[bold {get_theme_style('text_warning')}]⚠️ Error saat menjalankan git pull[/]\n\n[{get_theme_style('text_warning')}]{result['error']}[/]"
        )
        console.print(Panel(
            text,
            title=f"[{get_theme_style('text_title')}]📥 Update CLI[/]",
            border_style=get_theme_style("border_warning"),
            padding=(1, 2),
            expand=True
        ))
        pause()
        sys.exit(1)

def run_main():
    try:
        import master
        master.main()
    except KeyboardInterrupt:
        print_panel("👋 Keluar", "Aplikasi dihentikan oleh pengguna", border_style=get_theme_style("border_info"))
        sys.exit(0)
    except Exception as e:
        print_error("❌ Gagal menjalankan menu utama", f"{type(e).__name__} - {e}")
        pause()
        sys.exit(1)

if __name__ == "__main__":
    ensure_git()
    git_pull_rebase()
    run_main()
