# Bàn giao nhóm Griductive và các công việc còn lại

Danh sách kiểm tra này phản ánh hiện trạng kho mã nguồn. Hãy thay Thành viên 1–5 bằng họ tên và MSSV. Các mục đã đánh dấu mô tả phần công việc đã triển khai. Các mục chưa đánh dấu mô tả phần triển khai còn lại hoặc cần cả nhóm rà soát. Ghi nhận riêng mức độ đóng góp thực tế khi chuẩn bị báo cáo.

Các yêu cầu được nêu trong [AI - Project 2.pdf](AI%20-%20Project%202.pdf), các mục 4.1–4.7.
Sử dụng [README.md](README.md) để cài đặt, chạy và kiểm tra dự án.

## Phân công phụ trách hiện tại

| Người phụ trách | Hạng mục phụ trách | Phần hiện có để tái sử dụng | Sản phẩm bàn giao tiếp theo |
| --- | --- | --- | --- |
| Thành viên 1 | 4.1 Trò chơi và `GUI` (giao diện đồ họa), 10 điểm | Engine, `UI` (giao diện người dùng) Pygame, tài nguyên, ranh giới trạng thái công khai (public state), bộ chọn màn chơi, các nút điều khiển và hoạt ảnh | Rà soát bước tích hợp tác tử (agent) hoàn chỉnh và quay video minh họa `GUI` |
| Thành viên 2 | 4.2 Biểu diễn tri thức và `CNF` (dạng chuẩn hội), 10 điểm | Các mô hình dữ liệu bất biến `Clue`/`PublicState`, bộ nạp dữ liệu, các vùng và ví dụ ngữ nghĩa | Bộ mã hóa (encoder) tự động bao phủ đầy đủ các manh mối cốt lõi và mở rộng |
| Thành viên 3 | 4.3 `DPLL`, 10 điểm | Giao ước tích hợp công khai và các oracle (bộ kiểm chứng chuẩn) ngữ nghĩa để đối chiếu | Bộ giải `DPLL` tự xây dựng hỗ trợ mô hình đầy đủ (complete model), giả định (assumption) và các chỉ số đo lường |
| Thành viên 4 | 4.4 Tác tử suy diễn, 20 điểm | Vòng đời `GameEngine`, giao thức `Analyzer` và `CLI` (giao diện dòng lệnh) dạng plugin | Bộ chuyển đổi dùng `DPLL`, vết suy diễn (deduction trace) và `API` (giao diện lập trình ứng dụng) kiểm tra tính duy nhất |
| Thành viên 5 | 4.5 Thực nghiệm, 10 điểm | Mười ba màn chơi đã kiểm định, các kiểm thử phản chứng (negative test), bộ kiểm định ngoại tuyến và các vết suy diễn | Trình chạy đánh giá hiệu năng (benchmark) có thể tái lập và các bảng số liệu báo cáo |

Các thư mục `logic/`, `sat/`, `agent/` và `experiments/` bên dưới `griductive/` hiện mới chỉ chứa các tệp khung gói. Trò chơi mặc định đang sử dụng `engine/reference.py` và `engine/advanced_clues.py` để thực hiện quay lui ngữ nghĩa (semantic backtracking). Luồng xử lý `CNF`/`DPLL` được chấm điểm cùng các phép đo của nó vẫn cần được triển khai.

## Bắt đầu tại đây

- [ ] Tất cả thành viên chạy các bước cài đặt và bốn câu lệnh cơ sở trong `README.md`.
- [ ] Đọc `domain/models.py`, `engine/puzzle.py` và `engine/game.py` trước khi thay đổi các giao diện. Rà soát [docs/INTEGRATION.md](docs/INTEGRATION.md).
- [ ] Thành viên 2–4 thống nhất các kiểu dữ liệu `CNF` và kết quả `SAT` nội bộ, cách xử lý giả định, số lượng biến đã khai báo (declared variable), các trường chỉ số đo lường và cách biểu diễn quá thời gian (`timeout`).
- [ ] Thành viên 2–4 triển khai sáu mẫu manh mối cốt lõi và cách xử lý `QUOTE` trước, kết nối bộ chuyển đổi và vượt qua bộ kiểm tra trạng thái công khai hiện có.
- [ ] Bổ sung hỗ trợ tính chẵn lẻ (parity), phép so sánh, tính liên thông (connectivity) và phép kéo theo (implication), sau đó chạy bộ chuyển đổi trên toàn bộ các màn chơi. Từ màn chơi 03 trở lên sẽ kiểm tra các mẫu manh mối phong phú hơn.
- [ ] Thành viên 5 lựa chọn và chốt cố định bảng kê (manifest) thực nghiệm kèm đường dẫn màn chơi và hạt giống ngẫu nhiên (seed).
- [ ] Tất cả thành viên cập nhật danh sách kiểm tra này khi các sản phẩm bàn giao được rà soát.

