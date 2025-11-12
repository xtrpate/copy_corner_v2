from pathlib import Path
import tkinter as tk
from tkinter import Tk, Canvas, Button, PhotoImage, messagebox, Label, Radiobutton, StringVar, Entry, Frame, filedialog
import sys
import os
import shutil
from datetime import datetime
from decimal import Decimal, InvalidOperation


# NOTE: Removed 'from utils import get_db_connection, round_rectangle'
# We will mock these functions/values below.

# --- Mock get_db_connection and round_rectangle if they are not available ---
def get_db_connection():
    """Mock function to simulate database connection failure for standalone mode."""
    return None

# Assuming round_rectangle is not strictly necessary for UI functionality.

OUTPUT_PATH = Path(__file__).parent
# Adjusted path based on previous troubleshooting, assuming pay.py is one level up from 'build'
ASSETS_PATH = OUTPUT_PATH / "build" / "assets" / "frame0"


# ---Asset Path Constructor---
def relative_to_assets(path: str) -> Path:
    asset_file = ASSETS_PATH / Path(path)
    if not asset_file.is_file():
        print(f"Warning: Asset ({path}) not found at {asset_file}")
    return asset_file


# ---Database: Fetches Job Details (MOCKED)---
def fetch_job_details(job_id):
    """MOCKED: Returns predefined job details, ignoring database logic."""
    print(f"MOCK: Fetching details for Job ID {job_id}. Database access skipped.")
    return {
        'job_id': job_id,
        'username': 'MOCK_User',
        'file_name': 'MOCK_Standalone_File.pdf',
        'status': 'Approved',
        'pages': 25,
        'copies': 2,
        'paper_size': 'Letter',
        'color_option': 'B/W',
    }


# ---Database: Records Payment (MOCKED)---
def record_payment_and_update_status(job_id, payment_amount, payment_method, gcash_name=None, gcash_number=None,
                                     screenshot_path=None):
    """MOCKED: Simulates successful payment recording without connecting to the database."""
    print(f"MOCK: Recording payment for Job #{job_id} ({payment_method}).")
    if payment_method == "Gcash" and screenshot_path:
        print(f"MOCK: Saved screenshot to {screenshot_path}")

    # Display success message and return True (mocked success)
    messagebox.showinfo("Payment Successfully (MOCK)",
                        f"MOCK Payment recorded for Job #{job_id} using {payment_method}.")
    return True


