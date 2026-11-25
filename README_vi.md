# Griductive

[English](README.md) | [Tiếng Việt](README_vi.md)

Trò chơi suy luận được xây dựng bằng Python và Pygame cho môn CSC14003 — Nhập môn
Trí tuệ nhân tạo. Tham khảo luật chơi [Griductive](https://knotwise.games/games/griductive),
dự án kết hợp cơ chế mở dần manh mối với bộ mã hóa CNF, bộ giải DPLL và tác tử logic.

## Tính năng

- 13 màn: bốn màn 3×3, bốn màn 4×4 và năm màn 5×5.
- Chơi thủ công, gợi ý và giải tự động dựa trên kết luận được chứng minh.
- Manh mối định danh, đếm, chẵn lẻ, so sánh, kéo theo và liên thông.
- Chân dung nhân vật, hoạt ảnh mở thẻ, cuộn manh mối mượt và chọn nhạc.
- Bảng Agent bên cạnh bàn cờ, xem lại trạng thái công khai và các truy vấn SAT.
- Chọn heuristic DPLL: mã biến nhỏ nhất hoặc Jeroslow–Wang động hai phía.
- Kiểm định không giao diện và xuất kết quả thực nghiệm CSV/JSON.

## Cài đặt

Dùng Python 3.11 trở lên và chạy lệnh tại thư mục gốc của dự án.

### Windows PowerShell

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe main.py
```

### Linux / macOS

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python main.py
```

Để phát triển, cài `requirements-dev.txt` thay cho `requirements.txt`.
Các lệnh bên dưới dùng Python của môi trường đã chọn; trên Windows có thể thay
`python` bằng `.\.venv\Scripts\python.exe`.

## Chạy trò chơi

```bash
python main.py
python main.py --puzzle data/puzzles/5x5/level_05.json
python main.py --analyzer griductive.agent.adapter:Agent
```

Mặc định trò chơi dùng bộ phân tích quay lui ngữ nghĩa `ReferenceAnalyzer`.
Lệnh cuối khởi chạy với tác tử CNF/DPLL; cũng có thể đổi trực tiếp trong bảng Agent.

### Điều khiển

| Thao tác | Cách dùng |
| --- | --- |
| Chọn nhân vật | Nhấp chuột, WASD hoặc phím mũi tên |
| Mở / xác nhận lựa chọn | Enter; hộp thoại mặc định chọn Innocent |
| Chọn trạng thái | Chuột hoặc phím điều hướng trong hộp thoại |
| Đóng hộp thoại | Escape |
| Đổi / chơi lại màn | Stage / Restart |
| Tìm bước có thể chứng minh | Hint |
| Giải dần / tạm dừng | Auto Solve / Stop |
| Hướng dẫn / âm nhạc | ? / Music |

Chỉ kết luận suy ra được từ thông tin công khai mới mở thẻ và công bố manh mối.
Trò chơi phân biệt chưa đủ căn cứ với kết luận bị bác bỏ. Nhấp vào thẻ đã mở
hoặc manh mối để làm nổi bật những ô được nhắc đến.

Chân dung được xáo trộn khi nạp màn và giữ nguyên khi Restart. Màn có
`fixed_cast: true` giữ dàn nhân vật để bảo toàn manh mối phụ thuộc xuất xứ.

## Bảng Agent

Nhấn **Agent** để mở bảng quan sát bên cạnh bàn cờ.

- **Use Reference / Use Logic Agent**: đổi bộ phân tích.
- **Heuristic**: chuyển `smallest` ↔ `jw` khi dùng Logic Agent.
- **Analyze**: phân loại bàn cờ hiện tại mà không mở thẻ.
- **Next move**: chứng minh và mở một thẻ.
- **Previous call / Next call**: xem bàn cờ công khai sau hành động đã ghi;
  **Live** trở lại trạng thái hiện tại. Việc xem lại không tua ngược engine.

Mỗi lượt logic ghi heuristic, kết quả phân loại, truy vấn SAT, kích thước CNF và
các bộ đếm hiện có. Chỉ số gồm số biến chính/phụ, mệnh đề, lần gọi SAT, quyết định,
lan truyền, quay lui, bước suy diễn, đợt mở thẻ và thời gian phân tích. Kích thước
CNF thuộc đầu vào của lượt phân tích; bàn cờ xem lại thuộc trạng thái sau hành động.

Đổi bộ phân tích hoặc heuristic giữ thẻ đã chứng minh nhưng xóa lịch sử và
bộ đếm tích lũy. Restart và đổi màn cũng đặt lại lịch sử. Heuristic được giữ
trong phiên chơi. Không thể đổi khi đang phân tích, Auto Solve hoặc xem lịch sử.
Reference không gọi SAT; bộ đếm chưa có hiển thị **N/A**, cơ chế dự phòng
được ghi rõ trên giao diện.

## Kiểm định và thực nghiệm

```bash
python -m pip install -r requirements-dev.txt
python -m pytest tests -q
python main.py --headless --analyzer griductive.agent.adapter:Agent
python -m griductive.check_analyzer --analyzer griductive.agent.adapter:Agent
python scripts/validate_levels.py
python -m griductive.experiments.benchmark --runs 3 --timeout 3 --output results
```

Benchmark sử dụng [manifest cố định](griductive/experiments/manifest.json),
bắt buộc chạy CNF/DPLL và dùng heuristic `smallest`. Kết quả được lưu tại
`results/benchmark.csv` và `results/benchmark.json`, bao gồm cả lỗi và quá thời gian.
`--timeout` giới hạn từng lần gọi SAT, không giới hạn toàn màn.
Dữ liệu sinh ra trong `results/` được bỏ qua bởi Git.

Nguồn LaTeX và script so sánh hai heuristic nằm trên
[branch report](https://github.com/bumbleboo021/griductive/tree/report).
Script `report/experiments/compare_heuristics.py` so sánh `smallest` với `jw`;
lệnh benchmark bên trên chỉ đo `smallest`.

## Cấu trúc dự án

```text
main.py                    Điểm khởi chạy
griductive/
  domain/                  Mô hình dữ liệu công khai bất biến
  engine/                  Nạp màn, luật mở thẻ và bộ phân tích tham chiếu
  logic/                   Mã hóa CNF
  sat/                     Bộ giải DPLL và các heuristic
  agent/                   Suy diễn, ghi vết và kiểm tra nghiệm duy nhất
  ui/                      Giao diện, điều khiển, bảng Agent và âm nhạc
  experiments/             Manifest và trình chạy thực nghiệm
data/puzzles/              Màn chơi JSON
assets/                    Ảnh, nền, phông chữ và âm thanh
tests/                     Kiểm thử đơn vị và tích hợp
scripts/                   Sinh màn và kiểm định ngữ nghĩa
docs/                      Tài liệu kỹ thuật và tùy chỉnh
results/                   Kết quả thực nghiệm cục bộ
```

Engine giữ đáp án ẩn và manh mối chưa mở. Bộ phân tích chỉ nhận
`PublicState` bất biến qua giao diện `analyze(PublicState) -> Analysis`.

## Tài liệu

- [Báo cáo dự án (PDF, tiếng Việt)](Report.pdf)
- [Nguồn LaTeX và thực nghiệm báo cáo](https://github.com/bumbleboo021/griductive/tree/report/report)
- [Danh sách màn chơi](docs/LEVELS_vi.md)
- [Tích hợp và hợp đồng dữ liệu](docs/INTEGRATION_vi.md)
- [Ghi chú DPLL](docs/DPLL_NOTES.md)
- [Thiết kế màn chơi](docs/LEVEL_DESIGN_vi.md)
- [Tùy chỉnh giao diện](docs/UI_CUSTOMIZATION_vi.md)
- [Danh sách công việc](TODO_vi.md)

Cấu hình giao diện, lời thoại và thời gian hoạt ảnh nằm ở `griductive/ui/config.py`.
Script sinh màn ghi đè các tệp JSON tương ứng; cần kiểm định lại sau khi sửa
manh mối hoặc thẻ mở ban đầu.

## Nguồn tài nguyên

Xem [ghi nhận nguồn](assets/ATTRIBUTION.md) và
[thông báo về hình ảnh](assets/images/NOTICE.txt).
Ảnh, phông chữ và âm thanh của bên thứ ba tuân theo điều khoản của chủ sở hữu;
ghi nguồn không thay thế quyền phân phối.
Việc sử dụng AI được ghi tại [appendix.md](appendix.md).
