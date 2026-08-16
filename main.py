import flet as ft
import requests
import json
import threading
import os
import base64
from datetime import datetime
from notifications import get_notifications_view, build_notification_icon

# --- الثوابت ---
DB_URL = "https://alwafa-afcc1-default-rtdb.firebaseio.com/sub.json"
START_DATE = datetime(2026, 6, 12)
today = datetime.now()
total_fridays = (today - START_DATE).days // 7

def main(page: ft.Page):
    page.title = "كل جمعة"
    page.rtl = True
    page.bgcolor = ft.colors.BLACK
    page.fonts = {"font": "font/ar.ttf"}
    page.theme = ft.Theme(font_family="font", color_scheme=ft.ColorScheme(primary=ft.colors.ORANGE_400))
    page.padding = 0

    cached_data = page.client_storage.get("data_cache")
    all_data = cached_data if cached_data else {}
    
    images_cache = {}
    view_mode = "active"
    members_list = ft.ListView(expand=True, spacing=0)
    
    total_balance_text_header = ft.Text("0", size=20, weight="bold", color=ft.colors.ORANGE_600)
    total_balance_text_body = ft.Text("0", size=16, weight="bold", color=ft.colors.WHITE)
    total_retracted = ft.Text("0", size=16, weight="bold", color=ft.colors.WHITE)
    
    loading_overlay = ft.Container(
        visible=False, 
        bgcolor=ft.colors.with_opacity(0.8, ft.colors.BLACK), 
        alignment=ft.alignment.center, 
        expand=True, 
        content=ft.Column(
            alignment=ft.MainAxisAlignment.CENTER, 
            horizontal_alignment=ft.CrossAxisAlignment.CENTER, 
            controls=[
                ft.ProgressRing(), 
                ft.Text("جار التحميل...", color=ft.colors.WHITE, size=16, weight="bold")
            ]
        )
    )

    refresh_button = ft.FloatingActionButton(
        icon=ft.icons.REFRESH, 
        bgcolor=ft.colors.ORANGE_600, 
        on_click=lambda e: load_data(), 
        width=40, 
        height=40, 
        visible=False
    )

    class Tools(ft.Container):
        def __init__(self, on_click_members=None, on_click_pending=None):
            super().__init__()
            self.total_members = ft.Text("0", color=ft.colors.GREY_300, size=24, weight="bold")
            self.paid_members = ft.Text("0", color=ft.colors.LIME_700, size=24, weight="bold")
            self.pending_members = ft.Text("0", color="#e56328", size=24, weight="bold")
            
            self.content = ft.Row(
                spacing=5, 
                controls=[
                    self.tool_item("المشتركين", self.total_members, on_click=on_click_members), 
                    self.tool_item("المسددين", self.paid_members), 
                    self.tool_item("المطالبين", self.pending_members, on_click=on_click_pending)
                ]
            )

        def tool_item(self, title, counter, on_click=None):
            color = ft.colors.GREY_300 if title == "المشتركين" else (ft.colors.LIME_700 if title == "المسددين" else "#e56328")
            return ft.Container(
                expand=True, 
                height=80, 
                bgcolor=ft.colors.GREY_900, 
                border_radius=5, 
                padding=10, 
                on_click=on_click,
                content=ft.Column(
                    alignment=ft.MainAxisAlignment.CENTER, 
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER, 
                    controls=[ft.Text(title, color=color, size=12), counter]
                ),
                gradient=ft.LinearGradient(begin=ft.alignment.bottom_center, end=ft.alignment.top_center, colors=["#111113", "#111112"])
            )

        def update_stats(self, total, paid, pending):
            self.total_members.value = str(total)
            self.paid_members.value = str(paid)
            self.pending_members.value = str(pending)

    def switch_to_active(e):
        nonlocal view_mode
        if view_mode != "active":
            view_mode = "active"
            render_data(all_data, search_field.value)

    def switch_to_retracted(e):
        nonlocal view_mode
        if view_mode != "retracted":
            view_mode = "retracted"
            render_data(all_data, search_field.value)

    def switch_to_pending(e):
        nonlocal view_mode
        if view_mode != "pending":
            view_mode = "pending"
            render_data(all_data, search_field.value)

    tools_section = Tools(on_click_members=switch_to_active, on_click_pending=switch_to_pending)
    search_field = ft.TextField(
        hint_text="ابحث عن اسم المشترك...", 
        hint_style=ft.TextStyle(color=ft.colors.GREY_600, size=14), 
        prefix_icon=ft.icons.SEARCH, 
        bgcolor=ft.colors.GREY_900, 
        color=ft.colors.WHITE, 
        border=ft.InputBorder.NONE, 
        border_radius=20, 
        content_padding=14, 
        on_change=lambda e: render_data(all_data, e.control.value)
    )

    def get_total_amounts(type):
        total_amount = 0
        notif_data = page.client_storage.get("notifications_cache")
        if notif_data and isinstance(notif_data, dict):
            for key, val in notif_data.items():
                if isinstance(val, dict) and val.get("type") == f"{type}":
                    total_amount += val.get("amount", 0)
        return total_amount

    def cache_images_background(data):
        def background_worker():
            nonlocal images_cache
            updated = False
            for key, val in data.items():
                if isinstance(val, dict):
                    img_url = val.get("img")
                    if img_url and img_url.startswith("http"):
                        if key in images_cache:
                            continue
                        try:
                            img_res = requests.get(img_url, timeout=5)
                            if img_res.status_code == 200:
                                ext = "jpeg"
                                if "." in img_url:
                                    possible_ext = img_url.split("?")[0].rsplit(".", 1)[-1]
                                    if possible_ext in ["png", "jpg", "jpeg", "webp"]:
                                        ext = possible_ext
                                        if ext == "jpg":
                                            ext = "jpeg"
                                
                                # تحويل الصورة إلى Base64 Data URI لتعمل بسلاسة في المتصفح والتطبيقات
                                b64_str = base64.b64encode(img_res.content).decode("utf-8")
                                images_cache[key] = f"data:image/{ext};base64,{b64_str}"
                                updated = True
                        except Exception:
                            pass
            if updated:
                try:
                    render_data(all_data, search_field.value)
                except Exception:
                    pass

        threading.Thread(target=background_worker, daemon=True).start()

    def render_data(data, query=""):
        members_list.controls.clear()
        total, paid, pending, retracted_count, total_balance = 0, 0, 0, 0, 0

        total_withdrawals = get_total_amounts("w") if data else 0
        total_donations = get_total_amounts("don") if data else 0

        if data:
            now = today

            for key, val in data.items():
                if not isinstance(val, dict): 
                    continue

                is_retracted = val.get('ret') == True
                if is_retracted:
                    retracted_count += 1
                else:
                    total += 1
                    total_balance += val.get("amount", 0)

                    start_str = val.get("start_date", "2026-06-19")
                    try:
                        start_date = datetime.strptime(start_str, "%Y-%m-%d")
                        fridays_passed = (now - start_date).days // 7
                    except ValueError:
                        fridays_passed = 0

                    balance = val.get("total_paid", 0) - fridays_passed
                    is_pending = balance < 0

                    if is_pending:
                        pending += 1
                    else:
                        paid += 1

                if view_mode == "retracted" and not is_retracted:
                    continue
                if view_mode in ["active", "pending"] and is_retracted:
                    continue
                if view_mode == "pending" and not is_pending:
                    continue

                if query and query not in val.get("name", ""): 
                    continue

                if view_mode == "retracted":
                    members_list.controls.append(
                        ft.ListTile(
                            leading=ft.CircleAvatar(
                                content=ft.Icon(ft.icons.PERSON_OFF, color=ft.colors.RED_400), 
                                bgcolor=ft.colors.GREY_900
                            ),
                            title=ft.Text(val.get("name", "مجهول"), color=ft.colors.GREY_400),
                            subtitle=ft.Text("منسحب", color=ft.colors.RED_400, size=13)
                        )
                    )
                else:
                    status_text = f"متأخر {abs(balance)} جمعة" if balance < 0 else ("تم الدفع" if balance == 0 else f"مقدم {balance} جمعة")
                    icon = ft.icons.CANCEL if balance < 0 else ft.icons.CHECK_CIRCLE
                    icon_color = "#e56328" if balance < 0 else ft.colors.LIME_700
                    
                    profile_img = images_cache.get(key) or val.get("img", "profile.png")

                    m_value = val.get("m", 0)
                    if m_value == 1:
                        border_color = ft.colors.ORANGE
                    elif m_value == 2:
                        border_color = ft.colors.ORANGE_900
                    else:
                        border_color = ft.colors.ORANGE_100

                    members_list.controls.append(
                        ft.ListTile(
                            leading=ft.Container(
                                content=ft.CircleAvatar(
                                    content=ft.Image(
                                        src=profile_img,
                                        fit=ft.ImageFit.COVER,
                                        border_radius=50
                                    ),
                                    bgcolor=ft.colors.GREY_900,
                                ),
                                border=ft.border.all(1.5, border_color),
                                border_radius=50,
                                padding=2
                            ),
                            title=ft.Text(val.get("name", "مجهول"), color=ft.colors.GREY_200), 
                            subtitle=ft.Text(status_text, color=ft.colors.GREY_500, size=13), 
                            trailing=ft.Icon(icon, color=icon_color),
                            on_click=lambda _, contact=val.get("contact"): page.launch_url(contact) if contact else None
                        )
                    )
        if not members_list.controls:
            empty_msg = "لا يوجد مطالبين، المشتركين سددوا ما عليهم" if view_mode == "pending" else ("لا يوجد منسحبين" if view_mode == "retracted" else "لا يوجد مشتركين")
            members_list.controls.append(
                ft.Container(
                    padding=20,
                    alignment=ft.alignment.center,
                    content=ft.Text(empty_msg, color=ft.colors.GREY_500, size=16, weight="bold")
                )
            )

        tools_section.update_stats(total, paid, pending)
        display_val = f"{(total_balance - total_withdrawals):,.0f}"
        total_balance_text_header.value = display_val
        total_balance_text_body.value = f"{total_donations:,.0f}"
        total_retracted.value = str(retracted_count)
        try:
            page.update()
        except Exception:
            pass

    def load_data(e=None):
        refresh_button.visible = False
        loading_overlay.visible = True
        try:
            page.update()
        except Exception:
            pass

        def fetch_data():
            nonlocal all_data
            try:
                res = requests.get(DB_URL, timeout=10)
                if res.status_code == 200 and res.json():
                    all_data = res.json()
                    try:
                        page.client_storage.set("data_cache", all_data)
                    except Exception:
                        pass
            except Exception as err:
                print("Fetch error:", err)
                if not all_data:
                    all_data = page.client_storage.get("data_cache") or {}

            loading_overlay.visible = False
            refresh_button.visible = True
            render_data(all_data, search_field.value)
            try:
                page.update()
            except Exception:
                pass
            
            cache_images_background(all_data)

        threading.Thread(target=fetch_data, daemon=True).start()

    def close_onboarding(e):
        try:
            page.client_storage.set("onboarding_seen", "true")
        except Exception:
            pass
        onboarding_container.visible = False
        refresh_button.visible = True
        try:
            page.update()
        except Exception:
            pass
        load_data()

    onboarding_container = ft.Container(
        visible=False, 
        bgcolor=ft.colors.BLACK, 
        alignment=ft.alignment.center, 
        expand=True, 
        content=ft.Column(
            alignment=ft.MainAxisAlignment.CENTER, 
            horizontal_alignment=ft.CrossAxisAlignment.CENTER, 
            controls=[
                ft.Icon(ft.icons.WALLET, size=60, color=ft.colors.ORANGE_400), 
                ft.Text("نحول مدخراتنا الأسبوعية لفرصة إستثمارية حقيقية. يلا إشترك معانا والتزم بـ 1,000 جنيه كل يوم جمعة، كل دا عشان نسوي راس مال ، ونخطط لمشروع يخدمنا في المستقبل ويرفع مكانة الأسرة", size=20, color=ft.colors.GREY_300, text_align=ft.TextAlign.CENTER), 
                ft.Text("أكبر إدخار أسري أسبوعي", size=16, color="grey", text_align=ft.TextAlign.CENTER), 
                ft.Container(height=15), 
                ft.ElevatedButton("ابدأ الاستخدام", on_click=close_onboarding, style=ft.ButtonStyle(bgcolor=ft.colors.ORANGE_600, color=ft.colors.BLACK))
            ]
        )
    )

    def route_change(route):
        page.views.clear()
        
        retracted_container = ft.Container(
            on_click=switch_to_retracted,
            content=ft.Column(
                [ft.Text("المنسحبين", size=14, color=ft.colors.GREY_300), total_retracted], 
                horizontal_alignment=ft.CrossAxisAlignment.CENTER
            )
        )

        header = ft.Card(
            margin=ft.margin.all(0), 
            elevation=5, 
            content=ft.Container(
                padding=20, 
                border_radius=10, 
                gradient=ft.LinearGradient(begin=ft.alignment.bottom_left, end=ft.alignment.top_right, colors=["#110111", "#111212"]), 
                content=ft.Column(
                    spacing=10, 
                    controls=[
                        ft.Row(alignment=ft.MainAxisAlignment.SPACE_BETWEEN, controls=[ft.Row([ft.Text("أموال المشتركين", size=18, color=ft.colors.ORANGE_300), total_balance_text_header, ft.Text("جنيه", size=18, color=ft.colors.ORANGE_400)], spacing=3), build_notification_icon(page)]),
                        ft.Row(
                            alignment=ft.MainAxisAlignment.SPACE_EVENLY, 
                            controls=[
                                ft.Column([ft.Text("الجمعات", size=14, color=ft.colors.GREY_300), ft.Text(str(total_fridays), size=16, weight="bold", color=ft.colors.GREY_300)], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                                ft.VerticalDivider(), 
                                ft.Column([ft.Text("التبرعات", size=14, color=ft.colors.GREY_300), total_balance_text_body], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                                ft.VerticalDivider(), 
                                retracted_container
                            ]
                        )
                    ]
                )
            )
        )
        
        page.views.append(
            ft.View(
                "/", 
                bgcolor=ft.colors.BLACK, 
                padding=ft.padding.only(top=50, left=15, right=15), 
                controls=[ft.Stack(expand=True, controls=[ft.Column([header, tools_section, search_field, members_list], spacing=5), loading_overlay, onboarding_container])], 
                floating_action_button=refresh_button
            )
        )
        
        if page.route == "/notifications": 
            page.views.append(get_notifications_view(page))
            
        try:
            page.update()
        except Exception:
            pass

    page.on_route_change = route_change
    page.go("/")

    if all_data:
        render_data(all_data, search_field.value)
        cache_images_background(all_data)

    if not page.client_storage.get("onboarding_seen"): 
        onboarding_container.visible = True
        try:
            page.update()
        except Exception:
            pass
    else: 
        refresh_button.visible = True
        load_data()

if __name__ == "__main__":
    ft.app(target=main)
