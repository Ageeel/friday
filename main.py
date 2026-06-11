import flet as ft
import requests
import json
import os
import threading
from datetime import datetime

# إعدادات
CACHE_FILE = "data_cache.json"
DB_URL = "https://alwafa-afcc1-default-rtdb.firebaseio.com/friday.json"


# دالة حساب عدد أيام الجمعة من تاريخ معين
def get_fridays_count():
    start_date = datetime(2026, 6, 1)
    today = datetime.now()
    delta = today - start_date
    return delta.days // 7

def main(page: ft.Page):
    page.title = "كل جمعة"
    page.rtl = True
    page.bgcolor = ft.colors.BLACK
    page.fonts = {"font": "font/ar.ttf"}
    page.theme = ft.Theme(font_family="font", color_scheme=ft.ColorScheme(primary=ft.colors.ORANGE_400))

    class Tools(ft.Container):
        def __init__(self):
            super().__init__()
            self.total_members = ft.Text("0", color=ft.colors.GREY_300, size=24, weight="bold")
            self.paid_members = ft.Text("0", color="lime", size=24, weight="bold")
            self.pending_members = ft.Text("0", color=ft.colors.RED_400, size=24, weight="bold")
            self.content = ft.Row(
                spacing=10,
                controls=[
                    self.tool_item("المشتركين", self.total_members),
                    self.tool_item("المسددين", self.paid_members),
                    self.tool_item("المطالبين", self.pending_members)
                ]
            )
        def tool_item(self, title, counter):
            return ft.Container(
                expand=True, height=80, bgcolor=ft.colors.GREY_900, border_radius=10, padding=10,
                content=ft.Column(alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                                  controls=[ft.Text(title, color=ft.colors.ORANGE_400, size=12), counter])
            )

    tools_section = Tools()
    members_list = ft.ListView(expand=True, spacing=0)
    
    def update_ui(data):
        members_list.controls.clear()
        total, paid, pending = 0, 0, 0
        for key, val in data.items():
            if not isinstance(val, dict) or "name" not in val: continue
            total += 1
            is_paid = (val.get("status") == "تم الدفع")
            if is_paid: paid += 1
            else: pending += 1
            
            members_list.controls.append(
                ft.ListTile(
                    leading=ft.Container(content=ft.Icon(ft.icons.PERSON, color=ft.colors.ORANGE_400), 
                                         bgcolor=ft.colors.GREY_800, width=40, height=40, border_radius=20, alignment=ft.alignment.center),
                    title=ft.Text(val.get("name"), color=ft.colors.GREY_300, weight="bold"),
                    subtitle=ft.Text(f"عليه 3  جمعة ، المبلغ {val.get('amount')}", color=ft.colors.GREY_500),
                    trailing=ft.Icon(ft.icons.CHECK_CIRCLE if is_paid else ft.icons.CANCEL, 
                                     color="lime" if is_paid else ft.colors.RED_400)
                )
            )
        tools_section.total_members.value = str(total)
        tools_section.paid_members.value = str(paid)
        tools_section.pending_members.value = str(pending)
        page.update()

    def load_data(e=None):
        if os.path.exists(CACHE_FILE):
            with open(CACHE_FILE, "r", encoding="utf-8") as f:
                update_ui(json.load(f))
        try:
            response = requests.get(DB_URL, timeout=5)
            if response.status_code == 200:
                online_data = response.json()
                if online_data:
                    with open(CACHE_FILE, "w", encoding="utf-8") as f:
                        json.dump(online_data, f, ensure_ascii=False)
                    update_ui(online_data)
        except:
            pass 

    fridays = get_fridays_count()
    header = ft.Row(
        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
        controls=[
            ft.Container(
                content=ft.Text(f"عدد الجُمع: ({fridays})   - برصيد 57742", size=13, color=ft.colors.GREY_400),
                bgcolor=ft.colors.GREY_900, padding=10, border_radius=5, height=40, width=(page.width - 20))     
        ]
    )

    page.add(header, tools_section, ft.Divider(color=ft.colors.TRANSPARENT), members_list)
    
    page.floating_action_button = ft.FloatingActionButton(
        icon=ft.icons.REFRESH, on_click=load_data, bgcolor=ft.colors.ORANGE_400,height=45, width=45
    )

    threading.Thread(target=load_data, daemon=True).start()

ft.app(target=main, view=ft.AppView.WEB_BROWSER)
