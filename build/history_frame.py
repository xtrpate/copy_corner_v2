from pathlib import Path
from tkinter import Tk, Canvas, PhotoImage, messagebox, Frame, Label, Scrollbar, ttk
import tkinter as tk
import subprocess
import sys
import mysql.connector
from datetime import datetime
from utils import get_db_connection, round_rectangle

from printer_frame import PrinterFrame

WHITE = "#FFFFFF"
BLACK = "#000000"
LIGHT_GRAY = "#DDDDDD"


class HistoryFrame(tk.Frame):
    #---Initializes History UI---
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller

        self.user_id = controller.user_id

        controller.geometry("900x504")

        canvas = Canvas(self, bg="#FFFFFF", height=504, width=900, bd=0, highlightthickness=0, relief="ridge")
        canvas.place(x=0, y=0)
        self.canvas = canvas

        canvas.create_rectangle(0.0, 0.0, 900.0, 85.0, fill="#000000", outline="")
        canvas.create_text(300.0, 20.0, anchor="nw", text="Request History", fill="#FFFFFF", font=("Inter Bold", 36))

        canvas.create_rectangle(0.0, 85.0, 900.0, 132.0, fill=WHITE, outline="")
        canvas.create_text(31.0, 93.0, anchor="nw", text="#", fill="#000000", font=("Inter Bold", 20))
        canvas.create_text(200.0, 93.0, anchor="nw", text="File Name", fill="#000000", font=("Inter Bold", 20))
        canvas.create_text(700.0, 93.0, anchor="nw", text="Date Submitted", fill="#000000", font=("Inter Bold", 20))
        canvas.create_rectangle(0.0, 130.0, 900.0, 133.0, fill="#000000", outline="")

        HISTORY_X, HISTORY_Y = 0, 133
        HISTORY_W, HISTORY_H = 900, 300

        history_container = Frame(self, bg=WHITE)
        history_container.place(x=HISTORY_X, y=HISTORY_Y, width=HISTORY_W, height=HISTORY_H)

        self.history_canvas = Canvas(history_container, bg=WHITE, bd=0, highlightthickness=0)
        self.history_scrollbar = ttk.Scrollbar(history_container, orient="vertical", command=self.history_canvas.yview)
        self.history_canvas.configure(yscrollcommand=self.history_scrollbar.set)

        self.history_scrollbar.pack(side="right", fill="y")
        self.history_canvas.pack(side="left", fill="both", expand=True)

        self.history_content_frame = Frame(self.history_canvas, bg=WHITE)
        self.history_content_frame_window = self.history_canvas.create_window((0, 0), window=self.history_content_frame,
                                                                              anchor="nw")

        self.history_content_frame.bind("<Configure>", self._on_frame_configure)
        self.history_canvas.bind("<Configure>",
                                 lambda e: self.history_canvas.itemconfig(self.history_content_frame_window,
                                                                          width=e.width))

        self.history_canvas.bind("<Enter>", self._bind_mousewheel)
        self.history_canvas.bind("<Leave>", self._unbind_mousewheel)
        self.history_content_frame.bind("<Enter>", self._bind_mousewheel)
        self.history_content_frame.bind("<Leave>", self._unbind_mousewheel)

        back_rect = round_rectangle(canvas, 31, 450, 140, 493, r=15, fill="#000000", outline="#000000")
        back_text = canvas.create_text(60, 457, anchor="nw", text="Back", fill="#FFFFFF", font=("Inter Bold", 20))

        for tag in (back_rect, back_text):
            canvas.tag_bind(tag, "<Enter>",
                            lambda e: (canvas.itemconfig(back_rect, fill="#333333"), self.config(cursor="hand2")))
            canvas.tag_bind(tag, "<Leave>",
                            lambda e: (canvas.itemconfig(back_rect, fill="#000000"), self.config(cursor="")))
            canvas.tag_bind(tag, "<Button-1>", self.go_back)

        self.load_history()

    #---Loads History Data---
    def load_history(self):
        self.fetch_and_display_history(self.history_content_frame, self.user_id)

    #---Navigation: Go Back---
    def go_back(self, event=None):
        self.controller.geometry("859x534")
        self.controller.show_frame(PrinterFrame)

    #---Database: Fetches History---
    def fetch_and_display_history(self, frame, target_user_id):
        for widget in frame.winfo_children():
            widget.destroy()

        if target_user_id is None:
            Label(frame, text="Could not load history (User ID missing).",
                  font=("Inter Bold", 16), bg=WHITE, fg="red").pack(pady=20, padx=10)
            return
        conn = None
        try:
            conn = get_db_connection()
            if not conn: return

            cursor = conn.cursor(dictionary=True)
            sql_query = """
                SELECT pj.job_id, f.file_name, pj.created_at
                FROM print_jobs pj
                LEFT JOIN files f ON pj.file_id = f.file_id
                WHERE pj.user_id = %s
                ORDER BY pj.created_at DESC
            """
            cursor.execute(sql_query, (target_user_id,))
            history = cursor.fetchall()

            if not history:
                Label(frame, text="No print history found.",
                      font=("Inter Bold", 16), bg=WHITE, fg="grey").pack(pady=20, padx=10)
                return

            frame.columnconfigure(0, weight=1)
            frame.columnconfigure(1, weight=5)
            frame.columnconfigure(2, weight=3)
            row_index, item_number = 0, 1

            for item in history:
                job_id = item['job_id']
                file_name = item.get('file_name', 'File not found')
                created_at = item['created_at']
                date_str = created_at.strftime("%Y-%m-%d") if created_at else "N/A"
                time_str = created_at.strftime("%I:%M %p") if created_at else ""
                full_time_str = f"{date_str}\n{time_str}".strip()

                Label(frame, text=str(item_number), font=("Inter Bold", 16), bg=WHITE, anchor="nw").grid(row=row_index,
                                                                                                         column=0,
                                                                                                         padx=(30, 10),
                                                                                                         pady=10,
                                                                                                         sticky="nw")
                Label(frame, text=file_name, font=("Inter Bold", 16), bg=WHITE, anchor="nw", wraplength=350,
                      justify="left").grid(row=row_index, column=1, padx=10, pady=10, sticky="nw")
                Label(frame, text=full_time_str, font=("Inter Bold", 16), bg=WHITE, anchor="ne", justify="right").grid(
                    row=row_index, column=2, padx=(10, 30), pady=10, sticky="ne")
                ttk.Separator(frame, orient="horizontal").grid(row=row_index + 1, column=0, columnspan=3, sticky="ew",
                                                               padx=5)
                row_index += 2
                item_number += 1
        except mysql.connector.Error as err:
            messagebox.showerror("Database Error", f"Failed to fetch history: {err}")
        finally:
            if conn and conn.is_connected():
                if 'cursor' in locals() and cursor: cursor.close()
                conn.close()

    #---Updates Scrollable Area---
    def _on_frame_configure(self, event):
        self.history_canvas.configure(scrollregion=self.history_canvas.bbox("all"))

    #---Handles Mouse Wheel---
    def _on_mousewheel(self, event):
        self.history_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    #---Binds Mouse Wheel---
    def _bind_mousewheel(self, event):
        self.bind_all("<MouseWheel>", self._on_mousewheel)

    #---Unbinds Mouse Wheel---
    def _unbind_mousewheel(self, event):
        self.unbind_all("<MouseWheel>")