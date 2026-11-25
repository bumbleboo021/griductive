# Tài liệu thuật toán DPLL SAT Solver (Thành viên 3)

Tài liệu này tổng hợp phần thiết kế, quy tắc chọn biến, định nghĩa chỉ số đo lường và hướng dẫn tổng hợp số liệu cho `griductive/sat/dpll.py`, phục vụ phần **Algorithms** và **Experiments** trong `Report.pdf`.

---

## 1. Giao diện tích hợp và phân biệt 3 trạng thái kết quả

Hàm `solve(clauses, total_vars, assumptions=(), timeout_seconds=None, heuristic="smallest") -> SatResult` nhận vào:
- `clauses`: công thức CNF dạng chuẩn DIMACS (mỗi mệnh đề gồm các literal nguyên khác `0`; `+v` là $v = \text{True}$, `-v` là $v = \text{False}$).
- `total_vars`: tổng số biến đã khai báo `1..total_vars` (gồm cả biến chính và biến phụ do Encoder sinh ra).
- `assumptions`: tập giả định tạm thời cho riêng một lần gọi (ví dụ `(-v,)` để kiểm tra $KB_t \land \neg C_v$).
- `timeout_seconds`: giới hạn thời gian chạy (giây) hoặc `None`.
- `heuristic`: chiến lược chọn biến và cực tính rẽ nhánh (`"smallest"` mặc định, hoặc `"jw"` cho đối chứng thực nghiệm; báo `ValueError` nếu truyền giá trị khác).

Kết quả `SatResult` (frozen dataclass) phân biệt tường minh 3 trạng thái:

| Trạng thái | `is_sat` | `is_timeout` | `model` | Ý nghĩa với Agent (TV4) |
| :--- | :---: | :---: | :---: | :--- |
| **SAT** | `True` | `False` | `dict[int, bool]` đầy đủ `1..total_vars` | Tồn tại ít nhất 1 phép gán thỏa mãn $KB_t \land \text{assumptions}$ |
| **UNSAT** | `False` | `False` | `None` | Không tồn tại phép gán thỏa mãn $\rightarrow$ dùng để chứng minh hệ quả logic |
| **TIMEOUT** | `False` | `True` | `None` | Quá giới hạn thời gian; tuyệt đối không được suy diễn thành `UNSAT` hay `UNKNOWN` |

---

## 2. Luồng hoạt động của thuật toán DPLL

1. **Cô lập giả định (`assumptions`):**
   - Trước khi tìm kiếm, solver tạo mới một bảng gán cục bộ `assignment: dict[int, bool] = {}` và nạp từng literal trong `assumptions` vào bảng này mà **không sửa đổi `clauses` gốc**.
   - Nếu `assumptions` tự mâu thuẫn (chứa cả `+v` và `-v`), hàm kết thúc ngay và trả về `UNSAT`.
   - Vì mỗi lần gọi `solve()` khởi tạo mới toàn bộ trạng thái cục bộ, không có bất kỳ giả định nào bị rò rỉ giữa các truy vấn liên tiếp.

2. **Đánh giá từng mệnh đề (`_inspect_clause`):**
   - Mỗi mệnh đề được phân loại thành 1 trong 4 trạng thái:
     - `SAT`: có ít nhất một literal đang thỏa mãn.
     - `CONFLICT`: không có literal nào thỏa mãn và `0` literal chưa gán (bao gồm cả mệnh đề rỗng `()`).
     - `UNIT`: không có literal nào thỏa mãn và còn đúng `1` literal chưa gán (sau khi lọc trùng literal).
     - `OPEN`: không có literal nào thỏa mãn và còn $\ge 2$ literal chưa gán.

3. **Lan truyền đơn vị (`_unit_propagate`):**
   - Lặp lại vòng quét trên `clauses`:
     - Gặp `CONFLICT` $\rightarrow$ trả về `False` ngay lập tức để cắt tỉa nhánh tìm kiếm.
     - Gặp `UNIT` với `unit_lit` $\rightarrow$ ép gán `curr_assignment[abs(unit_lit)] = (unit_lit > 0)`, tăng `propagations`, và tiếp tục lặp để xử lý hiệu ứng dây chuyền.
   - Dừng khi hoàn tất một vòng quét mà không có biến mới nào được gán.

4. **Rẽ nhánh và quay lui (`_dpll`):**
   - Kiểm tra thời hạn `_check_timeout()` ở mỗi nút đệ quy và mỗi lượt lan truyền; nếu quá hạn thì ném ngoại lệ nội bộ `_SolveTimeout` để thoát thẳng về `solve()` và trả `is_timeout=True`.
   - Sau `_unit_propagate`, nếu không còn mệnh đề nào chưa `SAT`, trả về phép gán hiện tại.
   - Ngược lại, gọi bộ chọn rẽ nhánh theo `heuristic` để lấy `(best_var, first_val)`, tăng `decisions += 1`, và thử nhánh `first_val` trên một bản sao `curr_assignment.copy()`.
   - Nếu nhánh đầu trả về `None` (mọi đường đi dưới nó đều xung đột), tăng `backtracks += 1`, quay lui về trạng thái cha (không bị ảnh hưởng bởi các phép gán đã thử ở nhánh trước) và thử tiếp nhánh `not first_val` trên bản sao độc lập.

5. **Hoàn thiện biến tự do:**
   - Khi `_dpll` trả về nghiệm hợp lệ, mọi biến $v \in \{1, \dots, \text{total\_vars}\}$ chưa xuất hiện trong nghiệm (biến không bị ràng buộc hoặc chỉ nằm trong các mệnh đề đã thỏa) được gán mặc định `False`, đảm bảo `model` luôn phủ đầy đủ toàn bộ các biến đã khai báo.

