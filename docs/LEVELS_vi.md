🌐 **Ngôn ngữ:** [English](LEVELS.md) | [Tiếng Việt](LEVELS_vi.md)

# Danh mục màn chơi

Trò chơi bao gồm 13 màn chơi gốc. Bảy màn chơi đã được thêm vào trong bản cập nhật này và ba màn chơi hướng dẫn đã bị loại bỏ khỏi bộ sưu tập có thể chơi được. Các dữ liệu kiểm thử mẫu (fixture) phục vụ chuỗi phát triển nằm trong thư mục `tests/fixtures/`. Ứng dụng bắt đầu tại màn chơi 01 kích thước 3x3.

| Bàn cờ | Tệp | Tên màn chơi | Được lật sẵn từ đầu | Nước đi chứng minh được | Thẻ lời nhận xét |
| --- | --- | --- | --- | --- | --- |
| 3x3 | `data/puzzles/3x3/level_01.json` | 3x3 - Quiet Rows | A1 | 8 | 4 |
| 3x3 | `data/puzzles/3x3/level_02.json` | 3x3 - Crossed Testimonies | A1 | 8 | 3 |
| 3x3 | `data/puzzles/3x3/level_03.json` | 3x3 - Lantern Bridge | A1, C1 | 7 | 3 |
| 3x3 | `data/puzzles/3x3/level_04.json` | 3x3 - Shared Alibis | A1, C1 | 7 | 2 |
| 4x4 | `data/puzzles/4x4/level_01.json` | 4x4 - Quiet Rows | A1 | 15 | 8 |
| 4x4 | `data/puzzles/4x4/level_02.json` | 4x4 - Crossed Testimonies | A1 | 15 | 6 |
| 4x4 | `data/puzzles/4x4/level_03.json` | 4x4 - The Silent Courtyard | A1, D1 | 14 | 4 |
| 4x4 | `data/puzzles/4x4/level_04.json` | 4x4 - Crossing Paths | A1, D1 | 14 | 5 |
| 5x5 | `data/puzzles/5x5/level_01.json` | 5x5 - Quiet Rows | A1 | 24 | 14 |
| 5x5 | `data/puzzles/5x5/level_02.json` | 5x5 - Crossed Testimonies | A1 | 24 | 9 |
| 5x5 | `data/puzzles/5x5/level_03.json` | 5x5 - Threads of Evidence | A1, E1 | 23 | 10 |
| 5x5 | `data/puzzles/5x5/level_04.json` | 5x5 - The Boundary Case | A1, E1 | 23 | 10 |
| 5x5 | `data/puzzles/5x5/level_05.json` | 5x5 - Teyvat Conspiracy | A1, E1 | 23 | 7 |

## Độ bao phủ manh mối

Các màn chơi từ 03 trở lên giới thiệu tính liên thông trực giao (4 hướng) (orthogonal connectivity), các quan hệ đồng nhất không gian trực tiếp, so sánh số lượng, các mệnh đề điều kiện (conditional), tính chẵn lẻ (parity) của các ô lân cận chung và hạn mức theo vùng. Bộ sưu tập này bao gồm các loại manh mối `FACT`, `SAME`, `DIFFERENT`, `EXACTLY`, `AT_LEAST`, `AT_MOST`, `ODD`, `EVEN`, `COUNT_COMPARE`, `CONNECTED` và `IMPLIES`. Các loại vùng bao gồm hàng, cột, ô lân cận, ô lân cận chung, vùng giao nhau, các hướng liền kề, biên và toàn bộ lưới. Bộ nạp dữ liệu (loader) cũng hỗ trợ các góc và nhóm cố định (có tên).

Màn chơi 5x5 Teyvat Conspiracy bao gồm một phép đếm số lượng nhân vật đến từ Liyue. Màn chơi đó sử dụng `fixed_cast: true` để bảo toàn tư cách thành viên nhóm xuất xứ. Các màn chơi khác duy trì việc phân vai ảnh chân dung ngẫu nhiên cho dàn nhân vật. Tính liên thông bỏ qua các đường chéo. Các nhóm trạng thái đích ở dạng rỗng hoặc đơn phần tử (singleton) đều thỏa mãn `CONNECTED`. Một phép đếm bổ sung có thể khẳng định sự tồn tại.

Các manh mối có thể loại bỏ một cách an toàn sẽ trở thành các lời nhận xét `QUOTE` có thể cấu hình được. Bước cắt tỉa (pruning) xác minh tính duy nhất và khả năng giải tiến dần sau mỗi lần loại bỏ. Độ khó chưa được hiệu chỉnh thông qua quá trình chơi thử nghiệm bởi người thật.

## Chơi và xác minh

Chọn `Stage` (màn chơi) trong trò chơi hoặc khởi chạy trực tiếp một tệp.

```powershell
.\.venv-win\Scripts\python.exe main.py --puzzle data/puzzles/5x5/level_05.json
.\.venv-win\Scripts\python.exe scripts/validate_levels.py --output docs/level_validation.json
```

Quá trình xác thực kiểm tra mọi manh mối đối chiếu với lời giải của nó, tìm kiếm độc lập một mô hình đầy đủ (complete model) thứ hai và vận hành thử vòng lặp lật (mở) công khai. Báo cáo JSON bao gồm các `ID` (mã định danh) của manh mối đang kích hoạt và chuỗi kết luận / lượt lật được chấp nhận. Báo cáo này chứa nội dung tiết lộ trước lời giải. Trò chơi không bao giờ đọc báo cáo đó.

## Xây dựng lại các màn chơi

Các lệnh này sẽ ghi đè lên các tệp màn chơi đã sinh bằng các phiên bản có thể tái tạo của chúng.

```powershell
.\.venv-win\Scripts\python.exe scripts/build_levels.py
.\.venv-win\Scripts\python.exe scripts/build_extended_levels.py
.\.venv-win\Scripts\python.exe scripts/validate_levels.py --output docs/level_validation.json
```

Tập lệnh (script) đầu tiên xây dựng lại các màn chơi 01-02. Tập lệnh thứ hai xây dựng lại các màn chơi 03-04 cho lưới 3x3 và 4x4, và các màn chơi 03-05 cho lưới 5x5. Mỗi tập lệnh đều áp dụng bước cắt tỉa manh mối dư thừa (redundant clue). Bộ phân tích phát triển (tạm thời) (development analyzer) lúc chạy sử dụng thuật toán quay lui ngữ nghĩa (semantic backtracking). Các thành viên trong nhóm cần mở rộng bộ mã hóa `CNF` (dạng chuẩn hội) / `DPLL` của mình để hỗ trợ các trường manh mối công khai mới trước khi kết nối tác tử (agent) được đánh giá của họ với các màn chơi này.