Các `API` nội bộ được đề xuất là `encode(public_state) -> CNF` và `solve(cnf, assumptions=()) -> SatResult`. Thành viên 2–4 cần cùng nhau chốt các trường dữ liệu trả về cụ thể. Ranh giới giao tiếp bên ngoài đã triển khai là `analyze(PublicState) -> Analysis` và phải duy trì tính tương thích với `GameEngine`.

## Thành viên 1 - Trò chơi và giao diện

### Đã triển khai

- [x] Lưu trữ câu đố riêng tư, nạp cấu trúc màn chơi, các ô được lật sẵn từ đầu (initially revealed) và nút `Restart` (chơi lại).
- [x] Các ảnh chụp trạng thái (snapshot) công khai bất biến chứa các manh mối đã lật và các trạng thái đã chứng minh được.
- [x] Cửa sổ bật lên chọn `Criminal` (tội phạm) / `Innocent` (vô tội) trên các thẻ chưa xác định và các thông báo bác bỏ riêng biệt.
- [x] Các kết luận được chấp nhận sẽ lật mở dần các thẻ cùng manh mối của chúng.
- [x] Bộ chọn màn chơi sử dụng trường `name` trong JSON, kèm khả năng tương thích ngược với trường `title` cũ.
- [x] Các nút `Hint` (gợi ý), `Auto Solve` (tự động giải), `Stop` (dừng), bảng trợ giúp, nút bật/tắt nhạc và bộ chọn bản nhạc.
- [x] Hình nền, phông chữ cục bộ, căn chỉnh ảnh chân dung, nhãn xuất xứ và dàn nhân vật ngẫu nhiên.
- [x] Phản hồi khi di chuột/chọn thẻ, tô sáng nước đi tự động và hoạt ảnh lật thẻ.
- [x] Bảng manh mối có viền với thanh cuộn mượt mà và tính năng tô sáng các ô được tham chiếu.
- [x] Các bài kiểm thử engine và `UI` ngoại màn hình, bao gồm việc giữ nguyên trạng thái sau các lựa chọn bị bác bỏ.
- [x] Tài liệu hướng dẫn tích hợp, hướng dẫn `UI` và phụ lục về việc sử dụng AI hỗ trợ.

### Công việc còn lại

- [ ] Rà soát các phán đoán thủ công, `Hint`, `Auto Solve`, `Restart` và thao tác chuyển màn chơi cùng bộ chuyển đổi hoàn chỉnh của Thành viên 4, bao gồm cả hành vi xử lý lỗi và quá thời gian.
- [ ] Kiểm tra hiển thị đồ họa và âm thanh trên máy tính thực tế của các thành viên trong nhóm.
- [ ] Rà soát nội dung manh mối rút gọn trên thẻ đối chiếu với văn bản đầy đủ ở bảng bên cạnh cho các màn chơi hoàn chỉnh.
- [ ] Hoàn thiện ghi nhận nguồn gốc tài nguyên và hồ sơ giấy phép/quyền sử dụng đi kèm.
- [ ] Chuẩn bị phần minh họa `GUI` cho buổi trình bày cuối cùng sau khi hoàn tất tích hợp.

## Thành viên 2 - Biểu diễn logic và `CNF`

### Nền tảng hiện có

