import os
import json
import threading
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from yt_dlp import YoutubeDL

FFMPEG_DIR = os.path.join("ffmpeg", "bin")
OUTPUT_DIR = "output"
HISTORY_FILE = "history.json"
COOKIES_FILE = "cookies.txt"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Thêm ffmpeg vào PATH hệ thống (giống tool Shorts đang hoạt động tốt)
_ffmpeg_abs = os.path.abspath(FFMPEG_DIR)
os.environ["PATH"] = _ffmpeg_abs + os.pathsep + os.environ.get("PATH", "")

stop_flag = False
BROWSERS = ["chrome", "firefox", "edge", "brave", "opera", "chromium", "vivaldi"]
cookie_mode = "none"
selected_browser = "chrome"
cookies_file_path = COOKIES_FILE


# ─── History ──────────────────────────────────────────────────────────────────

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
    return video_url in load_history()

def add_to_history(video_url):
    history = load_history()
    if video_url not in history:
        history.append(video_url)
        save_history(history)


# ─── Cookies ──────────────────────────────────────────────────────────────────

def get_ydl_opts_base():
    opts = {'quiet': True}
    if cookie_mode == "file" and os.path.exists(cookies_file_path):
        opts['cookiefile'] = cookies_file_path
    elif cookie_mode == "browser":
        opts['cookiesfrombrowser'] = (selected_browser,)
    return opts


def export_cookies_from_browser():
    """Xuất cookies từ trình duyệt ra file cookies.txt."""
    browser = selected_browser
    out_file = os.path.abspath(COOKIES_FILE)

    def _do_export():
        set_status(f"Đang xuất cookies từ {browser}...")
        try:
            ydl_opts = {
                'quiet': True,
                'cookiesfrombrowser': (browser,),
                'cookiefile': out_file,
                'skip_download': True,
                'extract_flat': True,
            }
            with YoutubeDL(ydl_opts) as ydl:
                ydl.extract_info("https://www.youtube.com", download=False)

            if os.path.exists(out_file):
                set_status(f"Xuất cookies OK: {out_file}")
                cookie_mode_var.set("file")
                cookies_path_var.set(out_file)
                on_cookie_mode_change()
                messagebox.showinfo("Thành công",
                    f"Đã xuất cookies ra:\n{out_file}\n\n"
                    "Tool sẽ dùng file này, không cần đóng trình duyệt nữa.")
            else:
                set_status("Không xuất được cookies.")
                messagebox.showerror("Lỗi", "Không tạo được file cookies.txt.")
        except Exception as e:
            err = str(e)
            set_status("Lỗi xuất cookies.")
            if "Could not copy" in err or "locked" in err.lower():
                messagebox.showerror("Trình duyệt đang mở",
                    f"{browser} đang chạy nên không đọc được cookie database.\n\n"
                    "Chọn một trong hai cách:\n"
                    "① Đóng hẳn trình duyệt → bấm 'Xuất cookies' lại\n\n"
                    "② Cài extension 'Get cookies.txt LOCALLY' trên Chrome:\n"
                    "   https://chromewebstore.google.com/detail/get-cookiestxt-locally/cclelndahbckbenkjhflpdbgdldlbecc\n"
                    "   → Mở YouTube → bấm icon extension → Export\n"
                    "   → Bấm 'Chọn file...' để chỉ đường dẫn file vừa tải.")
            else:
                messagebox.showerror("Lỗi", err)

    threading.Thread(target=_do_export, daemon=True).start()


def browse_cookies_file():
    global cookies_file_path
    path = filedialog.askopenfilename(
        title="Chọn file cookies.txt",
        filetypes=[("Cookies file", "*.txt"), ("All files", "*.*")]
    )
    if path:
        cookies_file_path = path
        cookies_path_var.set(path)
        cookie_mode_var.set("file")
        on_cookie_mode_change()


# ─── Core logic ───────────────────────────────────────────────────────────────

def get_video_urls(url):
    ydl_opts = {**get_ydl_opts_base(), 'extract_flat': True, 'skip_download': True}
    with YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)
        if 'entries' in info:
            urls = []
            for entry in info['entries']:
                v_url = entry.get('webpage_url') or entry.get('url')
                if v_url:
                    urls.append(v_url)
            return urls
        else:
            return [info.get('webpage_url') or info.get('url') or url]

