# Đóng gói Luna thành file cài đặt Luna_Setup.exe

Mục tiêu: người dùng thường chỉ cần **tải 1 file, bấm Next → Next → Finish** như
cài app Windows, thay vì gõ lệnh.

## Nói thẳng về giới hạn (quan trọng)

File `.exe` giúp phần **chép mã nguồn + tạo shortcut** trở nên dễ như cài app. Nhưng
nó **không thể** bỏ qua 3 thứ mang tính bản chất của một ứng dụng AI:

1. **Máy phải có GPU NVIDIA** (khuyến nghị RTX 3060 12GB). Không có GPU thì Luna chạy
   được nhưng chậm tới mức không dùng nổi. Không installer nào "chế" ra GPU được.
2. **Phải tải ~10GB** lúc cài (PyTorch, model nền Qwen 8GB, giọng viXTTS 1.9GB) và
   **train ~10–20 phút**. Đây là lần cài đầu; các lần sau mở là chạy ngay.
3. **Cần Python 3.11.** Bộ cài sẽ cảnh báo nếu thiếu và chỉ chỗ tải.

Vì vậy kiến trúc là: **`.exe` chép file + `install.bat` lo phần nặng.** Đây là cách
làm chuẩn cho mọi app ML trên Windows (kể cả các app lớn) — không có "phép màu" nào khác.

## Cách build (một lần, trên máy của anh)

1. Tải **Inno Setup**: https://jrsoftware.org/isdl.php (miễn phí)
2. Cài xong, mở file `installer\luna_setup.iss` bằng **Inno Setup Compiler**
3. Bấm **Build → Compile** (hoặc Ctrl+F9)
4. Ra file: `installer\Output\Luna_Setup.exe`

Xong. Đưa `Luna_Setup.exe` này cho ai cũng cài được.

## Người dùng cuối làm gì

1. Cài **Python 3.11** một lần (bộ cài sẽ nhắc nếu thiếu) — tick "Add Python to PATH".
2. Bấm đúp **`Luna_Setup.exe`** → Next → chọn thư mục → Finish.
3. Ở màn hình cuối, để nguyên tick **"Cài đặt thư viện và model"** → cửa sổ đen hiện
   ra tự tải + train (~15–40 phút). Đây là bước lâu nhất, chỉ chạy 1 lần.
4. Xong. Vào Start Menu bấm **Luna** (chạy ẩn, hiện orb) hoặc **Luna (giọng nói)**.

## Bên trong bộ cài làm gì

- `[Files]`: chép mã nguồn vào `Documents\Luna`, **loại trừ** `.venv`, `checkpoints`,
  `voices`, `data\memory`, `data\knowledge` (dữ liệu nặng/riêng tư — không đóng gói).
- `[Icons]`: tạo shortcut Start Menu: Luna, Luna (giọng nói), Dừng Luna, Gỡ cài.
- `[Run]`: chạy `install.bat` sau khi chép (tải model + train).
- `[Code]`: kiểm tra Python 3.11, cảnh báo nếu thiếu.
- `[UninstallDelete]`: gỡ cài thì xoá luôn `.venv`, `checkpoints`, `voices`.

## Nếu muốn gọn hơn nữa (về sau)

- **Bundle sẵn Python**: Inno có thể kèm bộ cài Python 3.11 và tự chạy, bỏ được bước 1.
- **Bản Luna Lite**: dùng model nhỏ + giọng piper (nhẹ), tải ~2GB thay vì 10GB, hợp
  máy yếu. Đây là nhánh riêng mình đã bàn.
- **Phát hành qua GitHub Releases**: tải `luna_setup.iss` build ra .exe, kéo vào mục
  Releases của repo để người khác tải trực tiếp.
