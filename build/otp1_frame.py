import tkinter as tk
from tkinter import Canvas, Entry, messagebox, font
import random
from utils import round_rectangle, send_verification_email


class OTP1Frame(tk.Frame):
    #---Initializes OTP UI---
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller

        self.canvas = Canvas(self, bg="#FFFFFF", height=500, width=400, bd=0, highlightthickness=0, relief="ridge")
        self.canvas.place(x=0, y=0)

        self.canvas.create_text(200, 60, anchor="center", text="Password Reset", fill="#000000", font=("Inter Bold", 24))
        self.canvas.create_text(200, 110, anchor="center", text="We sent a code to your email:", fill="#333333", font=("Inter", 12))
        self.email_label = self.canvas.create_text(200, 135, anchor="center", text="", fill="#000000", font=("Inter Bold", 12))
        self.canvas.create_text(200, 175, anchor="center", text="Please enter the 6-digit code below.", fill="#333333", font=("Inter", 12))

        self.otp_entries = []
        entry_font = font.Font(family="Inter Bold", size=24); entry_width = 40; entry_padding = 10
        total_width = (entry_width * 6) + (entry_padding * 5); start_x = (400 - total_width) / 2
        vcmd = (self.register(self._validate_digit), '%P')

        for i in range(6):
            x_pos = start_x + (i * (entry_width + entry_padding))
            round_rectangle(self.canvas, x_pos, 220, x_pos + entry_width, 220 + 50, r=10, fill="#F0F0F0", outline="#CCCCCC")
            entry = Entry(self, bd=0, bg="#F0F0F0", fg="#000000", font=entry_font, justify="center", width=2, highlightthickness=0, insertbackground="#000000")
            entry.config(validate="key", validatecommand=vcmd)
            entry.bind("<Key>", lambda e, idx=i: self._on_key_press(e, idx))
            entry.bind("<Control-v>", lambda e, idx=i: self._on_paste(e, idx))
            entry.bind("<Command-v>", lambda e, idx=i: self._on_paste(e, idx))
            self.canvas.create_window(x_pos + (entry_width / 2), 245, window=entry)
            self.otp_entries.append(entry)

        verify_btn_bg = round_rectangle(self.canvas, 50, 320, 400 - 50, 370, r=15, fill="#000000", outline="")
        verify_btn_text = self.canvas.create_text(200, 345, anchor="center", text="Verify Code", fill="#FFFFFF", font=("Inter Bold", 14))
        self.canvas.tag_bind(verify_btn_bg, "<Button-1>", lambda e: self.verify_otp())
        self.canvas.tag_bind(verify_btn_text, "<Button-1>", lambda e: self.verify_otp())
        for tag in (verify_btn_bg, verify_btn_text):
             self.canvas.tag_bind(tag, "<Enter>", lambda e: self.config(cursor="hand2"))
             self.canvas.tag_bind(tag, "<Leave>", lambda e: self.config(cursor=""))

        self.canvas.create_text(200 - 30, 420, anchor="e", text="Didn't receive a code?", fill="#555555", font=("Inter", 11))
        resend_label = self.canvas.create_text(200 - 25, 420, anchor="w", text="Resend", fill="#000000", font=("Inter Bold", 11))
        self.canvas.tag_bind(resend_label, "<Button-1>", lambda e: self.resend_otp())
        self.canvas.tag_bind(resend_label, "<Enter>", lambda e: self.config(cursor="hand2"))
        self.canvas.tag_bind(resend_label, "<Leave>", lambda e: self.config(cursor=""))

    #---Prepares Frame on Show---
    def prepare_otp_entry(self):
        user_email = self.controller.temp_reset_email if self.controller.temp_reset_email else "N/A"
        self.canvas.itemconfig(self.email_label, text=user_email)

        for entry in self.otp_entries:
            if entry.winfo_exists():
                 entry.delete(0, 'end')

        if self.otp_entries and self.otp_entries[0].winfo_exists():
            self.otp_entries[0].focus_set()

    #---Validates OTP Digits---
    def _validate_digit(self, P):
        return (P.isdigit() and len(P) <= 1) or P == ""

    #---Handles Key Navigation---
    def _on_key_press(self, event, index):
        key = event.keysym
        widget = event.widget

        if key == "BackSpace":
            if index > 0:
                widget.delete(0, 'end')
                if self.otp_entries[index - 1].winfo_exists():
                    self.otp_entries[index - 1].focus()
                    self.otp_entries[index - 1].delete(0, 'end')
            else:
                widget.delete(0, 'end')
            return "break"

        elif key == "Left" and index > 0:
            if self.otp_entries[index - 1].winfo_exists():
                self.otp_entries[index - 1].focus()
            return "break"

        elif key == "Right" and index < 5:
            if self.otp_entries[index + 1].winfo_exists():
                self.otp_entries[index + 1].focus()
            return "break"

        elif len(key) == 1 and key.isdigit():
            widget.delete(0, 'end')
            widget.insert(0, key)
            if index < 5 and self.otp_entries[index + 1].winfo_exists():
                self.otp_entries[index + 1].focus()
            return "break"

        elif len(key) > 1 and key not in ("Shift_L", "Shift_R", "Control_L", "Control_R",
                                          "Alt_L", "Alt_R", "Tab", "Caps_Lock",
                                          "Meta_L", "Meta_R"):
             return "break"

        return None

    #---Handles Pasting OTP---
    def _on_paste(self, event, index):
        try:
            clipboard_data = self.clipboard_get()
        except tk.TclError:
            clipboard_data = ""

        pasted_digits = [c for c in clipboard_data if c.isdigit()]
        current_index = index

        for digit in pasted_digits:
            if current_index < 6:
                if self.otp_entries[current_index].winfo_exists():
                    self.otp_entries[current_index].delete(0, 'end')
                    self.otp_entries[current_index].insert(0, digit)
                    current_index += 1
            else:
                break

        focus_index = min(current_index, 5)
        if self.otp_entries[focus_index].winfo_exists():
            self.otp_entries[focus_index].focus()
        return "break"

    #---Handles Verify Button---
    def verify_otp(self):
        entered_otp = "".join(entry.get() for entry in self.otp_entries if entry.winfo_exists())
        correct_otp = self.controller.temp_otp

        if not correct_otp:
             messagebox.showerror("Error", "Verification code expired or missing. Please restart the password reset process.", parent=self)
             self.controller.show_login_frame()
             return

        if entered_otp == correct_otp:
            messagebox.showinfo("Success", "Email verified successfully.", parent=self)
            forgot_frame = self.controller.frames.get("ForgotFrame")
            if forgot_frame:
                forgot_frame.show_reset_stage()
                self.controller.show_forgot_frame()
            else:
                messagebox.showerror("Error", "Could not return to password reset screen.", parent=self)
                self.controller.show_login_frame()
        else:
            messagebox.showerror("Verification Failed", "Incorrect code. Please try again.", parent=self)
            for entry in self.otp_entries:
                 if entry.winfo_exists(): entry.delete(0, 'end')
            if self.otp_entries and self.otp_entries[0].winfo_exists():
                 self.otp_entries[0].focus()

    #---Handles Resend Button---
    def resend_otp(self):
        user_email = self.controller.temp_reset_email
        if not user_email:
             messagebox.showerror("Error", "Cannot resend OTP. Email missing. Please restart the process.", parent=self)
             self.controller.show_login_frame()
             return

        new_otp = f"{random.randint(0, 999999):06d}"

        email_sent = send_verification_email(
            user_email, new_otp,
            email_subject="Password Reset Verification Code", context="reset"
        )
        if email_sent:
            self.controller.temp_otp = new_otp
            messagebox.showinfo("Code Resent", f"A new 6-digit code has been sent to {user_email}.", parent=self)
            self.prepare_otp_entry()