def download_video(url):
    ydl_opts = {
        **get_ydl_opts_base(),
        'no_warnings': True,
        'format': 'bestvideo+bestaudio/best',
        'outtmpl': os.path.join(OUTPUT_DIR, '%(title)s.%(ext)s'),
        'merge_output_format': 'mp4',
        'postprocessors': [{
            'key': 'FFmpegVideoConvertor',
            'preferedformat': 'mp4',
        }],
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

    if cookie_mode == "file" and not os.path.exists(cookies_file_path):
        messagebox.showerror("Thiếu cookies",
            "Không tìm thấy file cookies.txt.\n"
            "Hãy bấm 'Xuất cookies' hoặc 'Chọn file...'")
        return

    set_ui_state("downloading")
    set_status("Đang phân tích liên kết...")

    try:
        video_urls = get_video_urls(url)
    except Exception as e:
        err = str(e)
        set_status("Đã xảy ra lỗi.")
        if "Sign in" in err or "bot" in err.lower() or "Could not copy" in err:
            messagebox.showerror("Lỗi xác thực YouTube",
                "YouTube yêu cầu đăng nhập hoặc không đọc được cookies.\n\n"
                "Giải pháp nhanh nhất:\n"
                "① Chọn 'Cookies từ file (.txt)'\n"
                "② Cài 'Get cookies.txt LOCALLY' trên Chrome, mở YouTube, xuất file\n"
                "③ Bấm 'Chọn file...' chọn file đó → Tải lại")
        else:
            messagebox.showerror("Lỗi", f"Không lấy được danh sách:\n{err}")
        set_ui_state("idle")
        return

    total = len(video_urls)
    downloaded, skipped, failed = [], [], []
    progress_bar["maximum"] = total

    for idx, v_url in enumerate(video_urls, start=1):
        if stop_flag:
            set_status(f"Đã dừng. Đã tải {len(downloaded)} video.")
            break
        if is_duplicate(v_url):
            skipped.append(v_url)
            set_status(f"Bỏ qua (đã tải): {idx}/{total}")
            progress_bar["value"] = idx
            continue
        set_status(f"Đang tải {idx}/{total}...")
        try:
            title = download_video(v_url)
            add_to_history(v_url)
            downloaded.append(title)
        except Exception as e:
            failed.append(v_url)
            print(f"[ERROR] {v_url}: {e}")
        progress_bar["value"] = idx

    msg = f"✅ Tải thành công: {len(downloaded)} video."
    if skipped:
        msg += f"\n⏭ Bỏ qua (đã tải): {len(skipped)} video."
    if failed:
        msg += f"\n❌ Lỗi: {len(failed)} video."
    set_status("Hoàn tất!" if not stop_flag else "Đã dừng.")
    messagebox.showinfo("Kết quả", msg)
    set_ui_state("idle")


def start_download():
    threading.Thread(target=run_download, daemon=True).start()

def stop_download():
    global stop_flag
    stop_flag = True
    set_status("Đang dừng...")


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
    win = tk.Toplevel(root)
    win.title("Lịch sử tải")
    win.geometry("600x400")
    txt = tk.Text(win, wrap="word")
    txt.insert("1.0", "\n".join(history[-30:]))
    txt.config(state="disabled")
    txt.pack(fill="both", expand=True, padx=10, pady=10)

def open_output_folder():
    os.startfile(os.path.abspath(OUTPUT_DIR))

def on_cookie_mode_change(*args):
    global cookie_mode
    cookie_mode = cookie_mode_var.get()
    frame_browser.pack_forget()
    frame_file.pack_forget()
    if cookie_mode == "none":
        lbl_status.config(text="⚠ Không dùng cookies — YouTube có thể chặn tải", fg="orange")
    elif cookie_mode == "browser":
        frame_browser.pack(anchor="w", pady=2, fill="x")
        lbl_status.config(
            text=f"⚠ Đọc cookie từ {browser_var.get()} — cần đóng trình duyệt trước!",
            fg="#c0392b")
    elif cookie_mode == "file":
        frame_file.pack(anchor="w", pady=2, fill="x")
        f = cookies_path_var.get()
        ok = os.path.exists(f)
        lbl_status.config(
            text=("✅ File cookies: " + os.path.basename(f)) if ok else "❌ Chưa có file cookies — xuất hoặc chọn file",
            fg="green" if ok else "red")

def on_browser_change(*args):
    global selected_browser
    selected_browser = browser_var.get()
    if cookie_mode == "browser":
        on_cookie_mode_change()


# ─── GUI ──────────────────────────────────────────────────────────────────────

root = tk.Tk()
root.title("YouTube Best Quality Downloader")
root.geometry("640x400")
root.resizable(False, False)

frame = tk.Frame(root)
frame.pack(pady=12, padx=20, fill="x")

tk.Label(frame, text="Nhập link video hoặc playlist:").pack(anchor="w")
url_entry = tk.Entry(frame, width=78)
url_entry.pack(pady=(3, 8), fill="x")

# ── Cookie mode ──
tk.Label(frame, text="Xác thực YouTube (chọn một):", font=("", 9, "bold")).pack(anchor="w")

cookie_mode_var = tk.StringVar(value="none")
cookie_mode_var.trace_add("write", on_cookie_mode_change)

rf = tk.Frame(frame)
rf.pack(anchor="w", pady=(2, 0))
tk.Radiobutton(rf, text="Không dùng cookies", variable=cookie_mode_var, value="none").pack(side="left")
tk.Radiobutton(rf, text="Từ trình duyệt (cần đóng browser)", variable=cookie_mode_var, value="browser").pack(side="left", padx=12)
tk.Radiobutton(rf, text="Từ file cookies.txt  ✅ Khuyên dùng", variable=cookie_mode_var, value="file").pack(side="left")

# Browser sub-frame
frame_browser = tk.Frame(frame)
browser_var = tk.StringVar(value="chrome")
browser_var.trace_add("write", on_browser_change)
tk.Label(frame_browser, text="  Trình duyệt:").pack(side="left")
ttk.Combobox(frame_browser, textvariable=browser_var, values=BROWSERS,
             state="readonly", width=13).pack(side="left", padx=4)
tk.Button(frame_browser, text="Xuất cookies → file cookies.txt",
          bg="#2980b9", fg="white", command=export_cookies_from_browser).pack(side="left", padx=6)

# File sub-frame
frame_file = tk.Frame(frame)
cookies_path_var = tk.StringVar(value=os.path.abspath(COOKIES_FILE))
tk.Label(frame_file, text="  File:").pack(side="left")
tk.Entry(frame_file, textvariable=cookies_path_var, width=32, state="readonly").pack(side="left", padx=4)
tk.Button(frame_file, text="Chọn file...", command=browse_cookies_file).pack(side="left", padx=2)
tk.Button(frame_file, text="Xuất từ trình duyệt",
          bg="#2980b9", fg="white", command=export_cookies_from_browser).pack(side="left", padx=6)

lbl_status = tk.Label(frame, text="⚠ Không dùng cookies — YouTube có thể chặn tải",
                       fg="orange", font=("", 8))
lbl_status.pack(anchor="w", pady=(3, 6))

# ── Buttons ──
btn_frame = tk.Frame(frame)
btn_frame.pack(pady=4)

btn_download = tk.Button(btn_frame, text="⬇ Tải video", width=18,
                          command=start_download, bg="#27ae60", fg="white", font=("", 10, "bold"))
btn_download.grid(row=0, column=0, padx=5)

btn_stop = tk.Button(btn_frame, text="⏹ Dừng", width=12,
                      command=stop_download, state="disabled", bg="#e74c3c", fg="white")
btn_stop.grid(row=0, column=1, padx=5)

tk.Button(btn_frame, text="📋 Lịch sử", width=12, command=view_history).grid(row=0, column=2, padx=5)
tk.Button(btn_frame, text="📁 Mở thư mục", width=14, command=open_output_folder).grid(row=0, column=3, padx=5)

progress_bar = ttk.Progressbar(frame, orient="horizontal", mode="determinate", length=580)
progress_bar.pack(pady=6, fill="x")

status_label = tk.Label(root, text="Sẵn sàng.", fg="gray")
status_label.pack()

root.mainloop()