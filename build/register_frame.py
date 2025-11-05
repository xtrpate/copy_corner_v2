from pathlib import Path
import tkinter as tk
from tkinter import Canvas, Entry, messagebox, font
import mysql.connector
import random
import bcrypt
from utils import get_db_connection, round_rectangle, send_verification_email

OUTPUT_PATH = Path(__file__).parent
ASSETS_PATH = OUTPUT_PATH / "assets" / "frame0"

#---Asset Path Constructor---
def relative_to_assets(path: str) -> Path:
    asset_file = ASSETS_PATH / Path(path)
    if not asset_file.is_file():
        print(f"Warning: Asset (RegisterFrame) not found at {asset_file}")
    return asset_file


class PlaceholderEntry(Entry):
    #---Initializes Placeholder---
    def __init__(self, master=None, placeholder="PLACEHOLDER", color="grey", show_char="", *args, **kwargs):
        super().__init__(master, *args, **kwargs)
        self.placeholder = placeholder
        self.placeholder_color = color
        self.default_fg_color = self["fg"]
        self.show_char = show_char
        self.bind("<FocusIn>", self.foc_in)
        self.bind("<FocusOut>", self.foc_out)
        self.put_placeholder()

    #---Sets Placeholder Text---
    def put_placeholder(self):
        if not self.winfo_exists(): return
        self.delete(0, "end")
        self.insert(0, self.placeholder)
        self["fg"] = self.placeholder_color
        if self.show_char: self.config(show="")

    #---Handles Focus In---
    def foc_in(self, *args):
        if not self.winfo_exists(): return
        if self["fg"] == self.placeholder_color:
            self.delete("0", "end")
            self["fg"] = self.default_fg_color
            if self.show_char: self.config(show=self.show_char)

    #---Handles Focus Out---
    def foc_out(self, *args):
        if not self.winfo_exists(): return
        if not self.get(): self.put_placeholder()


