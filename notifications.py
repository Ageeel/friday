import flet as ft
import json
import os
import requests
import threading

# --- Global Configurations ---
BG_COLOR = "#0D0D0D"
CARD_COLOR = "#1A1A1A"
ACCENT_GREEN = ft.colors.LIME_600
TEXT_COLOR = ft.colors.GREY_200
FIREBASE_URL = "https://alwafa-afcc1-default-rtdb.firebaseio.com/noti.json"
NOTIFICATIONS_FILE = "notifications.json"
COUNT_FILE = "last_count.json"

class NotificationCard(ft.Container):
    """Encapsulates the notification card layout, styling, and external image launcher."""
    def __init__(self, page: ft.Page, text: str, amount: float, noti_type: str, date: str, img_url: str = None):
        self.page = page
        
        # Configure icon and color based on notification type
        config = {
            "w": {"text": f"سحب {amount:,.0f}", "color": "#c94559", "icon": ft.icons.CALL_MADE},
            "d": {"text": f"إيداع {amount:,.0f}", "color": ACCENT_GREEN, "icon": ft.icons.CALL_RECEIVED},
            "don": {"text": f"تبرع بمبلغ {amount:,.0f}", "color": ft.colors.TEAL_100, "icon": ft.icons.MONETIZATION_ON},
            "s": {"text": "مشترك جديد", "color": "#79a995", "icon": ft.icons.PERSON_ADD_ALT_1},
            "u": {"text": "إنسحاب مشترك", "color": "#e56328", "icon": ft.icons.PERSON_REMOVE_ALT_1}
        }.get(noti_type, {"text": "إشعار عام", "color": "#BDBDBD", "icon": ft.icons.NOTIFICATIONS_OUTLINED})

        # Main layout elements: Title and Notification text first
        card_columns = [
            ft.Text(config["text"], color=TEXT_COLOR, weight=ft.FontWeight.BOLD, size=15),
            ft.Text(text, color="#9E9E9E", size=14)
        ]

        # Verify if img_url is valid and non-empty string
        if img_url and isinstance(img_url, str) and img_url.strip():
            # Compact "Bankak Notification" button with explicit icon size control
            view_img_btn = ft.TextButton(
                content=ft.Row(
                    controls=[
                        # تحكم بحجم الأيقونة هنا مباشرة عبر size (يمكنك تغيير 16 إلى أي حجم تريد)
                        ft.Icon(ft.icons.CHECK_CIRCLE, size=16, color=ft.colors.LIME_600),
                        ft.Text("إشعار بنكك", color=ft.colors.LIME_600, size=13)
                    ],
                    spacing=5,
                    tight=True
                ),
                style=ft.ButtonStyle(
                    padding=ft.padding.all(0)
                ),
                on_click=lambda _: self._launch_image_url(img_url.strip())
            )
            card_columns.append(
                ft.Container(
                    content=view_img_btn, 
                    margin=ft.margin.only(top=2, bottom=2)
                )
            )

        # Append the date at the very bottom
        card_columns.append(ft.Text("في يوم " + date, color="#616161", size=11))

        super().__init__(
            padding=ft.padding.only(right=10, left=10, top=10, bottom=15),
            bgcolor=CARD_COLOR,
            border_radius=15,
            margin=ft.margin.only(bottom=10)
        )
        
        self.content = ft.Row(
            controls=[
                ft.Container(
                    content=ft.Icon(config["icon"], color=config["color"], size=22),
                    padding=10,
                    bgcolor="#323232",
                    border_radius=12
                ),
                ft.Column(
                    controls=card_columns,
                    alignment=ft.MainAxisAlignment.CENTER,
                    spacing=3,
                    expand=True
                )
            ],
            spacing=10,
            vertical_alignment=ft.CrossAxisAlignment.START
        )

    def _launch_image_url(self, url: str):
        """Launches the image URL directly in the device's default browser to ensure 100% rendering success."""
        try:
            self.page.launch_url(url)
        except Exception:
            pass