class PaymentWindow(Tk):
    # ---Initializes Payment UI---
    def __init__(self, job_id, amount_from_args):
        super().__init__()
        self.job_id = job_id
        self.payment_amount = amount_from_args
        # fetch_job_details is now fully mocked
        self.job_details = fetch_job_details(job_id)
        self.selected_screenshot_path = None

        if not self.job_details:
            # Should not happen with mock data, but kept as a safeguard
            messagebox.showerror("Error", f"Could not fetch essential details for Job ID {job_id}.")
            self.destroy()
            return

        self.title(f"Payment for Job #{self.job_id}")
        window_width = 650
        window_height = 500
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        x = int((screen_width / 2) - (window_width / 2))
        y = int((screen_height / 2) - (window_height / 2))
        self.geometry(f"{window_width}x{window_height}+{x}+{y}")
        self.configure(bg="#FFFFFF")
        self.resizable(False, False)

        # --- Load GCash Asset ---
        self.gcash_icon = None
        try:
            # FIXED: Added the file extension ".png"
            self.gcash_icon = PhotoImage(file=relative_to_assets("gcash.png"))
        except tk.TclError:
            print("Warning: 'gcash.png' asset not found or invalid. GCash image box will be empty.")
            self.gcash_icon = None

        self.canvas = Canvas(
            self, bg="#FFFFFF", height=window_height, width=window_width,
            bd=0, highlightthickness=0, relief="ridge"
        )
        self.canvas.place(x=0, y=0)

        header_height = 74
        self.canvas.create_rectangle(0, 0, window_width, header_height, fill="#000000", outline="")
        self.canvas.create_text(20, header_height / 2, anchor="w", text="Payment Method:",
                                fill="#FFFFFF", font=("Inter Bold", 24))

        # --- Job Details Display (Y-position calculated) ---
        content_y_start = header_height + 20
        label_x = 30
        value_x = 180
        row_y = content_y_start
        details_font = ("Inter", 11)
        details_bold_font = ("Inter Bold", 11)
        Label(self, text="File Name:", font=details_bold_font, bg="#FFFFFF").place(x=label_x, y=row_y)
        Label(self, text=self.job_details['file_name'], font=details_font, bg="#FFFFFF", anchor="w",
              wraplength=window_width - value_x - 20).place(x=value_x, y=row_y)
        row_y += 25
        Label(self, text="Color:", font=details_bold_font, bg="#FFFFFF").place(x=label_x, y=row_y)
        Label(self, text=self.job_details['color_option'], font=details_font, bg="#FFFFFF", anchor="w").place(x=value_x,
                                                                                                              y=row_y)
        row_y += 25
        Label(self, text="Paper Size:", font=details_bold_font, bg="#FFFFFF").place(x=label_x, y=row_y)
        Label(self, text=self.job_details['paper_size'], font=details_font, bg="#FFFFFF", anchor="w").place(x=value_x,
                                                                                                            y=row_y)
        row_y += 25
        Label(self, text="Pages:", font=details_bold_font, bg="#FFFFFF").place(x=label_x, y=row_y)
        Label(self, text=str(self.job_details['pages']), font=details_font, bg="#FFFFFF", anchor="w").place(x=value_x,
                                                                                                            y=row_y)
        row_y += 25
        Label(self, text="Copies:", font=details_bold_font, bg="#FFFFFF").place(x=label_x, y=row_y)
        Label(self, text=str(self.job_details['copies']), font=details_font, bg="#FFFFFF", anchor="w").place(x=value_x,
                                                                                                             y=row_y)
        row_y += 35
        amount_text = f"₱{self.payment_amount:.2f}"
        Label(self, text="Total Amount:", font=("Inter Bold", 16), bg="#FFFFFF").place(x=label_x, y=row_y)
        Label(self, text=amount_text, font=("Inter Bold", 20, "bold"), bg="#FFFFFF", fg="#000000").place(x=value_x,
                                                                                                         y=row_y - 3)
        row_y += 50

        # --- Payment Method Selection ---
        Label(self, text="Select Method:", font=("Inter Bold", 14), bg="#FFFFFF").place(x=label_x, y=row_y)
        self.payment_method_var = StringVar(value="Cash")

        # Cash Radiobutton
        Radiobutton(self, text="Cash", variable=self.payment_method_var, value="Cash", font=("Inter", 12), bg="#FFFFFF",
                    anchor="w", command=self._update_payment_fields).place(x=label_x + 20, y=row_y + 30)

        # GCash Radiobutton (Text Only)
        Radiobutton(self, text="GCash", variable=self.payment_method_var, value="Gcash", font=("Inter", 12),
                    bg="#FFFFFF", anchor="w", command=self._update_payment_fields).place(x=label_x + 120, y=row_y + 30)

        # --- GCash Image Display (New Widget) ---
        self.gcash_image_label = Label(self, image=self.gcash_icon, bg="#FFFFFF")
        # Position the image on the right side of the window
        # The image will be shown/hidden in _update_payment_fields
        self.gcash_image_label_x = window_width - 150  # Example right-side position
        self.gcash_image_label_y = row_y

        row_y += 65

        # --- GCash Input Fields Frame ---
        self.gcash_frame = Frame(self, bg="#FFFFFF")
        Label(self.gcash_frame, text="GCash Name:", font=details_font, bg="#FFFFFF").grid(row=0, column=0, sticky="w",
                                                                                          pady=2)
        self.gcash_name_entry = Entry(self.gcash_frame, font=details_font, bd=1, relief="solid", width=30)
        self.gcash_name_entry.grid(row=0, column=1, sticky="w", padx=5, pady=2)
        Label(self.gcash_frame, text="GCash Number:", font=details_font, bg="#FFFFFF").grid(row=1, column=0, sticky="w",
                                                                                            pady=2)
        self.gcash_number_entry = Entry(self.gcash_frame, font=details_font, bd=1, relief="solid", width=30)
        self.gcash_number_entry.grid(row=1, column=1, sticky="w", padx=5, pady=2)
        Label(self.gcash_frame, text="Screenshot:", font=details_font, bg="#FFFFFF").grid(row=2, column=0, sticky="w",
                                                                                          pady=2)
        self.screenshot_button = Button(self.gcash_frame, text="Browse...", font=("Inter", 9),
                                        command=self._browse_screenshot, bg="#000000", fg="#FFFFFF",
                                        activebackground="#333333", activeforeground="#FFFFFF", bd=1, relief="raised")
        self.screenshot_button.grid(row=2, column=1, sticky="w", padx=5, pady=2)
        self.screenshot_label = Label(self.gcash_frame, text="No file selected.", font=("Inter Italic", 9),
                                      bg="#FFFFFF", fg="grey")
        self.screenshot_label.grid(row=2, column=2, sticky="w", padx=5, pady=2)

        # --- Buttons ---
        button_y = window_height - 60
        self.confirm_button = Button(self, text="Confirm Payment", font=("Inter Bold", 12),
                                     command=self.confirm_payment, relief="raised", bd=1, bg="#000000", fg="#FFFFFF",
                                     activebackground="#333333", activeforeground="#FFFFFF", cursor="hand2")
        self.confirm_button.place(x=window_width - 180, y=button_y, width=150, height=35)
        self.cancel_button = Button(self, text="Cancel", font=("Inter Bold", 12), command=self.destroy, relief="raised",
                                    bd=1, bg="#000000", fg="#FFFFFF", activebackground="#333333",
                                    activeforeground="#FFFFFF", cursor="hand2")
        self.cancel_button.place(x=label_x, y=button_y, width=100, height=35)

        self._update_payment_fields()  # Initial call to set visibility

    # ---Toggles GCash Fields and Image Visibility---
    def _update_payment_fields(self):
        if self.payment_method_var.get() == "Gcash":
            # 1. Show GCash inputs frame
            self.gcash_frame.place(relx=0.05, rely=0.68, relwidth=0.9)

            # 2. Show GCash image label (if it loaded)
            if self.gcash_icon:
                self.gcash_image_label.place(x=self.gcash_image_label_x, y=self.gcash_image_label_y)

            self.confirm_button.config(state=tk.NORMAL)
        else:  # Cash or other method selected
            # 1. Hide GCash inputs frame
            self.gcash_frame.place_forget()

            # 2. Hide GCash image label
            self.gcash_image_label.place_forget()

            self.confirm_button.config(state=tk.NORMAL)

    # ---Handles Browse Button---
    def _browse_screenshot(self):
        filepath = filedialog.askopenfilename(
            title="Select Screenshot",
            filetypes=[("Image Files", "*.png *.jpg *.jpeg *.bmp *.gif"), ("All Files", "*.*")]
        )
        if filepath:
            self.selected_screenshot_path = filepath
            filename = os.path.basename(filepath)
            display_name = filename if len(filename) < 25 else filename[:22] + "..."
            self.screenshot_label.config(text=display_name, fg="black", font=("Inter", 9))
        else:
            self.selected_screenshot_path = None
            self.screenshot_label.config(text="No file selected.", fg="grey", font=("Inter Italic", 9))

    # ---Handles Confirm Button---
    def confirm_payment(self):
        # ... (Payment confirmation logic remains the same, using the MOCKED record function)
        selected_method = self.payment_method_var.get()
        gcash_name = None
        gcash_number = None
        final_screenshot_db_path = None

        if not selected_method:
            messagebox.showwarning("Selection Missing", "Please select a payment method.")
            return

        if selected_method == "Gcash":
            gcash_name = self.gcash_name_entry.get().strip()
            gcash_number = self.gcash_number_entry.get().strip()
            if not gcash_name or not gcash_number:
                messagebox.showwarning("GCash Details Missing", "Please enter GCash Name and Number.")
                return
            if not self.selected_screenshot_path:
                messagebox.showwarning("Screenshot Missing", "Please select the payment screenshot file.")
                return

            try:
                # File saving logic for GCash screenshot (still useful even with mocked DB)
                screenshots_dir = Path("./gcash_screenshots").resolve()
                screenshots_dir.mkdir(parents=True, exist_ok=True)

                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                original_ext = Path(self.selected_screenshot_path).suffix
                unique_filename = f"job_{self.job_id}_{timestamp}{original_ext}"
                destination_path = screenshots_dir / unique_filename

                shutil.copy2(self.selected_screenshot_path, destination_path)

                final_screenshot_db_path = str(destination_path)
                print(f"Screenshot copied to: {final_screenshot_db_path}")

            except OSError as e:
                messagebox.showerror("File Error",
                                     f"Could not create directory or save screenshot.\nCheck permissions.\nError: {e}")
                return
            except Exception as e:
                messagebox.showerror("File Error", f"Could not save screenshot.\nError: {e}")
                return

        confirm_msg = f"Record payment of ₱{self.payment_amount:.2f} for Job #{self.job_id} using {selected_method}?"
        if selected_method == "Gcash":
            confirm_msg += f"\nName: {gcash_name}\nNumber: {gcash_number}"

        confirm = messagebox.askyesno("Confirm Payment", confirm_msg)

        if confirm:
            # Uses the MOCKED record_payment_and_update_status
            if record_payment_and_update_status(
                    self.job_id,
                    self.payment_amount,
                    selected_method,
                    gcash_name,
                    gcash_number,
                    final_screenshot_db_path
            ):
                self.destroy()


