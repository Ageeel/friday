import flet as ft
import requests
import json
import os
from datetime import datetime
from notifications import get_notifications_view, build_notification_icon

# --- الثوابت ---
DB_URL = "https://alwafa-afcc1-default-rtdb.firebaseio.com/sub.json"
CACHE_FILE = os.path.join(os.path.expanduser(""), "data_cache.json")
START_DATE = datetime(2026, 6, 12)
today = datetime.now()
total_fridays = (today - START_DATE).days // 7

# --- وظائف مساعدة ---
def get_total_withdrawals():
    total_w = 0
    if os.path.exists("notifications.json"):
        try:
            with open("notifications.json", "r", encoding="utf-8") as f:
                data = json.load(f)
                for key, val in data.items():
                    if isinstance(val, dict) and val.get("type") == "w":
                        total_w += val.get("amount", 0)
        except: pass
    return total_w

def main(page: ft.Page):
    page.title = "كل جمعة"
    page.rtl = True
    page.bgcolor = ft.colors.BLACK
    page.fonts = {"font": "font/ar.ttf"}
    page.theme = ft.Theme(font_family="font", color_scheme=ft.ColorScheme(primary=ft.colors.ORANGE_400))
    page.padding = 0

    # --- المكونات ---
    all_data = {}
    members_list = ft.ListView(expand=True, spacing=0)
    
    # تعريفات نصوص التوازن للعرض في مكانين
    total_balance_text_header = ft.Text("0", size=20, weight="bold", color=ft.colors.ORANGE_600)
    total_balance_text_body = ft.Text("0", size=16, weight="bold", color=ft.colors.WHITE)
    
    total_retracted = ft.Text("0", size=16, weight="bold", color=ft.colors.WHITE)
    loading_overlay = ft.Container(visible=False, bgcolor=ft.colors.with_opacity(0.8, ft.colors.BLACK), alignment=ft.alignment.center, expand=True, content=ft.Column(alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER, controls=[ft.ProgressRing(), ft.Text("جار التحميل...", color=ft.colors.WHITE, size=16, weight="bold")]))

    refresh_button = ft.FloatingActionButton(icon=ft.icons.REFRESH, bgcolor=ft.colors.ORANGE_600, on_click=lambda e: load_data(), width=45, height=45, visible=False)

    class Tools(ft.Container):
        def __init__(self):
            super().__init__()
            self.total_members = ft.Text("0", color=ft.colors.GREY_300, size=24, weight="bold")
            self.paid_members = ft.Text("0", color="lime", size=24, weight="bold")
            self.pending_members = ft.Text("0", color="#e56328", size=24, weight="bold")
            self.content = ft.Row(spacing=5, controls=[self.tool_item("المشتركين", self.total_members), self.tool_item("المسددين", self.paid_members), self.tool_item("المطالبين", self.pending_members)])
        def tool_item(self, title, counter):
            color = ft.colors.GREY_300 if title == "المشتركين" else (ft.colors.LIME_300 if title == "المسددين" else "#e56328")
            return ft.Container(expand=True, height=80, bgcolor=ft.colors.GREY_900, border_radius=5, padding=10, content=ft.Column(alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER, controls=[ft.Text(title, color=color, size=12), counter]))
        def update_stats(self, total, paid, pending):
            self.total_members.value = str(total); self.paid_members.value = str(paid); self.pending_members.value = str(pending)

    tools_section = Tools()
    search_field = ft.TextField(hint_text="ابحث عن اسم المشترك...", hint_style=ft.TextStyle(color=ft.colors.GREY_600, size=14), prefix_icon=ft.icons.SEARCH, bgcolor=ft.colors.GREY_900, color=ft.colors.WHITE, border=ft.InputBorder.NONE, border_radius=20, content_padding=14, on_change=lambda e: render_data(all_data, e.control.value))

    # --- المنطق ---
    def render_data(data, query=""):
        members_list.controls.clear()
        total, paid, pending, retracted_count, total_balance = 0, 0, 0, 0, 0
        total_withdrawals = get_total_withdrawals()
        if data:
            for key, val in data.items():
                if not isinstance(val, dict) or val.get('ret') == True:
                    if isinstance(val, dict): retracted_count += 1
                    continue
                if query and query not in val.get("name", ""): continue
                total += 1
                total_balance += val.get("amount", 0)
                start_date = datetime.strptime(val.get("start_date", "2026-06-19"), "%Y-%m-%d")
                fridays_passed = (today - start_date).days // 7
                balance = val.get("total_paid", 0) - fridays_passed
                status_text = f"متأخر {abs(balance)} جمعة" if balance < 0 else ("تم الدفع" if balance == 0 else f"مقدم {balance} جمعة")
                icon = ft.icons.CANCEL if balance < 0 else ft.icons.CHECK_CIRCLE
                icon_color = "#e56328" if balance < 0 else ft.colors.LIME_600
                if balance < 0: pending += 1
                else: paid += 1
                
                p_icon_col = ft.colors.ORANGE_100 if val.get("m") == 0 else (ft.colors.ORANGE_600 if val.get("m") == 1 else ft.colors.ORANGE_900)
                members_list.controls.append(ft.ListTile(leading=ft.CircleAvatar(content=ft.Icon(ft.icons.PERSON, color=p_icon_col), bgcolor=ft.colors.GREY_900), title=ft.Text(val.get("name", "مجهول"), color=ft.colors.GREY_200), subtitle=ft.Text(status_text, color=ft.colors.GREY_500, size=13), trailing=ft.Icon(icon, color=icon_color)))
        
        tools_section.update_stats(total, paid, pending)
        display_val = f"{(total_balance - total_withdrawals):,.0f}"
        total_balance_text_header.value = display_val
        total_balance_text_body.value = display_val
        total_retracted.value = str(retracted_count)
        page.update()

    def load_data(e=None):
        nonlocal all_data
        loading_overlay.visible = True; page.update()
        try:
            res = requests.get(DB_URL, timeout=10)
            if res.status_code == 200:
                all_data = res.json()
                with open(CACHE_FILE, "w", encoding="utf-8") as f: json.dump(all_data, f, ensure_ascii=False)
                render_data(all_data)
        except:
            if os.path.exists(CACHE_FILE):
                with open(CACHE_FILE, "r", encoding="utf-8") as f: all_data = json.load(f); render_data(all_data)
        loading_overlay.visible = False; page.update()

    def close_onboarding(e):
        page.client_storage.set("onboarding_seen", "true")
        onboarding_container.visible = False
        refresh_button.visible = True
        page.update()
        load_data()

    onboarding_container = ft.Container(visible=False, bgcolor=ft.colors.BLACK, alignment=ft.alignment.center, expand=True, content=ft.Column(alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER, controls=[ft.Icon(ft.icons.WALLET, size=60, color=ft.colors.ORANGE_400), ft.Text("نحول مدخراتنا الأسبوعية لفرصة إستثمارية حقيقية. يلا إشترك معانا والتزم بـ 1,000 جنيه كل يوم جمعة، كل دا عشان نسوي راس مال ، ونخطط لمشروع يخدمنا في المستقبل ويرفع مكانة الأسرة", size=22, color="white", text_align=ft.TextAlign.CENTER), ft.Text("أكبر إدخار أسري أسبوعي", size=16, color="grey", text_align=ft.TextAlign.CENTER), ft.Container(height=20), ft.ElevatedButton("ابدأ الاستخدام", on_click=close_onboarding, style=ft.ButtonStyle(bgcolor=ft.colors.ORANGE_600, color=ft.colors.BLACK))]))

    def route_change(route):
        page.views.clear()
        header = ft.Card(margin=ft.margin.all(0), elevation=5, content=ft.Container(padding=20, border_radius=10, gradient=ft.LinearGradient(begin=ft.alignment.bottom_left, end=ft.alignment.bottom_right, colors=["#222222", ft.colors.GREY_900]), content=ft.Column(spacing=10, controls=[
            ft.Row(alignment=ft.MainAxisAlignment.SPACE_BETWEEN, controls=[ft.Row([ft.Text("الأموال", size=20, color=ft.colors.ORANGE_300), total_balance_text_header, ft.Text("جنيه", size=20, color=ft.colors.ORANGE_400)]), build_notification_icon(page)]),
            ft.Row(alignment=ft.MainAxisAlignment.SPACE_EVENLY, controls=[
                ft.Column([ft.Text("الجمعات", size=13, color=ft.colors.GREY_300), ft.Text(str(total_fridays), size=16, weight="bold", color=ft.colors.GREY_300)], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                ft.VerticalDivider(), 
                ft.Column([ft.Text("الأموال", size=13, color=ft.colors.GREY_300), total_balance_text_body], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                ft.VerticalDivider(), 
                ft.Column([ft.Text("المنسحبين", size=13, color=ft.colors.GREY_300), total_retracted], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            ])
        ])))
        
        page.views.append(ft.View("/", bgcolor=ft.colors.BLACK, padding=ft.padding.only(top=50, left=15, right=15), controls=[ft.Stack(expand=True, controls=[ft.Column([header, tools_section, search_field, members_list], spacing=5), loading_overlay, onboarding_container])], floating_action_button=refresh_button))
        if page.route == "/notifications": page.views.append(get_notifications_view(page))
        page.update()

    page.on_route_change = route_change
    if not page.client_storage.get("onboarding_seen"): onboarding_container.visible = True
    else: refresh_button.visible = True; load_data()
    page.go("/")

if __name__ == "__main__":
    ft.app(target=main, view=ft.AppView.WEB_BROWSER)
