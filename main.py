import flet as ft
import requests
import json
import os
from datetime import datetime
from notifications import get_notifications_view

# إعدادات الروابط والملفات
DB_URL = "https://alwafa-afcc1-default-rtdb.firebaseio.com/.json"
CACHE_FILE = os.path.join(os.path.expanduser(""), "data_cache.json")
GREY = ft.colors.GREY_600

def get_fridays_count():
    start_date = datetime(2026, 6, 19) 
    today = datetime.now()
    delta = today - start_date
    return delta.days // 7

def main(page: ft.Page):
    page.title = "كل جمعة"
    page.rtl = True
    page.bgcolor = ft.colors.BLACK
    page.fonts = {"font": "font/ar.ttf"}
    page.theme = ft.Theme(font_family="font", color_scheme=ft.ColorScheme(primary=ft.colors.ORANGE_400))
    page.padding = 0

    all_data = {}
    members_list = ft.ListView(expand=True, spacing=0)
    total_balance_text = ft.Text("الرصيد 0", size=14, color=ft.colors.GREY_400)
    total_retracted = ft.Text("المنسحبين 0", size=14, color=ft.colors.GREY_400)
    loading_overlay = ft.Container(visible=False, bgcolor=ft.colors.with_opacity(0.8, ft.colors.BLACK), alignment=ft.alignment.center, expand=True, content=ft.ProgressRing())

    class Tools(ft.Container):
        def __init__(self):
            super().__init__()
            self.total_members = ft.Text("0", color=ft.colors.GREY_500, size=24, weight="bold")
            self.paid_members = ft.Text("0", color="lime", size=24, weight="bold")
            self.pending_members = ft.Text("0", color="#e56328", size=24, weight="bold")
            self.content = ft.Row(spacing=5, controls=[
                self.tool_item("المشتركين", self.total_members),
                self.tool_item("المسددين", self.paid_members),
                self.tool_item("المطالبين", self.pending_members)
            ])
        def tool_item(self, title, counter):
            color = ft.colors.GREY_500 if title == "المشتركين" else (ft.colors.LIME_300 if title == "المسددين" else "#e56328")
            return ft.Container(expand=True, height=80, bgcolor=ft.colors.GREY_900, border_radius=5, padding=10,
                content=ft.Column(alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                                  controls=[ft.Text(title, color=color, size=12), counter]))
        def update_stats(self, total, paid, pending):
            self.total_members.value = str(total); self.paid_members.value = str(paid); self.pending_members.value = str(pending)

    tools_section = Tools()
    search_field = ft.TextField(hint_text="ابحث عن اسم المشترك...", hint_style=ft.TextStyle(color=ft.colors.GREY_600, size=14), prefix_icon=ft.icons.SEARCH, bgcolor=ft.colors.GREY_900, color=ft.colors.WHITE, border=ft.InputBorder.NONE, border_radius=20, content_padding=14, on_change=lambda e: render_data(all_data, e.control.value))

    def render_data(data, query=""):
        members_list.controls.clear()
        total, paid, pending, retracted_count, total_balance = 0, 0, 0, 0, 0
        if data:
            for key, val in data.items():
                if isinstance(val, dict) and val.get('ret') == True: retracted_count += 1; continue
                if query and query not in val.get("name", ""): continue
                total += 1; total_balance += val.get("amount", 0)
                if val.get("status") == "دفع":
                    status_text = f"مقدم {val.get('to')} جمعة" if val.get('to', 0) > 0 else "تم الدفع"
                    paid += 1
                else:
                    status_text = f"متأخر {val.get('has')} جمعة"
                    pending += 1
                members_list.controls.append(ft.ListTile(leading=ft.CircleAvatar(content=ft.Icon(ft.icons.PERSON, color=ft.colors.ORANGE_400), bgcolor=ft.colors.GREY_900), title=ft.Text(val.get("name", "مجهول"), color=ft.colors.GREY_200),
subtitle= ft.Text(status_text, color=ft.colors.GREY_500, size=13), trailing=ft.Icon(ft.icons.CHECK_CIRCLE if val.get("status") == "دفع" else ft.icons.CANCEL, color=ft.colors.LIME_600 if val.get("status") == "دفع" else "#e56328")))
        tools_section.update_stats(total, paid, pending); total_balance_text.value = f"الرصيد {total_balance}"; total_retracted.value = f"المنسحبين {retracted_count}"; page.update()

    def load_data(e=None):
        nonlocal all_data
        loading_overlay.visible = True; page.update()
        try:
            res = requests.get(DB_URL, timeout=10)
            if res.status_code == 200: all_data = res.json(); render_data(all_data)
        except:
            if os.path.exists(CACHE_FILE):
                with open(CACHE_FILE, "r", encoding="utf-8") as f: all_data = json.load(f); render_data(all_data)
        loading_overlay.visible = False; page.update()

    def route_change(route):
        page.views.clear()
        header = ft.Container(bgcolor=ft.colors.GREY_900, padding=15, border_radius=10, content=ft.Row(alignment=ft.MainAxisAlignment.SPACE_BETWEEN, controls=[ft.Text(f"الجمعات {get_fridays_count()}", size=14, color=ft.colors.GREY_400), total_balance_text, total_retracted, ft.IconButton(ft.icons.NOTIFICATIONS, icon_color=GREY, on_click=lambda _: page.go("/notifications"))]))
        
        # الرئيسية
        page.views.append(ft.View("/", bgcolor=ft.colors.BLACK, padding=ft.padding.only(top=40, left=15, right=15), controls=[ft.Stack(expand=True, controls=[ft.Column([header, tools_section, search_field, members_list], spacing=5), loading_overlay])], floating_action_button=ft.FloatingActionButton(icon=ft.icons.REFRESH, bgcolor=ft.colors.ORANGE_600, on_click=load_data, width=45, height=45)))
      
        if page.route == "/notifications":
            page.views.append(get_notifications_view(page))
        
        page.update()

    page.on_route_change = route_change
    page.go("/notifications")
    load_data()

ft.app(target=main, view=ft.AppView.WEB_BROWSER)
