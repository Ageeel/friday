import flet as ft
import json
import os

GREY = ft.colors.GREY_600
NOTIFICATIONS_FILE = "notifications.json"

def notification_card(text, amount, type, date):
    if type == "w":
        f_amount = f"{amount:,.2f}".rstrip('0').rstrip('.')
        t_text = f"سحب {f_amount} جنيه"
        t_color = "#F95325"
        t_icon = ft.icons.CHECK_CIRCLE
    elif type == "d":
        f_amount = f"{amount:,.2f}".rstrip('0').rstrip('.')
        t_text = f"إيداع {f_amount} جنيه"
        t_color = ft.colors.LIME_700
        t_icon = ft.icons.BED
    elif type == "s":
        t_text = "مشترك جديد"
        t_color = "teal"
        t_icon = ft.icons.PERSON
    elif type == "u":
        t_text = "إنسحاب مشترك"
        t_color = "orange"
        t_icon = ft.icons.PERSON
    else:
        t_text = "إشعار للمشتركين"
        t_color = "#F7e8DC"
        t_icon = ft.icons.NOTIFICATIONS
        
    return ft.Container(
        bgcolor= "#161515",
        margin=ft.margin.only(left=10, right=10),
        padding=ft.padding.all(10),
        height=105,
        border_radius=5,
        content=ft.Column(controls=[
            ft.Row([ft.Icon(t_icon, size=16, color=t_color), ft.Text(t_text, color=t_color, size=14)], spacing=5),
            ft.Text(text, color=ft.colors.GREY_500),
            ft.Text(f"يوم {date}", color=GREY, size=12)
        ])
    )

def get_notifications_view(page: ft.Page):
    notif_list = ft.ListView(expand=True, spacing=5)
    total_deposit, total_withdraw = 0, 0
    
    if os.path.exists(NOTIFICATIONS_FILE):
        with open(NOTIFICATIONS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            for item in data.get("notifications", []):
                notif_list.controls.append(notification_card(
                    item.get('noti'), item.get('amount', 0), item.get('type'), item.get('date')
                ))
                if item.get("type") == "d":
                    total_deposit += item.get("amount", 0)
                elif item.get("type") == "w":
                    total_withdraw += item.get("amount", 0)
                    
    return ft.View(
        "/notifications", 
        bgcolor=ft.colors.BLACK, 
        padding=ft.padding.only(top=5), 
        controls=[
            # الحاوية العليا المعدلة للأرصدة
            ft.Container(
                bgcolor="#161515",
                height=90,
                margin=ft.margin.only(left=10, right=10),
                padding=ft.padding.symmetric(horizontal=20, vertical=10),
                border_radius=10,
                content=ft.Row(
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    spacing=20, # إضافة مسافة
                    controls=[
                        # عمود الودائع
                        ft.Column([
                            ft.Text("إجمالي الودائع", size=12, color=GREY),
                            ft.Text(f"{total_deposit:,.2f}", size=18, color=ft.colors.LIME_700, weight=ft.FontWeight.BOLD)
                        ], alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.START),
                        
                        # عمود السحب
                        ft.Column([
                            ft.Text("إجمالي السحب", size=12, color=GREY),
                            ft.Text(f"{total_withdraw:,.2f}", size=18, color="#F95325", weight=ft.FontWeight.BOLD)
                        ], alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.END),
                    ]
                )
            ),
            notif_list
        ], 
        floating_action_button=ft.FloatingActionButton(
            icon=ft.icons.ARROW_FORWARD, 
            bgcolor=ft.colors.ORANGE_600, 
            on_click=lambda _: page.go("/"), 
            width=45, 
            height=45
        )
    )