class RegisterFrame(tk.Frame):
    #---Initializes Register UI---
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller

        try:
            self.eye_image = controller.eye_image
            self.eye_slash_image = controller.eye_slash_image
        except AttributeError:
             messagebox.showerror("Error", "Eye icons not found in controller. Cannot load Register Frame.")
             self.destroy()
             return

        self.canvas = Canvas(self, bg="#FFFFFF", height=604, width=851, bd=0, highlightthickness=0, relief="ridge")
        self.canvas.place(x=0, y=0)

        round_rectangle(self.canvas, 10.0, 15.0, 839.0, 589.0, r=0, fill="#FFFFFF", outline="#000000", width=3)
        round_rectangle(self.canvas, 10.0, 15.0, 839.0, 100.0, r=0, fill="#000000", outline="")
        round_rectangle(self.canvas, 242.0, 32.0, 601.0, 575.0, r=25, fill="#FFFFFF", outline="#000000", width=2)
        self.canvas.create_text(283.0, 61.0, anchor="nw", text="CREATE ACCOUNT", fill="#000000", font=("Inter Bold", -32))
        self.canvas.create_text(346.0, 100.0, anchor="nw", text="Fill in your details to register", fill="#000000", font=("Inter", -13))

        round_rectangle(self.canvas, 367.0, 141.0, 545.0, 183.0, r=15, fill="#FFFFFF", outline="#000000", width=1)
        round_rectangle(self.canvas, 367.0, 199.0, 545.0, 241.0, r=15, fill="#FFFFFF", outline="#000000", width=1)
        round_rectangle(self.canvas, 367.0, 256.0, 545.0, 298.0, r=15, fill="#FFFFFF", outline="#000000", width=1)
        round_rectangle(self.canvas, 367.0, 313.0, 545.0, 355.0, r=15, fill="#FFFFFF", outline="#000000", width=1)
        round_rectangle(self.canvas, 367.0, 370.0, 545.0, 412.0, r=15, fill="#FFFFFF", outline="#000000", width=1)
        round_rectangle(self.canvas, 367.0, 427.0, 545.0, 469.0, r=15, fill="#FFFFFF", outline="#000000", width=1)

        self.canvas.create_text(299.0, 154.0, anchor="nw", text="Full Name", fill="#000000", font=("Inter", -13))
        self.canvas.create_text(297.0, 212.0, anchor="nw", text="Username", fill="#000000", font=("Inter", -13))
        self.canvas.create_text(295.0, 269.0, anchor="nw", text="Contact No.", fill="#000000", font=("Inter", -13))
        self.canvas.create_text(322.0, 326.0, anchor="nw", text="Email", fill="#000000", font=("Inter", -13))
        self.canvas.create_text(295.0, 384.0, anchor="nw", text="Password", fill="#000000", font=("Inter", -13))
        self.canvas.create_text(254.0, 442.0, anchor="nw", text="Confirm Password", fill="#000000", font=("Inter", -13))

        self.fullname_entry = Entry(self, bd=0, bg="#FFFFFF", highlightthickness=0, font=("Inter", 12))
        self.username_entry = Entry(self, bd=0, bg="#FFFFFF", highlightthickness=0, font=("Inter", 12))
        self.contact_entry = PlaceholderEntry(self, placeholder="e.g. 09xxxxxxxxx", bd=0, bg="#FFFFFF", highlightthickness=0, font=("Inter", 12))
        self.email_entry = Entry(self, bd=0, bg="#FFFFFF", highlightthickness=0, font=("Inter", 12))
        self.password_entry = Entry(self, bd=0, bg="#FFFFFF", highlightthickness=0, font=("Inter", 12), show="*")
        self.confirm_entry = Entry(self, bd=0, bg="#FFFFFF", highlightthickness=0, font=("Inter", 12), show="*")

        self.canvas.create_window(456, 162, window=self.fullname_entry, width=160, height=25)
        self.canvas.create_window(456, 220, window=self.username_entry, width=160, height=25)
        self.canvas.create_window(456, 277, window=self.contact_entry, width=160, height=25)
        self.canvas.create_window(456, 334, window=self.email_entry, width=160, height=25)
        self.canvas.create_window(456, 391, window=self.password_entry, width=125, height=25)
        self.canvas.create_window(456, 448, window=self.confirm_entry, width=125, height=25)

        pw_eye_icon_id = self.canvas.create_image(520, 382, anchor="nw", image=self.eye_slash_image)
        confirm_eye_icon_id = self.canvas.create_image(520, 439, anchor="nw", image=self.eye_slash_image)
        self.canvas.tag_bind(pw_eye_icon_id, "<Button-1>", lambda e: self.toggle_password(self.password_entry, pw_eye_icon_id))
        self.canvas.tag_bind(confirm_eye_icon_id, "<Button-1>", lambda e: self.toggle_password(self.confirm_entry, confirm_eye_icon_id))
        for eye_id in (pw_eye_icon_id, confirm_eye_icon_id):
             self.canvas.tag_bind(eye_id, "<Enter>", lambda e: self.config(cursor="hand2"))
             self.canvas.tag_bind(eye_id, "<Leave>", lambda e: self.config(cursor=""))

        self.signup_box = round_rectangle(self.canvas, 367.0, 484.0, 545.0, 526.0, r=20, fill="#000000", outline="")
        self.signup_text = self.canvas.create_text(456, 505, anchor="center", text="Sign Up", fill="#FFFFFF", font=("Inter Bold", -16))

        self.canvas.create_text(345.0, 536.0, anchor="nw", text="Already have account?", fill="#000000", font=("Inter", -14))
        login_text = self.canvas.create_text(500.0, 534.0, anchor="nw", text="Login", fill="blue", font=("Inter Black", -16))

        self.bind_signup_button()
        self.canvas.tag_bind(login_text, "<Button-1>", lambda e: self.open_login())
        self.canvas.tag_bind(login_text, "<Enter>", lambda e: self.config(cursor="hand2"))
        self.canvas.tag_bind(login_text, "<Leave>", lambda e: self.config(cursor=""))

    #---Binds Signup Button---
    def bind_signup_button(self):
        for tag in (self.signup_box, self.signup_text):
            self.canvas.tag_bind(tag, "<Button-1>", self.on_signup_click)
            self.canvas.tag_bind(tag, "<Enter>", self.on_hover_signup)
            self.canvas.tag_bind(tag, "<Leave>", self.on_leave_signup)

    #---Handles Signup Click---
    def on_signup_click(self, event=None):
        self.register_user()

    #---Handles Signup Hover---
    def on_hover_signup(self, event=None):
        self.config(cursor="hand2")

    #---Handles Signup Leave---
    def on_leave_signup(self, event=None):
        self.config(cursor="")

    #---Toggles Password Show/Hide---
    def toggle_password(self, entry, icon_item_id):
        is_placeholder = (hasattr(entry, 'placeholder') and
                          entry.get() == entry.placeholder and
                          entry["fg"] == entry.placeholder_color)
        if is_placeholder:
            return

        try:
            if entry.cget("show") == "":
                entry.config(show="*")
                self.canvas.itemconfig(icon_item_id, image=self.eye_slash_image)
            else:
                entry.config(show="")
                self.canvas.itemconfig(icon_item_id, image=self.eye_image)
        except tk.TclError:
            print("Warning: Eye icon could not be updated.")

    #---Handles Register Button---
    def register_user(self):
        fullname = self.fullname_entry.get().strip()
        username = self.username_entry.get().strip()
        contact = self.contact_entry.get().strip()
        email = self.email_entry.get().strip()
        password = self.password_entry.get()
        confirm = self.confirm_entry.get()

        is_contact_placeholder = (contact == self.contact_entry.placeholder and
                                  self.contact_entry["fg"] == self.contact_entry.placeholder_color)

        if not (fullname and username and email and password and confirm) or is_contact_placeholder:
            messagebox.showerror("Error", "All fields are required.", parent=self)
            return

        if contact == self.contact_entry.placeholder: contact = ""

        if not contact.isdigit():
            messagebox.showerror("Error", "Contact No. must contain only numbers.", parent=self); return
        if len(contact) != 11:
            messagebox.showerror("Error", "Contact No. must be 11 digits long.", parent=self); return
        if not contact.startswith("09"):
            messagebox.showerror("Error", "Contact No. must start with '09'.", parent=self); return
        if len(password) < 8:
            messagebox.showerror("Error", "Password must be at least 8 characters long.", parent=self); return
        if not any(c.isupper() for c in password):
            messagebox.showerror("Error", "Password needs uppercase letter.", parent=self); return
        if not any(c.islower() for c in password):
            messagebox.showerror("Error", "Password needs lowercase letter.", parent=self); return
        if not any(c.isdigit() for c in password):
            messagebox.showerror("Error", "Password needs digit.", parent=self); return
        if password != confirm:
            messagebox.showerror("Error", "Passwords do not match.", parent=self); return
        if not email.lower().endswith(("@gmail.com", "@yahoo.com")):
            messagebox.showerror("Error", "Email must end with @gmail.com or @yahoo.com", parent=self); return

        conn = None; cursor = None
        try:
            conn = get_db_connection()
            if not conn: return
            cursor = conn.cursor()
            cursor.execute("SELECT 1 FROM users WHERE fullname=%s OR username=%s OR email=%s",
                           (fullname, username, email))
            if cursor.fetchone():
                messagebox.showerror("Error", "User with this fullname, username, or email already exists!", parent=self)
                return
        except mysql.connector.Error as e:
            messagebox.showerror("Database Error", f"Error checking existing user:\n{e}", parent=self)
            return
        except Exception as e:
            messagebox.showerror("Error", f"An unexpected error occurred:\n{e}", parent=self)
            return
        finally:
            if cursor: cursor.close()
            if conn and conn.is_connected(): conn.close()

        self.canvas.itemconfig(self.signup_text, text="Loading...")
        for tag in (self.signup_box, self.signup_text):
            self.canvas.tag_unbind(tag, "<Button-1>")
            self.canvas.tag_unbind(tag, "<Enter>")
            self.canvas.tag_unbind(tag, "<Leave>")

        self.config(cursor="")
        self.update_idletasks()

        otp_code = f"{random.randint(0, 999999):06d}"

        email_sent = send_verification_email(email, otp_code)

        if not email_sent:
            self.canvas.itemconfig(self.signup_text, text="Sign Up")
            self.bind_signup_button()
            return

        self.controller.temp_user_data = {
            "fullname": fullname,
            "username": username,
            "email": email,
            "password": password,
            "contact": contact
        }
        self.controller.temp_otp = otp_code
        self.controller.show_otp_frame()

    #---Navigation: Open Login---
    def open_login(self):
        self.clear_fields()
        self.controller.show_login_frame()

    #---Clears Input Fields---
    def clear_fields(self):
        if hasattr(self, 'fullname_entry') and self.fullname_entry.winfo_exists(): self.fullname_entry.delete(0, 'end')
        if hasattr(self, 'username_entry') and self.username_entry.winfo_exists(): self.username_entry.delete(0, 'end')
        if hasattr(self, 'email_entry') and self.email_entry.winfo_exists(): self.email_entry.delete(0, 'end')
        if hasattr(self, 'password_entry') and self.password_entry.winfo_exists(): self.password_entry.delete(0, 'end')
        if hasattr(self, 'confirm_entry') and self.confirm_entry.winfo_exists(): self.confirm_entry.delete(0, 'end')
        if hasattr(self, 'contact_entry') and self.contact_entry.winfo_exists(): self.contact_entry.put_placeholder()

        if hasattr(self, 'signup_text'):
             try: self.canvas.itemconfig(self.signup_text, text="Sign Up")
             except tk.TclError: pass
        if hasattr(self, 'signup_box'): self.bind_signup_button()