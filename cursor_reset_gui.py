import tkinter as tk
from tkinter import ttk, messagebox, font as tkfont
import sys
import os
from datetime import datetime
from cursor_reset_logic import CursorResetLogic

class CursorResetGUI(tk.Frame):
    def __init__(self, master=None):
        super().__init__(master)
        self.master = master
        self.master.title("Cursor Reset Tool PRO")
        self.master.geometry("800x600")
        self.master.minsize(600, 450)
        
        # 初始化逻辑层，并传入状态更新回调
        self.logic = CursorResetLogic(self.update_status)
        
        self.style = ttk.Style()
        self._configure_style()
        
        self.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        self.master.grid_columnconfigure(0, weight=1)
        self.master.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
        
        self._create_widgets()
        
        # 设置初始状态消息
        self.update_status("欢迎使用 Cursor Reset Tool PRO\n请点击下方按钮开始重置过程。")
        
    def _configure_style(self):
        try:
            self.style.theme_use('clam')
        except tk.TclError:
            pass

        PRIMARY_COLOR = '#007bff'
        DANGER_COLOR = '#dc3545'
        BACKGROUND_COLOR = '#f8f9fa'
        CARD_COLOR = 'white'
        TEXT_COLOR = '#212529'
        
        self.master.configure(bg=BACKGROUND_COLOR)
        self.configure(background=BACKGROUND_COLOR)

        self.title_font = tkfont.Font(family="Segoe UI", size=24, weight="bold")
        self.subtitle_font = tkfont.Font(family="Segoe UI", size=12)
        self.status_font = tkfont.Font(family="Consolas", size=10)
        self.button_font = tkfont.Font(family="Segoe UI", size=12, weight="bold")

        self.style.configure("Main.TFrame", background=BACKGROUND_COLOR)
        self.style.configure("Card.TFrame", background=CARD_COLOR, borderwidth=1, relief="solid", bordercolor="#e9ecef")

        self.style.configure('Primary.TButton', 
                             font=self.button_font, 
                             foreground='white', 
                             background=PRIMARY_COLOR, 
                             borderwidth=0, 
                             relief='flat',
                             padding=[15, 10])
        self.style.map('Primary.TButton', 
                       background=[('active', '#0056b3'), ('pressed', '#0056b3')],
                       foreground=[('active', 'white'), ('pressed', 'white')])

        self.style.configure('Danger.TButton', 
                             font=self.button_font, 
                             foreground='white', 
                             background=DANGER_COLOR, 
                             borderwidth=0, 
                             relief='flat',
                             padding=[15, 10])
        self.style.map('Danger.TButton', 
                       background=[('active', '#c82333'), ('pressed', '#c82333')],
                       foreground=[('active', 'white'), ('pressed', 'white')])
        
        self.style.configure('Status.TLabel', background=CARD_COLOR, foreground=TEXT_COLOR, font=("Segoe UI", 14, "bold"))
        
    def _create_widgets(self):
        # Main frame with padding
        main_frame = ttk.Frame(self, style="Main.TFrame", padding="20 20 20 20")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        main_frame.grid_columnconfigure(0, weight=1)
        main_frame.grid_rowconfigure(1, weight=1)

        # Title Area
        title_frame = ttk.Frame(main_frame, style="Main.TFrame")
        title_frame.grid(row=0, column=0, pady=(0, 20), sticky=(tk.W, tk.E))
        title_frame.grid_columnconfigure(1, weight=1)
        
        icon_label = tk.Label(title_frame, 
                            text="✨",
                            font=("Segoe UI", 32),
                            bg=self.master['bg'],
                            fg=self.style.lookup('Primary.TButton', 'background'))
        icon_label.grid(row=0, column=0, padx=(0, 15), rowspan=2)
        
        title_label = tk.Label(title_frame,
                             text="Cursor Reset Tool PRO",
                             font=self.title_font,
                             bg=self.master['bg'],
                             fg='#2c3e50')
        title_label.grid(row=0, column=1, sticky=tk.W)
        
        subtitle_label = tk.Label(title_frame,
                                text="现代化底层代码与界面样式",
                                font=self.subtitle_font,
                                bg=self.master['bg'],
                                fg='#666666')
        subtitle_label.grid(row=1, column=1, sticky=tk.W)
        
        # Status Card
        status_card = ttk.Frame(main_frame, style="Card.TFrame", padding="20")
        status_card.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        status_card.grid_columnconfigure(0, weight=1)
        status_card.grid_rowconfigure(1, weight=1)
        
        status_title = ttk.Label(status_card,
                              text="操作日志",
                              style='Status.TLabel')
        status_title.grid(row=0, column=0, pady=(0, 10), sticky=tk.W)
        
        self.status_text = tk.Text(status_card,
                                 height=15,
                                 width=70,
                                 wrap=tk.WORD,
                                 font=self.status_font,
                                 bg='#ffffff',
                                 fg='#212529',
                                 relief='flat',
                                 highlightthickness=1,
                                 highlightbackground='#ced4da',
                                 padx=10,
                                 pady=10)
        self.status_text.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        scrollbar = ttk.Scrollbar(status_card, orient="vertical", command=self.status_text.yview)
        scrollbar.grid(row=1, column=1, sticky=(tk.N, tk.S))
        self.status_text.configure(yscrollcommand=scrollbar.set)
        
        self.status_text.config(state=tk.DISABLED)
        
        # Button Area
        button_frame = ttk.Frame(main_frame, style="Main.TFrame")
        button_frame.grid(row=2, column=0, pady=(20, 0), sticky=(tk.E))
        
        self.reset_button = ttk.Button(button_frame,
                                  text="一键重置 Cursor ID",
                                  style='Primary.TButton',
                                  cursor='hand2',
                                  command=self._on_reset_click)
        self.reset_button.grid(row=0, column=1, padx=5, sticky=tk.E)
        
        self.quit_button = ttk.Button(button_frame,
                                 text="退出程序",
                                 style='Danger.TButton',
                                 cursor='hand2',
                                 command=self.master.quit)
        self.quit_button.grid(row=0, column=0, padx=5, sticky=tk.W)

    def _on_reset_click(self):
        self.reset_button.config(state=tk.DISABLED)
        self.quit_button.config(state=tk.DISABLED)
        
        self.status_text.config(state=tk.NORMAL)
        self.status_text.delete('1.0', tk.END)
        self.status_text.config(state=tk.DISABLED)
        
        # 在UI线程中安全地运行后台逻辑
        self.master.after(100, self.run_reset_logic)
        
    def run_reset_logic(self):
        try:
            result = self.logic.reset_all_ids()
            if result:
                messagebox.showinfo("成功", "Cursor ID 已成功重置！")
            else:
                messagebox.showerror("失败", "Cursor ID 重置失败，请查看日志获取详情。")
        finally:
            self.reset_button.config(state=tk.NORMAL)
            self.quit_button.config(state=tk.NORMAL)

    def update_status(self, message):
        if not self.winfo_exists(): return
        self.status_text.config(state=tk.NORMAL)
        self.status_text.insert(tk.END, f"{datetime.now().strftime('%H:%M:%S')} - {message}\n")
        self.status_text.see(tk.END)
        self.status_text.config(state=tk.DISABLED)
        self.master.update_idletasks()

def main():
    root = tk.Tk()
    app = CursorResetGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()

