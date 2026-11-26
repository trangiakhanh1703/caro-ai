"""Khởi động giao diện Caro trên Windows mà không mở cửa sổ console."""

from tkinter import messagebox

try:
    from gui import main

    main()
except Exception as exc:  # Hiển thị lỗi vì pythonw.exe không có terminal.
    messagebox.showerror("Không thể mở Caro AI", str(exc))
