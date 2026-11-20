# Tùy chỉnh `UI` (giao diện người dùng)

Mỗi màn chơi và mỗi lần chơi lại đều bắt đầu với nhân vật ở góc trên bên trái được chọn sẵn. Các phím `WASD` và phím mũi tên di chuyển vùng chọn từng ô một mà không mở cửa sổ bật lên (popup). Các cạnh của bàn cờ sẽ chặn di chuyển. Phím `Enter` mở các lựa chọn của một thẻ chưa xác định với lựa chọn `Innocent` (vô tội) được chọn sẵn. Phím `A`/Mũi tên trái chọn `Innocent`, `D`/Mũi tên phải chọn `Criminal` (tội phạm), `S`/Mũi tên xuống chọn `Cancel` (hủy), và `W`/Mũi tên lên quay lại từ `Cancel` về `Innocent`. Phím `Enter` để xác nhận; phím `Escape` để đóng cửa sổ bật lên. Thao tác nhấp chuột vẫn mở thẻ và kích hoạt các lựa chọn như bình thường. Việc điều hướng trên thẻ đã giải sẽ chọn manh mối tương ứng của thẻ đó trong bảng bên cạnh. Quá trình điều hướng sẽ chờ trong khi tính năng phân tích hoặc `Auto Solve` (tự động giải) đang hoạt động, và bị chặn bởi các hộp thoại `Stage` (màn chơi), `Tracks` (danh sách nhạc), trợ giúp (`Help`) và hộp thoại thông báo bác bỏ.

Trình chọn `Stage` hỗ trợ cuộn bằng con lăn chuột và có thanh cuộn kéo thả ở cạnh phải. Giữ nút chuột trái trên con trượt (thumb) và kéo lên hoặc xuống. Nhấp vào rãnh thanh cuộn (track) sẽ nhảy danh sách về phía vị trí đó. Thanh cuộn sẽ bị ẩn khi tất cả màn chơi hiển thị vừa vặn trên màn hình.

Các manh mối đã lật dùng chung một khung bảng có viền với vùng cuộn được cắt gọn và một chỉ báo vị trí. Thao tác từ con lăn chuột và bàn di chuột (trackpad) sẽ cuộn mượt mà khi con trỏ nằm bên trong khung bảng đó. `CLUE_SCROLL_STEP` thiết lập số pixel cho mỗi nấc cuộn của con lăn và `CLUE_SCROLL_TIME_MS` điều khiển thời gian làm mượt chuyển động (easing). Thời gian làm mượt càng thấp thì chuyển động dừng lại càng nhanh.

Sử dụng nút **`Tracks`** bên cạnh `Music On/Off` (Bật/Tắt nhạc) để chọn nhạc. Trình chọn sẽ liệt kê các tệp `WAV`, `OGG`, `MP3` (bao gồm cả `VBR`) và `FLAC` nằm trực tiếp bên trong thư mục `assets/sounds/`. Việc chọn một bản nhạc sẽ phát bản nhạc đó và giữ nguyên lựa chọn trong suốt phiên chơi hiện tại. Đóng và mở lại `Tracks` sẽ làm mới danh sách tệp. Nhấn `Escape` hoặc `Close` (Đóng) để tắt hộp thoại này. Các tệp `M4A` sẽ không hiển thị trong danh sách. Hãy thêm phiên bản `MP3` của bản nhạc nếu bạn muốn sử dụng. Công tắc bật/tắt nhạc sẽ dừng hoặc phát lại bản nhạc đã chọn.

Điền thông tin nguồn gốc và giấy phép cho phần hình ảnh nghệ thuật (artwork), phông chữ và âm nhạc của bạn vào tệp `assets/ATTRIBUTION.md`. Lưu trữ các tệp giấy phép đi kèm trong thư mục `assets/licenses/`.

Các nút bấm, các hàng màn chơi và thẻ nhân vật đều có hiệu ứng chuyển động khi di chuột qua (hover) với độ nâng nhẹ và đường viền nổi bật. Bạn có thể điều chỉnh `HOVER_DURATION_MS` và `HOVER_LIFT` trong tệp `config.py`. Phản hồi khi di chuột áp dụng cho cửa sổ bật lên đang hoạt động và bỏ qua các nút điều khiển bị vô hiệu hóa.

