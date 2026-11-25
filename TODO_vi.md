# Danh sách công việc

[English](TODO.md) | [Tiếng Việt](TODO_vi.md)

Các chức năng đã triển khai và những việc cần rà soát tiếp. Hướng dẫn cài đặt,
sử dụng nằm ở [README_vi.md](README_vi.md). Nguồn báo cáo được lưu trên
[branch report](https://github.com/bumbleboo021/griductive/tree/report).

## Đã triển khai

- [x] Nạp và kiểm tra JSON, mô hình trạng thái công khai bất biến.
- [x] Giữ kín đáp án, kiểm tra kết luận và mở dần manh mối.
- [x] Phân biệt chưa đủ căn cứ với kết luận bị bác bỏ.
- [x] Giao diện Pygame, bàn phím, chọn màn, Restart, Hint và Auto Solve.
- [x] Chân dung, nền, phông chữ, chọn nhạc và hoạt ảnh tương tác.
- [x] Cuộn manh mối mượt và làm nổi bật ô liên quan.
- [x] Mười ba màn với các kích thước 3×3, 4×4 và 5×5.
- [x] Mã hóa CNF cho manh mối cơ bản, chẵn lẻ, so sánh, kéo theo và liên thông.
- [x] Cấp phát biến chính/phụ tất định và thống kê CNF.
- [x] DPLL tự cài đặt, lan truyền đơn vị, quay lui, giả định và giới hạn thời gian.
- [x] Heuristic mã biến nhỏ nhất và Jeroslow–Wang động hai phía.
- [x] Tác tử dùng dữ liệu công khai, ghi vết và kiểm tra nghiệm duy nhất với đủ manh mối.
- [x] Bảng Agent bên cạnh bàn cờ, xem lại, truy vấn SAT thực và bộ đếm tích lũy.
- [x] Đổi heuristic trong game, giữ thẻ đã mở và đặt lại lịch sử.
- [x] Kiểm định ngữ nghĩa, kiểm tra bộ giải và kiểm thử giao diện không màn hình.
- [x] Manifest cố định và benchmark CNF/DPLL không giao diện, xuất CSV/JSON.
- [x] Script so sánh hai heuristic, bảng và biểu đồ trên branch report.
- [x] Các chương báo cáo, tài liệu tham khảo, phụ lục và hình Agent mới.
- [x] Đưa PDF báo cáo vào repo và liên kết từ README.

## Rà soát và bàn giao

- [ ] Lưu và bàn giao CSV/JSON gốc dùng cho các bảng báo cáo, kèm môi trường,
  phiên bản mã nguồn, số lần chạy và giới hạn thời gian.
- [ ] Kiểm tra có thể tái lập kết quả thực nghiệm từ một bản checkout sạch.
- [ ] Rà PDF cuối, dẫn chiếu, hình ảnh và các tệp cần nộp.
- [ ] Quay video minh họa theo yêu cầu và kiểm tra liên kết chia sẻ trong báo cáo.
- [ ] Rà quyền phân phối tài nguyên và giữ các thông báo giấy phép cần thiết.
- [ ] Kiểm tra co giãn giao diện, bàn phím và âm thanh trên máy sử dụng thực tế.

Các mục này cần xác nhận riêng; việc đã có mã triển khai chưa xác nhận rằng
dữ liệu gốc, video và gói nộp bài đã được bàn giao.

## Cải tiến tiếp theo

- [ ] Đồng bộ `Agent.run_trace()` với vòng đời mở thẻ của engine để tránh gọi thêm
  một lượt phân tích chưa được ghi vào vết khi chấp nhận nước đi.
- [ ] Rà điều kiện dừng và xử lý lỗi của vết với lựa chọn bị từ chối, màn đã giải
  và trường hợp quá thời gian.
- [ ] Cân nhắc thêm lựa chọn cả hai heuristic vào CLI benchmark chính,
  thay vì chỉ dùng script so sánh riêng của báo cáo.
- [ ] Bổ sung độ phân tán thời gian chạy, chẳng hạn IQR, bên cạnh trung vị.
- [ ] Rà các hướng dẫn kỹ thuật cũ còn nội dung chia việc hoặc bàn giao lỗi thời.
