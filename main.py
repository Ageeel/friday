import flet as ft
import requests
import json
import os
import threading
from datetime import datetime

# إعدادات
CACHE_FILE = "data_cache.json"
DB_URL = "https://alwafa-afcc1-default-rtdb.firebaseio.com/friday.json"

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
    page.padding = 15 # هامش عام بسيط

    # --- أدوات الإحصائيات ---
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
    
    # --- صندوق البحث ---
    search_field = ft.TextField(
        hint_text="ابحث عن اسم المشترك...",
        prefix_icon=ft.icons.SEARCH,
        bgcolor=ft.colors.GREY_900,
        border=ft.InputBorder.NONE,
        border_radius=10,
        content_padding=15,
        color=ft.colors.WHITE,
    )

    members_list = ft.ListView(expand=True, spacing=0)
    
    def update_ui(data):
        members_list.controls.clear()
        total, paid, pending = 0, 0, 0
        for key, val in data.items():
            if not isinstance(val, dict) or "name" not in val: continue
            
            # الفلترة بناءً على البحث
            if search_field.value and search_field.value.lower() not in val.get("name", "").lower():
                continue
                
            total += 1
            is_paid = (val.get("status") == "تم الدفع")
            if is_paid: paid += 1
            else: pending += 1
            
            members_list.controls.append(
                ft.ListTile(
                    leading=ft.Container(content=ft.Icon(ft.icons.PERSON, color=ft.colors.ORANGE_400), 
                                         bgcolor=ft.colors.GREY_800, width=40, height=40, border_radius=20, alignment=ft.alignment.center),
                    title=ft.Text(val.get("name"), color=ft.colors.GREY_300, weight="bold"),
                    subtitle=ft.Text(f"عليه {get_fridays_count()} جمعة ، المبلغ {val.get('amount')}", color=ft.colors.GREY_500),
                    trailing=ft.Icon(ft.icons.CHECK_CIRCLE if is_paid else ft.icons.CANCEL, 
                                     color="lime" if is_paid else ft.colors.RED_400)
                )
            )
        tools_section.total_members.value = str(total)
        tools_section.paid_members.value = str(paid)
        tools_section.pending_members.value = str(pending)
        page.update()

    search_field.on_change = lambda e: update_ui(cached_data)

    def load_data(e=None):
        global cached_data
        if os.path.exists(CACHE_FILE):
            with open(CACHE_FILE, "r", encoding="utf-8") as f:
                cached_data = json.load(f)
                update_ui(cached_data)
        # ... (باقي كود التحميل)

    fridays = get_fridays_count()
    
    # الهيدر (بدون عرض ثابت ليتمدد تلقائياً)
    header = ft.Container(
        content=ft.Text(f"عدد الجُمع: ({fridays})   - برصيد 57742", size=13, color=ft.colors.GREY_400),
        bgcolor=ft.colors.GREY_900, padding=15, border_radius=5
    )

    # إضافة العناصر بالترتيب المطلوب
    page.add(header, tools_section, search_field, members_list)
    
    page.floating_action_button = ft.FloatingActionButton(
        icon=ft.icons.REFRESH, on_click=load_data, bgcolor=ft.colors.ORANGE_400, height=45, width=45
    )

    threading.Thread(target=load_data, daemon=True).start()

ft.app(target=main, view=ft.AppView.WEB_BROWSER)
