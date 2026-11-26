# Thực nghiệm trên 13 màn Griductive

Agent giải trọn 39/39 lượt. Trên lượt kiểm định độc lập của mỗi màn, Agent và ReferenceAnalyzer đồng ý về mọi ô chưa mở ở cả 205 trạng thái trước khi lật. Cả 13 màn có mọi clue đúng với đáp án JSON và có nghiệm duy nhất khớp đáp án khi sử dụng đầy đủ clue.

## Thiết lập

Chạy `python -m griductive.experiments.benchmark` tại thư mục gốc. Manifest v1 cố định đường dẫn, kích thước, seed và SHA-256 của JSON sau chuẩn hóa xuống dòng LF. Mỗi lượt dùng Agent và engine mới, nạp dàn nhân vật từ JSON. Quy tắc nhóm xuất xứ trong màn fixed_cast dùng đúng danh sách đã lưu. DPLL chọn biến bằng `smallest`. Giới hạn 3 giây cho từng truy vấn SAT, 3 giây cho mỗi lần phân tích tham chiếu. Môi trường đo là Python 3.12.14, Linux-6.18.57-x86_64-with-glibc2.41.

Mỗi màn chạy ba lần. Thời gian trong bảng là trung vị ba lượt. Đồng hồ bắt đầu sau khi nạp màn và khởi tạo engine, bao gồm encode, suy luận, lật thẻ và ghi số đo trong bộ nhớ. Solver ms cộng thời gian do DPLL trả về trong từng lượt rồi lấy trung vị. Kiểm tra clue, uniqueness và so sánh với bộ tham chiếu chạy trước vòng đo. Mỗi bước đo gọi đúng một lần `engine.step()`.

## Kết quả từng màn

Biến phụ và clauses lấy mức lớn nhất trên các KB công khai đã được mã hóa. Biến chính tương ứng số ô. Các bộ đếm dưới đây tính trên một lượt giải và giống nhau giữa ba lần lặp.

| Màn | Biến chính | Biến phụ peak | Clauses peak | SAT calls | Decisions | Propagations | Backtracks | Bước lật | Solver ms | Toàn lượt ms |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 3x3/01 | 9 | 11 | 40 | 74 | 0 | 573 | 0 | 8 | 0.98 | 1.57 |
| 3x3/02 | 9 | 28 | 76 | 71 | 0 | 1365 | 0 | 8 | 2.46 | 3.04 |
| 3x3/03 | 9 | 70 | 169 | 56 | 5 | 1392 | 0 | 7 | 3.95 | 4.59 |
| 3x3/04 | 9 | 86 | 199 | 57 | 6 | 2495 | 0 | 7 | 9.32 | 10.05 |
| 4x4/01 | 16 | 52 | 140 | 246 | 0 | 4158 | 0 | 15 | 8.49 | 10.57 |
| 4x4/02 | 16 | 40 | 130 | 244 | 90 | 3660 | 0 | 15 | 9.54 | 11.68 |
| 4x4/03 | 16 | 164 | 385 | 206 | 226 | 8141 | 0 | 14 | 41.97 | 44.53 |
| 4x4/04 | 16 | 172 | 397 | 212 | 230 | 7333 | 0 | 14 | 27.45 | 29.81 |
| 5x5/01 | 25 | 199 | 463 | 594 | 121 | 26080 | 0 | 24 | 77.05 | 82.66 |
| 5x5/02 | 25 | 80 | 231 | 591 | 675 | 23215 | 0 | 24 | 101.30 | 107.15 |
| 5x5/03 | 25 | 284 | 648 | 551 | 1783 | 26078 | 0 | 23 | 170.19 | 177.11 |
| 5x5/04 | 25 | 305 | 688 | 551 | 1552 | 35484 | 0 | 23 | 231.68 | 240.12 |
| 5x5/05 | 25 | 110 | 304 | 541 | 1033 | 26008 | 0 | 23 | 132.51 | 141.00 |

## Nhận xét và giới hạn

- Màn 3×3/01 cần 74 truy vấn cho 8 lần lật nhưng có 0 decisions. Clue mở đầu xác định cả hàng, và unit propagation đủ cho các truy vấn của màn này.
- 5×5/03 và 5×5/04 đều cần 551 truy vấn, trong khi số quyết định lần lượt là 1.783 và 1.552. Số lần hỏi SAT riêng lẻ chưa mô tả hết công việc trong mỗi truy vấn.
- Tất cả lượt đo có 0 backtracks theo định nghĩa của solver (số lần chuyển sang nhánh thứ hai). Một truy vấn UNSAT vẫn có thể kết thúc ngay khi unit propagation phát hiện xung đột.
- Về thiết kế, ở 3×3/01 người chơi có thể suy ra hai ô ngay từ một clue. Các màn mở rộng yêu cầu theo dõi thêm quan hệ giữa vùng hoặc trạng thái. Độ khó đối với người chơi cần được xác nhận bằng dữ liệu chơi thử. Runtime ở đây phụ thuộc máy và chỉ bao phủ 13 màn của nhóm.
- Bộ màn chính không phát sinh timeout hay bế tắc. Test riêng dùng giới hạn bằng 0 để ép timeout và bỏ toàn bộ thẻ mở sẵn để tạo bế tắc. Runner lưu trạng thái, lý do và số đo đến lúc dừng cho các lượt gặp lỗi.
- CSV ghi một dòng mỗi lượt cùng mean/max theo SAT call. JSON lưu thống kê từng truy vấn theo bước, thứ tự CNF là biến chính, biến phụ, clauses. Khi solver phát sinh exception, số lần gọi đã bắt đầu có thể lớn hơn số SatResult nhận được.

Biểu đồ được dựng từ CSV bằng `python -m griductive.experiments.plot_runtime` sau khi cài matplotlib.

![Trung vị thời gian giải theo màn](../../results/runtime_by_stage.png)
