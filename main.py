import os
import tkinter as tk
from tkinter import messagebox
from yt_dlp import YoutubeDL

FFMPEG_DIR = os.path.join("ffmpeg", "bin")
OUTPUT_DIR = "output"
HISTORY_FILE = "history.txt"
os.makedirs(OUTPUT_DIR, exist_ok=True)

def save_to_history_txt(video_title, video_url):
    with open(HISTORY_FILE, "a", encoding="utf-8") as f:
        f.write(f"{video_title} | {video_url}\n")

def is_duplicate_download(video_url):
    if not os.path.exists(HISTORY_FILE):
        return False
    with open(HISTORY_FILE, "r", encoding="utf-8") as f:
        return any(video_url in line for line in f.readlines())

def get_video_urls(url):
    try:
        with YoutubeDL({'quiet': True}) as ydl:
            info = ydl.extract_info(url, download=False)
            if 'entries' in info:
                return [entry['webpage_url'] for entry in info['entries']]
            else:
                return [info['webpage_url']]
    except Exception as e:
        raise RuntimeError("Không lấy được danh sách video: " + str(e))

def download_best_video(url):
    try:
        ydl_opts = {
            'format': 'bestvideo+bestaudio/best',
            'outtmpl': os.path.join(OUTPUT_DIR, '%(title)s.%(ext)s'),
            'ffmpeg_location': FFMPEG_DIR,
            'merge_output_format': 'mp4'
        }

        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            title = info.get('title', 'video')
            ext = info.get('ext', 'mp4')
            save_to_history_txt(title, info.get('webpage_url', url))
            return f"{title}.{ext}"
    except Exception as e:
        raise RuntimeError("Lỗi tải video: " + str(e))

def start_download():
    url = url_entry.get().strip()
    if not url:
        messagebox.showerror("Lỗi", "Vui lòng nhập link YouTube")
        return

    status_label.config(text="Đang phân tích liên kết...")
    root.update()

    try:
        video_urls = get_video_urls(url)
        downloaded = []
        skipped = []
        for idx, v_url in enumerate(video_urls, start=1):
            status_label.config(text=f"Đang tải video {idx}/{len(video_urls)}...")
            root.update()
            if is_duplicate_download(v_url):
                skipped.append(v_url)
                continue
            filename = download_best_video(v_url)
            downloaded.append(filename)

        message = f"Tải thành công {len(downloaded)} video."
        if skipped:
            message += f"\nBỏ qua {len(skipped)} video đã tải trước đó."

        messagebox.showinfo("Hoàn tất", message)
        status_label.config(text="Hoàn tất!")
    except Exception as e:
        status_label.config(text="Đã xảy ra lỗi.")
        messagebox.showerror("Lỗi", str(e))

def view_download_history():
    if not os.path.exists(HISTORY_FILE):
        messagebox.showinfo("Lịch sử", "Chưa có video nào được tải.")
        return
    with open(HISTORY_FILE, "r", encoding="utf-8") as f:
        history = f.read()
    messagebox.showinfo("Lịch sử tải", history)

# GUI đơn giản
root = tk.Tk()
root.title("YouTube Best Quality Downloader")
root.geometry("520x220")

frame = tk.Frame(root)
frame.pack(pady=20)

tk.Label(frame, text="Nhập link video hoặc danh sách phát:").pack()
url_entry = tk.Entry(frame, width=60)
url_entry.pack(pady=5)

btn_download = tk.Button(frame, text="Tải video chất lượng tốt nhất", command=start_download)
btn_download.pack(pady=10)

btn_history = tk.Button(frame, text="Xem lịch sử đã tải", command=view_download_history)
btn_history.pack()

status_label = tk.Label(root, text="")
status_label.pack(pady=5)

root.mainloop()
