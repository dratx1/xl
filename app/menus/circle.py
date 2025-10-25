from datetime import datetime
import json
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.align import Align
from rich.box import MINIMAL_DOUBLE_HEAD

from app.menus.util import pause, clear_screen, format_quota_byte
from app.client.engsel3 import (
    get_group_data, get_group_members, validate_circle_member,
    invite_circle_member, remove_circle_member, accept_circle_invitation
)
from app.service.auth import AuthInstance
from app.client.encrypt import decrypt_circle_msisdn
from app.config.theme_config import get_theme
from app.menus.util_helper import print_panel

console = Console()

def show_circle_info(api_key: str, tokens: dict):
    in_circle_menu = True
    user = AuthInstance.get_active_user()
    my_msisdn = user.get("number", "")

    while in_circle_menu:
        clear_screen()
        theme = get_theme()

        group_res = get_group_data(api_key, tokens)
        if group_res.get("status") != "SUCCESS":
            print_panel("⚠️ Error", "Gagal mengambil data Circle.")
            pause()
            return

        group_data = group_res.get("data", {})
        group_id = group_data.get("group_id", "")
        if not group_id:
            print_panel("ℹ️ Info", "Anda belum tergabung dalam Circle.")
            pause()
            return

        if group_data.get("group_status") == "BLOCKED":
            print_panel("🚫 Circle diblokir", "Circle ini sedang diblokir.")
            pause()
            return

        group_name = group_data.get("group_name", "N/A")
        owner_name = group_data.get("owner_name", "N/A")

        members_res = get_group_members(api_key, tokens, group_id)
        if members_res.get("status") != "SUCCESS":
            print_panel("⚠️ Error", "Gagal mengambil daftar anggota.")
            pause()
            return

        members_data = members_res.get("data", {})
        members = members_data.get("members", [])
        if not members:
            print_panel("ℹ️ Info", "Belum ada anggota dalam Circle.")
            pause()
            return

        parent_member_id = ""
        parent_msisdn = ""
        for member in members:
            if member.get("member_role") == "PARENT":
                parent_member_id = member.get("member_id", "")
                parent_msisdn = decrypt_circle_msisdn(api_key, member.get("msisdn", ""))

        package = members_data.get("package", {})
        benefit = package.get("benefit", {})
        formatted_allocation = format_quota_byte(benefit.get("allocation", 0))
        formatted_remaining = format_quota_byte(benefit.get("remaining", 0))

        console.print(Panel(
            Align.center(
                f"👨‍👩‍👧‍👦 Circle: {group_name} ({group_data.get('group_status')})\n"
                f"👑 Owner: {owner_name} {parent_msisdn}\n"
                f"📦 Paket: {package.get('name', 'N/A')} | Sisa: {formatted_remaining} / {formatted_allocation}"
            ),
            border_style=theme["border_info"],
            padding=(1, 2),
            expand=True
        ))

        member_table = Table(show_header=True, box=MINIMAL_DOUBLE_HEAD, expand=True)
        member_table.add_column("No", style=theme["text_key"], justify="right", width=4)
        member_table.add_column("Nama", style=theme["text_body"])
        member_table.add_column("Nomor", style=theme["text_body"])
        member_table.add_column("Status", style=theme["text_sub"])
        member_table.add_column("Kuota", style=theme["text_body"])

        for idx, member in enumerate(members, start=1):
            msisdn = decrypt_circle_msisdn(api_key, member.get("msisdn", ""))
            me_mark = " (You)" if msisdn == my_msisdn else ""
            name = member.get("member_name", "N/A")
            role = "👑 Parent" if member.get("member_role") == "PARENT" else "👤 Member"
            status = member.get("status", "N/A")
            join_date = datetime.fromtimestamp(member.get("join_date", 0)).strftime('%Y-%m-%d')
            used = format_quota_byte(member.get("allocation", 0) - member.get("remaining", 0))
            allocated = format_quota_byte(member.get("allocation", 0))
            member_table.add_row(
                str(idx),
                f"{name}{me_mark}",
                msisdn or "<No Number>",
                f"{role} | {status} | {join_date}",
                f"{used} / {allocated}"
            )

        console.print(Panel(member_table, border_style=theme["border_primary"], expand=True))

        console.print(Panel(
            "1. Invite Member\n"
            "del <n> - Hapus anggota ke-n\n"
            "acc <n> - Terima undangan anggota ke-n\n"
            "00. Kembali ke menu utama",
            title="📋 Opsi",
            border_style=theme["border_info"],
            padding=(1, 2),
            expand=True
        ))

        choice = console.input("Pilih opsi: ").strip()

        if choice == "00":
            in_circle_menu = False

        elif choice == "1":
            msisdn_to_invite = console.input("Masukkan nomor anggota yang ingin diundang: ").strip()
            validate_res = validate_circle_member(api_key, tokens, msisdn_to_invite)
            if validate_res.get("status") == "SUCCESS":
                if validate_res.get("data", {}).get("response_code") != "200-2001":
                    print_panel("⚠️ Tidak dapat mengundang", validate_res.get("data", {}).get("message", "Unknown error"))
                    pause()
                    continue

            member_name = console.input("Masukkan nama anggota: ").strip()
            invite_res = invite_circle_member(api_key, tokens, msisdn_to_invite, member_name, group_id, parent_member_id)
            if invite_res.get("status") == "SUCCESS" and invite_res.get("data", {}).get("response_code") == "200-00":
                print_panel("✅ Sukses", f"Undangan berhasil dikirim ke {msisdn_to_invite}")
            else:
                print_panel("⚠️ Gagal", invite_res.get("data", {}).get("message", "Unknown error"))
            pause()

        elif choice.startswith("del "):
            try:
                idx = int(choice.split(" ")[1])
                if idx < 1 or idx > len(members):
                    print_panel("⚠️ Error", "Nomor anggota tidak valid.")
                    pause()
                    continue
                member = members[idx - 1]
                if member.get("member_role") == "PARENT":
                    print_panel("⚠️ Error", "Tidak dapat menghapus pemilik Circle.")
                    pause()
                    continue
                if len(members) <= 2:
                    print_panel("⚠️ Error", "Tidak dapat menghapus anggota terakhir.")
                    pause()
                    continue
                msisdn = decrypt_circle_msisdn(api_key, member.get("msisdn", ""))
                confirm = console.input(f"Yakin ingin menghapus {msisdn}? (y/n): ").strip().lower()
                if confirm != "y":
                    print_panel("ℹ️ Info", "Penghapusan dibatalkan.")
                    pause()
                    continue
                res = remove_circle_member(api_key, tokens, member["member_id"], group_id, parent_member_id, False)
                if res.get("status") == "SUCCESS":
                    print_panel("✅ Info", f"{msisdn} berhasil dihapus dari Circle.")
                else:
                    print_panel("⚠️ Error", f"Gagal menghapus: {res}")
            except Exception:
                print_panel("⚠️ Error", "Format input tidak valid.")
            pause()

        elif choice.startswith("acc "):
            try:
                idx = int(choice.split(" ")[1])
                if idx < 1 or idx > len(members):
                    print_panel("⚠️ Error", "Nomor anggota tidak valid.")
                    pause()
                    continue
                member = members[idx - 1]
                if member.get("status") != "INVITED":
                    print_panel("⚠️ Error", "Anggota ini tidak dalam status undangan.")
                    pause()
                    continue
                msisdn = decrypt_circle_msisdn(api_key, member.get("msisdn", ""))
                confirm = console.input(f"Terima undangan untuk {msisdn}? (y/n): ").strip().lower()
                if confirm != "y":
                    print_panel("ℹ️ Info", "Aksi dibatalkan.")
                    pause()
                    continue
                res = accept_circle_invitation(api_key, tokens, group_id, member["member_id"])
                if res.get("status") == "SUCCESS":
                    print_panel("✅ Info", f"Undangan untuk {msisdn} telah diterima.")
                else:
                    print_panel("⚠️ Error", f"Gagal menerima undangan: {res}")
            except Exception:
                print_panel("⚠️ Error", "Format input tidak valid.")
            pause()

        else:
            print_panel("⚠️ Error", "Input tidak dikenali. Silakan coba lagi.")
            pause()
