# 22 — Hai chỉ số đánh giá lộ trình: τ so mục lục và tỉ lệ vi phạm cạnh vàng

**Nguồn chân lý:** [`doc/va-a9-a10-do-thi-tot-va-lo-trinh-dung-duoc-spec.md`](../../doc/va-a9-a10-do-thi-tot-va-lo-trinh-dung-duoc-spec.md)
V9 · thí nghiệm E9–E11 ở [`report/nghien-cuu-a9-a10-kiem-dinh-va-lo-trinh.md`](../../report/nghien-cuu-a9-a10-kiem-dinh-va-lo-trinh.md) mục 10

**What to build:** hai con số nói được "lộ trình này đúng hay sai", chạy bằng một lệnh, không gọi mô hình.

**Blocked by:** vé 21 — nếu đo τ trên lộ trình còn phá hoà theo thứ tự chương thì đối chứng đã nhiễm và con số bỏ đi.

**Ai làm:** Claude (cùng chỗ với bộ chấm bộ vàng của vé 05).

**Status:** **xong ngày 2026-09-23** — hai chỉ số, lệnh `a8-roadmap-score`, 7 test với 7/7 đột biến bị bắt.
Đã chấm trên bộ vàng thật: lộ trình vi phạm 26,1% cạnh vàng ở `doc-1`, 15,2% ở `doc-2`, và **13/13 ca vi phạm
là cạnh A8 không tìm ra**. Còn lại E11 (bảng ablation) và chuyển ba script đo của vòng 36 vào repo.

## Vì sao cần

Hiện **chưa có chỉ số nào** đo lộ trình. Hai con số dưới đây tính được bằng code thuần và **không tốn thêm một lượt
gán nhãn nào** ngoài bộ vàng vốn đã phải làm.

Kendall τ so thứ tự trình bày có nền thực nghiệm: nó tương quan **r = 0,45** với phán đoán mạch lạc của người và
**r = −0,48** với thời gian đọc, trong khi đồng thuận giữa người với người chỉ **r = 0,56** — tức τ gần bằng người.
Và **không tìm thấy công trình nào** dùng τ để so lộ trình khái niệm do mô hình sinh với mục lục giáo trình gốc;
đó là chỗ đóng góp rõ nhất của đợt này.

Số đo hiện tại để làm mốc so: lộ trình trùng thứ tự sách ở **51,0%** số cặp trên `baocao-canhan`, **55,5%** trên
`xstk-ch3-1`. Và trên bộ vàng thử nghiệm, **11/62 cạnh vàng bị lộ trình máy xếp ngược**.

## Việc phải làm

- [ ] **Kendall τ so thứ tự trình bày.** Trên mọi cặp khái niệm ở hai stage khác nhau **và** có thứ tự trình bày
      khác nhau: `τ = (thuận − nghịch) / (thuận + nghịch)`. Trả kèm **số cặp so được** và **số cặp bị loại vì hoà**.
- [ ] Ghi kèm cảnh báo của chính tác giả chỉ số: phép đo dùng **một** văn bản tham chiếu, trong khi có thể có nhiều
      thứ tự chấp nhận được.
- [ ] **Tỉ lệ vi phạm cạnh vàng.** Với mỗi cạnh vàng `p → t`, lộ trình vi phạm nếu xếp `p` **sau** `t`. Trả tỉ lệ
      **và danh sách cặp vi phạm kèm tên khái niệm** — con số không đủ, phải đọc được ca sai.
- [ ] Cả hai chạy được trên **hai tập cạnh** — cạnh vàng và cạnh máy — trên **cùng tập khái niệm**. Chỉ so hai con
      số ấy mới tách được "giáo trình sắp xếp kém" khỏi "đồ thị của ta nhiễu". Mốc trên bộ vàng thử nghiệm:
      vàng τ **+0,803**, máy τ **+0,603**.
- [ ] Đặt trong tầng domain cùng chỗ bộ chấm hiện có, là **hàm thuần**, không đọc đĩa, không gọi mô hình.
- [ ] Lệnh CLI cho ra cả hai, chạy được khi **chặn mạng**.
- [ ] **E11 — bảng ablation** cách gom stage: các biến thể × `W ∈ {4, 6, 8, 12}`, báo số stage, phân bố cỡ stage,
      τ, tỉ lệ vi phạm cạnh vàng, số cạnh nằm gọn trong stage. Đây là thứ thay cho mọi viện dẫn tâm lý học về con
      số 5–8 ở vé 21.
- [ ] Chuyển ba script đo của vòng 36 (`do_a9_a10_v2.py`, `mo_phong_stage.py`, `vang_vs_may.py`, hiện trong thư mục
      nháp) thành mã có test trong repo — hiện chúng không tái lập được ngoài phiên.
- [ ] Test ở seam đã có (`tests/unit/domain/test_gold_scoring.py`).

## Ca test phải có

- τ của lộ trình **trùng khít** thứ tự sách bằng **1**; đảo ngược hoàn toàn bằng **−1**.
- Cặp hoà bị loại khỏi mẫu số **và** được đếm riêng.
- Tỉ lệ vi phạm cạnh vàng bằng **0** khi lộ trình tôn trọng mọi cạnh vàng.
- Danh sách vi phạm nêu **đúng cặp**, không chỉ đúng số lượng.
- Cạnh vàng có đầu nằm ngoài tập khái niệm được xử lý tường minh, không âm thầm bỏ.

Đột biến tối thiểu: tính cả cặp hoà vào mẫu số; đảo dấu τ; coi "cùng stage" là vi phạm; bỏ danh sách chỉ trả con số;
bỏ qua cạnh vàng có đầu ngoài phạm vi mà không báo.
