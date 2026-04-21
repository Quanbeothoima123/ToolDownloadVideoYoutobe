import os
import json
import threading
import tkinter as tk
from tkinter import ttk, messagebox
from yt_dlp import YoutubeDL

FFMPEG_DIR = os.path.join("ffmpeg", "bin")
OUTPUT_DIR = "output"
HISTORY_FILE = "history.json"
os.makedirs(OUTPUT_DIR, exist_ok=True)

stop_flag = False
BROWSERS = ["chrome", "firefox", "edge", "brave", "opera", "chromium", "vivaldi"]
selected_browser = None  # None = không dùng cookies


# ─── History (dùng JSON thay vì txt) ──────────────────────────────────────────

def load_history():
    if os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return []

def save_history(history):
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(history, f, ensure_ascii=False, indent=2)

def is_duplicate(video_url):
    # So sánh chính xác, tránh false positive của cách cũ dùng `in`
    return video_url in load_history()

def add_to_history(video_url):
    history = load_history()
    if video_url not in history:
        history.append(video_url)
        save_history(history)


# ─── Core logic ───────────────────────────────────────────────────────────────

def get_ydl_opts_base():
    opts = {'quiet': True}
    if selected_browser:
        opts['cookiesfrombrowser'] = (selected_browser,)
    return opts

def get_video_urls(url):
    ydl_opts = {
        **get_ydl_opts_base(),
        'extract_flat': True,
        'skip_download': True,
    }
    with YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)
        if 'entries' in info:
            urls = []
            for entry in info['entries']:
                # Fallback an toàn nếu thiếu key
                v_url = entry.get('webpage_url') or entry.get('url')
                if v_url:
                    urls.append(v_url)
            return urls
        else:
            v_url = info.get('webpage_url') or info.get('url') or url
            return [v_url]

def download_video(url):
    ydl_opts = {
        **get_ydl_opts_base(),
        'no_warnings': True,
        'format': 'bestvideo+bestaudio/best',
        'outtmpl': os.path.join(OUTPUT_DIR, '%(title)s.%(ext)s'),
        'ffmpeg_location': FFMPEG_DIR,
        'merge_output_format': 'mp4',
    }
    with YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        return info.get('title', 'video')


# ─── Download thread ──────────────────────────────────────────────────────────

def run_download():
    global stop_flag
    stop_flag = False

    url = url_entry.get().strip()
    if not url:
        messagebox.showerror("Lỗi", "Vui lòng nhập link YouTube")
        return

    set_ui_state("downloading")
    set_status("Đang phân tích liên kết...")

    try:
        video_urls = get_video_urls(url)
    except Exception as e:
        set_status("Đã xảy ra lỗi.")
        messagebox.showerror("Lỗi", f"Không lấy được danh sách video:\n{e}")
        set_ui_state("idle")
        return

    total = len(video_urls)
    downloaded, skipped, failed = [], [], []

    progress_bar["maximum"] = total

    for idx, v_url in enumerate(video_urls, start=1):
        if stop_flag:
            set_status(f"⛔ Đã dừng. Đã tải {len(downloaded)} video.")
            break

        if is_duplicate(v_url):
            skipped.append(v_url)
            set_status(f"⏭ Bỏ qua (đã tải): {idx}/{total}")
            progress_bar["value"] = idx
            continue

        set_status(f"⬇ Đang tải {idx}/{total}...")
        try:
            title = download_video(v_url)
            add_to_history(v_url)
            downloaded.append(title)
        except Exception as e:
            failed.append(v_url)
            print(f"[ERROR] {v_url}: {e}")

        progress_bar["value"] = idx

    # Kết quả
    msg = f"✅ Tải thành công: {len(downloaded)} video."
    if skipped:
        msg += f"\n⏭ Bỏ qua (đã tải trước): {len(skipped)} video."
    if failed:
        msg += f"\n❌ Lỗi: {len(failed)} video."

    set_status("Hoàn tất!" if not stop_flag else "Đã dừng.")
    messagebox.showinfo("Kết quả", msg)
    set_ui_state("idle")


