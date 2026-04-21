# 🎬 YouTube Best Quality Downloader

Công cụ tải video **YouTube** chất lượng cao nhất với giao diện đơn giản. Hỗ trợ video đơn lẻ lẫn playlist, tự động bỏ qua video đã tải, có nút dừng giữa chừng và progress bar theo dõi tiến trình.

---

## ✨ Tính năng

- ⬇️ Tải video chất lượng cao nhất (video + audio merge qua FFmpeg → `.mp4`)
- 📋 Hỗ trợ cả **link video đơn** lẫn **playlist**
- ⏹ Nút **Dừng** để cancel bất kỳ lúc nào
- 📊 **Progress bar** hiển thị tiến trình theo thời gian thực
- ✅ Tự động **bỏ qua video đã tải** trước đó (lưu lịch sử bằng JSON)
- 📋 Xem **lịch sử tải** trong cửa sổ riêng, có thể cuộn
- 📁 Nút **Mở thư mục** output ngay sau khi tải xong
- 🖥️ Giao diện không bị đứng (download chạy trên thread riêng)

---

## 📁 Cấu trúc thư mục

```
ToolDownloadVideoYoutube/
├── ffmpeg/
│   └── bin/
│       └── ffmpeg.exe        ← Bắt buộc phải có
├── output/                   ← Video tải về sẽ nằm ở đây
├── history.json              ← Lịch sử tải (tự động tạo)
├── main.py                   ← File chính để chạy
├── requirements.txt
└── README.md
```

---

## 🛠️ Cài đặt

### 1. Yêu cầu hệ thống

- **Python 3.8+** — tải tại [python.org](https://www.python.org/downloads/)
  > ⚠️ Khi cài nhớ tích **"Add Python to PATH"**
- **Windows** (khuyến nghị)

---

### 2. Cài thư viện

Mở terminal tại thư mục dự án:

```bash
pip install -r requirements.txt
```

---

### 3. Chuẩn bị FFmpeg

1. Tải FFmpeg tại: [gyan.dev/ffmpeg/builds](https://www.gyan.dev/ffmpeg/builds/)
2. Giải nén, copy file `ffmpeg.exe` vào thư mục:

```
ffmpeg/bin/ffmpeg.exe
```

> Không cần cài FFmpeg vào PATH — chương trình tự nhận local.

---

## ▶️ Cách sử dụng

```bash
python main.py
```

**Các bước thực hiện:**

1. Dán link **video** hoặc **playlist** YouTube vào ô nhập
2. Nhấn **⬇ Tải video**
3. Theo dõi tiến trình qua progress bar và status bên dưới
4. Nhấn **📁 Mở thư mục** để xem video vừa tải
5. Nhấn **⏹ Dừng** nếu muốn cancel giữa chừng

---

## 🖼️ Giao diện

| Nút | Chức năng |
|---|---|
| ⬇ Tải video | Bắt đầu tải, UI không bị đứng |
| ⏹ Dừng | Dừng quá trình tải ngay lập tức |
| 📋 Lịch sử | Xem danh sách URL đã tải |
| 📁 Mở thư mục | Mở thư mục `output/` trong Explorer |

---

## ⚠️ Lưu ý

- Chỉ tải được **video công khai** trên YouTube.
- Video sau khi tải nằm trong thư mục `output/`, định dạng `.mp4`.
- Lịch sử tải lưu tại `history.json` — xóa file này để reset lịch sử.
- Cần kết nối internet ổn định, đặc biệt khi tải playlist dài.
- Nếu gặp lỗi FFmpeg, kiểm tra lại `ffmpeg/bin/ffmpeg.exe` có tồn tại chưa.

---

## 📜 License

Quenbeothoima License © 2025