**`Stage`** mở danh sách các màn chơi có đặt tên. Mỗi tệp `JSON` đi kèm hiện có một trường gốc `name`, chẳng hạn như `"name": "3x3 - Quiet Rows"`. Trình chọn và tiêu đề bàn cờ sẽ sử dụng trường này. Các tệp `JSON` cũ hơn sử dụng trường `title` vẫn có thể tải bình thường. Đặt các tệp màn chơi mới vào thư mục `data/puzzles/`. Cuộn danh sách để xem thêm các màn chơi khác, chọn một màn để chơi hoặc đóng bằng phím `Escape`.

Nút **`?`** ở góc trên bên phải mở bảng hướng dẫn cách chơi. Nhấn `Escape` hoặc `Got it` (Đã hiểu) để đóng bảng này. Việc mở bảng trợ giúp sẽ tạm dừng `Auto Solve` sau khi hoàn tất bất kỳ quá trình phân tích nào đang diễn ra.

**`Music Off / Music On`** bật/tắt đoạn nhạc nền lặp nguyên bản đi kèm. Nhạc mặc định tắt khi khởi động và sẽ tiếp tục phát xuyên suốt khi chuyển đổi giữa các màn chơi nếu được bật. Đặt `MUSIC_FILE` thành tên một tệp trong `assets/sounds/` và `MUSIC_VOLUME` thành một giá trị từ 0 đến 1. Tệp mặc định `ambient.wav` là một đoạn lặp tổng hợp dài 16 giây được tạo riêng cho dự án này. Nếu thiết bị âm thanh hoặc tệp nhạc không khả dụng, bảng thông báo sẽ báo lỗi.

Nhấp vào một nhân vật chưa xác định để mở cửa sổ bật lên chọn phán đoán `Criminal`/`Innocent`. Nhấn `Cancel`, `Escape` hoặc nhấp ra bên ngoài sẽ đóng cửa sổ này mà không làm thay đổi trạng thái trò chơi. Đối với các thẻ đã giải, thao tác nhấp sẽ chọn manh mối của thẻ đó. Các nút phán đoán cố định và dòng chữ `Selected` (Đã chọn) đã được loại bỏ. Các nút `Load` (tải màn chơi)/`Restart` (chơi lại)/`Hint` (gợi ý)/`Auto Solve` hiện tạo thành một nhóm điều khiển gồm hai hàng nằm bên dưới bảng manh mối; bảng thông báo nằm ngay bên dưới nhóm nút này.

Chỉnh sửa `CHARACTER_QUOTES` trong tệp `griductive/ui/config.py` để định nghĩa các lời nhận xét cá nhân cho những thẻ có manh mối logic đã được lược bỏ một cách an toàn. Một câu nhận xét sẽ được chọn cho mỗi cặp thẻ/dàn nhân vật và giữ nguyên ổn định qua các khung hình cũng như khi nhấn `Restart`. Các lời nhận xét không thể tiết lộ bất kỳ manh mối ẩn nào và không ảnh hưởng đến bộ giải (solver). Chúng được gắn nhãn `Personal remark` (Lời nhận xét cá nhân) trong bảng bên cạnh. Danh sách nhận xét trống sẽ mặc định hiển thị thành `...`.

`RANDOMIZE_CAST = True` sẽ chọn một dàn ảnh chân dung nhân vật mới, không trùng lặp mỗi khi `GUI` (giao diện đồ họa) tải một màn chơi. Các nhân vật được gán vào các ô theo thứ tự ngẫu nhiên; thao tác `Restart` vẫn giữ nguyên cách phân bổ này. Nếu không có đủ biểu tượng (icon), dàn nhân vật đã lưu của câu đố sẽ được sử dụng. Đặt tùy chọn này thành `False` để luôn sử dụng tên nhân vật trong tệp `JSON`. Các bài đánh giá hiệu năng (benchmark) ở chế độ không giao diện (headless) luôn giữ nguyên dàn nhân vật gốc trong `JSON` để đảm bảo tính tái lập. Chỉ có tên và xuất xứ thay đổi; lời giải, các tham chiếu manh mối, mã ô (`ID`) và các ô được lật sẵn từ đầu vẫn giữ nguyên.