- [x] Các lớp dữ liệu dùng chung `Status`, `Character`, `Clue`, `PublicState` và `Analysis`.
- [x] Thứ tự ô tất định theo thứ tự ưu tiên hàng (row-major order) và cơ chế mở rộng vùng đã được kiểm định.
- [x] Hỗ trợ ngữ nghĩa cho tất cả các mẫu màn chơi trong bộ phân tích phát triển (tạm thời) (development analyzer).
- [x] Các bài kiểm thử vét cạn trên vùng nhỏ và các bước kiểm tra ngữ nghĩa ngoại tuyến độc lập.

### Phần triển khai còn lại

- [ ] Gán các biến chính (primary variable) từ mã ô, với giá trị chân lý `True` mang nghĩa là tội phạm. Cấp phát riêng biệt và tất định các biến phụ trợ (auxiliary variable).
- [ ] Mã hóa `FACT`, `SAME`, `DIFFERENT`, `EXACTLY`, `AT_LEAST` và `AT_MOST`.
- [ ] Thêm các kết luận công khai dưới dạng mệnh đề đơn vị (unit clause) và chỉ mã hóa các manh mối công khai.
- [ ] Xem `QUOTE` như một thành phần đóng góp rỗng vào `CNF`.
- [ ] Mã hóa `ODD` và `EVEN` trên số lượng tội phạm đã được chuẩn hóa (normalize).
- [ ] Mã hóa `COUNT_COMPARE` sử dụng đúng trạng thái đích thực tế của nó, cả hai vùng, và ngữ nghĩa so sánh nghiêm ngặt `GT`/`LT` hoặc bằng `EQ`. Kiểm thử các vùng giao nhau và trường hợp triệt tiêu.
- [ ] Mã hóa `IMPLIES` với các ô tiền đề/kết luận có thứ tự và trạng thái riêng của từng ô.
- [ ] Mã hóa `CONNECTED` với quan hệ kề theo tính liên thông trực giao (4 hướng) bên trong vùng đã cho. Bảo toàn ngữ nghĩa hiện tại đối với vùng rỗng/vùng một phần tử và kiểm thử trường hợp chỉ tiếp xúc theo đường chéo.
- [ ] Xử lý các vùng đã mở rộng từ bộ nạp dữ liệu, bao gồm phần giao, các ô lân cận chung (common neighbors), các hướng trực tiếp, biên (boundary), toàn lưới và các nhóm cố định (có tên) (fixed named group).
- [ ] Duy trì các bộ đánh giá ngữ nghĩa (semantic evaluator) độc lập cho các manh mối mà bộ mã hóa hỗ trợ.
- [ ] Thống kê số lượng biến chính, biến phụ trợ và số lượng mệnh đề (clause) được sinh ra.
- [ ] Đối chiếu tính thỏa mãn được (satisfiability) của `CNF` với ngữ nghĩa trực tiếp một cách vét cạn trên các trường hợp nhỏ. Cố định phép gán của các biến chính và cho phép phép gán của các biến phụ trợ thay đổi.
- [ ] Bao phủ các trường hợp vùng rỗng, các giá trị cực biên của phép đếm, chuẩn hóa mục tiêu vô tội, mệnh đề điều kiện (conditional), vùng dùng chung, tính liên thông và dữ liệu đầu vào không hợp lệ.
- [ ] Viết phần biến đổi công thức cho báo cáo đối với một manh mối hai ngôi, một manh mối đếm số lượng và các phần mở rộng.

Sau khi nạp dữ liệu, các trường `kind` và `count` của các ràng buộc đếm số lượng (cardinality) / tính chẵn lẻ cốt lõi đã mô tả trực tiếp số lượng tội phạm. Ví dụ, chính xác 1 người vô tội trong 3 ô được lưu trữ dưới dạng `EXACTLY` 2 tội phạm. Hãy sử dụng trực tiếp ràng buộc đã được chuẩn hóa này. `COUNT_COMPARE` và `CONNECTED` sử dụng trực tiếp `target_status`. Xem bảng lược đồ trong `README.md`.

Tiêu chí nghiệm thu (acceptance) yêu cầu sự thống nhất giữa ngữ nghĩa và `CNF`, cấp phát biến có thể tái lập, thống kê mệnh đề và tích hợp thành công với Thành viên 3 và 4.

## Thành viên 3 - Bộ giải `DPLL` `SAT`

