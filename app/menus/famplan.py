from datetime import datetime
import json
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.align import Align
from rich.box import MINIMAL_DOUBLE_HEAD

from app.menus.util import pause, clear_screen, format_quota_byte
from app.client.engsel2 import get_family_data, change_member, remove_member, set_quota_limit, validate_msisdn
from app.config.theme_config import get_theme
from app.menus.util_helper import print_panel

console = Console()

def show_family_info(api_key: str, tokens: dict):
    in_family_menu = True
    while in_family_menu:
        clear_screen()
        theme = get_theme()

        res = get_family_data(api_key, tokens)
        if not res.get("data"):
            print_panel("⚠️ Error", "Gagal mengambil data Family Plan.")
            pause()
            return

        family_detail = res["data"]
        info = family_detail["member_info"]
        plan_type = info.get("plan_type", "")
        if not plan_type:
            print_panel("ℹ️ Info", "Anda bukan organizer Family Plan.")
            pause()
            return

        parent_msisdn = info.get("parent_msisdn", "N/A")
        members = info.get("members", [])
        empty_slots = [m for m in members if m.get("msisdn") == ""]

        total_quota = format_quota_byte(info.get("total_quota", 0))
        remaining_quota = format_quota_byte(info.get("remaining_quota", 0))
        end_date = datetime.fromtimestamp(info.get("end_date", 0)).strftime("%Y-%m-%d")

        console.print(Panel(
            Align.center(f"👨‍👩‍👧‍👦 Family Plan: {plan_type}\n👑 Parent: {parent_msisdn}\n📦 Kuota: {remaining_quota} / {total_quota} | Exp: {end_date}"),
            border_style=theme["border_info"],
            padding=(1, 2),
            expand=True
        ))

        member_table = Table(show_header=True, box=MINIMAL_DOUBLE_HEAD, expand=True)
        member_table.add_column("No", style=theme["text_key"], justify="right", width=4)
        member_table.add_column("Nomor", style=theme["text_body"])
        member_table.add_column("Alias", style=theme["text_body"])
        member_table.add_column("Tipe", style=theme["text_sub"])
        member_table.add_column("Kuota", style=theme["text_body"])
        member_table.add_column("Chances", style=theme["text_body"])

        for idx, member in enumerate(members, start=1):
            msisdn = member.get("msisdn", "")
            alias = member.get("alias", "N/A")
            member_type = member.get("member_type", "N/A")
            usage = member.get("usage", {})
            quota_used = format_quota_byte(usage.get("quota_used", 0))
            quota_allocated = format_quota_byte(usage.get("quota_allocated", 0))
            chances = f"{member.get('add_chances', 0)}/{member.get('total_add_chances', 0)}"
            member_table.add_row(
                str(idx),
                msisdn or "<Empty Slot>",
                alias,
                member_type,
                f"{quota_used} / {quota_allocated}",
                chances
            )

        console.print(Panel(member_table, border_style=theme["border_primary"], expand=True))

        console.print(Panel(
            "1. Ganti Anggota\n"
            "limit <n> <MB> - Set kuota anggota ke-n\n"
            "del <n> - Hapus anggota ke-n\n"
            "00. Kembali ke menu utama",
            title="📋 Opsi",
            border_style=theme["border_info"],
            padding=(1, 2),
            expand=True
        ))

        choice = console.input("Pilih opsi: ").strip()

        if choice == "00":
            return

        elif choice == "1":
            try:
                slot_idx = int(console.input("Slot yang ingin diisi: ").strip())
                if slot_idx < 1 or slot_idx > len(members):
                    print_panel("⚠️ Error", "Nomor slot tidak valid.")
                    pause()
                    continue
                if members[slot_idx - 1].get("msisdn"):
                    print_panel("⚠️ Error", "Slot sudah terisi.")
                    pause()
                    continue

                target_msisdn = console.input("Nomor anggota baru (62xxx): ").strip()
                parent_alias = console.input("Alias Anda: ").strip()
                child_alias = console.input("Alias anggota baru: ").strip()

                validation = validate_msisdn(api_key, tokens, target_msisdn)
                if validation.get("status") != "SUCCESS":
                    print_panel("⚠️ Error", validation.get("message", "Validasi gagal."))
                    pause()
                    continue

                role = validation["data"].get("family_plan_role", "")
                if role != "NO_ROLE":
                    print_panel("⚠️ Error", f"{target_msisdn} sudah tergabung sebagai {role}.")
                    pause()
                    continue

                confirm = console.input(f"Yakin ingin mengisi slot {slot_idx} dengan {target_msisdn}? (y/n): ").strip().lower()
                if confirm != "y":
                    print_panel("ℹ️ Info", "Aksi dibatalkan.")
                    pause()
                    continue

                slot = members[slot_idx - 1]
                res = change_member(api_key, tokens, parent_alias, child_alias, slot["slot_id"], slot["family_member_id"], target_msisdn)
                if res.get("status") == "SUCCESS":
                    print_panel("✅ Sukses", "Anggota berhasil ditambahkan.")
                else:
                    print_panel("⚠️ Error", res.get("message", "Gagal mengganti anggota."))
                console.print(json.dumps(res, indent=2))
            except Exception:
                print_panel("⚠️ Error", "Input tidak valid.")
            pause()

        elif choice.startswith("del "):
            try:
                slot_idx = int(choice.split(" ")[1])
                if slot_idx < 1 or slot_idx > len(members):
                    print_panel("⚠️ Error", "Nomor slot tidak valid.")
                    pause()
                    continue
                member = members[slot_idx - 1]
                if not member.get("msisdn"):
                    print_panel("⚠️ Error", "Slot sudah kosong.")
                    pause()
                    continue
                confirm = console.input(f"Hapus anggota {member['msisdn']} dari slot {slot_idx}? (y/n): ").strip().lower()
                if confirm != "y":
                    print_panel("ℹ️ Info", "Penghapusan dibatalkan.")
                    pause()
                    continue
                res = remove_member(api_key, tokens, member["family_member_id"])
                if res.get("status") == "SUCCESS":
                    print_panel("✅ Sukses", "Anggota berhasil dihapus.")
                else:
                    print_panel("⚠️ Error", res.get("message", "Gagal menghapus anggota."))
                console.print(json.dumps(res, indent=2))
            except Exception:
                print_panel("⚠️ Error", "Format input tidak valid.")
            pause()

        elif choice.startswith("limit "):
            try:
                _, slot_num, quota_mb = choice.split(" ")
                slot_idx = int(slot_num)
                quota_byte = int(quota_mb) * 1024 * 1024
                if slot_idx < 1 or slot_idx > len(members):
                    print_panel("⚠️ Error", "Nomor slot tidak valid.")
                    pause()
                    continue
                member = members[slot_idx - 1]
                if not member.get("msisdn"):
                    print_panel("⚠️ Error", "Slot kosong. Tidak bisa set limit.")
                    pause()
                    continue
                original_byte = member.get("usage", {}).get("quota_allocated", 0)
                res = set_quota_limit(api_key, tokens, original_byte, quota_byte, member["family_member_id"])
                if res.get("status") == "SUCCESS":
                    print_panel("✅ Sukses", f"Kuota anggota slot {slot_idx} berhasil diubah.")
                else:
                    print_panel("⚠️ Error", res.get("message", "Gagal mengubah kuota."))
                console.print(json.dumps(res, indent=2))
            except Exception:
                print_panel("⚠️ Error", "Format input tidak valid.")
            pause()

        else:
            print_panel("⚠️ Error", "Opsi tidak dikenali.")
            pause()
