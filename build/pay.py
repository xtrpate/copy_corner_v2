from pathlib import Path
import tkinter as tk
from tkinter import Tk, Canvas, Button, PhotoImage, messagebox, Label, Radiobutton, StringVar, Entry, Frame, filedialog
import sys
import mysql.connector
import os
import shutil
from datetime import datetime
from decimal import Decimal, InvalidOperation
from utils import get_db_connection, round_rectangle


OUTPUT_PATH = Path(__file__).parent
ASSETS_PATH = OUTPUT_PATH / "assets" / "frame0"

#---Asset Path Constructor---
def relative_to_assets(path: str) -> Path:
    asset_file = ASSETS_PATH / Path(path)
    if not asset_file.is_file():
        print(f"Warning: Asset (pay.py) not found at {asset_file}")
    return asset_file

#---Database: Fetches Job Details---
def fetch_job_details(job_id):
    details = None
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        if not conn:
            messagebox.showerror("Database Error", "Could not connect to database.")
            return None
        cursor = conn.cursor(dictionary=True)
        query = """
            SELECT
                pj.job_id, u.username, f.file_name, pj.status,
                pj.pages, pj.copies, pj.paper_size, pj.color_option
            FROM print_jobs pj
            LEFT JOIN users u ON pj.user_id = u.user_id
            LEFT JOIN files f ON pj.file_id = f.file_id
            WHERE pj.job_id = %s
        """
        cursor.execute(query, (job_id,))
        details = cursor.fetchone()

        if not details:
            messagebox.showerror("Error", f"Job ID {job_id} not found.")
            return None

        details['file_name'] = details.get('file_name', 'N/A')
        details['color_option'] = details.get('color_option', 'N/A')
        details['pages'] = details.get('pages', 'N/A')
        details['copies'] = details.get('copies', 'N/A')
        details['paper_size'] = details.get('paper_size', 'N/A')

    except mysql.connector.Error as err:
        messagebox.showerror("Database Error", f"Error fetching job details:\n{err}")
        return None
    except Exception as e:
         messagebox.showerror("Error", f"An unexpected error occurred fetching details: {e}")
         return None
    finally:
        if cursor:
            cursor.close()
        if conn and conn.is_connected():
            conn.close()
    return details

#---Database: Records Payment---
def record_payment_and_update_status(job_id, payment_amount, payment_method, gcash_name=None, gcash_number=None, screenshot_path=None):
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        if not conn:
            messagebox.showerror("Database Error", "Could not connect to record payment.")
            return False

        conn.start_transaction()
        cursor = conn.cursor()

        insert_query = """
            INSERT INTO payments
            (job_id, payment_amount, payment_method, gcash_name, gcash_number, gcash_screenshot_path, payment_timestamp)
            VALUES (%s, %s, %s, %s, %s, %s, NOW())
        """
        payment_data = (
            job_id,
            payment_amount,
            payment_method,
            gcash_name if payment_method == "Gcash" else None,
            gcash_number if payment_method == "Gcash" else None,
            screenshot_path if payment_method == "Gcash" else None
        )
        cursor.execute(insert_query, payment_data)
        payment_id = cursor.lastrowid
        print(f"Payment record {payment_id} inserted for job {job_id}.")

        new_status = "Cash" if payment_method == "Cash" else "Paid"

        update_query = """
            UPDATE print_jobs
            SET status = %s, 
                payment_method = %s
            WHERE job_id = %s AND status = 'Approved'
        """
        cursor.execute(update_query, (new_status, payment_method, job_id))
        affected_rows = cursor.rowcount

        conn.commit()
        print(f"Job {job_id} status updated to Paid (Affected rows: {affected_rows}). Transaction committed.")


        if affected_rows > 0:
            messagebox.showinfo("Payment Successfully", f"Payment successfully.")
            return True
        else:
            messagebox.showwarning("Payment Recorded (Status Unchanged)",
                                   f"Payment recorded for Job #{job_id}, but its status was not 'Approved' and remains unchanged.")
            return True

    except mysql.connector.Error as err:
        messagebox.showerror("Database Error", f"Error recording payment:\n{err}")
        if conn:
            print("Rolling back transaction due to error.")
            conn.rollback()
        return False
    except Exception as e:
        messagebox.showerror("Error", f"An unexpected error occurred:\n{e}")
        if conn:
            print("Rolling back transaction due to unexpected error.")
            conn.rollback()
        return False
    finally:
        if cursor:
            cursor.close()
        if conn and conn.is_connected():
            conn.close()


