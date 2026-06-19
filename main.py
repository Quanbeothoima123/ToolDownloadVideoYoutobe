import os
import json
import threading
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from yt_dlp import YoutubeDL

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FFMPEG_DIR = os.path.join(BASE_DIR, "ffmpeg", "bin")
FFMPEG_EXE = os.path.join(FFMPEG_DIR, "ffmpeg.exe")
OUTPUT_DIR = os.path.join(BASE_DIR, "output")
HISTORY_FILE = os.path.join(BASE_DIR, "history.json")
COOKIES_FILE = os.path.join(BASE_DIR, "cookies.txt")
BEST_QUALITY_FORMAT = (
    "bv*[height>=1080]+ba/b[height>=1080]/"
    "bv*+ba/b"
)
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Thêm ffmpeg vào PATH hệ thống (giống tool Shorts đang hoạt động tốt)
os.environ["PATH"] = FFMPEG_DIR + os.pathsep + os.environ.get("PATH", "")

stop_flag = False
BROWSERS = ["chrome", "firefox", "edge", "brave", "opera", "chromium", "vivaldi"]
cookie_mode = "none"
selected_browser = "chrome"
cookies_file_path = COOKIES_FILE


# ─── History ──────────────────────────────────────────────────────────────────

def has_cookie_file(path):
    return os.path.isfile(path) and os.path.getsize(path) > 0

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
    for entry in load_history():
        url = entry.get("url") if isinstance(entry, dict) else entry
        if url == video_url:
            file_path = entry.get("file") if isinstance(entry, dict) else None
            return bool(file_path and os.path.exists(file_path))
    return False

def add_to_history(video_url, title="", file_path=""):
    history = load_history()
    for entry in history:
        if isinstance(entry, dict) and entry.get("url") == video_url:
            entry.update({"title": title, "url": video_url, "file": file_path})
            save_history(history)
            return
    history.append({"title": title, "url": video_url, "file": file_path})
    save_history(history)


# ─── Cookies ──────────────────────────────────────────────────────────────────

def get_ydl_opts_base():
    opts = {
        'quiet': True,
        'js_runtimes': {'node': {}},
        'remote_components': {'ejs:github': {}},
    }
    if cookie_mode == "file" and has_cookie_file(cookies_file_path):
        opts['cookiefile'] = cookies_file_path
    elif cookie_mode == "browser":
        opts['cookiesfrombrowser'] = (selected_browser,)
    return opts


def describe_cookie_source():
    if cookie_mode == "file":
        if os.path.exists(cookies_file_path):
            return f"file={cookies_file_path} size={os.path.getsize(cookies_file_path)}"
        return f"file={cookies_file_path} missing"
    if cookie_mode == "browser":
        return f"browser={selected_browser}"
    return "none"


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

            if has_cookie_file(out_file):
                set_status(f"Xuất cookies OK: {out_file}")
                cookie_mode_var.set("file")
                cookies_path_var.set(out_file)
                on_cookie_mode_change()
                messagebox.showinfo("Thành công",
                    f"Đã xuất cookies ra:\n{out_file}\n\n"
                    "Tool sẽ dùng file này, không cần đóng trình duyệt nữa.")
            else:
                set_status("Không xuất được cookies.")
                messagebox.showerror("Lỗi", "Không tạo được file cookies.txt hoặc file cookies đang rỗng.")
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


def describe_format(info):
    if not info:
        return "không có thông tin format"

    formats = info.get("requested_downloads") or info.get("requested_formats") or [info]
    details = []
    for fmt in formats:
        height = fmt.get("height") or "?"
        fps = fmt.get("fps")
        fps_text = f"{fps}fps" if fps else "fps?"
        codec = fmt.get("vcodec") or fmt.get("acodec") or "codec?"
        ext = fmt.get("ext") or "ext?"
        format_id = fmt.get("format_id") or "id?"
        if fmt.get("vcodec") != "none":
            details.append(f"{height}p {fps_text} {codec} ({ext}, {format_id})")
        elif fmt.get("acodec") != "none":
            details.append(f"audio {codec} ({ext}, {format_id})")

    return " + ".join(details) if details else "không đọc được format"


def summarize_available_formats(info):
    formats = info.get("formats") or []
    video_formats = []
    audio_formats = []

    for fmt in formats:
        format_id = fmt.get("format_id") or "id?"
        ext = fmt.get("ext") or "ext?"
        height = fmt.get("height")
        fps = fmt.get("fps")
        vcodec = fmt.get("vcodec")
        acodec = fmt.get("acodec")
        tbr = fmt.get("tbr") or 0

        if vcodec and vcodec != "none":
            fps_text = f"{fps}fps" if fps else ""
            video_formats.append((height or 0, tbr, f"{format_id}:{height or '?'}p{fps_text}:{ext}:{vcodec}"))
        elif acodec and acodec != "none":
            audio_formats.append((tbr, f"{format_id}:audio:{ext}:{acodec}"))

    video_formats.sort(reverse=True)
    audio_formats.sort(reverse=True)
    video_text = ", ".join(item[2] for item in video_formats[:12]) or "none"
    audio_text = ", ".join(item[1] for item in audio_formats[:6]) or "none"
    return f"video[{video_text}] audio[{audio_text}] total={len(formats)}"


