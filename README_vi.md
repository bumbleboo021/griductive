🌐 **Ngôn ngữ:** [English](README.md) | [Tiếng Việt](README_vi.md)

# Griductive

Trò chơi suy luận bằng Python/Pygame cho môn CSC14003, Nhập môn Trí tuệ Nhân tạo.
Yêu cầu đồ án nằm trong tệp [AI - Project 2.pdf](AI%20-%20Project%202.pdf).
Lối chơi tuân theo [Griductive](https://knotwise.games/games/griductive).

## Bàn giao hiện tại

Engine trò chơi, giao diện, phần tích hợp tài nguyên và 13 màn chơi có thể chơi được đã sẵn sàng để các thành viên trong nhóm tích hợp. Ứng dụng hiện đang sử dụng bộ phân tích tham chiếu (reference analyzer) dựa trên quay lui ngữ nghĩa (semantic backtracking). Bộ mã hóa (encoder) `CNF` (dạng chuẩn hội), bộ giải `DPLL` được chấm điểm, bộ chuyển đổi cuối cùng cho tác tử (agent) logic và trình chạy đánh giá hiệu năng (benchmark) vẫn cần được cài đặt.

| Mảng công việc | Phần đã cài đặt hiện tại | Người phụ trách tiếp theo |
| --- | --- | --- |
| Trò chơi và `UI` (giao diện người dùng) | Cửa sổ bật lên chọn phán đoán thủ công, lật (mở) manh mối, thông báo bác bỏ, `Stage` (màn chơi), `Restart` (chơi lại), `Hint` (gợi ý), `Auto Solve` (tự động giải), trợ giúp, âm nhạc, hiệu ứng di chuột và lật thẻ | Thành viên 1 rà soát tích hợp cuối cùng |
| Mô hình dùng chung và nạp dữ liệu | Các mô hình dữ liệu công khai bất biến, tệp JSON đã được kiểm tra tính hợp lệ, các vùng đã được mở rộng, các manh mối đếm số lượng đã được chuẩn hóa | Thành viên 2 xây dựng bộ mã hóa dựa trên các mô hình này |
| `SAT` | `griductive/sat/` chứa khung gói (package placeholder) | Thành viên 3 cài đặt `DPLL` |
| Tác tử logic | `griductive/agent/` chứa khung gói (package placeholder) | Thành viên 4 bổ sung bộ chuyển đổi, vết suy diễn (deduction trace) và `API` (giao diện lập trình ứng dụng) kiểm tra tính duy nhất |
| Màn chơi và kiểm định | 4 màn chơi cho kích thước 3x3, 4 màn chơi cho 4x4, 5 màn chơi cho 5x5, trình kiểm định ngữ nghĩa và các vết suy diễn đã lưu | Thành viên 5 xây dựng các thực nghiệm (experiment) có thể tái lập |

Xem [TODO.md](TODO.md) để biết phân công nhiệm vụ và các bước kiểm tra nghiệm thu.

## Chạy cục bộ trên máy

Sử dụng Python 3.11 trở lên và chạy các lệnh từ thư mục gốc của kho mã nguồn.
Tạo môi trường ảo trên hệ điều hành nơi trò chơi sẽ chạy.

### Windows PowerShell

```powershell
python -m venv .venv-win
.\.venv-win\Scripts\python.exe -m pip install -r requirements-dev.txt
.\.venv-win\Scripts\python.exe main.py
```

Nếu bản sao mã nguồn này đã có sẵn thư mục `.venv-win` hoạt động được, hãy dùng trực tiếp trình thông dịch Python trong đó.
Thư mục môi trường này nằm ở máy cục bộ và được loại trừ khỏi Git. Nếu lệnh `python` trỏ đến một trình thông dịch không hỗ trợ `venv`, hãy chọn một trình thông dịch CPython đã cài đặt trong IDE của bạn và dùng trình thông dịch đó để tạo môi trường.

### Linux hoặc macOS

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements-dev.txt
.venv/bin/python main.py
```

`requirements.txt` cài đặt Pygame. `requirements-dev.txt` cài đặt bổ sung pytest.
Các ví dụ sau sử dụng lệnh `python` sau khi đã kích hoạt môi trường bạn chọn.
Trên Windows, bạn có thể thay thế bằng `.\.venv-win\Scripts\python.exe` trong mỗi lệnh.

## Cách chơi và chọn màn chơi

```text
python main.py
python main.py --puzzle data/puzzles/5x5/level_05.json
```

- Nhấp vào một nhân vật chưa xác định và chọn `Criminal` (tội phạm) hoặc `Innocent` (vô tội) trong cửa sổ bật lên.
- Thẻ ở góc trên bên trái được chọn mặc định khi bắt đầu. Phím WASD hoặc các phím mũi tên dùng để di chuyển sang các thẻ liền kề và dừng lại ở mép bàn cờ. Phím Enter mở cửa sổ bật lên chọn phán đoán của một thẻ chưa xác định với lựa chọn mặc định là `Innocent`. Phím A/Mũi tên trái chọn `Innocent`, D/Mũi tên phải chọn `Criminal`, và S/Mũi tên xuống chọn `Cancel` (hủy); phím W/Mũi tên lên quay lại từ `Cancel` về `Innocent`. Phím Enter xác nhận lựa chọn, và phím Escape đóng cửa sổ bật lên. Chọn một thẻ đã giải sẽ hiển thị manh mối của thẻ đó.
- Một phán đoán được chấp nhận sẽ lật mở một manh mối. Các lựa chọn bị bác bỏ sẽ hiển thị thông báo `Incorrect verdict` (Phán đoán sai) hoặc `Not enough evidence` (Chưa đủ bằng chứng). Việc sử dụng `Hint` là không bắt buộc.
- Nhấp vào một thẻ đã giải hoặc manh mối đã lật để làm nổi bật các ô được tham chiếu bởi manh mối đó. Bảng manh mối cuộn mượt mà và hiển thị toàn bộ nội dung của các manh mối bị rút gọn trên thẻ.
- `Stage` mở danh sách các màn chơi theo tên. `Restart` khôi phục lại trạng thái được lật sẵn từ đầu. `Hint` chỉ ra một nhân vật có trạng thái suy ra được chắc chắn. `Auto Solve` tự động thực hiện các nước đi đã chứng minh được và `Stop` (dừng) sẽ tạm dừng quá trình này sau khi hoàn tất lượt phân tích đang chạy dở.
- Nút `?` ở góc trên bên phải giải thích luật chơi. `Music` mở bảng chọn bản nhạc, gồm nút bật/tắt và các tệp WAV, OGG, MP3 hoặc FLAC từ thư mục `assets/sounds/`.
- Phím Escape đóng cửa sổ bật lên đang mở. Ở màn hình chính, phím này dùng để thoát trò chơi.

Màn chơi mặc định là `data/puzzles/3x3/level_01.json`. Mỗi màn chơi có một trường gốc `name` để hiển thị. Các trường `title` kiểu cũ vẫn được chấp nhận. Các màn chơi hướng dẫn đã bị loại bỏ khỏi danh sách chọn. Dữ liệu kiểm thử mẫu (fixture) dạng chuỗi `FACT` dùng cho các bài kiểm thử nằm trong thư mục `tests/fixtures/`.

Ảnh chân dung được xáo trộn ngẫu nhiên khi tải một màn chơi và giữ nguyên không đổi khi nhấn `Restart`.
Tệp `5x5/level_05.json` sử dụng `fixed_cast: true` vì manh mối về xuất xứ Liyue của màn chơi này phụ thuộc vào dàn nhân vật. Tên nhân vật trong tệp JSON nguồn hiện bắt buộc phải là duy nhất và sắp xếp theo thứ tự bảng chữ cái theo thứ tự ưu tiên hàng (row-major order). Việc xáo trộn ngẫu nhiên trên `GUI` (giao diện đồ họa) diễn ra sau khi nạp dữ liệu.

Tên các màn chơi, độ bao phủ và hướng dẫn kiểm định nằm trong [docs/LEVELS.md](docs/LEVELS.md).

## Quan sát tác tử trong trò chơi

Nhấn **Agent** ở phía trên bên phải bàn cờ để mở bảng bên cạnh trò chơi.
Cửa sổ mở rộng khi bật bảng và trở lại kích thước ban đầu khi đóng. Nhấp vào
bàn cờ để chơi, hoặc nhấp vào bảng tác tử để dùng phím mũi tên cuộn và xem lịch sử.
**Analyze** phân loại trạng thái công
khai mà không mở thẻ; **Next move** chứng minh và mở một nhân vật. **Auto Solve /
Stop** chạy hoặc dừng giải tự động, đồng thời ghi lại các lượt phân tích. Dùng
Previous/Next để xem lịch sử; cuộn bằng bánh xe hoặc phím mũi tên.
Khi xem lịch sử, bàn cờ hiển thị trạng thái công khai sau hành động tương ứng,
không thay đổi engine thật. Nhấn **Live**, chuyển đến lượt mới nhất hoặc đóng
bảng để trở về bàn cờ hiện tại. Chế độ lịch sử chỉ đọc và tạm dừng Auto Solve.

Bảng có số biến chính/phụ, số mệnh đề CNF, lượt gọi SAT, quyết định/lan truyền/
quay lui, số bước suy diễn/lượt mở và thời gian phân tích. Số liệu từng lượt và
tổng tích lũy được tách riêng. Không tính thẻ mở sẵn hoặc Hint là bước suy diễn;
thời gian không gồm hoạt ảnh, chờ và mã hóa bổ sung phục vụ hiển thị. Bộ đếm
solver chưa cung cấp hiển thị **N/A**, không suy đoán bằng 0. Chạy Reference
không gọi SAT; kích thước CNF là mã hóa chẩn đoán của đầu vào công khai.
Các thao tác Hint và chọn trạng thái thủ công cũng được ghi nhận.

Mỗi lượt hiển thị bộ phân tích thực tế, manh mối công khai, kết quả phân loại,
thời gian, số biến/mệnh đề CNF nếu có, các giả định và kết quả SAT đã ghi nhận,
cùng manh mối vừa mở. Lưu tối đa 128 lượt; Restart và chuyển màn xóa lịch sử.
Một lượt phân tích không đồng nghĩa với một bước mở thẻ.

**Use Reference** và **Use Logic Agent** đổi bộ phân tích, giữ nguyên các thẻ đã
chứng minh và xóa lịch sử. Nếu chưa có CNF/DPLL, tác tử ghi rõ **Reference fallback**;
không tạo kết quả SAT giả cho bộ phân tích tham chiếu. Nhánh hiện tại vẫn cần
`griductive/sat/dpll.py` để chạy DPLL thật.

## Các bước kiểm tra đầu tiên sau khi kéo dự án về

```text
python -m pytest tests -q
python main.py --headless
python -m griductive.check_analyzer
python scripts/validate_levels.py
```

| Lệnh | Nội dung kiểm tra |
| --- | --- |
| `pytest` | Các bước chuyển trạng thái của engine, ngữ nghĩa manh mối, các màn chơi và tương tác Pygame không hiển thị màn hình |
| `main.py --headless` | Giải tiến dần (progressive solving) màn chơi được chọn bằng bộ phân tích đã chọn |
| `griductive.check_analyzer` | Kết quả phân loại công khai đối chiếu với bộ phân tích tham chiếu trên màn chơi 01 ở mọi kích thước bàn cờ và các trường hợp nhỏ về ràng buộc cơ bản / tính chẵn lẻ (parity) |
| `scripts/validate_levels.py` | Tính đúng của mọi manh mối được lưu trữ, tính duy nhất (khi có đủ manh mối), và khả năng giải tiến dần công khai trên tất cả 13 màn chơi |

Trình kiểm tra hiện tại bao phủ các trường hợp cơ bản / tính chẵn lẻ và bộ màn chơi 01 gốc.
Thành viên 4 cần bổ sung phần đối chiếu cho tác tử mở rộng từ màn chơi 03 trở lên.
Trình kiểm định màn chơi độc lập sử dụng tìm kiếm ngữ nghĩa và bộ phân tích tham chiếu.
Việc kiểm định `CNF`/`DPLL` cuối cùng và đo lường thực nghiệm vẫn nằm trong danh sách công việc cần hoàn thành.

Một số hệ thống có thể xuất ra thông báo `no fast renderer available` khi chạy dưới trình điều khiển kiểm thử không màn hình của SDL.
Hãy kiểm tra riêng kết quả của pytest và bất kỳ lỗi thực tế nào (nếu có).

## Kết nối tác tử của thành viên trong nhóm

Thành viên 4 cần cài đặt một lớp không tham số hoặc hàm khởi tạo trong tệp `griductive/agent/adapter.py`. Giao diện công khai hiện có là `analyze(state: PublicState) -> Analysis`.

```text
python main.py --analyzer griductive.agent.adapter:Agent
python main.py --headless --analyzer griductive.agent.adapter:Agent
python -m griductive.check_analyzer --analyzer griductive.agent.adapter:Agent
python main.py --headless --puzzle data/puzzles/5x5/level_05.json --analyzer griductive.agent.adapter:Agent
```

Các lệnh chạy bộ chuyển đổi này sẽ khả dụng sau khi mô-đun đó được cài đặt.

bộ chuyển đổi nhận đầu vào gồm các manh mối đã lật, các kết luận đã chứng minh được và siêu dữ liệu công khai của nhân vật.
Trả về `Analysis(False, ())` nếu `KB` (cơ sở tri thức) mâu thuẫn. Với một `KB` nhất quán, trả về `Analysis(True, verdicts)` sao cho mọi ô chưa xác định đều được phân loại đúng một lần theo thứ tự ưu tiên hàng, sử dụng `Status.CRIMINAL`, `Status.INNOCENT` hoặc `Status.UNKNOWN`.
Ném ngoại lệ khi gặp mẫu manh mối không được hỗ trợ hoặc khi quá thời gian (timeout). Engine sẽ kiểm tra cấu trúc kết quả trả về này và nắm quyền xử lý việc chấp nhận phán đoán cũng như lật mở manh mối.

Giữ cho `ID` (mã định danh) của các biến chính (primary variable) gắn cố định với từng ô thay vì gắn với tên hiển thị đã được xáo trộn ngẫu nhiên.
`GUI` tuần tự hóa các lời gọi bộ phân tích thông qua một luồng nền (background worker). Một thực thể của bộ phân tích phải xử lý được các ảnh chụp trạng thái (snapshot) công khai bất kỳ, bao gồm cả trường hợp màn chơi được chơi lại.
Bộ phân tích mặc định `ReferenceAnalyzer` có hạn chót (deadline) là ba giây cho mỗi lượt phân tích.

Lược đồ chi tiết và các ví dụ tích hợp nằm trong [docs/INTEGRATION.md](docs/INTEGRATION.md).

## Các quy tắc manh mối mà bộ mã hóa phải bảo toàn

| Mẫu manh mối công khai | Quy ước mã hóa |
| --- | --- |
| `FACT` | `cells` chứa một ô duy nhất và `status` là trạng thái được khẳng định của ô đó |
| `SAME` / `DIFFERENT` | Hai ô có trạng thái Boolean bằng nhau / khác nhau |
| `EXACTLY` / `AT_LEAST` / `AT_MOST` | `kind` và `count` đã mô tả sẵn số lượng tội phạm sau khi chuẩn hóa |
| `ODD` / `EVEN` | `kind` đã mô tả sẵn tính chẵn lẻ của số lượng tội phạm |
| `COUNT_COMPARE` | So sánh số lượng các ô mang trạng thái `target_status` thực tế trong `cells` và `other_cells`, sử dụng toán tử `operator` là `GT`, `LT` hoặc `EQ` |
| `CONNECTED` | Các ô mang trạng thái đích tạo thành một nhóm liên thông trực giao (4 hướng) bên trong `cells`. Nhóm rỗng và nhóm chỉ có một phần tử đều thỏa mãn ràng buộc này |
| `IMPLIES` | `cells[0]` mang trạng thái `antecedent_status` kéo theo (implication) `cells[1]` mang trạng thái `consequent_status`. Phải bảo toàn đúng thứ tự này |
| `QUOTE` | Lời nhận xét cá nhân và không mang ràng buộc logic nào |

Đối với các manh mối đếm số lượng / tính chẵn lẻ cơ bản, `target_status` giữ nguyên cách diễn đạt dùng để hiển thị.
bộ nạp dữ liệu đã chuyển đổi sẵn số lượng vô tội cùng các cận / tính chẵn lẻ của chúng sang ràng buộc theo tội phạm. Việc áp dụng phép chuyển đổi đó thêm một lần nữa sẽ làm sai lệch ý nghĩa.
`COUNT_COMPARE` và `CONNECTED` giữ nguyên trạng thái đích thực tế để đánh giá.
Trường `clue.referenced_cells` bao gồm cả hai vùng của phép so sánh nhằm phục vụ việc làm nổi bật trên giao diện.

Các vùng được bộ nạp dữ liệu mở rộng sẵn, bao gồm hàng, cột, ô lân cận, giao của các vùng, ô lân cận chung, hướng, toàn bộ lưới, biên, góc và các nhóm cố định (có tên). Ô lân cận bao gồm cả các ô lân cận theo đường chéo. Tính liên thông chỉ xét theo bốn hướng trực giao.

## Sơ đồ kho mã nguồn

```text
main.py                          Entry point
griductive/app.py                CLI and analyzer factory loading
griductive/domain/models.py      Public models and clue fields
griductive/engine/puzzle.py      Private puzzle model, schema and regions
griductive/engine/game.py        Verdict checks and reveal lifecycle
griductive/engine/reference.py   Development semantic analyzer
griductive/engine/advanced_clues.py  Extended semantic constraints
griductive/ui/                   Rendering, input, assets, config and music
griductive/logic/                Person 2 encoder implementation area
griductive/sat/                  Person 3 DPLL implementation area
griductive/agent/                Person 4 adapter and trace implementation area
griductive/experiments/          Person 5 benchmark implementation area
data/puzzles/                   Thirteen playable stage JSON files
tests/fixtures/                 Development chain fixtures
scripts/validate_levels.py       Offline semantic validator
scripts/build_levels.py          Rebuild levels 01-02
scripts/build_extended_levels.py Rebuild levels 03 and above
scripts/polish_levels.py         Replace removable clues with quote cards
docs/level_validation.json       Saved semantic validation traces
results/                        Generated experiment outputs, ignored by Git
```

Các kịch bản tạo màn chơi sẽ ghi đè lên các tệp đã sinh trước đó. Hãy phối hợp với Thành viên 5 khi thay đổi màn chơi và chạy lại quá trình kiểm định sau khi chỉnh sửa manh mối hoặc các ô được lật sẵn từ đầu.

## Giao diện, tài nguyên và tư liệu báo cáo

Chỉnh sửa tệp `griductive/ui/config.py` để cấu hình màu sắc, phông chữ, kích thước thẻ, thời gian hiệu ứng di chuột / lật thẻ, tốc độ cuộn manh mối, lời nhận xét và các thiết lập nhạc mặc định. Kích thước cửa sổ logic hiện tại là 1180x850 và Pygame sẽ tự co giãn cho phù hợp với màn hình hiển thị. Tên tệp ảnh chân dung cung cấp thông tin về tên và xuất xứ của nhân vật.

- [Tùy chỉnh giao diện](docs/UI_CUSTOMIZATION.md)
- [Ghi chú thiết kế màn chơi](docs/LEVEL_DESIGN.md)
- [Mẫu ghi nhận nguồn tài nguyên](assets/ATTRIBUTION.md)
- [Hướng dẫn thư mục giấy phép tài nguyên](assets/licenses/README.md)
- [Phụ lục sử dụng trợ lý AI](appendix.md)

Hãy điền đầy đủ các mục trống trong phần ghi nhận nguồn tài nguyên và giữ nguyên các thông báo bản quyền đi kèm với tài nguyên. Mỗi thành viên cần rà soát lại phụ lục sử dụng trợ lý AI và bổ sung quá trình sử dụng tiếp theo cùng đóng góp thực tế của mình trước khi nộp báo cáo cuối kỳ.
