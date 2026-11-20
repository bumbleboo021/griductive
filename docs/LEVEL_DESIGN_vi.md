# Thiết kế các màn chơi Griductive có thể giải được

Cập nhật triển khai sau khi mở rộng màn chơi: Bộ nạp dữ liệu và bộ phân tích phát triển (tạm thời) hiện đã hỗ trợ `COUNT_COMPARE`, `CONNECTED` và `IMPLIES`, cùng với các vùng ô lân cận chung, vùng theo hướng, vùng toàn bộ lưới, vùng biên và vùng góc. Bảy màn chơi sử dụng các tính năng này đã được bổ sung và xác thực. Xem `LEVELS.md` và `INTEGRATION.md` để biết danh mục và lược đồ hiện tại. Việc hỗ trợ `CNF` (dạng chuẩn hội) / `DPLL` vẫn là nhiệm vụ tích hợp của thành viên nhóm.

## Nguồn tham khảo nghiên cứu

Tài liệu hướng dẫn này tách biệt hành vi đã được ghi nhận của trò chơi khỏi bản triển khai đề xuất cho kho mã nguồn này. Tài liệu không tuyên bố tái tạo lại bộ sinh màn chơi gốc.

- [Hướng dẫn cách chơi và bảng thuật ngữ chính thức](https://knotwise.games/games/griductive/how-to-play)
- [Hướng dẫn chiến thuật chính thức](https://knotwise.games/games/griductive/strategy)
- [Giải thích của nhà phát triển về cách sinh câu đố](https://dev.to/_a80b26c075279295b18e9/what-is-griductive-and-how-the-puzzles-are-made-24f5)

Bài viết của nhà phát triển mô tả quá trình chọn một lời giải, thu thập các manh mối ứng viên đúng, lựa chọn các ràng buộc, kiểm tra tính duy nhất, ước tính độ khó và xây dựng các gợi ý. Bài viết cũng mô tả một quy trình kiểm tra giải tiến dần độc lập. Đây là một tài liệu tham khảo hữu ích về mặt kiến trúc, không phải mã nguồn hay tập dữ liệu màn chơi được xuất sẵn.
[Nguồn](https://dev.to/_a80b26c075279295b18e9/what-is-griductive-and-how-the-puzzles-are-made-24f5)

## Từ vựng manh mối gốc so với mức độ hỗ trợ hiện tại

Bảng thuật ngữ định nghĩa các hàng, cột, ô lân cận bao gồm cả đường chéo, cạnh/góc, vùng nằm giữa, ô lân cận chung, các hướng liền kề, số lượng chính xác/tối thiểu, số lượng lẻ, phép so sánh và so sánh nhất theo nhóm. Tính liên thông sử dụng các bước trực giao (4 hướng). Các phát biểu vẫn luôn đúng ngay cả khi được nói ra bởi một tội phạm.
[Nguồn](https://knotwise.games/games/griductive/how-to-play)

Hướng dẫn chiến thuật thảo luận tường minh về các manh mối kết hợp thành viên và số lượng, vùng giao nhau, hạn mức số lượng, các nhóm liên thông và tính chẵn lẻ (parity) lẻ. Tài liệu cho biết tính chẵn lẻ chẵn có tồn tại trong engine nhưng chưa được phát hành trong các câu đố hiện tại. Định dạng câu đố hằng ngày hiện tại của trò chơi có kích thước 4 cột nhân 5 hàng, vì vậy các kích thước lưới hình vuông của chúng ta là một sự điều chỉnh riêng cho dự án.
[Nguồn](https://knotwise.games/games/griductive/strategy)

Dưới đây là các ví dụ tự tạo nhằm minh họa cho các họ manh mối đó, không phải là các phát biểu sao chép từ câu đố có sẵn. Các tên nội bộ là tên lược đồ được đề xuất, không phải là các `API` (giao diện lập trình ứng dụng) chính thức.

| Họ manh mối | Ví dụ | Hỗ trợ trong kho mã nguồn này |
| --- | --- | --- |
| Số lượng chính xác | Có chính xác 2 tội phạm ở hàng 1. | `EXACTLY` |
| Số lượng bằng không | Không có tội phạm nào ở cột C. | `EXACTLY` với số lượng 0 |
| Số lượng tối thiểu | Có ít nhất 1 tội phạm trong số A1, B1, C1. | `AT_LEAST` |
| Số lượng ô lân cận | Có chính xác 1 tội phạm là ô lân cận của B2. | `EXACTLY` với vùng ô lân cận |
| Số lượng vùng giao | Có chính xác 1 tội phạm vừa nằm ở hàng 1 vừa là ô lân cận của B2. | Đếm số lượng trên một vùng giao nhau |
| Số lượng lẻ | Hàng 2 chứa một số lẻ tội phạm. | `ODD` |
| Thành viên và số lượng | A1 là tội phạm, và có chính xác 2 tội phạm là ô lân cận của B2. | Cần một manh mối ghép hoặc hai ràng buộc; không thể biểu diễn dưới dạng một manh mối đơn lẻ trên thẻ theo cấu trúc hiện tại |
| So sánh vùng | Hàng 1 chứa nhiều tội phạm hơn hàng 2. | `COUNT_COMPARE` trong bộ phân tích phát triển (tạm thời) |
| Nhóm liên thông | Các tội phạm ở cột B tạo thành một nhóm liên thông trực giao (4 hướng). | `CONNECTED` trong bộ phân tích phát triển (tạm thời) |
| Cực đại nghiêm ngặt | Hàng 1 có nhiều tội phạm hơn mọi hàng khác. | Chưa được triển khai |
| Số lượng khớp duy nhất | Trong số các cột, chỉ duy nhất cột B có chính xác 2 tội phạm. | Chưa được triển khai |

Mã nguồn hiện tại còn chấp nhận thêm `FACT`, `SAME`, `DIFFERENT`, `AT_MOST` và `EVEN`. Đây là các tính năng mở rộng của dự án; sự hiện diện của chúng trong lược đồ của chúng ta không đồng nghĩa với việc chúng là các mẫu câu độc lập trong các trò chơi hằng ngày hiện tại. Đối với các màn chơi thiết kế theo phong cách bản gốc, hãy ưu tiên các manh mối đếm số lượng, ô lân cận, vùng giao nhau và `ODD` trước khi triển khai các họ manh mối phức tạp hơn.

Các phân biệt quan trọng về mặt ngữ nghĩa:

- Một thành viên được chỉ định tên kết hợp với một số lượng là một phép hội (conjunction). Một tội phạm được chỉ định tên với tư cách thành viên bắt buộc phải thuộc về vùng được đếm; việc chỉ mã hóa riêng số lượng sẽ làm mất thông tin.
- Một phát biểu đưa ra tổng số lượng và số lượng của vùng con đòi hỏi cả hai ràng buộc. Ví dụ, 3 tội phạm trong R với 1 tội phạm trong phần giao giữa R và S khác với việc chỉ đếm phần giao nhau.
- Việc đếm số người vô tội có thể được quy đổi sang đếm số lượng tội phạm trên một vùng cố định: có chính xác k người vô tội đồng nghĩa với việc có chính xác `len(region) - k` tội phạm.
- Sử dụng các mã ô (`ID`) cố định trong các ràng buộc; tên nhân vật chỉ là thành phần thay thế phục vụ hiển thị.
- Tổng số lượng của các vùng dùng chung cần có một quy tắc hợp/khử trùng lặp tường minh trong lược đồ của chúng ta.
- Khi triển khai tính liên thông, hãy định nghĩa tường minh hành vi đối với các nhóm rỗng; yêu cầu số lượng dương nếu câu dự định khẳng định có người tồn tại.

Đây là các quy tắc triển khai nhằm tránh các phép mã hóa mơ hồ, không phải là tuyên bố rằng mọi cách diễn đạt nêu trên đều đã được Bộ nạp dữ liệu hỗ trợ.

## Ba bước kiểm tra tính đúng đắn độc lập

Một màn chơi được đề xuất phải vượt qua cả ba bước:

1. **Tính đúng của manh mối:** mỗi manh mối đều đúng dưới lời giải đầy đủ được lưu trữ.
2. **Tính duy nhất khi có đủ manh mối:** tất cả các manh mối, cùng với các trạng thái đã biết ban đầu, chỉ chấp nhận duy nhất một phép gán đầy đủ cho các biến trạng thái chính.
3. **Khả năng giải tiến dần:** chỉ sử dụng các thẻ được lật ban đầu và các trạng thái/manh mối được chứng minh sau đó, luôn tồn tại một nước đi bắt buộc khả dụng cho đến khi mọi thẻ đều được lật.

Chỉ riêng tính đúng của manh mối là chưa đủ. Tính duy nhất khi có đủ manh mối cũng vậy. Ví dụ, một thẻ ban đầu có thể lật mở một hằng đúng (tautology) trong khi mọi manh mối hữu ích đều vẫn bị khóa; câu đố hoàn chỉnh có thể có nghiệm duy nhất, nhưng lại không có nước đi hợp lệ nào ở bước đầu tiên.

Đối với biến Boolean Ci mang ý nghĩa là tội phạm, một kết luận được chứng minh thông qua các truy vấn sau:

```text
if SAT(KB) is false:
    INCONSISTENT
elif SAT(KB AND NOT Ci) is false:
    Ci is CRIMINAL
elif SAT(KB AND Ci) is false:
    Ci is INNOCENT
else:
    Ci is UNKNOWN
```

Hãy kiểm tra tính nhất quán cơ sở trước tiên: một `KB` (cơ sở tri thức) mâu thuẫn không thể thiết lập các kết luận hữu ích. Quá thời gian (timeout) là một kết quả tách biệt và tuyệt đối không bao giờ được coi là bằng chứng suy diễn hay trạng thái `UNKNOWN`.

Để kiểm tra tính duy nhất, hãy giải `KB` chứa đầy đủ manh mối một lần, sau đó chặn phép gán biến chính của mô hình (phép gán thỏa mãn) đó và giải lại:

```text
block = OR( NOT Ci if model[Ci] else Ci, for every primary Ci )
unique iff SAT(full_KB) and UNSAT(full_KB AND block)
```

Không chặn các biến phụ trợ: các phép gán biến phụ trợ khác nhau có thể cùng mã hóa cho một lời giải nhân vật giống nhau. Đồng thời, hãy đối chiếu mô hình đầu tiên với lời giải đã lưu trữ.

## Quy trình sinh màn chơi được đề xuất cho dự án này

Đây là một đề xuất thiết kế thực tế, không phải một bộ sinh màn chơi đã được triển khai.

1. Chọn kích thước bàn cờ và một lời giải tội phạm/vô tội được tạo ngẫu nhiên từ một hạt giống (seed). Tránh các bàn cờ có toàn bộ trạng thái giống hệt nhau cho tập màn chơi ban đầu; hãy chọn một tỷ lệ pha trộn hợp lý.
2. Liệt kê các hàng, cột, vùng ô lân cận và các vùng giao nhau hữu ích. Danh sách ô tường minh có thể biểu diễn các hình dạng cố định khác, nhưng nên ưu tiên các nhóm hình học dễ đọc.
3. Tính toán số lượng tội phạm thực tế của từng vùng và xây dựng các manh mối ứng viên đúng thuộc loại `EXACTLY`, `AT_LEAST`, `AT_MOST` và `ODD`. Loại bỏ các hằng đúng rỗng và các cận tối thiểu/tối đa tầm thường. Tránh biến mọi manh mối thành `FACT`.
4. Chọn một hoặc nhiều thẻ được lật sẵn từ đầu. Trạng thái và manh mối của chúng là tri thức khởi đầu duy nhất. Hãy dành một manh mối mở đầu giàu thông tin cho các thẻ này.
5. Gán các manh mối ứng viên cho chủ sở hữu thẻ và mô phỏng quá trình giải công khai. Khi một thẻ mới được chứng minh, manh mối của thẻ đó sẽ trở nên khả dụng. Ưu tiên các phép gán manh mối tạo ra một lộ trình suy diễn liên tục.
6. Nếu rơi vào bế tắc, hãy sửa đổi một manh mối trên thẻ đã khả dụng, tăng số lượng thẻ được lật ban đầu, hoặc loại bỏ lần thử này. Việc chỉ thêm một manh mối hữu ích vào một thẻ vẫn đang ẩn sẽ không thể khai thông trạng thái hiện tại. Khởi động lại quá trình xác thực sau mỗi lần sửa đổi.
7. Chạy ba bước kiểm tra tính đúng đắn. Lưu lại vết suy diễn cho thấy những manh mối công khai nào đã chứng minh cho từng nước đi. Lưu hạt giống ngẫu nhiên và kết quả xác thực cùng với siêu dữ liệu của màn chơi.
8. Thử loại bỏ/thay thế các ràng buộc dư thừa hoặc giảm số lượng thẻ được lật ban đầu. Sau mỗi thay đổi, hãy chạy lại các bước kiểm tra tính đúng của manh mối, tính duy nhất và khả năng giải tiến dần.
9. Đo lường độ khó và cho người chơi thử nghiệm câu đố trước khi phát hành chính thức.

Mã giả đề xuất:

```python
for attempt in range(max_attempts):
    solution = sample_solution(size, rng)
    pool = true_readable_clues(solution, supported_templates)
    puzzle = assign_clues_to_cards(pool, solution, initial_reveals, rng)
    if not all_clues_true(puzzle):
        continue
    if not full_clue_solution_is_unique(puzzle):
        continue
    trace = solve_with_progressive_reveals(puzzle)
    if trace.completed:
        return puzzle, trace
raise GenerationError("No validated puzzle within attempt/time budget")
```

Các hàm trợ giúp ở trên vẫn cần được triển khai. Đừng nhầm lẫn lệnh `--headless` hiện có với một trình xác thực tính duy nhất đầy đủ: lệnh này minh họa vòng lặp lật mở công khai, chứ không xác thực độc lập tính đúng của mọi manh mối đang ẩn.

## Một ví dụ nhỏ về thiết kế suy diễn

Giả sử một bàn cờ 3x3 bắt đầu với A1 được biết là vô tội. Manh mối của A1 cho biết cột C không có tội phạm nào. Điều đó ngay lập tức ép buộc C1, C2 và C3 phải là vô tội.

Gán cho C3 một manh mối nói rằng có chính xác một tội phạm là ô lân cận của C3. Các ô lân cận của C3 gồm B2, C2 và B3. Sau khi C2 đã được biết là vô tội, chỉ riêng manh mối này vẫn để lại hai khả năng; nó chưa thể chứng minh được B2 hay B3.

Để tiếp tục, hãy cung cấp một ràng buộc khả dụng khác giúp phân biệt hai ô đó, hoặc chọn B3 làm một thẻ vô tội ban đầu bổ sung. Khi đó B2 bắt buộc phải là tội phạm. Manh mối mới được lật của B2 có thể tiếp tục ràng buộc vùng tiếp theo. Tiếp tục thiết kế cho đến khi mọi trạng thái đều bị ép buộc xác định, sau đó chạy toàn bộ quy trình xác thực.

Ví dụ này chỉ nhằm minh họa các mối quan hệ phụ thuộc. Đây không phải là một câu đố chín thẻ hoàn chỉnh và không nên được lưu dưới dạng một màn chơi đã xác thực nếu thiếu các manh mối và bước kiểm tra còn lại.

## Độ khó ngoài yếu tố kích thước bàn cờ

Đối với tập màn chơi của chúng ta, hãy ghi nhận:

- Số lượng thẻ được lật ban đầu và tổng số nước đi được chứng minh.
- Các nước đi bắt buộc khả dụng ở mỗi bước; việc có nhiều nước đi bắt buộc đồng thời thường cho thấy một khởi đầu rộng mở và dễ dàng.
- Liệu các bước suy diễn có đòi hỏi phải kết hợp nhiều manh mối đã lật hay không.
- Độ sâu phụ thuộc, sự chồng lấp vùng và tính đa dạng của các họ manh mối.
- Thời gian chạy của bộ giải và số quyết định (decisions), được ghi nhận tách biệt với độ khó đối với người chơi.

Đây là các phép đo được đề xuất cho dự án. Một truy vấn `SAT` chạy nhanh không nhất thiết đồng nghĩa với việc người chơi thấy manh mối đó dễ. Không được trình bày một điểm số chưa qua hiệu chuẩn như là công thức tính độ khó chính thức của Griductive.

## Ảnh chân dung ngẫu nhiên và tính an toàn của manh mối

`GUI` (giao diện đồ họa) của chúng ta ngẫu nhiên hóa tên và xuất xứ của nhân vật trong khi vẫn bảo toàn các manh mối dựa trên ô. Điều này an toàn đối với các ràng buộc hiện tại. Một manh mối trong tương lai về nhóm nghề nghiệp hoặc xuất xứ sẽ trở nên không an toàn nếu việc thay đổi dàn nhân vật làm biến đổi thành viên của nhóm đó.

Đối với các manh mối như vậy, hãy khóa cố định dàn nhân vật theo từng câu đố hoặc sinh lại/xác thực lại các vùng manh mối sau khi phân vai dàn nhân vật. Giữ các tham chiếu tới một nhân vật được chỉ định tên dưới dạng mã ô cố định và chỉ thay thế bằng tên hiển thị hiện tại khi kết xuất lên giao diện.

## Đề xuất triển khai tiếp theo

Hãy bắt đầu với một trình xác thực màn chơi ngoại tuyến, sau đó là một bộ sinh màn chơi có hạt giống ngẫu nhiên sử dụng `EXACTLY`, `AT_LEAST`, đếm số lượng ô lân cận, đếm số lượng vùng giao nhau và `ODD`. Xác thực các trường hợp 3x3 trước, sau đó đến 4x4 và 5x5. Giữ sẵn sáu mẫu phân công cho các bài kiểm thử độ bao phủ. Chỉ bổ sung các manh mối so sánh, manh mối ghép và manh mối tính liên thông khi cả bộ đánh giá độc lập lẫn luồng xử lý `CNF`/`DPLL` đều có thể xử lý chúng một cách chính xác.

Bộ nạp dữ liệu hiện tại chỉ kiểm tra cấu trúc chứ chưa kiểm tra đầy đủ ba thuộc tính đúng đắn. Tệp `engine/reference.py` cung cấp một bộ phân tích trạng thái công khai tạm thời. Tác tử cuối cùng của thành viên nhóm cần cung cấp luồng xử lý dựa trên `DPLL` phục vụ đánh giá; các công cụ sinh và xác thực màn chơi có thể sử dụng luồng xử lý đó thông qua một bộ chuyển đổi (adapter) được định nghĩa rõ ràng.