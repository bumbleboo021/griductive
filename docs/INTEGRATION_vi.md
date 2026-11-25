🌐 **Ngôn ngữ:** [English](INTEGRATION.md) | [Tiếng Việt](INTEGRATION_vi.md)

# Bắt đầu tích hợp mô-đun của bạn

Engine và `UI` (giao diện người dùng) Pygame của Thành viên 1 đã được cài đặt. Ảnh chân dung (portrait) và phông chữ Genshin cục bộ được tải từ `assets/`. Tên tệp ảnh chân dung sử dụng định dạng `Name · Origin · Game.png`; phần thứ hai được hiển thị nguyên văn, bao gồm cả các nhãn tùy chỉnh như Chef. Các tệp màn chơi sử dụng dàn nhân vật (cast) nguồn được sắp xếp theo bảng chữ cái lấy từ các tài nguyên này. Các câu đố mới nên đặt `name` theo tên ảnh chân dung và `origin` theo nhãn của ảnh chân dung đó. Các trường `profession` (nghề nghiệp) cũ vẫn được tải bình thường, và `Character.origin` đóng vai trò bí danh cho trường có sẵn đó của mô hình. Một nhân vật không khớp sẽ hiển thị ảnh giữ chỗ (placeholder) mặc định ban đầu. Các tệp phông chữ sẽ lùi về phông chữ mặc định của Pygame nếu bị thiếu. Hãy giữ tệp `assets/images/NOTICE.txt` đi kèm với bộ ảnh minh họa. Bộ phân tích mặc định hiện là một bản cài đặt quay lui ngữ nghĩa (semantic backtracking) tạm thời. Nó không phải là bộ mã hóa `CNF` (dạng chuẩn hội), bộ giải `DPLL`, vết suy diễn (deduction trace), bộ kiểm tra tính duy nhất hay bộ thực nghiệm (experiment suite) theo yêu cầu. Những phần đó vẫn thuộc trách nhiệm của Thành viên 2–5.

## Chạy và kiểm tra

Sử dụng Python 3.11+ và cài đặt `requirements-dev.txt` vào môi trường dành cho hệ điều hành của bạn. Từ thư mục gốc của kho mã nguồn (repository):

```text
python main.py
python main.py --puzzle data/puzzles/4x4/level_01.json
python main.py --headless
python -m pytest tests -q
python -m griductive.check_analyzer
```

Bộ chọn `Stage` (màn chơi) chứa 13 màn chơi gốc. Các dữ liệu kiểm thử mẫu (fixture) dạng chuỗi `FACT` phục vụ phát triển được lưu trữ trong `tests/fixtures/` và bị loại trừ khỏi bộ chọn. Màn chơi mặc định là `3x3/level_01.json`. Xem `docs/LEVELS.md` để biết danh mục đầy đủ.

Trong `GUI` (giao diện đồ họa), hãy nhấp vào một thẻ chưa xác định và chọn `Criminal` (tội phạm) hoặc `Innocent` (vô tội) trong cửa sổ bật lên của thẻ đó. Nhấn `Cancel` (hủy), phím Escape hoặc nhấp chuột ra bên ngoài để đóng cửa sổ đó. Chọn một manh mối đã lật để làm nổi bật các ô được manh mối đó tham chiếu. `Hint` (gợi ý) chọn một nhân vật bắt buộc phải suy ra được mà không lật thẻ đó. `Auto Solve` (tự động giải) lật từng thẻ một; `Stop` (dừng) sẽ dừng lại sau lượt phân tích hiện tại. `Load` (tải màn chơi) liệt kê các tệp JSON trong `data/puzzles/` và cũng chấp nhận đường dẫn tệp được nhập thủ công. Cuộn bảng manh mối hoặc danh sách tệp để xem thêm các mục khác. Phím Escape sẽ đóng bộ chọn hoặc trò chơi.

## Thành viên 4: Kết nối tác tử (agent)

