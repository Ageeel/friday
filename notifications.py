import flet as ft
import json
import os
import requests
import threading

# init variables
BG_COLOR = "#0D0D0D"
CARD_COLOR = "#1A1A1A"
ACCENT_GREEN = ft.colors.LIME_600
TEXT_COLOR = ft.colors.GREY_200
FIREBASE_URL = "https://alwafa-afcc1-default-rtdb.firebaseio.com/noti.json"
NOTIFICATIONS_FILE = "notifications.json"
COUNT_FILE = "last_count.json"

def notification_card(text, amount, type, date):
    config = {
        "w": {"text": f"سحب {amount:,.0f}", "color": "#c94559", "icon": ft.icons.CALL_MADE},
        "d": {"text": f"إيداع {amount:,.0f}", "color": ACCENT_GREEN, "icon": ft.icons.CALL_RECEIVED},
        "don":{"text": f"تبرع بمبلغ {amount:,.0f}", "color": ft.colors.TEAL_100,"icon": ft.icons.MONETIZATION_ON},
        "s": {"text": "مشترك جديد", "color": "#79a995", "icon": ft.icons.PERSON_ADD_ALT_1},
        "u": {"text": "إنسحاب مشترك", "color": "#e56328", "icon": ft.icons.PERSON_REMOVE_ALT_1}
    }.get(type, {"text": "إشعار عام", "color": "#BDBDBD", "icon": ft.icons.NOTIFICATIONS_OUTLINED})

    return ft.Container(
        content=ft.Row(
            controls=[
                ft.Container(
                    content=ft.Icon(config["icon"], color=config["color"], size=22),
                    padding=10,
                    bgcolor="#323232",
                    border_radius=12
                ),
                ft.Column(
                    controls=[
                        ft.Text(config["text"], color=TEXT_COLOR, weight=ft.FontWeight.BOLD, size=15),
                        ft.Text(text, color="#9E9E9E", size=14),
                        ft.Text("في يوم " + date, color="#616161", size=12)
                    ],
                    alignment=ft.MainAxisAlignment.CENTER,
                    spacing=5,
                    expand=True
                )
            ],
            spacing=10,
            vertical_alignment=ft.CrossAxisAlignment.START
        ),
        padding=ft.padding.only(right=10, left=10, top=10, bottom=15),
        bgcolor=CARD_COLOR,
        border_radius=15,
        #border=ft.border.all(1, "#333333"),
        margin=ft.margin.only(bottom=10)
    )

def get_notifications_view(page: ft.Page):
    notif_list = ft.ListView(expand=True, spacing=0)
    loading_ring = ft.ProgressRing(color=ft.colors.ORANGE_600)
    loading_container = ft.Container(content=loading_ring, alignment=ft.alignment.center, expand=True)
    
    view = ft.View("/notifications", bgcolor=BG_COLOR, padding=20, controls=[loading_container])

    def fetch_data():
        total_deposit, total_withdraw = 0, 0
        data = None
        try:
            response = requests.get(FIREBASE_URL, timeout=5)
            if response.status_code == 200:
                data = response.json()
                items = data.values() if isinstance(data, dict) else data
                with open(COUNT_FILE, "w") as f: json.dump(len(items), f)
                with open(NOTIFICATIONS_FILE, "w", encoding="utf-8") as f: json.dump(data, f, ensure_ascii=False)
        except:
            if os.path.exists(NOTIFICATIONS_FILE):
                with open(NOTIFICATIONS_FILE, "r", encoding="utf-8") as f: data = json.load(f)

        if data:
            items = data.values() if isinstance(data, dict) else data
            for item in items:
                if item:
                    notif_list.controls.append(notification_card(item.get('noti', ''), item.get('amount', 0), item.get('type'), item.get('date', '')))
                    if item.get("type") == "d": total_deposit += item.get("amount", 0)
                    elif item.get("type") == "w": total_withdraw += item.get("amount", 0)
        
        header = ft.Container(gradient=ft.LinearGradient(begin=ft.alignment.bottom_left, end=ft.alignment.top_right, colors=["#211111", "#222822"]),
        content=ft.Row([
            ft.Column([ft.Text("إجمالي الودائع", color=ACCENT_GREEN, size=14), ft.Text(f"{total_deposit:,.0f}", color=ACCENT_GREEN, size=20, weight=ft.FontWeight.BOLD)], expand=True, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            ft.VerticalDivider(width=1, color="#333333"),
            ft.Column([ft.Text("إجمالي السحب", color="#c94559", size=14), ft.Text(f"{total_withdraw:,.0f}", color="#c94559", size=20, weight=ft.FontWeight.BOLD)], expand=True, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
        ]), padding=20, bgcolor=CARD_COLOR, border_radius=20, margin=ft.margin.only(top=30))
        
        view.controls = [header, notif_list]
        view.floating_action_button = ft.FloatingActionButton(icon=ft.icons.ARROW_FORWARD, bgcolor=ft.colors.ORANGE_600, on_click=lambda _: page.go("/"), width=45, height=45)
        page.update()

    threading.Thread(target=fetch_data, daemon=True).start()
    return view

def build_notification_icon(page):
    try:
        res = requests.get(FIREBASE_URL, timeout=3).json()
        current_count = len(res) if res else 0
    except: current_count = 0
    
    saved_count = 0
    if os.path.exists(COUNT_FILE):
        try:
            with open(COUNT_FILE, "r") as f:
                content = f.read()
                if content:
                    saved_count = json.loads(content)
        except (json.JSONDecodeError, ValueError):
            saved_count = 0
            
    has_new = current_count > saved_count
    return ft.Stack([
        ft.IconButton(icon=ft.icons.NOTIFICATIONS,icon_color=ft.colors.GREY_400, on_click=lambda _: page.go("/notifications")),
        ft.Container(content=ft.CircleAvatar(bgcolor=ft.colors.RED, radius=5), visible=has_new, top=5, right=5)
    ])
