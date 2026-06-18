import flet as ft
import requests
import threading
import time
import json
import os
from datetime import datetime
from plyer import notification

# إعدادات الروابط والملفات
DB_URL = "https://alwafa-afcc1-default-rtdb.firebaseio.com/.json"
NOTIFICATIONS_URL = "https://alwafa-afcc1-default-rtdb.firebaseio.com/notifications.json"

def get_cache_path():
    return os.path.join(os.path.expanduser("~"), "data_cache.json")

CACHE_FILE = get_cache_path()

notification_icon = ft.Container(
    content=ft.Icon(ft.icons.NOTIFICATIONS, color=ft.colors.GREY_600, size=20),
    padding=7,
    bgcolor=ft.colors.BLACK,
    border_radius=24
)

def get_fridays_count():
    start_date = datetime(2026, 6, 19)
    today = datetime.now()
    delta = today - start_date
    return delta.days // 7

def check_notifications(page):
    last_count = 0
    while True:
        try:
            response = requests.get(NOTIFICATIONS_URL, timeout=5)
            if response.status_code == 200:
                data = response.json()
                if data:
                    current_list = list(data.values())
                    if len(current_list) > last_count:
                        last_count = len(current_list)
                        new_item = current_list[-1]
                        notification.notify(title=new_item.get("title", "تنبيه"), message=new_item.get("message", ""), app_name='تطبيق الجمعة', timeout=10)
                        notification_icon.content.color = ft.colors.RED
                        page.update()
        except:
            pass
        time.sleep(300)

def main(page: ft.Page):
    page.title = "كل جمعة"
    page.rtl = True
    page.bgcolor = ft.colors.BLACK
    page.fonts = {"font": "font/ar.ttf"}
    page.theme = ft.Theme(font_family="font", color_scheme=ft.ColorScheme(primary=ft.colors.ORANGE_400))
    page.padding = 15

    all_data = {} 
    
    search_field = ft.TextField(
        hint_text="ابحث عن اسم المشترك...",
        hint_style=ft.TextStyle(color=ft.colors.GREY_600),
        prefix_icon=ft.icons.SEARCH,
        bgcolor=ft.colors.GREY_900,
        color=ft.colors.WHITE,
        border=ft.InputBorder.NONE,
        border_radius=20,
        content_padding=ft.padding.only(left=20, right=20, top=10, bottom=10),
        on_change=lambda e: filter_list(e.control.value)
    )

    loading_overlay = ft.Container(
        content=ft.Column(
            alignment=ft.MainAxisAlignment.CENTER,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            controls=[
                ft.ProgressRing(width=40, height=40, color=ft.colors.ORANGE_400),
                ft.Text("جارٍ التحميل، انتظر قليلاً", color=ft.colors.WHITE, size=16)
            ]
        ),
        visible=False,
        bgcolor=ft.colors.with_opacity(0.8, ft.colors.BLACK),
        alignment=ft.alignment.center,
        expand=True
    )

    class Tools(ft.Container):
        def __init__(self):
            super().__init__()
            self.total_members = ft.Text("0", color=ft.colors.GREY_500, size=24, weight="bold")
            self.paid_members = ft.Text("0", color="lime", size=24, weight="bold")
            self.pending_members = ft.Text("0", color="#e56328", size=24, weight="bold")
            self.content = ft.Row(spacing=5, controls=[
                self.tool_item("المشتركون", self.total_members),
                self.tool_item("المسددون", self.paid_members),
                self.tool_item("المطالبون", self.pending_members)
            ])

        def tool_item(self, title, counter):
            if title == "المشتركون":
                title_color = ft.colors.GREY_500
            elif title == "المسددون":
                title_color = ft.colors.LIME_300
            else: 
                title_color = "#e56328"
 
            return ft.Container(expand=True, height=80, bgcolor=ft.colors.GREY_900, border_radius=5, padding=10,
                content=ft.Column(alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                                  controls=[ft.Text(title, color=title_color, size=12), counter]))

        def update_stats(self, total, paid, pending):
            self.total_members.value = str(total)
            self.paid_members.value = str(paid)
            self.pending_members.value = str(pending)

    tools_section = Tools()
    members_list = ft.ListView(expand=True, spacing=0)
    total_balance_text = ft.Text("الرصيد 0", size=14, color=ft.colors.GREY_400)
    total_retracted = ft.Text("المنسحبون 0", size=14, color=ft.colors.GREY_400)

    def filter_list(query):
        render_data(all_data, query)

    def render_data(data, query=""):
        members_list.controls.clear()
        total, paid, pending, retracted_count, total_balance = 0, 0, 0, 0, 0
        
        if data:
            for key, val in data.items():
                if isinstance(val, dict) and val.get('ret') == True:
                    retracted_count += 1
                    continue
                
                if query and query not in val.get("name", ""):
                    continue
                    
                total += 1
                has_count, to_count = val.get('has', 0), val.get('to', 0)
                total_balance += val.get("amount", 0)

                if val.get("status") == "دفع":
                    icon = ft.icons.CHECK_CIRCLE
                    color = ft.colors.LIME_600
                    status = f"مقدم {to_count} جمعة" if to_count > 0 else "تم الدفع"
                    paid += 1
                else:
                    icon = ft.icons.CANCEL
                    color = "#e56328"
                    status = f"مطالب {has_count} جمعة"
                    pending += 1
                   
                members_list.controls.append(ft.ListTile(
                    leading=ft.CircleAvatar(content=ft.Icon(ft.icons.PERSON, color=ft.colors.ORANGE_400), bgcolor=ft.colors.GREY_900),
                    title=ft.Text(val.get("name", "مجهول"), color=ft.colors.GREY_200),
                    subtitle=ft.Text(f"{status}", color=ft.colors.GREY_600, size=13),
                    trailing=ft.Icon(icon, color=color)
                ))
        
        tools_section.update_stats(total, paid, pending)
        total_balance_text.value = f"الرصيد {total_balance}"
        total_retracted.value = f"المنسحبون {retracted_count}"
        
        members_list.update()
        tools_section.update()
        page.update()

    def load_data(e=None):
        nonlocal all_data
        loading_overlay.visible = True
        page.update()
        try:
            response = requests.get(DB_URL, timeout=10)
            if response.status_code == 200:
                all_data = response.json()
                with open(CACHE_FILE, "w", encoding="utf-8") as f:
                    json.dump(all_data, f, ensure_ascii=False)
                render_data(all_data)
        except:
            if os.path.exists(CACHE_FILE):
                with open(CACHE_FILE, "r", encoding="utf-8") as f:
                    all_data = json.load(f)
                    render_data(all_data)
        loading_overlay.visible = False
        page.update()

    header = ft.Container(bgcolor=ft.colors.GREY_900, padding=15, border_radius=10,
        content=ft.Row(alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            controls=[ft.Text(f"الجمعات {get_fridays_count()}", size=14, color=ft.colors.GREY_400), total_balance_text, total_retracted, notification_icon]))

    page.add(ft.Stack(expand=True, controls=[ft.Column([header, tools_section, search_field, members_list], spacing=5), loading_overlay]))
    page.floating_action_button = ft.FloatingActionButton(icon=ft.icons.REFRESH, bgcolor=ft.colors.ORANGE_400, on_click=load_data, height=45, width=45)
    
    threading.Thread(target=check_notifications, args=(page,), daemon=True).start()
    load_data()



ft.app(target=main, view=ft.AppView.WEB_BROWSER)