Tạo tệp `griductive/agent/adapter.py` với một hàm khởi tạo hoặc lớp không tham số có tên là `Agent`:

```python
from griductive.domain.models import Analysis, PublicState, Status

class Agent:
    def analyze(self, state: PublicState) -> Analysis:
        # Build CNF from state.clues and state.verdicts using Person 2's encoder.
        # Check consistency and entailment with Person 3's DPLL solver.
        # Return Analysis(False, ()) if the public KB is UNSAT.
        # Otherwise classify EVERY unresolved cell in state.characters order.
        # Example shape (not a correct implementation):
        # Analysis(True, (("B1", Status.CRIMINAL), ("C1", Status.UNKNOWN), ...))
        raise NotImplementedError("Connect the team's encoder and DPLL here")
```

```text
python main.py --analyzer griductive.agent.adapter:Agent
python main.py --headless --analyzer griductive.agent.adapter:Agent
python -m griductive.check_analyzer --analyzer griductive.agent.adapter:Agent
```

Trình kiểm tra sẽ so sánh các kết quả phân loại công khai với bộ phân tích tham chiếu (reference analyzer), kiểm thử các lượt lật mở tiến dần trên các dữ liệu kiểm thử mẫu 3x3/4x4/5x5, đồng thời kiểm tra các trường hợp chưa biết (unknown), mâu thuẫn, nhị phân, đếm số lượng và tính chẵn lẻ (parity). Trình kiểm tra sẽ thoát với mã khác không (nonzero) nếu thất bại. Đây chỉ là bước kiểm tra nhanh (smoke check), không phải bằng chứng về tính đúng đắn của thuật toán hay sự thay thế cho các bài kiểm thử đơn vị (unit test) của riêng bạn.

Hãy trả về các thành viên của enum `Status`, không trả về chuỗi ký tự thuần túy. Kết quả phải tuân theo thứ tự ưu tiên hàng (row-major order) và chứa mọi ô chưa xác định đúng một lần. Không phân loại các ô đã lật. Không bao giờ trả về các nhãn của một mô hình (model – phép gán thỏa mãn) như là các hệ quả logic (entailment). Hãy ném ngoại lệ (raise) khi gặp tình trạng quá thời gian (timeout) hoặc manh mối không được hỗ trợ; một quá trình tìm kiếm chưa hoàn tất tuyệt đối không được báo cáo là `UNKNOWN` hoặc như một kết luận bắt buộc.

`GUI` chạy tác vụ phân tích trong một luồng nền (background worker) duy nhất. Các lời gọi được thực hiện tuần tự. `Load` và `Restart` (chơi lại) bị vô hiệu hóa trong khi luồng này đang hoạt động. Hãy cài đặt một hạn chót (deadline) bên trong bộ giải của bạn: một plugin bị treo sẽ khiến các thao tác thay đổi trạng thái trò chơi tiếp tục bị vô hiệu hóa, mặc dù việc vẽ giao diện và đóng cửa sổ vẫn hoạt động. Các plugin là mã Python đáng tin cậy, không chạy trong sandbox (sandboxed). `API` (giao diện lập trình ứng dụng) dữ liệu ngăn chặn việc truy cập dữ liệu ẩn (hidden data) ngoài ý muốn; không được đọc các tệp câu đố bên trong một bộ phân tích.

## Thành viên 2: Sử dụng các mô hình công khai

### Lược đồ màn chơi mở rộng

Mô hình `Clue` công khai hiện bao gồm các mẫu và trường sau đây. Hãy cập nhật bộ đánh giá độc lập và bộ mã hóa `CNF` của bạn trước khi chạy các màn chơi từ 03 trở lên.