---

## 3. Quy tắc chọn biến rẽ nhánh xác định

Bộ giải hỗ trợ hai chiến lược chọn biến tất định (không dùng yếu tố ngẫu nhiên):

### 3.1. Chiến lược cơ sở: Smallest-Variable-ID (`heuristic="smallest"`, mặc định)
- **Quy tắc:** Chọn biến chưa gán có chỉ số nguyên dương nhỏ nhất trong số các literal xuất hiện ở những mệnh đề chưa đạt trạng thái `SAT`, và luôn thử phân cực **`True` trước, `False` sau**.
- **Lý do lựa chọn làm baseline:**
  1. **Tính tất định tuyệt đối:** Cùng một đầu vào luôn cho ra cùng cây tìm kiếm, cùng `model` và cùng các bộ đếm.
  2. **Ưu tiên biến chính trước biến phụ:** Bộ mã hóa của Thành viên 2 cấp phát biến chính (các ô trên lưới) là `1..N²` và biến phụ là `N² + 1..total_vars`. Việc ưu tiên ID nhỏ nhất giúp DPLL rẽ nhánh trên các biến bàn cờ trước, để các biến phụ của ràng buộc đếm tuần tự (`EXACTLY`/`AT_MOST`/`AT_LEAST`), chẵn lẻ (`ODD`/`EVEN`) và liên thông (`CONNECTED`) tự động được suy ra qua Unit Propagation.
  3. **Tránh rẽ nhánh dư thừa:** Bỏ qua các biến chỉ nằm trong mệnh đề đã `SAT` và các biến tự do.

### 3.2. Chiến lược đối chứng: Dynamic Two-Sided Jeroslow–Wang (`heuristic="jw"`)
- **Công thức:** Tại mỗi nút rẽ nhánh, trên các mệnh đề chưa `SAT` (với $|C'|$ là số literal chưa gán phân biệt còn lại trong mệnh đề $C$), tính trọng số cho từng literal:
  $$J(\ell) = \sum_{\substack{C \in \text{UnSAT} \\ \ell \in C}} 2^{-|C'|}$$
- **Chọn biến & cực tính:**
  - Chọn biến $v$ tối đa hóa tổng $J(+v) + J(-v)$; nếu hòa điểm, ưu tiên `v` nhỏ nhất (qua khóa `(score, -v)`) để đảm bảo tính tất định 100%.
  - Thử `True` trước nếu $J(+v) \ge J(-v)$, ngược lại thử `False` trước.
- **Nhận xét đối chứng sơ bộ trên 13 màn chơi (`timeout_seconds=10.0`):** Cả hai chiến lược đều giải **13/13 màn** với `0` backtracks; `jw` giảm tổng số quyết định trên toàn bộ 13 màn từ `11,442` xuống `10,122` (**giảm 11.5%**, nổi bật nhất ở `5x5/level_02` giảm `36.9%` từ `1,350` xuống `852`), với tổng thời gian solver giảm nhẹ từ `5.39s` xuống `5.30s`.

---

## 4. Định nghĩa bộ đếm và cách tổng hợp cho Thực nghiệm

Mỗi lần gọi `solve()` trả về một đối tượng `SatResult` với các bộ đếm cho **riêng lần gọi đó**:

- **`decisions` (`int`):** Số nút rẽ nhánh đã mở, tính mỗi khi `_dpll` chọn một biến chưa gán `best_var` để tách thành hai nhánh giá trị. Các phép ép từ `UNIT` và `assumptions` đầu vào không tính vào `decisions`.
- **`propagations` (`int`):** Số phép gán biến được suy ra bắt buộc từ một mệnh đề `UNIT` trong `_unit_propagate` (bao gồm cả mệnh đề đơn vị sẵn có ở gốc và các mệnh đề trở thành đơn vị trong quá trình lan truyền dây chuyền). Các phần tử trong `assumptions` đầu vào không tính vào `propagations`.
- **`backtracks` (`int`):** Số lần nhánh thử đầu tiên (`first_val`) thất bại do xung đột và bộ giải quay lui sang thử giá trị còn lại (`not first_val`) tại một nút quyết định.
- **`runtime` (`float`):** Thời gian đồng hồ thực (tính bằng giây qua `time.perf_counter()`) từ lúc bắt đầu `solve()` đến khi trả về `SatResult`.

### Quy ước tổng hợp số liệu trên một màn chơi (cho Thành viên 5)
Trong một màn chơi Griductive, mỗi bước lật thẻ gồm **1 truy vấn kiểm tra KB gốc** và **1–2 truy vấn phản chứng cho từng ô chưa giải** (`assumptions = (-v,)` và có thể thêm `(+v,)`). Khi lập bảng thực nghiệm (Mục 4.5), cần phân biệt rõ:
- **Theo từng lần gọi SAT (per-call):** giá trị trung bình / lớn nhất (peak) của `decisions`, `propagations`, `backtracks`, `runtime` trên mỗi lần gọi `solve()`.
- **Theo toàn màn chơi (per-puzzle total):**
  - `total_sat_calls`: tổng số lần gọi `solve()` từ bước đầu đến khi kết thúc màn.
  - `total_decisions = sum(res.decisions)`, `total_propagations = sum(res.propagations)`, `total_backtracks = sum(res.backtracks)`.
  - `total_solver_runtime = sum(res.runtime)` (tổng thời gian nằm trong DPLL, tách biệt với thời gian encode CNF hay giao diện).