- [ ] Triển khai lan truyền đơn vị (unit propagation) và phát hiện xung đột (conflict).
- [ ] Triển khai chọn biến tất định, rẽ nhánh (branching) và quay lui (backtracking).
- [ ] Trả về `SAT` kèm một phép gán đầy đủ trên các biến đã khai báo, hoặc `UNSAT`.
- [ ] Xử lý tường minh các công thức rỗng (empty formula), mệnh đề rỗng (empty clause), các mệnh đề đơn vị mâu thuẫn nhau và các biến không bị ràng buộc.
- [ ] Hỗ trợ các giả định tạm thời (temporary assumption) mà không làm biến đổi cơ sở tri thức (`KB`) bền vững hay làm rò rỉ giả định giữa các truy vấn hệ quả logic (entailment query).
- [ ] Ghi nhận số quyết định (rẽ nhánh) (decision), số lần lan truyền (propagation), số lần quay lui (backtrack) và thời gian chạy cho mỗi lần gọi. Viết tài liệu định nghĩa các bộ đếm và cách tổng hợp số liệu.
- [ ] Biểu diễn trạng thái quá thời gian (`timeout`) tách biệt khỏi `SAT` và `UNSAT`.
- [ ] Đối chiếu các công thức nhỏ với bộ kiểm chứng bằng bảng chân trị (truth-table oracle) và kiểm thử các lần gọi lặp lại.
- [ ] Phối hợp với Thành viên 2 để kiểm chứng các công thức có chứa biến phụ trợ.
- [ ] Viết tài liệu mô tả `DPLL` và quy tắc chọn biến rẽ nhánh (branching rule) xác định đã chọn cho báo cáo.
- [ ] Tùy chọn sau khi đã đảm bảo tính đúng đắn: bổ sung một chiến lược heuristic khác để thực hiện các so sánh có đối chứng.

Tiêu chí nghiệm thu yêu cầu trả về mô hình đầy đủ, kết quả có thể tái lập, các giả định được cô lập và các bộ đếm chính xác thông qua các lời gọi kiểm tra hệ quả logic (entailment) của Thành viên 4.

## Thành viên 4 - Tác tử logic suy diễn

- [ ] Triển khai `griductive/agent/adapter.py` với hàm khởi tạo `Agent` không tham số cung cấp phương thức `analyze(state: PublicState) -> Analysis`.
- [ ] Gọi bộ mã hóa của Thành viên 2 và bộ giải `DPLL` của Thành viên 3.
- [ ] Kiểm tra tính nhất quán (consistency) của `KB` gốc trước tiên. Trả về `Analysis(False, ())` khi `UNSAT`.
- [ ] Phân loại mọi ô chưa xác định theo thứ tự ưu tiên hàng. Nếu `UNSAT` dưới giả định `NOT Ci` thì chứng minh được là tội phạm. Nếu `UNSAT` dưới giả định `Ci` thì chứng minh được là vô tội. Nếu cả hai đều `SAT` thì kết quả là `UNKNOWN`.
- [ ] Trả về các phần tử thuộc kiểu liệt kê `Status` và chính xác một kết quả cho mỗi ô chưa xác định.
- [ ] Phát sinh lỗi tường minh đối với các manh mối không được hỗ trợ hoặc các trường hợp quá thời gian.
- [ ] Giới hạn mọi truy vấn trực tiếp trong phạm vi ảnh chụp trạng thái công khai được cung cấp. Các nhãn ẩn (hidden label) và nội dung manh mối chưa lật thuộc quyền quản lý của engine.
- [ ] Xử lý chính xác các ảnh chụp trạng thái sau khi nhấn `Restart` nếu có sử dụng bộ nhớ đệm cho các cơ sở tri thức hoặc kết quả.
- [ ] Vượt qua lệnh kiểm tra `python -m griductive.check_analyzer --analyzer griductive.agent.adapter:Agent`.
- [ ] Mở rộng kiểm thử đối chiếu (differential check) cho các loại manh mối mới và tất cả các màn chơi từ 03 trở lên.
- [ ] Chạy các phán đoán thủ công, `Hint` và `Auto Solve` thông qua `GUI` bằng bộ chuyển đổi này.
- [ ] Ghi nhận số thứ tự bước, danh sách `ID` (mã định danh) manh mối đang kích hoạt, các truy vấn/kết quả `SAT`, kết luận được chấp nhận và manh mối mới được lật. Phối hợp thống nhất ranh giới giữa engine và vết suy diễn với Thành viên 1.
- [ ] Bổ sung bước kiểm tra ngoại tuyến riêng biệt về tính duy nhất khi có đủ manh mối (complete-clue uniqueness). Tìm một mô hình, chặn phép gán biến chính của mô hình đó và kiểm tra xem có tồn tại mô hình nào khác không. Loại trừ các biến phụ trợ khỏi mệnh đề chặn (blocking clause).
- [ ] Kiểm thử các trạng thái đã giải, bế tắc (stalled), mâu thuẫn (inconsistent) và quá thời gian, cùng với tính độc lập đối với dữ liệu ẩn (hidden data). Phân biệt rõ giữa trạng thái bế tắc do thiếu tri thức công khai với sự nhập nhằng khi đã có đủ manh mối.
- [ ] Viết tài liệu cho báo cáo về hệ quả logic, tính duy nhất và giải tiến dần (progressive solving).