| Loại (Kind) | Các trường và ý nghĩa |
| --- | --- |
| `COUNT_COMPARE` | So sánh số lượng ô mang `target_status` trong `cells` với số lượng ô mang trạng thái đó trong `other_cells`, sử dụng toán tử `GT`, `LT` hoặc `EQ`. `other_region_label` cung cấp câu chữ hiển thị của vùng thứ hai. Các trạng thái đích này được sử dụng trực tiếp mà không thực hiện chuẩn hóa (normalization) số lượng. |
| `CONNECTED` | Các ô mang `target_status` bên trong `cells` phải được liên kết với nhau bằng các bước di chuyển trực giao (4 hướng) hoàn toàn nằm trong vùng đó. Các nhóm rỗng hoặc chỉ có một phần tử đều thỏa mãn ràng buộc này. |
| `IMPLIES` | `cells[0]` mang trạng thái `antecedent_status` kéo theo (implication) `cells[1]` mang trạng thái `consequent_status`. Thứ tự của các ô có ý nghĩa quan trọng. |

Sử dụng `clue.referenced_cells` để làm nổi bật cả hai vùng so sánh hoặc cả hai ô trong mệnh đề điều kiện. Các manh mối đếm số lượng (cardinality) / tính chẵn lẻ cốt lõi vẫn chuẩn hóa về các ràng buộc tội phạm, như mô tả bên dưới. Trường `target_status` được lưu của chúng vẫn bảo toàn câu chữ gốc. Các mẫu so sánh và tính liên thông mới giữ nguyên trạng thái đích thực tế của chúng.

```json
{"id":"compare","type":"COUNT_COMPARE","region":{"type":"neighbors","cell":"B2"},"other_region":{"type":"neighbors","cell":"C2"},"operator":"GT","target_status":"CRIMINAL"}
{"id":"connected","type":"CONNECTED","region":{"type":"row","index":1},"target_status":"INNOCENT"}
{"id":"conditional","type":"IMPLIES","if":{"cell":"A1","status":"CRIMINAL"},"then":{"cell":"B1","status":"INNOCENT"}}
```

Các kiểu vùng bổ sung bao gồm `grid`, `boundary`, `corners`, `common_neighbors` với hai ô phân biệt trong `cells`, và `direction` với một ô tham chiếu `cell` kèm theo hướng `direction` (`above`, `below`, `left`, `right`). Các tham chiếu chỉ hướng nằm ngoài bàn cờ sẽ không vượt qua bước kiểm tra tính hợp lệ. Một vùng `group` bao gồm danh sách ô cố định (`cells`) và một nhãn hiển thị dễ đọc (`label`). Sử dụng `fixed_cast: true` ở cấp gốc khi câu chữ của nhóm phụ thuộc vào dàn nhân vật nguồn. Màn chơi có phần đếm xuất xứ Liyue sử dụng tùy chọn này.

Cập nhật hỗ trợ manh mối: `QUOTE` là một lời nhận xét phi logic không có ô nào; hãy bỏ qua nó khi mã hóa các ràng buộc (tương đương với việc mã hóa hằng đúng `True`, tức không thêm mệnh đề nào vào `CNF`). `region_label` bảo toàn câu chữ mô tả vùng dễ đọc. `target_status` ghi nhận việc manh mối nguồn đếm số người vô tội hay tội phạm, nhưng `kind` và `count` LUÔN được bộ nạp dữ liệu chuẩn hóa về số lượng tội phạm. Không được chuyển đổi số lượng người vô tội thêm lần thứ hai. Ví dụ, 1 người vô tội trong một cột gồm ba ô sẽ trở thành `EXACTLY` 2 tội phạm. `UI` sẽ tái tạo lại câu chữ gốc. Các dạng vùng `rows`/`columns` mới chấp nhận các danh sách `indices`/`labels` và mở rộng phép hợp của chúng; phép giao (`intersection`) vẫn khả dụng để giới hạn các ô lân cận trong phạm vi nhiều hàng. Các lời nhận xét trên `GUI` được lấy từ `config.CHARACTER_QUOTES` và không bao giờ được truyền vào như các ràng buộc thực tế.

`griductive/domain/models.py` định nghĩa các dataclass bất biến (frozen):

