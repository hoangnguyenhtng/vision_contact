import tkinter as tk
from tkinter import ttk

import cv2
from PIL import Image, ImageTk


class AppUI:
    """Chỉ tạo widget và cập nhật dữ liệu trên giao diện."""

    def __init__(self, root, actions, classes):
        self.root = root
        self.actions = actions
        self.classes = classes
        self.camera_photo = None

        self.username_var = tk.StringVar()
        self.password_var = tk.StringVar()
        self.status_var = tk.StringVar(value="Hệ thống đang dừng")
        self.timer_var = tk.StringVar(value="Thời gian: 00:00:00")
        self.first_detection_var = tk.StringVar(value="First detection: --")
        self.count_vars = {
            name: tk.IntVar(value=0) for name in self.classes
        }
        self.total_var = tk.IntVar(value=0)

        self.build_ui()
        self.set_logged_in(False)

    # -------------------- BUILD UI --------------------
    def build_ui(self):
        self.root.title("Production Counting System")
        self.root.geometry("1200x750")
        self.root.minsize(1000, 650)

        self.root.columnconfigure(0, weight=4)
        self.root.columnconfigure(1, weight=1)
        self.root.rowconfigure(0, weight=3)
        self.root.rowconfigure(1, weight=1)

        self.build_camera_zone()
        self.build_right_zone()
        self.build_table_zone()

    def build_camera_zone(self):
        zone = ttk.LabelFrame(self.root, text="Camera Zone", padding=8)
        zone.grid(row=0, column=0, sticky="nsew", padx=8, pady=8)
        zone.rowconfigure(0, weight=1)
        zone.columnconfigure(0, weight=1)

        self.camera_label = tk.Label(
            zone,
            text="VIDEO\nChưa hoạt động",
            background="black",
            foreground="white",
        )
        self.camera_label.grid(row=0, column=0, sticky="nsew")

    def build_right_zone(self):
        zone = ttk.Frame(self.root)
        zone.grid(row=0, column=1, sticky="nsew", padx=(0, 8), pady=8)
        zone.columnconfigure(0, weight=1)
        zone.rowconfigure(2, weight=1)

        self.build_login_zone(zone)
        self.build_control_zone(zone)
        self.build_counting_zone(zone)

    def build_login_zone(self, parent):
        zone = ttk.LabelFrame(parent, text="Login Zone", padding=10)
        zone.grid(row=0, column=0, sticky="ew", pady=(0, 8))
        zone.columnconfigure(1, weight=1)

        ttk.Label(zone, text="Username").grid(row=0, column=0, sticky="w")
        ttk.Entry(zone, textvariable=self.username_var).grid(
            row=0, column=1, sticky="ew", pady=3
        )
        ttk.Label(zone, text="Password").grid(row=1, column=0, sticky="w")
        ttk.Entry(zone, textvariable=self.password_var, show="*").grid(
            row=1, column=1, sticky="ew", pady=3
        )
        ttk.Button(zone, text="Login", command=self.actions.login).grid(
            row=2, column=0, columnspan=2, sticky="ew", pady=5
        )

    def build_control_zone(self, parent):
        zone = ttk.LabelFrame(parent, text="Button and Control Zone", padding=10)
        zone.grid(row=1, column=0, sticky="ew", pady=(0, 8))
        zone.columnconfigure((0, 1), weight=1)

        self.start_button = ttk.Button(
            zone, text="Start", command=self.actions.start
        )
        self.stop_button = ttk.Button(
            zone, text="Stop", command=self.actions.stop
        )
        self.reset_button = ttk.Button(
            zone, text="Reset", command=self.actions.reset
        )
        self.export_button = ttk.Button(
            zone, text="Export Data", command=self.actions.export_data
        )
        self.import_button = ttk.Button(
            zone, text="Import Video", command=self.actions.import_video
        )

        self.start_button.grid(row=0, column=0, sticky="ew", padx=3, pady=3)
        self.stop_button.grid(row=0, column=1, sticky="ew", padx=3, pady=3)
        self.reset_button.grid(row=1, column=0, sticky="ew", padx=3, pady=3)
        self.export_button.grid(row=1, column=1, sticky="ew", padx=3, pady=3)
        self.import_button.grid(
            row=2, column=0, columnspan=2, sticky="ew", padx=3, pady=(8, 3)
        )

    def build_counting_zone(self, parent):
        zone = ttk.LabelFrame(parent, text="Counting Zone", padding=10)
        zone.grid(row=2, column=0, sticky="nsew")
        zone.columnconfigure((0, 1), weight=1)

        for index, name in enumerate(self.classes):
            item = ttk.Frame(zone)
            item.grid(row=index // 2, column=index % 2, padx=5, pady=5)
            ttk.Label(
                item,
                textvariable=self.count_vars[name],
                font=("Segoe UI", 18, "bold"),
            ).pack()
            ttk.Label(item, text=name.upper()).pack()

        ttk.Separator(zone).grid(
            row=2, column=0, columnspan=2, sticky="ew", pady=8
        )
        ttk.Label(
            zone, textvariable=self.total_var, font=("Segoe UI", 22, "bold")
        ).grid(row=3, column=0, columnspan=2)
        ttk.Label(zone, text="TOTAL").grid(row=4, column=0, columnspan=2)
        ttk.Label(zone, textvariable=self.timer_var).grid(
            row=5, column=0, columnspan=2, pady=(10, 2)
        )
        ttk.Label(zone, textvariable=self.first_detection_var).grid(
            row=6, column=0, columnspan=2, pady=2
        )
        ttk.Label(zone, textvariable=self.status_var, wraplength=220).grid(
            row=7, column=0, columnspan=2, pady=2
        )

    def build_table_zone(self):
        zone = ttk.LabelFrame(self.root, text="Table Zone", padding=8)
        zone.grid(
            row=1,
            column=0,
            columnspan=2,
            sticky="nsew",
            padx=8,
            pady=(0, 8),
        )
        zone.rowconfigure(0, weight=1)
        zone.columnconfigure(0, weight=1)

        columns = ("time", *self.classes, "total", "reason")
        self.tree = ttk.Treeview(zone, columns=columns, show="headings")
        headings = {
            "time": "DateTime",
            **{name: name.upper() for name in self.classes},
            "total": "Total",
            "reason": "Reason",
        }

        for column in columns:
            self.tree.heading(column, text=headings[column])
            self.tree.column(column, anchor="center", width=110)

        self.tree.grid(row=0, column=0, sticky="nsew")
        scrollbar = ttk.Scrollbar(zone, orient="vertical", command=self.tree.yview)
        scrollbar.grid(row=0, column=1, sticky="ns")
        self.tree.configure(yscrollcommand=scrollbar.set)

    # -------------------- UPDATE UI --------------------
    def set_logged_in(self, logged_in):
        state = "normal" if logged_in else "disabled"
        self.start_button.configure(state=state)
        self.stop_button.configure(state=state)
        self.reset_button.configure(state=state)
        self.import_button.configure(state=state)

        # Theo đề: chưa đăng nhập vẫn được phép Export Data.
        self.export_button.configure(state="normal")

    def show_frame(self, frame):
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        image = Image.fromarray(rgb_frame)

        width = self.camera_label.winfo_width()
        height = self.camera_label.winfo_height()
        if width < 100:
            width = 800
        if height < 100:
            height = 500
        image.thumbnail((width, height), Image.Resampling.LANCZOS)

        self.camera_photo = ImageTk.PhotoImage(image)
        self.camera_label.configure(image=self.camera_photo, text="")

    def show_counts(self, counts, total):
        for name, value in counts.items():
            self.count_vars[name].set(value)
        self.total_var.set(total)

    def add_record(self, values):
        self.tree.insert("", "end", values=values)

    def get_table_data(self):
        headings = [
            self.tree.heading(column, "text") for column in self.tree["columns"]
        ]
        rows = [
            self.tree.item(item_id, "values")
            for item_id in self.tree.get_children()
        ]
        return headings, rows