Các manh mối hiển thị sẽ ánh xạ mã ô sang tên nhân vật hiện tại: `B1 is innocent` trở thành `Ayaka is innocent`. Đặt `SHOW_CELL_IN_CLUES = True` để hiển thị dưới dạng `Ayaka (B1)`. Các manh mối có cấu trúc bên dưới vẫn tham chiếu đến các mã ô cố định dành cho bộ giải.

Các thẻ hiện sử dụng phần tiêu đề chứa tên/xuất xứ cùng một ảnh chân dung lớn. Sau khi có kết luận đã được chứng minh, ảnh chân dung sẽ thu nhỏ lại và di chuyển lên góc trên bên trái; manh mối mới được công khai của thẻ đó sẽ hiện rõ dần bên dưới phần tiêu đề. Các thẻ được lật sẵn từ đầu sẽ bắt đầu ngay ở bố cục hoàn chỉnh. Nhấp vào một thẻ đã giải sẽ chọn và cuộn tới toàn bộ manh mối của thẻ đó trong bảng bên cạnh; các manh mối dài trên thẻ sẽ kết thúc bằng dấu ba chấm. Thao tác `Restart` và `Load` sẽ đặt lại trạng thái hoạt ảnh.

Các tùy chọn điều khiển bổ sung trong `config.py`:

```python
REVEAL_DURATION_MS = 650
SOLVED_PORTRAIT_SIZE = {3: 36, 4: 28, 5: 24}
BACKGROUND_FILE = 'Background · Genshin Impact.png'
BACKGROUND_DIM = 155
```

Đặt thời lượng về 0 để có hiệu ứng lật mở tức thì. Thời lượng càng lớn thì quá trình chuyển tiếp diễn ra càng chậm. Manh mối xuất hiện trong 35% thời gian cuối của quá trình chuyển tiếp; `Auto Solve` sẽ chờ hết thời gian chuyển tiếp cộng thêm 150 ms giữa các nước đi được chấp nhận. Tên tệp hình nền được tính tương đối theo thư mục `assets/images/`; hình ảnh sẽ lấp đầy cửa sổ trong khi vẫn giữ nguyên tỷ lệ khung hình và cắt bớt các cạnh thừa. Giá trị làm tối (dim) chạy từ 0 (sáng rõ) đến 255 (đen hoàn toàn).

Chỉnh sửa tệp `griductive/ui/config.py`, lưu lại, sau đó đóng và khởi động lại trò chơi:

```powershell
.\.venv-win\Scripts\python.exe main.py
```

## Ảnh chân dung và khung nhân vật

```python
PORTRAIT_SIZE = {3: 110, 4: 76, 5: 52}
```

Các khóa (key) là kích thước bàn cờ (3x3, 4x4, 5x5). Các giá trị (value) là chiều rộng/chiều cao mong muốn của biểu tượng tính bằng pixel. Tăng giá trị để có biểu tượng lớn hơn hoặc giảm giá trị để biểu tượng nhỏ lại. `UI` sẽ căn giữa các ảnh chân dung chưa xác định và giới hạn kích thước tối đa của chúng theo chiều rộng bên trong thẻ cũng như chiều cao khả dụng bên dưới phần tên/xuất xứ. Một khi đã chạm mức giới hạn này, việc chỉ tăng giá trị cấu hình sẽ không còn tác dụng.

Kích thước thẻ được tính toán dựa trên kích thước bàn cờ:

```python
cell_width = (BOARD_WIDTH - CARD_GAP * (size - 1)) // size
cell_height = (BOARD_HEIGHT - CARD_GAP * (size - 1)) // size
```

