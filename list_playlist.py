import os
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import threading
from yt_dlp import YoutubeDL


def fetch_titles(url: str, output_path: str, status_var: tk.StringVar, btn: tk.Button):
    try:
        ydl_opts = {
            "quiet": True,
            "extract_flat": True,   # không download, chỉ lấy metadata
            "skip_download": True,
        }
        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)

        # Hỗ trợ cả playlist lẫn single video
        if "entries" in info:
            titles = [
                entry.get("title") or entry.get("url", f"Video {i+1}")
                for i, entry in enumerate(info["entries"])
                if entry
            ]
        else:
            titles = [info.get("title", url)]

        with open(output_path, "w", encoding="utf-8") as f:
            f.write("\n".join(titles))

        status_var.set(f"✓ Đã ghi {len(titles)} tiêu đề vào:\n{output_path}")
        messagebox.showinfo("Hoàn thành", f"Đã ghi {len(titles)} tiêu đề vào:\n{output_path}")

    except Exception as e:
        status_var.set(f"Lỗi: {e}")
        messagebox.showerror("Lỗi", str(e))
    finally:
        btn.config(state="normal")


def start():
    url = url_var.get().strip()
    if not url:
        messagebox.showwarning("Thiếu URL", "Vui lòng nhập URL playlist / video.")
        return

    output_path = filedialog.asksaveasfilename(
        title="Lưu danh sách tiêu đề",
        defaultextension=".txt",
        filetypes=[("Text files", "*.txt")],
        initialfile="playlist_titles.txt",
    )
    if not output_path:
        return

    btn_start.config(state="disabled")
    status_var.set("Đang tải thông tin, vui lòng chờ...")
    threading.Thread(
        target=fetch_titles,
        args=(url, output_path, status_var, btn_start),
        daemon=True,
    ).start()


# ─── UI ───────────────────────────────────────────────────────────────────────
root = tk.Tk()
root.title("YouTube Playlist Title Exporter")
root.resizable(False, False)

frame = ttk.Frame(root, padding=16)
frame.pack(fill="both", expand=True)

ttk.Label(frame, text="URL Playlist / Video:").grid(row=0, column=0, sticky="w")
url_var = tk.StringVar()
ttk.Entry(frame, textvariable=url_var, width=60).grid(row=1, column=0, pady=(4, 12))

btn_start = ttk.Button(frame, text="Lấy tiêu đề & Lưu file", command=start)
btn_start.grid(row=2, column=0, pady=(0, 12))

status_var = tk.StringVar(value="")
ttk.Label(frame, textvariable=status_var, wraplength=450, justify="left").grid(row=3, column=0)

root.mainloop()
