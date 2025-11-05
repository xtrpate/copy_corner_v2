from pathlib import Path
import tkinter as tk
from tkinter import Canvas, Entry, Text, Button, PhotoImage, messagebox, font
import mysql.connector
import bcrypt
from utils import get_db_connection, round_rectangle


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


class RadioTile(tk.Canvas):
    #---Initializes Radio Button---
    def __init__(self, master, text, variable, value, width=270, height=30, radius=12, **kwargs):
        super().__init__(master, width=width, height=height, bg="#F2F6F5", highlightthickness=0, **kwargs)
        self.variable = variable
        self.value = value
        self.text = text
        self.radius = radius
        self.width = width
        self.height = height
        self.draw_tile()
        self.bind("<Button-1>", self.select_tile)
        self.tag_bind("text", "<Button-1>", self.select_tile)
        self.bind("<Enter>", lambda e: self.config(cursor="hand2"))
        self.bind("<Leave>", lambda e: self.config(cursor=""))

    #---Draws Radio Button---
    def draw_rounded_rect(self, x1, y1, x2, y2, r, fill):
        points = [x1 + r, y1, x2 - r, y1, x2, y1, x2, y1 + r, x2, y2 - r, x2, y2,
                  x2 - r, y2, x1 + r, y2, x1, y2, x1, y2 - r, x1, y1 + r, x1, y1]
        return self.create_polygon(points, smooth=True, fill=fill, outline="black", width=1)

    #---Updates Radio Button---
    def draw_tile(self):
        self.delete("all")
        if self.variable.get() == self.value:
            fill, text_color = "black", "white"
        else:
            fill, text_color = "#F0F0F0", "black"
        self.draw_rounded_rect(1, 1, self.width - 2, self.height - 2, self.radius, fill=fill)
        self.create_text(self.width / 2, self.height / 2,
                         text=self.text, fill=text_color, font=("Inter", 12, "bold"), tags="text")

    #---Handles Radio Click---
    def select_tile(self, event=None):
        self.variable.set(self.value)
        if self.master and self.master.winfo_exists():
            for sibling in self.master.winfo_children():
                if isinstance(sibling, RadioTile) and sibling.winfo_exists():
                    try:
                        sibling.draw_tile()
                    except tk.TclError:
                        print(f"Warning: Could not redraw sibling tile {sibling}")


OUTPUT_PATH = Path(__file__).parent
ASSETS_PATH = OUTPUT_PATH / "assets" / "frame0"


#---Asset Path Constructor---
def relative_to_assets(path: str) -> Path:
    asset_file = ASSETS_PATH / Path(path)
    if not asset_file.is_file():
        print(f"Warning: Asset file (LoginFrame) not found at {asset_file}")
    return asset_file