def start_download():
    t = threading.Thread(target=run_download, daemon=True)
    t.start()

def stop_download():
    global stop_flag
    stop_flag = True
    set_status("⏹ Đang dừng...")


# ─── UI helpers ───────────────────────────────────────────────────────────────

def set_status(text):
    status_label.config(text=text)
    root.update_idletasks()

def set_ui_state(state):
    if state == "downloading":
        btn_download.config(state="disabled")
        btn_stop.config(state="normal")
    else:
        btn_download.config(state="normal")
        btn_stop.config(state="disabled")
        progress_bar["value"] = 0

def view_history():
    history = load_history()
    if not history:
        messagebox.showinfo("Lịch sử", "Chưa có video nào được tải.")
        return
    text = "\n".join(history[-30:])  # Hiển thị 30 video gần nhất
    win = tk.Toplevel(root)
    win.title("Lịch sử tải")
    win.geometry("600x400")
    txt = tk.Text(win, wrap="word")
    txt.insert("1.0", text)
    txt.config(state="disabled")
    txt.pack(fill="both", expand=True, padx=10, pady=10)

def open_output_folder():
    abs_path = os.path.abspath(OUTPUT_DIR)
    os.startfile(abs_path)

def on_browser_change(event=None):
    global selected_browser
    val = browser_var.get()
    selected_browser = val if val != "Không dùng cookies" else None
    lbl_browser_status.config(
        text=f"🍪 Đang dùng cookies từ: {selected_browser}" if selected_browser else "⚠ Không dùng cookies (có thể bị chặn)",
        fg="green" if selected_browser else "orange"
    )


# ─── GUI ──────────────────────────────────────────────────────────────────────

root = tk.Tk()
root.title("YouTube Best Quality Downloader")
root.geometry("600x320")
root.resizable(False, False)

frame = tk.Frame(root)
frame.pack(pady=15, padx=20, fill="x")

tk.Label(frame, text="Nhập link video hoặc playlist:").pack(anchor="w")
url_entry = tk.Entry(frame, width=70)
url_entry.pack(pady=5, fill="x")

# ── Chọn trình duyệt để lấy cookies ──
browser_frame = tk.Frame(frame)
browser_frame.pack(anchor="w", pady=(0, 4))
tk.Label(browser_frame, text="Trình duyệt lấy cookies:").pack(side="left")
browser_var = tk.StringVar(value="Không dùng cookies")
browser_combo = ttk.Combobox(browser_frame, textvariable=browser_var,
                              values=["Không dùng cookies"] + BROWSERS,
                              state="readonly", width=18)
browser_combo.pack(side="left", padx=6)
browser_combo.bind("<<ComboboxSelected>>", on_browser_change)
lbl_browser_status = tk.Label(browser_frame,
                               text="⚠ Không dùng cookies (có thể bị chặn)",
                               fg="orange")
lbl_browser_status.pack(side="left", padx=4)

btn_frame = tk.Frame(frame)
btn_frame.pack(pady=8)

btn_download = tk.Button(btn_frame, text="⬇ Tải video", width=20, command=start_download, bg="#2ecc71", fg="white")
btn_download.grid(row=0, column=0, padx=5)

btn_stop = tk.Button(btn_frame, text="⏹ Dừng", width=12, command=stop_download, state="disabled", bg="#e74c3c", fg="white")
btn_stop.grid(row=0, column=1, padx=5)

btn_history = tk.Button(btn_frame, text="📋 Lịch sử", width=12, command=view_history)
btn_history.grid(row=0, column=2, padx=5)

btn_open = tk.Button(btn_frame, text="📁 Mở thư mục", width=14, command=open_output_folder)
btn_open.grid(row=0, column=3, padx=5)

progress_bar = ttk.Progressbar(frame, orient="horizontal", mode="determinate", length=500)
progress_bar.pack(pady=8, fill="x")

status_label = tk.Label(root, text="Sẵn sàng.", fg="gray")
status_label.pack()

root.mainloop()