| Trường | Ý nghĩa |
| --- | --- |
| `PublicState.size` | Chiều rộng/chiều cao của lưới, nhận giá trị 3, 4, hoặc 5 |
| `characters` | Tuple gồm các `Character(cell, name, profession)` theo thứ tự ưu tiên hàng; `origin` là bí danh của `profession` |
| `verdicts` | Tuple gồm các cặp `(cell, Status)` chỉ dành cho các thẻ đã lật |
| `clues` | Tuple chỉ gồm các đối tượng `Clue` hiện đã lật |
| `Clue.id` | `ID` (mã định danh) duy nhất của manh mối |
| `Clue.kind` | `FACT`/`SAME`/`DIFFERENT`/`EXACTLY`/`AT_LEAST`/`AT_MOST`/`EVEN`/`ODD` |
| `Clue.cells` | Tuple đã mở rộng gồm các mã ô duy nhất, theo thứ tự ưu tiên hàng |
| `Clue.count` | Số lượng đối với các manh mối đếm số lượng; ngược lại là `None` |
| `Clue.status` | Trạng thái đối với `FACT`; ngược lại là `None` |

Các vùng được bộ nạp dữ liệu mở rộng sẵn, do đó bộ mã hóa có thể sử dụng trực tiếp `clue.cells`. Điều này bao gồm cả các phép giao. Các ô lân cận theo đường chéo được tính vào; ô trung tâm được loại trừ. Tên và nghề nghiệp chỉ là siêu dữ liệu phục vụ hiển thị. Sử dụng thứ tự ưu tiên hàng của các mã ô để đánh số các biến chính (primary variables) một cách tất định. Bộ phân tích tham chiếu mặc định không cài đặt `CNF`; hãy viết các bộ đánh giá ngữ nghĩa (semantic evaluator) độc lập và các bài kiểm thử phép mã hóa như đã lên kế hoạch.

## Thành viên 3: Kết nối `DPLL` thông qua tác tử

`GUI` không bao giờ gọi trực tiếp `DPLL`. Hãy thống nhất các kiểu dữ liệu `CNF`/kết quả với Thành viên 2 và Thành viên 4, sau đó cung cấp hàm `solve(cnf, assumptions=())`. Bộ chuyển đổi (adapter) sẽ chuyển dịch các kết quả `SAT` thành `Analysis`. Giữ cho các giả định tạm thời (temporary assumptions) được tách biệt, kiểm tra tính nhất quán của `KB` (cơ sở tri thức) trước tiên, và hoàn thiện các mô hình `SAT` trên toàn bộ các biến đã khai báo (declared variables). Số quyết định (rẽ nhánh) / số lần lan truyền / số lần quay lui và thời gian chạy của bạn thuộc về kết quả của bộ giải, không nằm trong mã Pygame.

## Thành viên 5: Viết dữ liệu kiểm thử mẫu và các bài kiểm tra tích hợp

Sao chép một tệp JSON màn chơi và thay đổi dữ liệu của tệp đó. Cấu trúc tệp:

```json
{
  "title": "My puzzle",
  "size": 3,
  "initially_revealed": ["A1"],
  "characters": [
    {
      "cell": "A1", "name": "Ada", "profession": "Artist",
      "status": "INNOCENT",
      "clue": {"id": "clue-A1", "type": "FACT", "cells": ["B1"], "status": "CRIMINAL"}
    }
  ]
}
```

Ví dụ rút gọn này cần bổ sung thêm tám nhân vật còn lại để trở thành một tệp hợp lệ. Hãy cung cấp chính xác một thẻ cho mỗi ô, tên duy nhất được sắp xếp theo bảng chữ cái theo thứ tự ưu tiên hàng, `ID` manh mối duy nhất, và một lời giải `CRIMINAL`/`INNOCENT` cho mọi thẻ. `initially_revealed` có thể để trống cho các bài kiểm thử phản chứng (negative test). Bộ nạp dữ liệu chỉ kiểm tra cấu trúc, không kiểm tra tính duy nhất của toàn bộ câu đố hay khả năng giải tiến dần (solvability); các kiểm tra đó thuộc phạm vi công việc của tác tử / thực nghiệm.

