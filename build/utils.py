import mysql.connector
from tkinter import messagebox, Canvas
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv
import bcrypt

load_dotenv()


#---Database: Get Connection---
def get_db_connection():
    try:
        return mysql.connector.connect(
            host=os.getenv("DB_HOST", "localhost"),
            user=os.getenv("DB_USER", "root"),
            password=os.getenv("DB_PASS", ""),
            database=os.getenv("DB_NAME", "copy_corner_db")
        )
    except mysql.connector.Error as err:
        messagebox.showerror("Database Error", f"Failed to connect to database: {err}")
        return None


#---UI: Create Rounded Rectangle---
def round_rectangle(canvas: Canvas, x1: float, y1: float, x2: float, y2: float, r: int = 15, **kwargs):
    points = [
        x1 + r, y1, x2 - r, y1, x2, y1, x2, y1 + r, x2, y2 - r, x2, y2,
        x2 - r, y2, x1 + r, y2, x1, y2, x1, y2 - r, x1, y1 + r, x1, y1,
        x1 + r, y1
    ]
    return canvas.create_polygon(points, smooth=True, **kwargs)


#---Email: Send OTP---
def send_verification_email(user_email, otp_code, email_subject="Email Verification", context="verify"):
    sender_email = os.getenv("EMAIL_USER")
    app_password = os.getenv("EMAIL_PASS")

    if not sender_email or not app_password:
        messagebox.showerror("Configuration Error",
                             "Email credentials not found in .env file (EMAIL_USER, EMAIL_PASS).")
        return False

    if context == "reset":
        intro_line = "You requested to reset your password. Please use the following code to verify your email address:"
        note_line = "If you did not request this, please ignore this email."
    elif context == "email change":
        intro_line = "You requested to change your account's email. Please use the following code to verify your new email address:"
        note_line = "If you did not request this, please ignore this email."
    else:
        intro_line = "Your account is nearly set up. Please use this code to verify your email address."
        note_line = ""

    html_body = f"""
        <html>
        <body style="font-family: Arial, sans-serif; background-color: #f4f4f4; padding: 20px;">
            <div style="max-width: 600px; margin: auto; background: white; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">
                <div style="background-color: #ffffff; padding: 20px; text-align: center;">
                    <h2 style="color: #222;">{email_subject}</h2>
                </div>
                <div style="padding: 30px; color: #333;">
                    <p>Hello,</p>
                    <p>{intro_line}</p>
                    <div style="background-color: #f1f1f1; border-radius: 5px; text-align: center; font-size: 28px;
                                letter-spacing: 5px; padding: 15px 0; margin: 25px 0; font-weight: bold; color: #333;">
                        {otp_code}
                    </div>
                    <p style="font-size: 14px; text-align: center; color: #555;">
                        <b>{note_line} Code will expire in 30 minutes.</b>
                    </p>
                </div>
            </div>
        </body>
        </html>
        """
    message = MIMEMultipart("alternative")
    message["From"] = sender_email
    message["To"] = user_email
    message["Subject"] = email_subject
    message.attach(MIMEText(html_body, "html"))

    try:
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(sender_email, app_password)
        server.sendmail(sender_email, user_email, message.as_string())
        server.quit()
        return True
    except Exception as e:
        print("Error sending email:", e)
        messagebox.showerror("Email Error", f"Could not send email.\n\nError: {e}")
        return False


#---Database: Update User---
def update_user_data_in_db(controller, user_id, data_to_update):
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        if not conn: return False
        cursor = conn.cursor()
        set_clauses = []
        params = []

        if "fullname" in data_to_update:
            set_clauses.append("fullname = %s")
            params.append(data_to_update["fullname"])
        if "username" in data_to_update:
            set_clauses.append("username = %s")
            params.append(data_to_update["username"])
        if "email" in data_to_update:
            set_clauses.append("email = %s")
            params.append(data_to_update["email"])
        if "contact" in data_to_update:
            set_clauses.append("contact = %s")
            params.append(data_to_update["contact"])
        if "profile_picture" in data_to_update:
            set_clauses.append("profile_picture = %s")
            params.append(data_to_update["profile_picture"])
        if "password" in data_to_update:
            hashed_password = bcrypt.hashpw(data_to_update["password"].encode('utf-8'), bcrypt.gensalt())
            set_clauses.append("password = %s")
            params.append(hashed_password)

        if not set_clauses:
            messagebox.showinfo("No Changes", "No fields were modified.")
            return True

        sql = f"UPDATE users SET {', '.join(set_clauses)} WHERE user_id = %s"
        params.append(user_id)

        cursor.execute(sql, tuple(params))
        conn.commit()

        if "fullname" in data_to_update and controller:
            controller.fullname = data_to_update["fullname"]

        messagebox.showinfo("Success", "Profile updated successfully!")
        return True

    except mysql.connector.Error as err:
        if conn: conn.rollback()
        if err.errno == 1062:
            if 'username' in err.msg:
                messagebox.showerror("Update Error", "Username already exists.")
            elif 'email' in err.msg:
                messagebox.showerror("Update Error", "Email address already registered.")
            else:
                messagebox.showerror("Database Error", f"Duplicate data error:\n{err}")
        else:
            messagebox.showerror("Database Error", f"Failed to update profile:\n{err}")
        return False
    except Exception as e:
        if conn: conn.rollback()
        messagebox.showerror("Error", f"Unexpected error during update: {e}")
        return False
    finally:
        if cursor: cursor.close()
        if conn and conn.is_connected(): conn.close()