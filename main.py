import flet as ft
import requests
import json
import os
import threading
import time
from datetime import datetime
from plyer import notification

# إعدادات
CACHE_FILE = "data_cache.json"
DB_URL = "https://alwafa-afcc1-default-rtdb.firebaseio.com/friday.json"
NOTIFICATIONS_URL = "https://alwafa-afcc1-default-rtdb.firebaseio.com/notifications.json"

# متغير عالمي للنقطة الحمراء
notification_badge_icon = ft.IconButton(icon=ft.icons.NOTIFICATIONS, icon_color="#e5Fee5", size=20)
notification_badge = ft.Badge(content=notification_badge_icon, visible=False)

def get_fridays_count():
    start_date = datetime(2026, 6, 1)
    today = datetime.now()
    delta = today - start_date
    return delta.days // 7

def check_notifications(page):
    """دالة تعمل في الخلفية لجلب الإشعارات"""
    last_count = 0
    while True:
        try:
            response = requests.get(NOTIFICATIONS_URL)
            if response.status_code == 200:
                data = response.json()
                if data:
                    current_list = list(data.values())
                    if len(current_list) > last_count:
                        last_count = len(current_list)
                        new_item = current_list[-1]
                        # إرسال إشعار للنظام
                        notification.notify(
                            title=new_item.get("title", "تنبيه جديد"),
                            message=new_item.get("message", "هناك تحديث جديد في التطبيق"),
                            app_name='تطبيق الجمعة',
                            timeout=10
                        )
                        notification_badge.visible = True
                        page.update()
        except Exception as e:
            print(f"Error checking notifications: {e}")
        time.sleep(300) # فحص كل 5 دقائق

def main(page: ft.Page):
    page.title = "كل جمعة"
    page.rtl = True
    page.bgcolor = ft.colors.BLACK
    page.fonts = {"font": "font/ar.ttf"}
    page.theme = ft.Theme(font_family="font", color_scheme=ft.ColorScheme(primary=ft.colors.ORANGE_400))
    page.padding = 15

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
    search_field = ft.TextField(hint_text="ابحث عن اسم المشترك...", prefix_icon=ft.icons.SEARCH, bgcolor=ft.colors.GREY_900, border=ft.InputBorder.NONE, border_radius=20, content_padding=15, color=ft.colors.WHITE)
    members_list = ft.ListView(expand=True, spacing=0)

    def update_ui(data):
        members_list.controls.clear()
        # ... (منطق التحديث الخاص بك كما هو) ...
        page.update()

    # تشغيل مراقب الإشعارات
    threading.Thread(target=check_notifications, args=(page,), daemon=True).start()

    fridays = get_fridays_count()
    
    # الهيدر مع الـ Badge
    header = ft.Container(
        bgcolor=ft.colors.GREY_900, padding=15, border_radius=5,
        content=ft.Row([
            ft.Text(f"عدد الجُمع: ({fridays}) - برصيد 57742", size=13, color=ft.colors.GREY_400),
            notification_badge
        ])
    )

    page.add(header, tools_section, search_field, members_list)
    page.floating_action_button = ft.FloatingActionButton(icon=ft.icons.REFRESH, bgcolor=ft.colors.ORANGE_400, height=45, width=45)

ft.app(target=main)