class LoginFrame(tk.Frame):
    #---Initializes Login UI---
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller

        try:
            self._eye_image = controller.eye_image
            self._eye_slash_image = controller.eye_slash_image
            self._image_image_1 = PhotoImage(file=relative_to_assets("image_-1.png"))
            self._image_image_2 = PhotoImage(file=relative_to_assets("image_2.png"))
            self._image_image_3 = PhotoImage(file=relative_to_assets("image_3.png"))
            self._image_image_4 = PhotoImage(file=relative_to_assets("image_4.png"))
            self._image_image_5 = PhotoImage(file=relative_to_assets("image_5.png"))
        except tk.TclError as e:
            messagebox.showerror("Asset Error", f"Could not find assets in the 'frame0' folder.\n{e}", parent=self)
            if controller and controller.winfo_exists(): controller.destroy()
            return
        except AttributeError:
            messagebox.showerror("Error", "Eye icons not found in controller. Cannot load Login Frame.", parent=self)
            if controller and controller.winfo_exists(): controller.destroy()
            return

        canvas = Canvas(
            self, bg="#FFFFFF", height=534, width=859, bd=0, highlightthickness=0, relief="ridge"
        )
        canvas.place(x=0, y=0)
        self.canvas = canvas

        canvas.create_rectangle(15.0, 14.0, 844.0, 518.0, fill="#FFFFFF", outline="#000000", width=1.5)
        canvas.create_text(84.0, 208.0, anchor="nw", text="Your Documents, Our Priority", fill="#000000",
                           font=("Inter", -20))
        canvas.create_rectangle(427.0, 14.0, 844.0, 518.0, fill="#F2F6F5", outline="#000000", width=1.5)
        register_text = canvas.create_text(700.0, 468.0, anchor="nw", text="Register Now", fill="#000000",
                                           font=("Inter", 11, "bold"))
        text = "WELCOME!"
        font_style = font.Font(family="Inter Black", size=42, weight="bold")
        shadow_offset_x, shadow_offset_y, shadow_color = 1, 3, "#999999"
        canvas.create_text(506.0 + shadow_offset_x, 58.0 + shadow_offset_y, anchor="nw", text=text, fill=shadow_color,
                           font=font_style)
        canvas.create_text(506.0, 58.0, anchor="nw", text=text, fill="#000000", font=font_style)
        text1 = "Login with Email / Username"
        font_style1 = font.Font(family="Inter Black", size=12, weight="bold")
        shadow_offset_x1, shadow_offset_y1, shadow_color1 = 1, 1, "#999999"
        canvas.create_text(553.0 + shadow_offset_x1, 131.0 + shadow_offset_y1, anchor="nw", text=text1,
                           fill=shadow_color1,
                           font=font_style1)
        canvas.create_text(553.0, 131.0, anchor="nw", text=text1, fill="#000000", font=font_style1)

        y_shift = 40
        self.entry_email, _ = self.create_rounded_entry(500, 241 - y_shift, placeholder="Email or Username")
        self.entry_password, self.eye_icon_id = self.create_rounded_entry(500, 313 - y_shift, placeholder="Password",
                                                                          show_char="*", with_eye=True)

        self.entry_email.bind("<Return>", lambda event: self.login_user())
        self.entry_password.bind("<Return>", lambda event: self.login_user())

        canvas.create_text(500.0, 215.0 - y_shift, anchor="nw", text="Email or Username", fill="#000000",
                           font=("Inter Bold", -20))
        canvas.create_text(500.0, 287.0 - y_shift, anchor="nw", text="Password", fill="#000000",
                           font=("Inter Bold", -20))
        btn_login = round_rectangle(canvas, 553, 405 - y_shift, 731, 447 - y_shift, r=10, fill="#000000", outline="")
        btn_login_text = canvas.create_text(642, 426 - y_shift, anchor="center", text="Login", fill="#FFFFFF",
                                            font=("Inter Bold", -20))
        self.forgot_pw_label = canvas.create_text(671.0, 359.0 - y_shift, anchor="nw", text="Forgot Password?",
                                                  fill="#000000",
                                                  font=("Inter", 11, "bold"), state="hidden")

        canvas.create_text(506.0, 468.0, anchor="nw", text="Don’t have an account?", fill="#000000",
                           font=("Inter", -16))
        canvas.create_image(220.0, 110.0, image=self._image_image_1)
        canvas.create_rectangle(169.0, 390.0, 427.0, 391.0, fill="#000000", outline="#000000")
        canvas.create_image(475.0, 65.0, image=self._image_image_2)
        canvas.create_rectangle(14.0, 390.0, 24.0, 391.0, fill="#000000", outline="")
        canvas.create_image(97.0, 417.0, image=self._image_image_3)
        canvas.create_image(360.0, 464.0, image=self._image_image_4)
        canvas.create_image(249.0, 426.0, image=self._image_image_5)

        canvas.tag_bind(btn_login, "<Button-1>", lambda e: self.login_user())
        canvas.tag_bind(btn_login_text, "<Button-1>", lambda e: self.login_user())
        for tag in (btn_login, btn_login_text):
            canvas.tag_bind(tag, "<Enter>",
                            lambda e: (self.canvas.itemconfig(btn_login, fill="#333333"), self.config(cursor="hand2")))
            canvas.tag_bind(tag, "<Leave>",
                            lambda e: (self.canvas.itemconfig(btn_login, fill="#000000"), self.config(cursor="")))
        for tag in (self.forgot_pw_label, register_text):
            canvas.tag_bind(tag, "<Enter>", lambda e: self.config(cursor="hand2"))
            canvas.tag_bind(tag, "<Leave>", lambda e: self.config(cursor=""))
        canvas.tag_bind(self.forgot_pw_label, "<Button-1>", lambda e: self.open_forgot())
        canvas.tag_bind(register_text, "<Button-1>", lambda e: self.open_register())

    #---Navigation: Open Register---
    def open_register(self):
        self.clear_fields()
        self.controller.show_register_frame()

    #---Navigation: Open Forgot---
    def open_forgot(self):
        self.clear_fields()
        self.controller.show_forgot_frame()

    #---Handles Login Button---
    def login_user(self):
        username_or_email = self.entry_email.get()
        password = self.entry_password.get()

        if username_or_email == self.entry_email.placeholder and self.entry_email[
            "fg"] == self.entry_email.placeholder_color:
            username_or_email = ""
        if password == self.entry_password.placeholder and self.entry_password[
            "fg"] == self.entry_password.placeholder_color:
            password = ""

        if not username_or_email or not password:
            messagebox.showerror("Error", "Please enter both username/email and password.", parent=self)
            return

        password_bytes = password.encode('utf-8')
        conn = None
        cursor = None
        try:
            conn = get_db_connection()
            if not conn: return

            cursor = conn.cursor(dictionary=True)

            cursor.execute("SELECT * FROM admin_login WHERE admin_username = %s", (username_or_email,))
            admin = cursor.fetchone()

            if admin and admin['admin_password'] == password:
                admin_name = admin.get('admin_username')
                self.controller.on_admin_login(admin_name)
                return

            cursor.execute("""
                SELECT user_id, fullname, status, password
                FROM users WHERE (username = %s OR email = %s)
            """, (username_or_email, username_or_email))
            user = cursor.fetchone()

            if user and isinstance(user.get('password'), (bytes, str)) and bcrypt.checkpw(password_bytes,
                                                                                          user['password'].encode(
                                                                                                  'utf-8')):
                if user.get('status') == 'disabled':
                    messagebox.showerror("Account Disabled", "Sorry, your account was disabled.", parent=self)
                elif user.get('status') == 'active':
                    user_id = user.get('user_id')
                    fullname = user.get('fullname')
                    self.controller.on_login_success(user_id, fullname)
                    return
                else:
                    messagebox.showerror("Error", "Your account status is invalid.", parent=self)
                return

            messagebox.showerror("Error", "Invalid username/email or password.", parent=self)
            if hasattr(self, 'forgot_pw_label'):
                self.canvas.itemconfigure(self.forgot_pw_label, state="normal")

        except mysql.connector.Error as db_err:
            messagebox.showerror("Database Error", f"Database operation failed:\n{db_err}", parent=self)
        except Exception as e:
            messagebox.showerror("Error", f"An unexpected error occurred during login:\n{e}", parent=self)
        finally:
            if cursor: cursor.close()
            if conn and conn.is_connected(): conn.close()

    #---Creates Entry Widget---
    def create_rounded_entry(self, x_pos, y_pos, placeholder="", show_char="", with_eye=False):
        round_rectangle(self.canvas, x_pos, y_pos + 7, 802, y_pos + 37, r=10, fill="#DDDDDD", outline="")
        round_rectangle(self.canvas, x_pos, y_pos + 5, 800, y_pos + 35, r=10, fill="white", outline="#CCCCCC",
                        width=1)
        entry = PlaceholderEntry(
            self, placeholder=placeholder, bd=0, bg="white", fg="#000000",
            show_char=show_char, highlightthickness=0, font=("Inter", 12)
        )
        icon_item_id = None
        entry_width = 800 - x_pos - 10
        entry_x_offset = (800 - x_pos) / 2

        if with_eye:
            entry_width = 800 - x_pos - 35
            entry_x_offset = (800 - x_pos - 30) / 2
            icon_item_id = self.canvas.create_image(775, y_pos + 10, anchor="nw",
                                                    image=self._eye_slash_image)
            self.canvas.tag_bind(icon_item_id, "<Button-1>", lambda e: self.toggle_password(entry, icon_item_id))
            self.canvas.tag_bind(icon_item_id, "<Enter>", lambda e: self.config(cursor="hand2"))
            self.canvas.tag_bind(icon_item_id, "<Leave>", lambda e: self.config(cursor=""))

        self.canvas.create_window(x_pos + entry_x_offset, y_pos + 20, width=entry_width, height=20, window=entry,
                                  anchor="center")

        return entry, icon_item_id

    #---Toggles Password Show/Hide---
    def toggle_password(self, entry, icon_id):
        is_placeholder = (hasattr(entry, 'placeholder') and
                          entry.get() == entry.placeholder and
                          entry["fg"] == entry.placeholder_color)
        if is_placeholder: return

        try:
            if entry.cget("show") == "":
                entry.config(show="*")
                self.canvas.itemconfig(icon_id, image=self._eye_slash_image)
            else:
                entry.config(show="")
                self.canvas.itemconfig(icon_id, image=self._eye_image)
        except tk.TclError:
            print("Warning: Eye icon could not be updated.")

    #---Clears Input Fields---
    def clear_fields(self):
        if hasattr(self, 'entry_email') and self.entry_email.winfo_exists():
            self.entry_email.put_placeholder()
        if hasattr(self, 'entry_password') and self.entry_password.winfo_exists():
            self.entry_password.put_placeholder()
            self.entry_password.config(show='*')
            if hasattr(self, 'eye_icon_id') and self.eye_icon_id:
                try:
                    self.canvas.itemconfig(self.eye_icon_id, image=self._eye_slash_image)
                except tk.TclError:
                    print("Warning: Could not reset eye icon image.")

        if hasattr(self, 'forgot_pw_label'):
            try:
                if self.canvas.find_withtag(self.forgot_pw_label):
                    self.canvas.itemconfigure(self.forgot_pw_label, state="hidden")
            except tk.TclError:
                print("Warning: Could not hide 'Forgot Password' label.")