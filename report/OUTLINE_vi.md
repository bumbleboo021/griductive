# Gợi ý nội dung chương 3–6

Đây là dàn ý để các thành viên viết tiếp theo phần đã cài đặt. Mỗi chương nên trình bày ý tưởng, cách cài đặt và một ví dụ minh họa; không cần liệt kê toàn bộ hàm hoặc đưa bảng kết quả kiểm thử vào báo cáo.

## Chương 3 — Biểu diễn tri thức và mã hóa CNF

**Người 2 — Lê Thanh Phi** · Tệp dự kiến: `chapter3.tex`

- **3.1. Biểu diễn bài toán:** biến Boolean cho từng ô, quy ước đúng là tội phạm; ánh xạ biến tất định và phân biệt biến chính với biến phụ.
- **3.2. Xây dựng cơ sở tri thức:** chỉ dùng manh mối công khai và trạng thái đã chứng minh; giải thích vùng hàng, cột và lân cận.
- **3.3. Mã hóa manh mối:** trình bày sáu mẫu cốt lõi và các mở rộng thực sự đã hỗ trợ. Dẫn xuất ít nhất một ví dụ hai ngôi (`SAME`/`DIFFERENT`) và một ví dụ đếm (`EXACTLY`).
- **3.4. Tổ chức encoder:** mô tả ngắn đầu vào `PublicState`, đầu ra CNF và cách thống kê biến/mệnh đề. Chú ý các ràng buộc đếm đã được loader chuẩn hóa về số tội phạm.

## Chương 4 — Bộ giải SAT bằng DPLL

**Người 3 — Vương Thành Phát** · Tệp dự kiến: `chapter4.tex`

- **4.1. Ý tưởng DPLL:** mục tiêu tìm một phép gán thỏa mãn hoặc kết luận không thỏa mãn.
- **4.2. Các bước xử lý:** lan truyền đơn vị, phát hiện xung đột, chọn biến tất định, rẽ nhánh và quay lui; kèm mã giả ngắn.
- **4.3. Ví dụ minh họa:** dùng một công thức CNF nhỏ để mô tả các bước lan truyền hoặc quay lui.
- **4.4. Giao diện bộ giải:** đầu vào CNF và giả định; đầu ra SAT kèm mô hình đầy đủ, UNSAT hoặc timeout. Nêu cách đếm quyết định, lan truyền, quay lui để chương 6 sử dụng.

## Chương 5 — Tác tử suy diễn logic

**Người 4 — Trần Đình Hưng** · Tệp dự kiến: `chapter5.tex`

- **5.1. Kiểm tra hệ quả logic:** kiểm tra KB nhất quán trước; giải thích `KB ∧ ¬Ci` UNSAT suy ra tội phạm, `KB ∧ Ci` UNSAT suy ra vô tội; cả hai SAT thì UNKNOWN.
- **5.2. Vòng suy diễn:** tạo KB → phân loại → chọn kết luận bắt buộc → gửi engine → nhận manh mối mới → lặp. Nêu điều kiện dừng khi giải xong, bế tắc, mâu thuẫn hoặc lỗi.
- **5.3. Vết suy diễn:** minh họa một vài bước gồm số bước, mã manh mối đang dùng, truy vấn SAT, kết luận và manh mối vừa mở.
- **5.4. Kiểm tra tính duy nhất:** thực hiện riêng trên tập manh mối đầy đủ; tìm mô hình thứ hai bằng cách chặn phép gán của các biến chính, không chặn theo biến phụ.
- **5.5. Tích hợp trò chơi:** mô tả ngắn adapter và giao diện `analyze(PublicState) -> Analysis`. Phân biệt solver DPLL thật với bộ phân tích tham chiếu dự phòng.

## Chương 6 — Thực nghiệm và đánh giá

**Người 5 — Nguyễn Quốc Thái** · Tệp dự kiến: `chapter6.tex`

- **6.1. Thiết lập thực nghiệm:** môi trường chạy, phiên bản mã nguồn, tập màn 3×3/4×4 và 5×5 nếu dùng làm trường hợp lớn; cố định dữ liệu và cấu hình so sánh.
- **6.2. Chỉ số đánh giá:** số biến chính/phụ, số mệnh đề, số lượt gọi SAT, quyết định, lan truyền, quay lui, số bước suy diễn và thời gian.
- **6.3. Kết quả và nhận xét:** chọn bảng/biểu đồ gọn từ số liệu đo thực tế; giải thích ảnh hưởng của kích thước lưới và loại manh mối. Ghi nhận cả lỗi và timeout.
- **6.4. Hạn chế và hướng phát triển:** nêu nút thắt quan sát được và đề xuất cải thiện phù hợp với kết quả.

Chương 6 trình bày số liệu thực nghiệm của hệ thống hoàn chỉnh; không cần đưa dữ liệu kiểm thử đơn vị/giao diện. Không điền số liệu giả hoặc dùng thời gian của bộ phân tích tham chiếu để kết luận hiệu năng DPLL.

## Ghép vào báo cáo

Sau khi các chương được viết xong, thêm các dòng sau ngay sau `\input{chapter2}` và trước `\insertbibliography` trong `main.tex`:

```tex
\input{chapter3}
\input{chapter4}
\input{chapter5}
\input{chapter6}
```

Mỗi người bổ sung nguồn đã sử dụng vào `biblio.bib` và trích dẫn bằng `\cite{...}`. Phần giới thiệu luật chơi đã có ở chương 2 nên các chương sau tập trung vào nhiệm vụ của mình.
