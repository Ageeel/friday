import flet as ft
import requests
import json
import os
import threading

# ملف التخزين المحلي للعمل بدون إنترنت
CACHE_FILE = "data_cache.json"
DB_URL = "https://alwafa-afcc1-default-rtdb.firebaseio.com/friday.json"

def main(page: ft.Page):
    page.title = "كل جمعة"
    page.rtl = True
    page.bgcolor = ft.colors.BLACK
    page.theme = ft.Theme(color_scheme=ft.ColorScheme(primary=ft.colors.ORANGE_400))

    # --- الحاويات العلوية ---
    class Tools(ft.Container):
        def __init__(self):
            super().__init__()
            self.total_members = ft.Text("0", color=ft.colors.WHITE, size=24, weight="bold")
            self.paid_members = ft.Text("0", color=ft.colors.GREEN, size=24, weight="bold")
            self.pending_members = ft.Text("0", color=ft.colors.RED, size=24, weight="bold")
            self.content = ft.Row(
                spacing=10,
                controls=[
                    self.tool_item("المشتركين", self.total_members),
                    self.tool_item("المسدد", self.paid_members),
                    self.tool_item("المطلوب", self.pending_members)
                ]
            )
        def tool_item(self, title, counter):
            return ft.Container(
                expand=True, height=90, bgcolor=ft.colors.GREY_900, border_radius=15, padding=10,
                content=ft.Column(alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                                  controls=[ft.Text(title, color=ft.colors.ORANGE_400, size=12), counter])
            )

    tools_section = Tools()
    members_list = ft.ListView(expand=True, spacing=0)
    
    # --- دالة تحديث الواجهة ---
    def update_ui(data):
        members_list.controls.clear()
        total, paid, pending = 0, 0, 0
        for key, val in data.items():
            # فلترة البيانات لضمان عدم عرض عناصر فارغة
            if not isinstance(val, dict) or "name" not in val: continue
            
            total += 1
            is_paid = (val.get("status") == "تم الدفع")
            if is_paid: paid += 1
            else: pending += 1
            
            members_list.controls.append(
                ft.ListTile(
                    leading=ft.Container(content=ft.Icon(ft.icons.PERSON, color=ft.colors.ORANGE_400), 
                                         bgcolor=ft.colors.GREY_800, width=40, height=40, border_radius=20, alignment=ft.alignment.center),
                    title=ft.Text(val.get("name"), color=ft.colors.WHITE, weight="bold"),
                    subtitle=ft.Text(f"المبلغ: {val.get('amount')} | {val.get('date')}", color=ft.colors.GREY_600),
                    trailing=ft.Icon(ft.icons.CHECK_CIRCLE if is_paid else ft.icons.CANCEL, 
                                     color=ft.colors.GREEN if is_paid else ft.colors.RED)
                )
            )
        tools_section.total_members.value = str(total)
        tools_section.paid_members.value = str(paid)
        tools_section.pending_members.value = str(pending)
        page.update()

    # --- دالة تحميل البيانات ---
    def load_data(e=None):
        # 1. تحميل محلي (Offline)
        if os.path.exists(CACHE_FILE):
            with open(CACHE_FILE, "r", encoding="utf-8") as f:
                update_ui(json.load(f))

        # 2. تحميل من الإنترنت (Online)
        try:
            response = requests.get(DB_URL, timeout=5)
            if response.status_code == 200:
                online_data = response.json()
                if online_data:
                    # حفظ النسخة الجديدة محلياً
                    with open(CACHE_FILE, "w", encoding="utf-8") as f:
                        json.dump(online_data, f, ensure_ascii=False)
                    update_ui(online_data)
        except:
            pass 

    # --- بناء الصفحة ---
    header = ft.Container(content=ft.Text("كل جمعة", size=30, weight="bold", color=ft.colors.ORANGE_400), padding=10)
    page.add(header, tools_section, ft.Divider(color=ft.colors.TRANSPARENT), members_list)
    
    page.floating_action_button = ft.FloatingActionButton(
        icon=ft.icons.REFRESH, on_click=load_data, bgcolor=ft.colors.ORANGE_400
    )

    # التحميل الأولي في الخلفية
    threading.Thread(target=load_data, daemon=True).start()

ft.app(target=main, view=ft.AppView.WEB_BROWSER)