if __name__ == "__main__":
    job_id_to_pay = None
    amount_from_args = Decimal('0.00')

    # --- Set Default Values for Standalone Testing ---
    DEFAULT_JOB_ID = 101
    DEFAULT_AMOUNT = Decimal('75.50').quantize(Decimal("0.01"))

    # Check if arguments are provided (expected > 2: script_name job_id amount)
    if len(sys.argv) > 2:
        try:
            # Use arguments provided by the command line
            job_id_to_pay = int(sys.argv[1])
            amount_from_args = Decimal(sys.argv[2]).quantize(Decimal("0.01"))
            print(f"Running with arguments. Job ID: {job_id_to_pay}, Amount: {amount_from_args}")
        except (ValueError, InvalidOperation, IndexError) as e:
            # Fallback if arguments were provided but invalid
            print(f"Argument Error: Invalid arguments provided. Using defaults. Error: {e}")
            job_id_to_pay = DEFAULT_JOB_ID
            amount_from_args = DEFAULT_AMOUNT
    else:
        # Use default values if no arguments are provided (running standalone)
        print(f"Running standalone. Using default Job ID: {DEFAULT_JOB_ID}, Default Amount: {DEFAULT_AMOUNT}")
        job_id_to_pay = DEFAULT_JOB_ID
        amount_from_args = DEFAULT_AMOUNT

    if job_id_to_pay is not None:
        app = PaymentWindow(job_id_to_pay, amount_from_args)
        app.mainloop()