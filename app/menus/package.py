import json
import sys

import requests
from app.service.auth import AuthInstance
from app.client.engsel import get_family, get_package, get_addons, get_package_details, send_api_request, unsubscribe
from app.client.ciam import get_auth_code
from app.service.bookmark import BookmarkInstance
from app.client.purchase.redeem import settlement_bounty, settlement_loyalty, bounty_allotment
from app.menus.util import clear_screen, pause, display_html
from app.client.purchase.qris import show_qris_payment
from app.client.purchase.ewallet import show_multipayment
from app.client.purchase.balance import settlement_balance
from app.type_dict import PaymentItem
from app.menus.purchase import purchase_n_times, purchase_n_times_by_option_code
from app.menus.util import format_quota_byte
from app.service.decoy import DecoyInstance

def show_package_details(api_key, tokens, package_option_code, is_enterprise, option_order = -1):
    active_user = AuthInstance.active_user
    subscription_type = active_user.get("subscription_type", "")
    
    clear_screen()
    print("-------------------------------------------------------")
    print("Detail Paket")
    print("-------------------------------------------------------")
    package = get_package(api_key, tokens, package_option_code)
    # print(f"[SPD-202]:\n{json.dumps(package, indent=1)}")
    if not package:
        print("Failed to load package details.")
        pause()
        return False

    price = package["package_option"]["price"]
    detail = display_html(package["package_option"]["tnc"])
    validity = package["package_option"]["validity"]

    option_name = package.get("package_option", {}).get("name","") #Vidio
    family_name = package.get("package_family", {}).get("name","") #Unlimited Turbo
    variant_name = package.get("package_detail_variant", "").get("name","") #For Xtra Combo
    option_name = package.get("package_option", {}).get("name","") #Vidio
    
    title = f"{family_name} - {variant_name} - {option_name}".strip()
    
    family_code = package.get("package_family", {}).get("package_family_code","")
    parent_code = package.get("package_addon", {}).get("parent_code","")
    if parent_code == "":
        parent_code = "N/A"
    
    token_confirmation = package["token_confirmation"]
    ts_to_sign = package["timestamp"]
    payment_for = package["package_family"]["payment_for"]
    
    payment_items = [
        PaymentItem(
            item_code=package_option_code,
            product_type="",
            item_price=price,
            item_name=f"{variant_name} {option_name}".strip(),
            tax=0,
            token_confirmation=token_confirmation,
        )
    ]
    
    print("-------------------------------------------------------")
    print(f"Nama: {title}")
    print(f"Harga: Rp {price}")
    print(f"Payment For: {payment_for}")
    print(f"Masa Aktif: {validity}")
    print(f"Point: {package['package_option']['point']}")
    print(f"Plan Type: {package['package_family']['plan_type']}")
    print("-------------------------------------------------------")
    print(f"Family Code: {family_code}")
    print(f"Parent Code (for addon/dummy): {parent_code}")
    print("-------------------------------------------------------")
    benefits = package["package_option"]["benefits"]
    if benefits and isinstance(benefits, list):
        print("Benefits:")
        for benefit in benefits:
            print("-------------------------------------------------------")
            print(f" Name: {benefit['name']}")
            print(f"  Item id: {benefit['item_id']}")
            data_type = benefit['data_type']
            if data_type == "VOICE" and benefit['total'] > 0:
                print(f"  Total: {benefit['total']/60} menit")
            elif data_type == "TEXT" and benefit['total'] > 0:
                print(f"  Total: {benefit['total']} SMS")
            elif data_type == "DATA" and benefit['total'] > 0:
                if benefit['total'] > 0:
                    quota = int(benefit['total'])
                    # It is in byte, make it in GB
                    if quota >= 1_000_000_000:
                        quota_gb = quota / (1024 ** 3)
                        print(f"  Quota: {quota_gb:.2f} GB")
                    elif quota >= 1_000_000:
                        quota_mb = quota / (1024 ** 2)
                        print(f"  Quota: {quota_mb:.2f} MB")
                    elif quota >= 1_000:
                        quota_kb = quota / 1024
                        print(f"  Quota: {quota_kb:.2f} KB")
                    else:
                        print(f"  Total: {quota}")
            elif data_type not in ["DATA", "VOICE", "TEXT"]:
                print(f"  Total: {benefit['total']} ({data_type})")
            
            if benefit["is_unlimited"]:
                print("  Unlimited: Yes")
    print("-------------------------------------------------------")
    addons = get_addons(api_key, tokens, package_option_code)
    

    bonuses = addons.get("bonuses", [])
    
    # Pick 1st bonus if available, need more testing
    # if len(bonuses) > 0:
    #     payment_items.append(
    #         PaymentItem(
    #             item_code=bonuses[0]["package_option_code"],
    #             product_type="",
    #             item_price=0,
    #             item_name=bonuses[0]["name"],
    #             tax=0,
    #             token_confirmation="",
    #         )
    #     )
    
    # Pick all bonuses, need more testing
    # for bonus in bonuses:
    #     payment_items.append(
    #         PaymentItem(
    #             item_code=bonus["package_option_code"],
    #             product_type="",
    #             item_price=0,
    #             item_name=bonus["name"],
    #             tax=0,
    #             token_confirmation="",
    #         )
    #     )

    print(f"Addons:\n{json.dumps(addons, indent=2)}")
    print("-------------------------------------------------------")
    print(f"SnK MyXL:\n{detail}")
    print("-------------------------------------------------------")
    
    in_package_detail_menu = True
    while in_package_detail_menu:
        print("Options:")
        print("1. Beli dengan Pulsa")
        print("2. Beli dengan E-Wallet")
        print("3. Bayar dengan QRIS")
        print("4. Pulsa + Decoy")
        print("5. Pulsa + Decoy V2")
        print("6. QRIS + Decoy (+1K)")
        print("7. QRIS + Decoy V2")
        print("8. Pulsa N kali")
        # print("9. Debug Share Package")

        # Sometimes payment_for is empty, so we set default to BUY_PACKAGE
        if payment_for == "":
            payment_for = "BUY_PACKAGE"
        
        if payment_for == "REDEEM_VOUCHER":
            print("B. Ambil sebagai bonus (jika tersedia)")
            print("BA. Kirim bonus (jika tersedia)")
            print("L. Beli dengan Poin (jika tersedia)")
        
        if option_order != -1:
            print("0. Tambah ke Bookmark")
        print("00. Kembali ke daftar paket")

        choice = input("Pilihan: ")
        if choice == "00":
            return False
        elif choice == "0" and option_order != -1:
            # Add to bookmark
            success = BookmarkInstance.add_bookmark(
                family_code=package.get("package_family", {}).get("package_family_code",""),
                family_name=package.get("package_family", {}).get("name",""),
                is_enterprise=is_enterprise,
                variant_name=variant_name,
                option_name=option_name,
                order=option_order,
            )
            if success:
                print("Paket berhasil ditambahkan ke bookmark.")
            else:
                print("Paket sudah ada di bookmark.")
            pause()
            continue
        
        elif choice == '1':
            settlement_balance(
                api_key,
                tokens,
                payment_items,
                payment_for,
                True
            )
            input("Silahkan cek hasil pembelian di aplikasi MyXL. Tekan Enter untuk kembali.")
            return True
        elif choice == '2':
            show_multipayment(
                api_key,
                tokens,
                payment_items,
                payment_for,
                True,
            )
            input("Silahkan lakukan pembayaran & cek hasil pembelian di aplikasi MyXL. Tekan Enter untuk kembali.")
            return True
        elif choice == '3':
            show_qris_payment(
                api_key,
                tokens,
                payment_items,
                payment_for,
                True,
            )
            input("Silahkan lakukan pembayaran & cek hasil pembelian di aplikasi MyXL. Tekan Enter untuk kembali.")
            return True
        elif choice == '4':
            # Balance with Decoy            
            decoy = DecoyInstance.get_decoy("balance")
            
            decoy_package_detail = get_package(
                api_key,
                tokens,
                decoy["option_code"],
            )
            
            if not decoy_package_detail:
                print("Failed to load decoy package details.")
                pause()
                return False

            payment_items.append(
                PaymentItem(
                    item_code=decoy_package_detail["package_option"]["package_option_code"],
                    product_type="",
                    item_price=decoy_package_detail["package_option"]["price"],
                    item_name=decoy_package_detail["package_option"]["name"],
                    tax=0,
                    token_confirmation=decoy_package_detail["token_confirmation"],
                )
            )

            overwrite_amount = price + decoy_package_detail["package_option"]["price"]
            res = settlement_balance(
                api_key,
                tokens,
                payment_items,
                payment_for,
                False,
                overwrite_amount=overwrite_amount,
            )
            
            if res and res.get("status", "") != "SUCCESS":
                error_msg = res.get("message", "Unknown error")
                if "Bizz-err.Amount.Total" in error_msg:
                    error_msg_arr = error_msg.split("=")
                    valid_amount = int(error_msg_arr[1].strip())
                    
                    print(f"Adjusted total amount to: {valid_amount}")
                    res = settlement_balance(
                        api_key,
                        tokens,
                        payment_items,
                        payment_for,
                        False,
                        overwrite_amount=valid_amount,
                    )
                    if res and res.get("status", "") == "SUCCESS":
                        print("Purchase successful!")
            else:
                print("Purchase successful!")
            pause()
            return True
        elif choice == '5':
            # Balance with Decoy v2 (use token confirmation from decoy)
            decoy = DecoyInstance.get_decoy("balance")
            
            decoy_package_detail = get_package(
                api_key,
                tokens,
                decoy["option_code"],
            )
            
            if not decoy_package_detail:
                print("Failed to load decoy package details.")
                pause()
                return False

            payment_items.append(
                PaymentItem(
                    item_code=decoy_package_detail["package_option"]["package_option_code"],
                    product_type="",
                    item_price=decoy_package_detail["package_option"]["price"],
                    item_name=decoy_package_detail["package_option"]["name"],
                    tax=0,
                    token_confirmation=decoy_package_detail["token_confirmation"],
                )
            )

            overwrite_amount = price + decoy_package_detail["package_option"]["price"]
            res = settlement_balance(
                api_key,
                tokens,
                payment_items,
                "🤫",
                False,
                overwrite_amount=overwrite_amount,
                token_confirmation_idx=1
            )
            
            if res and res.get("status", "") != "SUCCESS":
                error_msg = res.get("message", "Unknown error")
                if "Bizz-err.Amount.Total" in error_msg:
                    error_msg_arr = error_msg.split("=")
                    valid_amount = int(error_msg_arr[1].strip())
                    
                    print(f"Adjusted total amount to: {valid_amount}")
                    res = settlement_balance(
                        api_key,
                        tokens,
                        payment_items,
                        "🤫",
                        False,
                        overwrite_amount=valid_amount,
                        token_confirmation_idx=-1
                    )
                    if res and res.get("status", "") == "SUCCESS":
                        print("Purchase successful!")
            else:
                print("Purchase successful!")
            pause()
            return True
        elif choice == '6':
            # QRIS decoy + Rpx
            decoy = DecoyInstance.get_decoy("qris")
            
            decoy_package_detail = get_package(
                api_key,
                tokens,
                decoy["option_code"],
            )
            
            if not decoy_package_detail:
                print("Failed to load decoy package details.")
                pause()
                return False

            payment_items.append(
                PaymentItem(
                    item_code=decoy_package_detail["package_option"]["package_option_code"],
                    product_type="",
                    item_price=decoy_package_detail["package_option"]["price"],
                    item_name=decoy_package_detail["package_option"]["name"],
                    tax=0,
                    token_confirmation=decoy_package_detail["token_confirmation"],
                )
            )
            
            print("-"*55)
            print(f"Harga Paket Utama: Rp {price}")
            print(f"Harga Paket Decoy: Rp {decoy_package_detail['package_option']['price']}")
            print("Silahkan sesuaikan amount (trial & error, 0 = malformed)")
            print("-"*55)

            show_qris_payment(
                api_key,
                tokens,
                payment_items,
                "SHARE_PACKAGE",
                True,
                token_confirmation_idx=1
            )
            
            input("Silahkan lakukan pembayaran & cek hasil pembelian di aplikasi MyXL. Tekan Enter untuk kembali.")
            return True
        elif choice == '7':
            # QRIS decoy + Rp0
            decoy = DecoyInstance.get_decoy("qris0")
            
            decoy_package_detail = get_package(
                api_key,
                tokens,
                decoy["option_code"],
            )
            
            if not decoy_package_detail:
                print("Failed to load decoy package details.")
                pause()
                return False

            payment_items.append(
                PaymentItem(
                    item_code=decoy_package_detail["package_option"]["package_option_code"],
                    product_type="",
                    item_price=decoy_package_detail["package_option"]["price"],
                    item_name=decoy_package_detail["package_option"]["name"],
                    tax=0,
                    token_confirmation=decoy_package_detail["token_confirmation"],
                )
            )
            
            print("-"*55)
            print(f"Harga Paket Utama: Rp {price}")
            print(f"Harga Paket Decoy: Rp {decoy_package_detail['package_option']['price']}")
            print("Silahkan sesuaikan amount (trial & error, 0 = malformed)")
            print("-"*55)

            show_qris_payment(
                api_key,
                tokens,
                payment_items,
                "SHARE_PACKAGE",
                True,
                token_confirmation_idx=1
            )
            
            input("Silahkan lakukan pembayaran & cek hasil pembelian di aplikasi MyXL. Tekan Enter untuk kembali.")
            return True
        elif choice == '8':
            #Pulsa N kali
            use_decoy_for_n_times = input("Use decoy package? (y/n): ").strip().lower() == 'y'
            n_times_str = input("Enter number of times to purchase (e.g., 3): ").strip()

            delay_seconds_str = input("Enter delay between purchases in seconds (e.g., 25): ").strip()
            if not delay_seconds_str.isdigit():
                delay_seconds_str = "0"

            try:
                n_times = int(n_times_str)
                if n_times < 1:
                    raise ValueError("Number must be at least 1.")
            except ValueError:
                print("Invalid number entered. Please enter a valid integer.")
                pause()
                continue
            purchase_n_times_by_option_code(
                n_times,
                option_code=package_option_code,
                use_decoy=use_decoy_for_n_times,
                delay_seconds=int(delay_seconds_str),
                pause_on_success=False,
                token_confirmation_idx=1
            )
        elif choice == '9':
            pin = input("Enter PIN: ")
            if len(pin) != 6:
                print("PIN too short.")
                pause()
                continue
            auth_code = get_auth_code(
                tokens,
                pin,
                active_user["number"]
            )
            
            if not auth_code:
                print("Failed to get auth_code")
                continue
            
            target_msisdn = input("Target number start with 62:")
            
            url = "https://me.mashu.lol/pg-decoy-edu.json"
            
            response = requests.get(url, timeout=30)
            if response.status_code != 200:
                print("Gagal mengambil data decoy package.")
                pause()
                return None
            
            decoy_data = response.json()
            decoy_package_detail = get_package_details(
                api_key,
                tokens,
                decoy_data["family_code"],
                decoy_data["variant_code"],
                decoy_data["order"],
                decoy_data["is_enterprise"],
                decoy_data["migration_type"],
            )

            # payment_items.append(
            #     PaymentItem(
            #         item_code=decoy_package_detail["package_option"]["package_option_code"],
            #         product_type="",
            #         item_price=decoy_package_detail["package_option"]["price"],
            #         item_name=decoy_package_detail["package_option"]["name"],
            #         tax=0,
            #         token_confirmation=decoy_package_detail["token_confirmation"],
            #     )
            # )

            overwrite_amount = price + decoy_package_detail["package_option"]["price"]
            res = show_qris_payment(
                api_key,
                tokens,
                payment_items,
                "SHARE_PACKAGE",
                False,
                overwrite_amount=overwrite_amount,
                token_confirmation_idx=0,
                topup_number=target_msisdn,
                stage_token=auth_code,
            )
            
            if res and res.get("status", "") != "SUCCESS":
                error_msg = res.get("message", "Unknown error")
                if "Bizz-err.Amount.Total" in error_msg:
                    error_msg_arr = error_msg.split("=")
                    valid_amount = int(error_msg_arr[1].strip())
                    
                    print(f"Adjusted total amount to: {valid_amount}")
                    res = show_qris_payment(
                        api_key,
                        tokens,
                        payment_items,
                        "SHARE_PACKAGE",
                        False,
                        overwrite_amount=valid_amount,
                        token_confirmation_idx=0,
                        topup_number=target_msisdn,
                        stage_token=auth_code,
                    )
                    if res and res.get("status", "") == "SUCCESS":
                        print("Purchase successful!")
            else:
                print("Purchase successful!")
            
            payment_items.pop()
            pause()            
        elif choice.lower() == 'b':
            settlement_bounty(
                api_key=api_key,
                tokens=tokens,
                token_confirmation=token_confirmation,
                ts_to_sign=ts_to_sign,
                payment_target=package_option_code,
                price=price,
                item_name=variant_name
            )
            input("Silahkan lakukan pembayaran & cek hasil pembelian di aplikasi MyXL. Tekan Enter untuk kembali.")
            return True
        elif choice.lower() == 'ba':
            destination_msisdn = input("Masukkan nomor tujuan bonus (mulai dengan 62): ").strip()
            bounty_allotment(
                api_key=api_key,
                tokens=tokens,
                ts_to_sign=ts_to_sign,
                destination_msisdn=destination_msisdn,
                item_name=option_name,
                item_code=package_option_code,
                token_confirmation=token_confirmation,
            )
            pause()
            return True
        elif choice.lower() == 'l':
            settlement_loyalty(
                api_key=api_key,
                tokens=tokens,
                token_confirmation=token_confirmation,
                ts_to_sign=ts_to_sign,
                payment_target=package_option_code,
                price=price,
            )
            input("Silahkan lakukan pembayaran & cek hasil pembelian di aplikasi MyXL. Tekan Enter untuk kembali.")
            return True
        else:
            print("Purchase cancelled.")
            return False
    pause()
    sys.exit(0)