`CARD_GAP` thay đổi khoảng cách giữa các thẻ. `CARD_PADDING` thay đổi khoảng đệm bên trong thẻ. `CARD_RADIUS` thay đổi độ bo tròn các góc. `PORTRAIT_TOP` định vị ảnh chân dung chưa xác định nằm bên dưới tên và xuất xứ. `STATUS_HEIGHT` dành sẵn không gian cho dòng trạng thái ở dưới cùng sau khi có kết luận. `ORIGIN_GAP` và `ORIGIN_MIN_WIDTH` là các thiết lập cũ từ bố cục thẻ đặt cạnh nhau trước đây và không còn ảnh hưởng đến các thẻ mới.

`BOARD_X` và `BOARD_Y` định vị toàn bộ lưới. Hãy giữ cạnh phải của lưới nằm ở vị trí nhỏ hơn hoặc bằng 758 và cạnh dưới nằm ở vị trí nhỏ hơn hoặc bằng `MESSAGE_Y - 20`. Bàn cờ lấp đầy phía bên trái với các thẻ dạng dọc. `WINDOW_SIZE = (1180, 1020)` xác định vùng vẽ logic và `Pygame` sẽ tự động co giãn cửa sổ cho vừa với màn hình hiển thị. `MESSAGE_Y` định vị phần thông báo phản hồi bên dưới bàn cờ. Tọa độ chuột được ánh xạ tương ứng vào vùng vẽ logic.

## Phông chữ, màu sắc và hình ảnh nghệ thuật

Trong tệp `config.py`, hãy thay đổi `FONT_SIZE`, `SMALL_FONT_SIZE`, `TINY_FONT_SIZE` và `HEADING_FONT_SIZE`. Tên các tệp phông chữ (`BODY_FONT`, `HEADING_FONT`) được tính tương đối theo thư mục `assets/fonts/`. Phông chữ lớn hơn có thể đòi hỏi nhiều không gian hơn ở phần tiêu đề thẻ hoặc trên các nút bấm.

Màu sắc là các bộ giá trị màu RGB (tuple) gồm ba giá trị từ 0 đến 255. Hãy chỉnh sửa `BG`, `PANEL`, `TEXT`, `MUTED`, `ACCENT`, `CRIMINAL_CARD`, `INNOCENT_CARD`, `HIGHLIGHT`, `BUTTON` hoặc `BUTTON_DISABLED` ngay trong cùng tệp đó.

Ảnh chân dung được lưu trong thư mục `assets/images/Character Icons/` và khớp với tên nhân vật trong câu đố. Định dạng tên tệp: `Name · Origin · Game.png`. Thông tin xuất xứ được lấy từ phân đoạn thứ hai của tên tệp. Hãy thêm tên nhân vật khớp với tên tệp vào tệp `JSON` của câu đố để sử dụng biểu tượng tương ứng. Việc gán ảnh chân dung mang tính tất định (deterministic); việc thay đổi trạng thái không làm thay đổi ảnh chân dung đã gán.

## Bố cục và tương tác khác

`character_card.py` kết xuất nội dung thẻ và nội suy hoạt ảnh lật mở. `assets.py` lưu đệm (cache) các bề mặt ảnh chân dung và tải hình nền. `window.py` chứa các hàm `draw()` (bàn cờ, bảng manh mối, các nút điều khiển), `draw_picker()` (cửa sổ bật lên `Load`), `button()` (kiểu dáng nút bấm), `event()` (xử lý đầu vào) và `action()` (các hành động). Để tạo một nút bấm mới, hãy thêm lệnh gọi vẽ nút đó trong `draw()` và hành vi xử lý trong `action()`; hàm `button()` sẽ tự động đăng ký vùng hình chữ nhật có thể nhấp chuột của nút đó.

Sau khi chỉnh sửa bố cục, hãy kiểm tra tất cả các kích thước bàn cờ:

```powershell
.\.venv-win\Scripts\python.exe main.py --puzzle data/puzzles/3x3/level_01.json
.\.venv-win\Scripts\python.exe main.py --puzzle data/puzzles/4x4/level_01.json
.\.venv-win\Scripts\python.exe main.py --puzzle data/puzzles/5x5/level_01.json
.\.venv-win\Scripts\python.exe -m pytest tests/integration/test_ui.py -q
```