Engine vốn đã tự chọn kết luận bắt buộc đầu tiên theo thứ tự ưu tiên hàng và lật thẻ tương ứng. Hãy tích hợp bộ phân tích thông qua điểm móc khởi tạo của `CLI` hiện có. Phối hợp mọi hàm gọi lại ghi vết hoặc vòng lặp tác tử bổ sung với vòng đời hiện có đó.

Tiêu chí nghiệm thu yêu cầu giải không cần đoán mò toàn bộ các màn chơi được hỗ trợ bằng luồng `CNF`/`DPLL` của nhóm và tạo ra vết suy diễn có thể tái lập của chuỗi lật mở công khai.

## Thành viên 5 - Thực nghiệm và rà soát màn chơi

### Nền tảng hiện có

- [x] Mười ba màn chơi gốc kèm tên và hạt giống ngẫu nhiên, bao gồm 4 màn kích thước 3x3, 4 màn 4x4 và 5 màn 5x5.
- [x] Bộ kiểm định ngoại tuyến kiểm tra tính đúng của manh mối (clue truth), tính duy nhất khi có đủ manh mối và khả năng giải tiến dần (progressive solvability).
- [x] Các vết kiểm định ngữ nghĩa đã được lưu trong `docs/level_validation.json`.
- [x] Các kiểm thử phản chứng đối với manh mối sai, tính nhập nhằng và tình trạng bế tắc khi giải tiến dần.
- [x] Các kịch bản dựng dữ liệu có thể tái lập và cơ chế loại bỏ (cắt tỉa) manh mối dư thừa (redundant clue pruning) để chuyển thành thẻ lời nhận xét (quote card).

### Phần thực nghiệm còn lại

- [ ] Rà soát thiết kế màn chơi và độ khó đối với người chơi. Đưa các trường hợp đại diện (cốt lõi và mở rộng) vào một bảng kê cố định kèm đường dẫn, hạt giống ngẫu nhiên và thông tin phiên bản.
- [ ] Chạy lại các bước kiểm định tính đúng của manh mối, tính duy nhất và giải tiến dần bằng tác tử của nhóm.
- [ ] Bổ sung trình chạy đánh giá hiệu năng ở chế độ không giao diện (headless) trong thư mục `griductive/experiments/`, xuất dữ liệu CSV/JSON ra thư mục `results/` và ghi rõ một câu lệnh tái lập duy nhất.
- [ ] Ghi nhận số biến chính/biến phụ trợ, số mệnh đề, số lần gọi `SAT`, số quyết định, số lần lan truyền, số lần quay lui, số bước/đợt lật thẻ và thời gian chạy.
- [ ] Chỉ rõ số lượng biến/mệnh đề ở thời điểm cuối cùng hoặc mức đỉnh khi `KB` mở rộng dần. Phân biệt rõ số liệu thống kê theo từng lần gọi `SAT` với tổng số liệu trên toàn màn chơi.
- [ ] Xác định rõ số lần chạy, hạt giống ngẫu nhiên, giới hạn quá thời gian và chi tiết môi trường thực nghiệm. Giữ lại cả các trường hợp thất bại và quá thời gian trong các bảng kết quả đầu ra.
- [ ] Sử dụng cùng một bảng kê màn chơi cho mọi phép so sánh. Chỉ so sánh các chiến lược heuristic tùy chọn của bộ giải sau khi phiên bản cơ sở đã hoạt động chính xác.
- [ ] Rà soát cơ chế hiển thị dàn nhân vật ngẫu nhiên và màn chơi sử dụng nhóm xuất xứ cố định (`fixed_cast`). Sử dụng dữ liệu JSON đã lưu cho các thực nghiệm không giao diện có thể tái lập.
- [ ] Tạo các bảng biểu/biểu đồ, rút ra nhận xét, phân tích lỗi và nêu các hạn chế.
- [ ] Điều phối các bước kiểm tra tích hợp cuối cùng và tổng hợp báo cáo.

