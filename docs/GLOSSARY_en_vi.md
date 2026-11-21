# GLOSSARY: Bảng thuật ngữ Griductive (EN → VI)

Cột **Nhóm**: `G` = Giữ nguyên 100% tiếng Anh, `D` = Dịch chuẩn chuyên ngành.
Quy tắc chung: từ giữ nguyên luôn đặt trong `code font`; thuật ngữ dịch được ghi kèm tiếng Anh trong ngoặc ở lần xuất hiện đầu tiên của mỗi tài liệu.

| STT | Nhóm | Thuật ngữ gốc (EN) | Cách xử lý / Dịch sang (VI) | Loại từ / Ngữ cảnh | Ghi chú quy tắc |
| --- | --- | --- | --- | --- | --- |
| 1 | G | `CNF`, `DPLL`, `SAT`, `UNSAT`, `KB` | Giữ nguyên | Từ khóa logic mệnh đề / SAT | Viết hoa như gốc. Lần đầu có thể chú thích: `CNF` (dạng chuẩn hội), `KB` (cơ sở tri thức). |
| 2 | G | `literal`, `SatResult`, `CNF` (kiểu dữ liệu), `encode`, `solve` | Giữ nguyên | `API` nội bộ Người 2–4 | `encode(public_state) -> CNF`, `solve(cnf, assumptions=())`. Không dịch trong code hay chữ ký hàm. |
| 3 | G | `FACT`, `SAME`, `DIFFERENT`, `EXACTLY`, `AT_LEAST`, `AT_MOST`, `EVEN`, `ODD` | Giữ nguyên | Tên loại manh mối (`Clue.kind`) | Luôn viết hoa, gạch dưới. Khi mô tả ý nghĩa thì dịch riêng. |
| 4 | G | `COUNT_COMPARE`, `CONNECTED`, `IMPLIES`, `QUOTE` | Giữ nguyên | Tên loại manh mối mở rộng | Như trên. |
| 5 | G | `GT`, `LT`, `EQ` | Giữ nguyên | Toán tử của `COUNT_COMPARE` | Không dịch khi tham chiếu giá trị. |
| 6 | G | `CRIMINAL`, `INNOCENT`, `UNKNOWN`, `Status` | Giữ nguyên | Giá trị enum trạng thái | Nói về khái niệm trong câu thì dùng "tội phạm / vô tội / chưa biết" (dòng 41). |
| 7 | G | `ACCEPTED`, `SOLVED`, `HINT`, `NOT_PROVABLE`, `CONTRADICTED`, `ALREADY_REVEALED`, `STALLED`, `INCONSISTENT`, `ERROR` | Giữ nguyên | Mã kết quả (outcome codes) của `GameEngine` | Có thể thêm chú giải tiếng Việt trong ngoặc, không thay thế mã. |
| 8 | G | `target_status`, `other_cells`, `other_region_label`, `antecedent_status`, `consequent_status`, `region_label`, `referenced_cells`, `fixed_cast`, `initially_revealed`, `count`, `cells`, `if` / `then` | Giữ nguyên | Trường JSON / thuộc tính `Clue` | Giữ cả khi xuất hiện giữa câu. |
| 9 | G | `row`, `column`, `neighbors`, `intersection`, `common_neighbors`, `direction`, `grid`, `boundary`, `corners`, `group`, `rows`, `columns`, `indices`, `labels` | Giữ nguyên | Kiểu vùng (`region.type`) trong JSON | Diễn giải bằng lời thì dùng "hàng, cột, ô lân cận…" (nhóm D). |
| 10 | G | `above`, `below`, `left`, `right` | Giữ nguyên | Giá trị của `direction` | |
| 11 | G | `Character`, `Clue`, `PublicState`, `Analysis`, `Agent`, `GameEngine`, `ReferenceAnalyzer`, `Analyzer` | Giữ nguyên | Tên class / protocol | Giữ đúng PascalCase. |
| 12 | G | `analyze`, `public_state`, `hint`, `step`, `restart`, `load_puzzle` | Giữ nguyên | Tên hàm / phương thức | Giữ cả `()` khi có. |
| 13 | G | `CHARACTER_QUOTES`, `RANDOMIZE_CAST`, `SHOW_CELL_IN_CLUES`, `PORTRAIT_SIZE`, `CARD_GAP`, `CARD_PADDING`, `CARD_RADIUS`, `PORTRAIT_TOP`, `STATUS_HEIGHT`, `BOARD_X`, `BOARD_Y`, `WINDOW_SIZE`, `MESSAGE_Y`, `REVEAL_DURATION_MS`, `HOVER_DURATION_MS`, `HOVER_LIFT`, `CLUE_SCROLL_STEP`, `CLUE_SCROLL_TIME_MS`, `MUSIC_FILE`, `MUSIC_VOLUME`, `BACKGROUND_FILE`, `BACKGROUND_DIM`, `BG`, `PANEL`, `TEXT`, `ACCENT` | Giữ nguyên | Hằng số cấu hình trong `config.py` | Mọi hằng số viết hoa giữ nguyên. |
| 14 | G | `main.py`, `config.py`, `models.py`, `adapter.py`, `game.py`, `puzzle.py`, `reference.py`, `window.py`, `assets.py`, `character_card.py`, `validate_levels.py` | Giữ nguyên | Tên file | Giữ cả đuôi file. |
| 15 | G | `griductive/agent/`, `griductive/sat/`, `griductive/logic/`, `griductive/experiments/`, `data/puzzles/3x3/level_01.json`, `tests/fixtures/`, `docs/`, `assets/`, `results/` | Giữ nguyên | Đường dẫn | Giữ nguyên dấu `/` và `\`. |
| 16 | G | `python main.py --headless`, `--puzzle`, `--analyzer`, `python -m pytest tests -q` | Giữ nguyên | Lệnh `CLI` và cờ | Không dịch gì trong khối lệnh. |
| 17 | G | `griductive.agent.adapter:Agent` | Giữ nguyên | Đường dẫn import `module:Class` | |
| 18 | G | Python, Pygame, pytest, PowerShell, JSON, CSV, Git, SDL, `.venv-win`, WAV, OGG, MP3, FLAC, M4A | Giữ nguyên | Công nghệ, định dạng, môi trường | |
| 19 | G | `GUI`, `CLI`, `API`, `ID`, `UI` | Giữ nguyên | Viết tắt phổ biến | Lần đầu chú thích, ví dụ `GUI` (giao diện đồ họa). |
| 20 | G | Griductive, Knotwise, Genshin Impact, Liyue, Teyvat, Quiet Rows, Crossed Testimonies, Lantern Bridge, Shared Alibis, The Silent Courtyard, Crossing Paths, Threads of Evidence, The Boundary Case, Teyvat Conspiracy | Giữ nguyên | Tên riêng, tên game, tên màn chơi | Tên màn chơi hiển thị đúng như `name` trong JSON. |
| 21 | G | `Stage`, `Restart`, `Hint`, `Auto Solve`, `Stop`, `Load`, `Tracks`, `Music On/Off`, `Criminal`, `Innocent`, `Cancel`, `Got it` | Giữ nguyên | Nhãn nút trên giao diện | Khớp chữ trên màn hình. Lần đầu chú thích tiếng Việt, ví dụ `Hint` (gợi ý), `Restart` (chơi lại), `Auto Solve` (tự động giải). |
| 22 | D | entailment / entailed | **hệ quả logic (entailment)**; "được suy ra" | Danh từ / động từ, suy diễn | Khác *implication*. Dùng "chứng minh được / suy ra được" cho *proved*. |
| 23 | D | implication / conditional | **phép kéo theo (implication)**; "mệnh đề điều kiện" | Logic mệnh đề | Dùng cho `IMPLIES`. |
| 24 | D | unit propagation | **lan truyền đơn vị** | Thuật toán DPLL | Giữ nhất quán. |
| 25 | D | backtracking / backtrack | **quay lui** | Thuật toán, bộ đếm | Bộ đếm "backtracks" → "số lần quay lui". |
| 26 | D | decision / branching / branching rule | **quyết định (rẽ nhánh)** / **rẽ nhánh** / **quy tắc chọn biến rẽ nhánh** | DPLL | "decisions" → "số quyết định". |
| 27 | D | propagation (counter) | **lan truyền** / "số lần lan truyền" | Bộ đếm DPLL | |
| 28 | D | conflict | **xung đột** | DPLL | |
| 29 | D | clause | **mệnh đề (clause)** | CNF | Lần đầu viết "mệnh đề (clause)", sau đó dùng "mệnh đề" hoặc `clause`. Không dùng "mệnh đề tuyển". Xem lưu ý trùng từ ở dòng 32. |
| 30 | D | unit clause | **mệnh đề đơn vị** | CNF | |
| 31 | D | empty clause / empty formula | **mệnh đề rỗng** / **công thức rỗng** | CNF | |
| 32 | D | proposition / Boolean variable | **mệnh đề logic (proposition) / biến Boolean** | Logic | Vì "mệnh đề" đã dành cho *clause* (dòng 29), *proposition* luôn viết "mệnh đề logic" hoặc "biến mệnh đề". Giữ "Boolean". |
| 33 | D | primary variables | **biến chính** | Mã hóa CNF | Đối ứng *auxiliary*. true = tội phạm. |
| 34 | D | auxiliary variables | **biến phụ trợ** | Mã hóa CNF | |
| 35 | D | declared variables | **biến đã khai báo** | SAT | |
| 36 | D | encoder / encoding / encode | **bộ mã hóa** / **phép mã hóa** / **mã hóa** | Biểu diễn tri thức | |
| 37 | D | knowledge base (KB) | **cơ sở tri thức (KB)** | AI | "public KB" → "KB công khai". |
| 38 | D | satisfiable / unsatisfiable | **thỏa mãn được / không thỏa mãn được** | SAT | `SAT`/`UNSAT` giữ tiếng Anh. |
| 39 | D | consistency / consistent / inconsistent | **tính nhất quán / nhất quán / mâu thuẫn** | KB | Mã `INCONSISTENT` giữ nguyên. |
| 40 | D | model / complete model | **mô hình (phép gán thỏa mãn)** / **mô hình đầy đủ** | SAT | Không nhầm với mô hình học máy. |
| 41 | D | criminal / innocent (khái niệm) | **tội phạm / vô tội** | Ngữ cảnh game | Enum `CRIMINAL`/`INNOCENT` giữ nguyên. |
| 42 | D | assumption(s) | **giả định** | Gọi SAT tạm thời | "temporary assumptions" → "giả định tạm thời". |
| 43 | D | truth table / truth-table oracle | **bảng chân trị** / **bộ kiểm chứng bằng bảng chân trị** | Kiểm thử | |
| 44 | D | oracle | **oracle (bộ kiểm chứng chuẩn)** | Kiểm thử | Giữ "oracle" kèm giải thích lần đầu. |
| 45 | D | tautology / contradiction | **hằng đúng / mâu thuẫn** | Logic | |
| 46 | D | conjunction | **phép hội** | Logic | |
| 47 | D | cardinality (clue / constraint) | **ràng buộc đếm số lượng (cardinality)** | Mã hóa | Lần đầu kèm (cardinality). |
| 48 | D | parity | **tính chẵn lẻ** | `ODD`/`EVEN` | |
| 49 | D | normalize / normalization | **chuẩn hóa** | Loader chuẩn hóa về đếm tội phạm | |
| 50 | D | semantic evaluator / semantic backtracking | **bộ đánh giá ngữ nghĩa** / **quay lui ngữ nghĩa** | Phân tích tham chiếu | |
| 51 | D | reference analyzer / development analyzer | **bộ phân tích tham chiếu** / **bộ phân tích phát triển (tạm thời)** | `ReferenceAnalyzer` | |
| 52 | D | (deductive) agent | **tác tử (suy diễn)** | Mục 4.4 | Dùng "tác tử" thống nhất. Tên class `Agent` và đường dẫn `agent/` giữ nguyên. |
| 53 | D | deduction trace | **vết suy diễn** | Agent | |
| 54 | D | progressive solving / solvability | **giải tiến dần** / **khả năng giải tiến dần** | Kiểm tra mức 3 | Đồng nhất cả tài liệu. |
| 55 | D | clue truth | **tính đúng của manh mối** | Kiểm tra mức 1 | |
| 56 | D | (complete-clue) uniqueness | **tính duy nhất (khi có đủ manh mối)** | Kiểm tra mức 2 | |
| 57 | D | blocking clause | **mệnh đề chặn** | Kiểm tra tính duy nhất | |
| 58 | D | entailment query | **truy vấn hệ quả logic** | Agent | |
| 59 | D | verdict | **phán đoán / kết luận** | Lựa chọn Criminal/Innocent | Quy ước: "phán đoán" cho lựa chọn của người chơi, "kết luận" cho kết quả hệ thống chứng minh/chấp nhận. "rejected verdict" → "phán đoán bị bác bỏ". `verdicts` (trường) giữ nguyên. |
| 60 | D | clue | **manh mối** | Cơ chế game | |
| 61 | D | reveal / revealed / unresolved | **lật (mở)** / **đã lật** / **chưa xác định** | Cơ chế game | "initially revealed" → "được lật sẵn từ đầu". |
| 62 | D | card / character | **thẻ** / **nhân vật** | `UI` game | |
| 63 | D | solved card | **thẻ đã giải** | `UI` | |
| 64 | D | quote card / personal remark | **thẻ lời nhận xét** / **lời nhận xét cá nhân** | `QUOTE` hiển thị | Chi tiết trang trí, không phải ràng buộc logic. |
| 65 | D | stage / level / puzzle | **màn chơi** / **màn chơi** / **câu đố** | Game | *stage* và *level* đều dịch "màn chơi". Tên file như `level_01.json` và nhãn nút `Stage` giữ nguyên. |
| 66 | D | board / grid / cell | **bàn cờ** / **lưới** / **ô** | Game | "cell `ID`" → "mã ô". |
| 67 | D | row-major order | **thứ tự ưu tiên hàng** | Thứ tự ô | Trái sang phải, trên xuống dưới. |
| 68 | D | region | **vùng** | Manh mối | |
| 69 | D | neighbors / diagonal neighbors | **ô lân cận** / **ô lân cận theo đường chéo** | Vùng | Gồm đường chéo, không gồm ô trung tâm. |
| 70 | D | orthogonal connectivity | **tính liên thông trực giao (4 hướng)** | `CONNECTED` | Không tính đường chéo. |
| 71 | D | common neighbors | **ô lân cận chung** | Vùng | |
| 72 | D | boundary / corners | **biên** / **góc** | Vùng | |
| 73 | D | fixed (named) group | **nhóm cố định (có tên)** | Vùng | |
| 74 | D | cast / portrait / origin / profession | **dàn nhân vật** / **ảnh chân dung** / **xuất xứ** / **nghề nghiệp** | Hiển thị | Nhãn origin lấy nguyên văn theo tên file (ví dụ Chef). |
| 75 | D | hint / Auto Solve (mô tả tính năng) | **gợi ý** / **tự động giải** | Mô tả tính năng | Nhãn nút giữ nguyên (dòng 21). |
| 76 | D | public state / snapshot | **trạng thái công khai** / **ảnh chụp trạng thái (snapshot)** | Engine | |
| 77 | D | hidden data / hidden label | **dữ liệu ẩn** / **nhãn ẩn** | Ranh giới engine–agent | |
| 78 | D | timeout / deadline | **quá thời gian (timeout)** / **hạn chót** | SAT, `GUI` | Timeout không phải kết quả UNKNOWN. |
| 79 | D | stalled / stall | **bế tắc** | Giải tiến dần | Mã `STALLED` giữ nguyên. |
| 80 | D | headless | **chế độ không giao diện (headless)** | `CLI` | |
| 81 | D | background worker | **luồng nền** | `GUI` | |
| 82 | D | plugin / sandboxed | **plugin** / **chạy trong sandbox** | Agent | |
| 83 | D | fixture / negative test | **dữ liệu kiểm thử mẫu (fixture)** / **kiểm thử phản chứng (negative test)** | Kiểm thử | |
| 84 | D | smoke check | **kiểm tra nhanh (smoke check)** | Kiểm thử | |
| 85 | D | differential check | **kiểm thử đối chiếu** | Kiểm thử | |
| 86 | D | redundant clue / pruning | **manh mối dư thừa** / **loại bỏ (cắt tỉa)** | Sinh màn chơi | |
| 87 | D | benchmark / experiment | **đánh giá hiệu năng (benchmark)** / **thực nghiệm** | Mục 4.5 | |
| 88 | D | manifest / seed | **bảng kê (manifest)** / **hạt giống ngẫu nhiên (seed)** | Thực nghiệm | |
| 89 | D | acceptance (criteria) | **tiêu chí nghiệm thu** | TODO | |
| 90 | D | handoff | **bàn giao** | README / TODO | |
| 91 | D | Person 1–5 | **Thành viên 1–5** | Phân công | Thay bằng tên và MSSV khi có. |
| 92 | D | Section 4.x | **Mục 4.x** | Tham chiếu đề bài | |

## Quy ước áp dụng khi dịch

1. Nhãn nút giao diện (dòng 21) giữ nguyên tiếng Anh, lần đầu có chú thích tiếng Việt.
2. "Mệnh đề (clause)" dùng cho *clause* (dòng 29); *proposition* luôn viết "mệnh đề logic" (dòng 32).
3. "Tác tử" dùng cho *agent* (dòng 52); tên class `Agent` và thư mục `agent/` giữ nguyên.
4. "Phán đoán" cho lựa chọn của người chơi, "kết luận" cho kết quả hệ thống chứng minh hoặc chấp nhận (dòng 59).
5. *stage* và *level* đều dịch là "màn chơi" (dòng 65).