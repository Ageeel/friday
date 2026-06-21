import flet as ft
import json
import os
import requests

# الإعدادات
BG_COLOR = "#0D0D0D"
CARD_COLOR = "#1A1A1A"
ACCENT_ORANGE = "#FF6B00"
ACCENT_GREEN = "#00C853"
TEXT_COLOR = "#E0E0E0"
FIREBASE_URL = "https://alwafa-afcc1-default-rtdb.firebaseio.com/notifications.json"
NOTIFICATIONS_FILE = "notifications.json"

def notification_card(text, amount, type, date):
    # إزالة الفاصلة العشرية باستخدام :.0f
    config = {
        "w": {"text": f"سحب {amount:,.0f}", "color": "#FF5252", "icon": ft.icons.CALL_MADE},
        "d": {"text": f"إيداع {amount:,.0f}", "color": ACCENT_GREEN, "icon": ft.icons.CALL_RECEIVED},
        "s": {"text": "مشترك جديد", "color": "#2979FF", "icon": ft.icons.PERSON_ADD_ALT_1},
        "u": {"text": "إنسحاب مشترك", "color": "#FF9100", "icon": ft.icons.PERSON_REMOVE_ALT_1}
    }.get(type, {"text": "إشعار", "color": "#BDBDBD", "icon": ft.icons.NOTIFICATIONS_OUTLINED})

    return ft.Container(
        content=ft.Row([
            ft.Container(
                content=ft.Icon(config["icon"], color=config["color"], size=22),
                padding=10,
                bgcolor=f"{config['color']}20",
                border_radius=12
            ),
            ft.Column([
                ft.Text(config["text"], color=TEXT_COLOR, weight=ft.FontWeight.BOLD, size=15),
                ft.Text(text, color="#9E9E9E", size=12, max_lines=1, overflow=ft.TextOverflow.ELLIPSIS),
                ft.Text(date, color="#616161", size=10)
            ], alignment=ft.MainAxisAlignment.CENTER, spacing=2, expand=True)
        ], spacing=15),
        padding=15,
        bgcolor=CARD_COLOR,
        border_radius=16,
        border=ft.border.all(1, "#333333"),
        margin=ft.margin.only(bottom=10)
    )

def get_notifications_view(page: ft.Page):
    notif_list = ft.ListView(expand=True, spacing=5)
    total_deposit, total_withdraw = 0, 0
    data = None

    try:
        response = requests.get(FIREBASE_URL, timeout=5)
        if response.status_code == 200:
            data = response.json()
            with open(NOTIFICATIONS_FILE, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False)
    except:
        if os.path.exists(NOTIFICATIONS_FILE):
            with open(NOTIFICATIONS_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)

    if data:
        items = data.values() if isinstance(data, dict) else data
        for item in items:
            if item:
                notif_list.controls.append(notification_card(
                    item.get('noti', ''), item.get('amount', 0), item.get('type'), item.get('date', '')
                ))
                if item.get("type") == "d":
                    total_deposit += item.get("amount", 0)
                elif item.get("type") == "w":
                    total_withdraw += item.get("amount", 0)
    
    return ft.View(
        "/notifications",
        bgcolor=BG_COLOR,
        # إضافة مسافة علوية (50) في بداية الواجهة
        padding=ft.padding.only(top=50, left=20, right=20, bottom=20),
        controls=[
            ft.Container(
                content=ft.Row([
                    ft.Column([ft.Text("إجمالي الودائع", color="#9E9E9E", size=12), ft.Text(f"{total_deposit:,.0f}", color=ACCENT_GREEN, size=20, weight=ft.FontWeight.BOLD)], expand=True, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                    ft.VerticalDivider(width=1, color="#333333"),
                    ft.Column([ft.Text("إجمالي السحب", color="#9E9E9E", size=12), ft.Text(f"{total_withdraw:,.0f}", color="#FF5252", size=20, weight=ft.FontWeight.BOLD)], expand=True, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                ]),
                padding=20,
                bgcolor=CARD_COLOR,
                border_radius=20,
                border=ft.border.all(1, "#333333")
            ),
            notif_list
        ],
        floating_action_button=ft.FloatingActionButton(
            icon=ft.icons.ARROW_BACK,
            bgcolor=ACCENT_ORANGE,
            on_click=lambda _: page.go("/"),
            width=45,
            height=45
        )
    )
