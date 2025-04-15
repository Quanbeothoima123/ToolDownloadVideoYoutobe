# 🎬 YouTube Best Quality Downloader

Một công cụ có giao diện đơn giản để tải video chất lượng cao từ **YouTube**, hỗ trợ cả video riêng lẻ lẫn danh sách phát (playlist). Công cụ còn tự động tránh tải trùng và lưu lịch sử tải xuống để dễ dàng kiểm tra.

## 📁 Cấu trúc thư mục

```
youtube_best_downloader/
│
├── ffmpeg/
│   └── bin/
│       └── ffmpeg.exe       ← FFmpeg bản local (bắt buộc)
├── output/                  ← Nơi chứa các video sau khi tải
├── history.json             ← Tự động tạo để lưu lịch sử video đã tải
├── main.py                  ← File chính để chạy chương trình
└── README.md                ← File hướng dẫn này
```

---

## ⚙️ Yêu cầu

- Python 3.7+
- Các thư viện Python:
  - `yt_dlp`
  - `tkinter` (mặc định có sẵn trên Windows)

---

## 🧩 Cài đặt

### Bước 1: Cài Python và pip

Tải và cài Python từ: https://www.python.org/downloads/

Nhớ tích chọn **Add Python to PATH** khi cài.

---

### Bước 2: Cài thư viện cần thiết

Mở CMD tại thư mục chứa `main.py` và chạy:

```bash
pip install yt-dlp
```

---

### Bước 3: Chuẩn bị FFmpeg

1. Tải bản FFmpeg cho Windows tại: https://www.gyan.dev/ffmpeg/builds/
2. Giải nén, sao chép file `ffmpeg.exe` vào:

```
youtube_best_downloader/ffmpeg/bin/ffmpeg.exe
```

> ⚠️ Không cần thêm vào PATH – chương trình đã tự nhận FFmpeg local.

---

## 🚀 Cách sử dụng

1. Mở file `main.py` (click đúp hoặc chạy `python main.py` từ CMD).
2. Giao diện hiện ra:

   - Dán link **video YouTube** hoặc **playlist**.
   - Nhấn nút **"Tải video chất lượng cao"**.
   - Quá trình tải sẽ hiển thị bên dưới.
   - Video sau khi tải sẽ nằm trong thư mục `output/`.

3. Để xem lịch sử các video đã tải:
   - Nhấn nút **"Xem lịch sử đã tải"**.

---

## 🧠 Tính năng nổi bật

✅ Hỗ trợ tải video chất lượng cao nhất (có cả audio/video merge bằng FFmpeg)  
✅ Tải từ link video lẻ hoặc danh sách phát YouTube  
✅ Lưu lịch sử tải vào `history.txt`  
✅ Tự động **bỏ qua video đã tải** trước đó (dựa vào ID video)  
✅ Giao diện dễ dùng với thông báo tiến trình rõ ràng

---

## 📌 Lưu ý

- Tool chỉ hỗ trợ tải **video công khai** trên YouTube.
- Đảm bảo kết nối internet ổn định để tránh lỗi khi tải danh sách dài.
- Nếu gặp lỗi không có FFmpeg, hãy kiểm tra lại file `ffmpeg.exe` trong `ffmpeg/bin`.

---

## 🧑‍💻 Tác giả

Tool được xây dựng bằng Python, sử dụng `yt_dlp` và `tkinter`.  
Được phát triển để phục vụ nhu cầu cá nhân tải video chất lượng cao mà không cần thao tác dòng lệnh.

---

## ❤️ Nếu bạn thấy tool hữu ích...

Hãy chia sẻ cho bạn bè hoặc góp ý để công cụ ngày càng tốt hơn!