def get_downloaded_files(info):
    paths = []
    candidates = []
    for item in info.get("requested_downloads") or []:
        candidates.extend([item.get("filepath"), item.get("filename")])
    candidates.extend([info.get("filepath"), info.get("_filename")])

    for path in candidates:
        if path and os.path.exists(path) and os.path.isfile(path):
            paths.append(path)
    return paths


def download_video(url):
    ydl_opts = {
        **get_ydl_opts_base(),
        'quiet': False,
        'no_warnings': False,
        'ffmpeg_location': FFMPEG_DIR,
        'outtmpl': os.path.join(OUTPUT_DIR, '%(title)s.%(ext)s'),
        'format': BEST_QUALITY_FORMAT,
        'merge_output_format': 'mp4',
        'ignoreerrors': False,
    }
    with YoutubeDL(ydl_opts) as ydl:
        probe_info = ydl.extract_info(url, download=False)
        print(f"[COOKIE] {describe_cookie_source()}")
        print(f"[AVAILABLE FORMATS] {summarize_available_formats(probe_info)}")
        info = ydl.extract_info(url, download=True)
        if info is None:
            return None, "không có thông tin format", []
        downloaded_files = get_downloaded_files(info)
        if not downloaded_files:
            raise RuntimeError("yt-dlp không tạo file hoàn chỉnh trong thư mục output.")
        return info.get('title', 'video'), describe_format(info), downloaded_files


# ─── Download thread ──────────────────────────────────────────────────────────

def run_download():
    global stop_flag
    stop_flag = False
    url = url_entry.get().strip()
    if not url:
        messagebox.showerror("Lỗi", "Vui lòng nhập link YouTube")
        return

    if cookie_mode == "file" and not has_cookie_file(cookies_file_path):
        messagebox.showerror("Thiếu cookies",
            "Không tìm thấy file cookies.txt hợp lệ hoặc file đang rỗng.\n"
            "Video members-only cần cookies của tài khoản đã có quyền xem.")
        return

    if not os.path.exists(FFMPEG_EXE):
        messagebox.showerror("Thiếu FFmpeg",
            f"Không tìm thấy FFmpeg tại:\n{FFMPEG_EXE}\n\n"
            "Không có FFmpeg thì không ghép được best video + best audio, "
            "rất dễ chỉ tải bản một-file chất lượng thấp.")
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
    downloaded_formats = []
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
            title, format_info, files = download_video(v_url)
            add_to_history(v_url, title or "", files[0])
            downloaded.append(title)
            downloaded_formats.append(f"{title}: {format_info}")
            print(f"[FORMAT] {title}: {format_info}")
            print(f"[FILE] {files[0]}")
            set_status(f"Đã tải {idx}/{total}: {format_info}")
        except Exception as e:
            failed.append(f"{v_url}: {e}")
            print(f"[ERROR] {v_url}: {e}")
        progress_bar["value"] = idx

    msg = f"✅ Tải thành công: {len(downloaded)} video."
    if skipped:
        msg += f"\n⏭ Bỏ qua (đã tải): {len(skipped)} video."
    if failed:
        msg += f"\n❌ Lỗi: {len(failed)} video."
        msg += "\n\nLỗi đầu tiên:\n" + failed[0]
    if downloaded_formats:
        msg += "\n\nFormat đã tải:\n" + "\n".join(downloaded_formats[:5])
        if len(downloaded_formats) > 5:
            msg += f"\n... và {len(downloaded_formats) - 5} video khác"
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
    win.title(f"Lịch sử tải ({len(history)} video)")
    win.geometry("780x460")
    txt = tk.Text(win, wrap="word")
    lines = []
    for entry in history[-50:]:
        if isinstance(entry, dict):
            title = entry.get("title") or "(chưa có tên)"
            url   = entry.get("url", "")
            lines.append(f"{title}\n  {url}")
        else:
            lines.append(entry)
    txt.insert("1.0", "\n\n".join(lines))
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
        ok = has_cookie_file(f)
        lbl_status.config(
            text=("✅ File cookies: " + os.path.basename(f)) if ok else "❌ Chưa có file cookies hợp lệ — file rỗng không dùng được",
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