Bộ kiểm định ngữ nghĩa đóng vai trò làm mốc cơ sở trong quá trình phát triển. Các bộ đếm và kết quả đánh giá hiệu năng phải được thu thập từ chính phần triển khai `CNF`/`DPLL` có đo đạc của nhóm.

## Các mốc kiểm tra tích hợp

1. Thành viên 2–4 thống nhất các kiểu dữ liệu trả về của `CNF`/`SAT`, cách đánh số biến và các chỉ số đo lường.
2. Mã hóa và giải một `KB` công khai nhỏ, sau đó kết nối bộ chuyển đổi và vượt qua các bài kiểm tra cốt lõi.
3. Hỗ trợ mọi mẫu manh mối được sử dụng từ màn chơi 03 trở lên và kiểm định toàn bộ 13 màn chơi.
4. Thành viên 1 và 4 kiểm thử toàn bộ vòng lặp lật mở trên `GUI`, các trường hợp lỗi và nút `Restart`.
5. Thành viên 5 chốt cố định dữ liệu đầu vào, chạy các thực nghiệm có thể tái lập và chuẩn bị kết quả cho báo cáo.
6. Tất cả thành viên rà soát báo cáo, phụ lục, phần ghi nhận nguồn, video minh họa và gói nén nộp bài.

## Công việc chung về báo cáo và nộp bài

- [ ] Mục 4.6, 30 điểm. Mỗi thành viên tự viết phần phương pháp và kết quả của mình, đồng thời ghi nhận tỷ lệ phần trăm hoàn thành/đóng góp thực tế. Thành viên 5 tổng hợp báo cáo.
- [ ] Bao gồm đầy đủ các nội dung: biến, ngữ nghĩa manh mối, `KB` công khai, giao thức lật mở, các ví dụ `CNF`, `DPLL`, hệ quả logic, tính duy nhất, thực nghiệm, hạn chế và tài liệu tham khảo.
- [ ] Rà soát [appendix.md](appendix.md) và bổ sung các lần sử dụng AI cùng các câu lệnh (prompt) phát sinh sau đó.
- [ ] Hoàn thiện [assets/ATTRIBUTION.md](assets/ATTRIBUTION.md), bổ sung điều khoản nguồn gốc vào thư mục `assets/licenses/` và giữ lại tệp `assets/images/NOTICE.txt`.
- [ ] Mục 4.7, 10 điểm. Chuẩn bị video minh họa dài 5–10 phút trình bày quá trình chơi thủ công và tự động giải, có thuyết minh hoặc phụ đề tiếng Anh hoặc tiếng Việt. Gắn liên kết Google Drive vào báo cáo và kiểm tra quyền xem cho bất kỳ ai có liên kết trong trình duyệt ẩn danh.
- [ ] Kiểm chứng quy trình cài đặt sạch từ đầu cùng các hướng dẫn chạy, kiểm thử và thực nghiệm hiện hành.
- [ ] Đóng gói `Source/` và `Report.pdf` vào tệp nén đặt tên theo MSSV đúng như yêu cầu của đề bài. Loại bỏ các môi trường ảo và bộ nhớ đệm. Tuân thủ quy định nộp qua Drive đối với các tệp nén lớn hơn 20 MB và kiểm tra kỹ hạn chót (deadline) của môn học.