Các dạng manh mối:

```json
{"id":"c1", "type":"SAME", "cells":["A1","B1"]}
{"id":"c2", "type":"DIFFERENT", "cells":["A1","B1"]}
{"id":"c3", "type":"EXACTLY", "count":1, "region":{"type":"row","index":1}}
{"id":"c4", "type":"AT_LEAST", "count":1, "region":{"type":"column","label":"B"}}
{"id":"c5", "type":"AT_MOST", "count":2, "region":{"type":"neighbors","cell":"B2"}}
{"id":"c6", "type":"EVEN", "region":{"type":"cells","cells":["A1","B1"]}}
{"id":"c7", "type":"ODD", "region":{"type":"intersection","regions":[{"type":"row","index":1},{"type":"column","label":"B"}]}}
```

Sử dụng `EXACTLY` với `count` bằng 0 để biểu diễn trường hợp "không có" (NO). Giới hạn của `count` nằm trong khoảng từ 0 đến kích thước của vùng. Engine ngăn chặn trường hợp một kết luận đã chứng minh được mâu thuẫn với lời giải đã lưu: nó sẽ trả về `ERROR` mà không lật thẻ. Đây là cơ chế chẩn đoán dữ liệu/backend, không phải là phương án thay thế cho việc kiểm tra tính hợp lệ của hệ quả logic. Tất cả các phát biểu manh mối đều phải đúng bất kể trạng thái của nhân vật sở hữu manh mối đó là gì.

`API` tích hợp chế độ không giao diện (headless):

```python
from griductive.engine.game import GameEngine
from griductive.engine.puzzle import load_puzzle
from griductive.engine.reference import ReferenceAnalyzer

engine = GameEngine(load_puzzle("data/puzzles/3x3/level_01.json"), ReferenceAnalyzer())
snapshot = engine.public_state()
hint = engine.hint()  # No mutation.
outcome = engine.step()  # One entailed verdict and reveal, or a terminal result.
```

Các mã kết quả: `ACCEPTED`, `SOLVED`, `HINT`, `NOT_PROVABLE`, `CONTRADICTED`, `ALREADY_REVEALED`, `STALLED`, `INCONSISTENT`, `ERROR`. Các phán đoán bị bác bỏ không làm thay đổi trạng thái. `restart()` khôi phục các thẻ được lật sẵn từ đầu. Mỗi câu đố được tải sẽ nhận một bộ phân tích mới; một bộ phân tích đang tồn tại phải xử lý được các ảnh chụp trạng thái (snapshot) bất kỳ, bao gồm cả các lần khởi động lại (`restart()`).

## Công việc tiếp nối của Thành viên 1 khi tích hợp cuối cùng

`GUI` đã được kiểm thử bằng phương thức kết xuất không hiển thị ra màn hình thực tế của Pygame và các sự kiện chuột giả lập. Hãy chạy ứng dụng trên máy tính để bàn của các thành viên trong nhóm để kiểm tra tỷ lệ hiển thị và kích thước cửa sổ. Cửa sổ logic có kích thước 1180x1020 và Pygame sẽ tự động co giãn để vừa với màn hình. Các thẻ dọc lấp đầy khu vực bàn cờ bên trái. Tên/xuất xứ dài sẽ bị cắt bớt cho vừa với thẻ của chúng; hãy giữ cho các nhãn trong dữ liệu kiểm thử mẫu thật ngắn gọn. Các manh mối có một bảng cuộn riêng. Ảnh chân dung được lưu vào bộ nhớ đệm theo tên nhân vật và kích thước kết xuất. `ui/assets.py` quản lý việc tải ảnh minh họa và phông chữ. Hãy rà soát lại luồng xử lý cuối cùng chạy trên nền `DPLL` cùng với Thành viên 4 và quay video minh họa sau khi cả nhóm hoàn thành các thuật toán và thực nghiệm.