import os
import tkinter as tk
from tkinter import filedialog, messagebox


def main():
    root = tk.Tk()
    root.withdraw()

    folder = filedialog.askdirectory(title="Chọn thư mục cần lấy danh sách file")
    if not folder:
        return

    names = []
    for entry in os.scandir(folder):
        if entry.is_file():
            name_no_ext = os.path.splitext(entry.name)[0]
            names.append(name_no_ext)

    names.sort()

    output_path = os.path.join(folder, "file_list.txt")
    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(names))

    messagebox.showinfo(
        "Hoàn thành",
        f"Đã ghi {len(names)} tên file vào:\n{output_path}"
    )


if __name__ == "__main__":
    main()