class NotificationManager:
    """Handles data fetching, sorting, and local storage management using requests."""
    def __init__(self):
        self.url = FIREBASE_URL
        self.file_path = NOTIFICATIONS_FILE
        self.count_path = COUNT_FILE

    def fetch_sorted_notifications(self) -> list:
        """Fetches data from Firebase or local cache and returns a chronologically sorted list (newest first)."""
        data = None
        try:
            response = requests.get(self.url, timeout=5)
            if response.status_code == 200:
                data = response.json()
                if data:
                    with open(self.count_path, "w") as f:
                        json.dump(len(data), f)
                    with open(self.file_path, "w", encoding="utf-8") as f:
                        json.dump(data, f, ensure_ascii=False)
        except Exception:
            if os.path.exists(self.file_path):
                with open(self.file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)

        sorted_items = []
        if data and isinstance(data, dict):
            sorted_keys = sorted(data.keys(), reverse=True)
            for key in sorted_keys:
                if data[key]:
                    sorted_items.append(data[key])
        elif data and isinstance(data, list):
            sorted_items = list(reversed([item for item in data if item]))
            
        return sorted_items

    def send_notification(self, text: str, amount: float, noti_type: str, date: str, img_url: str = None) -> bool:
        """Sends a new notification using POST request."""
        payload = {
            "noti": text,
            "amount": amount,
            "type": noti_type,
            "date": date
        }
        if img_url and isinstance(img_url, str) and img_url.strip():
            payload["img"] = img_url.strip()

        try:
            response = requests.post(self.url, json=payload, timeout=5)
            return response.status_code == 200
        except Exception:
            return False

    def check_new_notifications(self) -> bool:
        """Compares live data count with saved count to determine if there are new alerts."""
        try:
            res = requests.get(self.url, timeout=3).json()
            current_count = len(res) if res else 0
        except Exception:
            current_count = 0
            
        saved_count = 0
        if os.path.exists(self.count_path):
            try:
                with open(self.count_path, "r") as f:
                    content = f.read()
                    if content:
                        saved_count = json.loads(content)
            except (json.JSONDecodeError, ValueError):
                saved_count = 0
                
        return current_count > saved_count

class NotificationViewManager:
    """Manages the UI creation and thread handling for the notifications screen."""
    def __init__(self, page: ft.Page):
        self.page = page
        self.manager = NotificationManager()
        self.notif_list = ft.ListView(expand=True, spacing=0)
        self.loading_ring = ft.ProgressRing(color=ft.colors.ORANGE_600)
        self.loading_container = ft.Container(content=self.loading_ring, alignment=ft.alignment.center, expand=True)
        self.view = ft.View("/notifications", bgcolor=BG_COLOR, padding=20, controls=[self.loading_container])

    def build_view(self) -> ft.View:
        threading.Thread(target=self._load_data_thread, daemon=True).start()
        return self.view

    def _load_data_thread(self):
        total_deposit = 0
        total_withdraw = 0
        
        items = self.manager.fetch_sorted_notifications()
        
        for item in items:
            self.notif_list.controls.append(
                NotificationCard(
                    page=self.page,
                    text=item.get('noti', ''),
                    amount=item.get('amount', 0),
                    noti_type=item.get('type', ''),
                    date=item.get('date', ''),
                    img_url=item.get('img')
                )
            )
            if item.get("type") == "d":
                total_deposit += item.get("amount", 0)
            elif item.get("type") == "w":
                total_withdraw += item.get("amount", 0)
        
        header = ft.Container(
            gradient=ft.LinearGradient(
                begin=ft.alignment.bottom_left, 
                end=ft.alignment.top_right, 
                colors=["#211111", "#222822"]
            ),
            content=ft.Row([
                ft.Column([
                    ft.Text("إجمالي الودائع", color=ACCENT_GREEN, size=14), 
                    ft.Text(f"{total_deposit:,.0f}", color=ACCENT_GREEN, size=20, weight=ft.FontWeight.BOLD)
                ], expand=True, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                ft.VerticalDivider(width=1, color="#333333"),
                ft.Column([
                    ft.Text("إجمالي السحب", color="#c94559", size=14), 
                    ft.Text(f"{total_withdraw:,.0f}", color="#c94559", size=20, weight=ft.FontWeight.BOLD)
                ], expand=True, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            ]), 
            padding=20, 
            bgcolor=CARD_COLOR, 
            border_radius=20, 
            margin=ft.margin.only(top=30)
        )
        
        self.view.controls = [header, self.notif_list]
        self.view.floating_action_button = ft.FloatingActionButton(
            icon=ft.icons.ARROW_FORWARD, 
            bgcolor=ft.colors.ORANGE_600, 
            on_click=lambda _: self.page.go("/"), 
            width=40, height=40
        )
        self.page.update()

# --- Helper Functions for External Usage ---
def get_notifications_view(page: ft.Page):
    """Bridge function to match your routing system."""
    view_manager = NotificationViewManager(page)
    return view_manager.build_view()

def build_notification_icon(page: ft.Page):
    """Generates the notification button with a dynamic unread badge."""
    manager = NotificationManager()
    has_new = manager.check_new_notifications()
    
    return ft.Stack([
        ft.IconButton(
            icon=ft.icons.NOTIFICATIONS,
            icon_color=ft.colors.GREY_400, 
            on_click=lambda _: page.go("/notifications")
        ),
        ft.Container(
            content=ft.CircleAvatar(bgcolor=ft.colors.RED, radius=5), 
            visible=has_new, 
            top=5, 
            right=5
        )
    ])