class PaymentWindow(Tk):
    #---Initializes Payment UI---
    def __init__(self, job_id, amount_from_args):
        super().__init__()
        self.job_id = job_id
        self.payment_amount = amount_from_args
        self.job_details = fetch_job_details(job_id)
        self.selected_screenshot_path = None

        if not self.job_details:
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

        self.canvas = Canvas(
            self, bg="#FFFFFF", height=window_height, width=window_width,
            bd=0, highlightthickness=0, relief="ridge"
        )
        self.canvas.place(x=0, y=0)

        header_height = 74
        self.canvas.create_rectangle(0, 0, window_width, header_height, fill="#000000", outline="")
        self.canvas.create_text(20, header_height / 2, anchor="w", text="Payment Method:",
                                fill="#FFFFFF", font=("Inter Bold", 24))
        content_y_start = header_height + 20
        label_x = 30
        value_x = 180
        row_y = content_y_start
        details_font = ("Inter", 11)
        details_bold_font = ("Inter Bold", 11)
        Label(self, text="File Name:", font=details_bold_font, bg="#FFFFFF").place(x=label_x, y=row_y)
        Label(self, text=self.job_details['file_name'], font=details_font, bg="#FFFFFF", anchor="w", wraplength=window_width-value_x-20).place(x=value_x, y=row_y)
        row_y += 25
        Label(self, text="Color:", font=details_bold_font, bg="#FFFFFF").place(x=label_x, y=row_y)
        Label(self, text=self.job_details['color_option'], font=details_font, bg="#FFFFFF", anchor="w").place(x=value_x, y=row_y)
        row_y += 25
        Label(self, text="Paper Size:", font=details_bold_font, bg="#FFFFFF").place(x=label_x, y=row_y)
        Label(self, text=self.job_details['paper_size'], font=details_font, bg="#FFFFFF", anchor="w").place(x=value_x, y=row_y)
        row_y += 25
        Label(self, text="Pages:", font=details_bold_font, bg="#FFFFFF").place(x=label_x, y=row_y)
        Label(self, text=str(self.job_details['pages']), font=details_font, bg="#FFFFFF", anchor="w").place(x=value_x, y=row_y)
        row_y += 25
        Label(self, text="Copies:", font=details_bold_font, bg="#FFFFFF").place(x=label_x, y=row_y)
        Label(self, text=str(self.job_details['copies']), font=details_font, bg="#FFFFFF", anchor="w").place(x=value_x, y=row_y)
        row_y += 35
        amount_text = f"₱{self.payment_amount:.2f}"
        Label(self, text="Total Amount:", font=("Inter Bold", 16), bg="#FFFFFF").place(x=label_x, y=row_y)
        Label(self, text=amount_text, font=("Inter Bold", 20, "bold"), bg="#FFFFFF", fg="#000000").place(x=value_x, y=row_y - 3)
        row_y += 50
        Label(self, text="Select Method:", font=("Inter Bold", 14), bg="#FFFFFF").place(x=label_x, y=row_y)
        self.payment_method_var = StringVar(value="Cash")
        Radiobutton(self, text="Cash", variable=self.payment_method_var, value="Cash", font=("Inter", 12), bg="#FFFFFF", anchor="w", command=self._update_payment_fields).place(x=label_x + 20, y=row_y + 30)
        Radiobutton(self, text="GCash", variable=self.payment_method_var, value="Gcash", font=("Inter", 12), bg="#FFFFFF", anchor="w", command=self._update_payment_fields).place(x=label_x + 120, y=row_y + 30)
        row_y += 65
        self.gcash_frame = Frame(self, bg="#FFFFFF")
        Label(self.gcash_frame, text="GCash Name:", font=details_font, bg="#FFFFFF").grid(row=0, column=0, sticky="w", pady=2)
        self.gcash_name_entry = Entry(self.gcash_frame, font=details_font, bd=1, relief="solid", width=30)
        self.gcash_name_entry.grid(row=0, column=1, sticky="w", padx=5, pady=2)
        Label(self.gcash_frame, text="GCash Number:", font=details_font, bg="#FFFFFF").grid(row=1, column=0, sticky="w", pady=2)
        self.gcash_number_entry = Entry(self.gcash_frame, font=details_font, bd=1, relief="solid", width=30)
        self.gcash_number_entry.grid(row=1, column=1, sticky="w", padx=5, pady=2)
        Label(self.gcash_frame, text="Screenshot:", font=details_font, bg="#FFFFFF").grid(row=2, column=0, sticky="w", pady=2)
        self.screenshot_button = Button(self.gcash_frame, text="Browse...", font=("Inter", 9), command=self._browse_screenshot, bg="#000000", fg="#FFFFFF", activebackground="#333333", activeforeground="#FFFFFF", bd=1, relief="raised")
        self.screenshot_button.grid(row=2, column=1, sticky="w", padx=5, pady=2)
        self.screenshot_label = Label(self.gcash_frame, text="No file selected.", font=("Inter Italic", 9), bg="#FFFFFF", fg="grey")
        self.screenshot_label.grid(row=2, column=2, sticky="w", padx=5, pady=2)
        button_y = window_height - 60
        self.confirm_button = Button(self, text="Confirm Payment", font=("Inter Bold", 12), command=self.confirm_payment, relief="raised", bd=1, bg="#000000", fg="#FFFFFF", activebackground="#333333", activeforeground="#FFFFFF", cursor="hand2")
        self.confirm_button.place(x=window_width - 180, y=button_y, width=150, height=35)
        self.cancel_button = Button(self, text="Cancel", font=("Inter Bold", 12), command=self.destroy, relief="raised", bd=1, bg="#000000", fg="#FFFFFF", activebackground="#333333", activeforeground="#FFFFFF", cursor="hand2")
        self.cancel_button.place(x=label_x, y=button_y, width=100, height=35)

        self._update_payment_fields()

    #---Toggles GCash Fields---
    def _update_payment_fields(self):
        if self.payment_method_var.get() == "Gcash":
            self.gcash_frame.place(relx=0.05, rely=0.68, relwidth=0.9)
            self.confirm_button.config(state=tk.NORMAL)
        else:
            self.gcash_frame.place_forget()
            self.confirm_button.config(state=tk.NORMAL)

    #---Handles Browse Button---
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

    #---Handles Confirm Button---
    def confirm_payment(self):
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
                messagebox.showerror("File Error", f"Could not create directory or save screenshot.\nCheck permissions.\nError: {e}")
                return
            except Exception as e:
                messagebox.showerror("File Error", f"Could not save screenshot.\nError: {e}")
                return

        confirm_msg = f"Record payment of ₱{self.payment_amount:.2f} for Job #{self.job_id} using {selected_method}?"
        if selected_method == "Gcash":
            confirm_msg += f"\nName: {gcash_name}\nNumber: {gcash_number}"

        confirm = messagebox.askyesno("Confirm Payment", confirm_msg)

        if confirm:
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

    if len(sys.argv) > 2:
        try:
            job_id_to_pay = int(sys.argv[1])
            amount_from_args = Decimal(sys.argv[2]).quantize(Decimal("0.01"))
            print(f"Received Job ID: {job_id_to_pay}, Amount: {amount_from_args}")
        except (ValueError, InvalidOperation, IndexError) as e:
            messagebox.showerror("Error", f"Invalid or missing arguments provided.\nExpected: JobID Amount\nError: {e}")
            sys.exit(1)
    elif len(sys.argv) <= 2:
        messagebox.showerror("Error", "Missing required arguments.\nExpected: JobID Amount")
        sys.exit(1)

    if job_id_to_pay is not None:
        app = PaymentWindow(job_id_to_pay, amount_from_args)
        app.mainloop()