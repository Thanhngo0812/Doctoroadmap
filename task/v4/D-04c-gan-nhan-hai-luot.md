# D-04c — Gán nhãn cạnh ngược hai lượt độc lập

**Nguồn chân lý:** [đặc tả D-04](D-04-dac-ta-nhan-canh-nguoc.md), bước 3 và mục "Kiểm chất lượng".
**Ai:** **chủ dự án**, bằng agentic · Claude kiểm định dạng · **Chi phí mô hình:** do chủ dự án chọn dịch vụ agentic · **Chặn bởi:** D-04a, D-04b ·
**Trạng thái:** xong 2026-10-16

## Vì sao

Một lượt agentic là không đủ: ở D-01, cùng mô hình nhưng khác ngữ cảnh chỉ đạt kappa 0,43. Hai lượt độc lập cho biết độ nhiễu, và phần đồng thuận
là nhãn dùng để đo luật.

## Cần làm

- Chủ dự án quyết dịch vụ nào được nhận phiếu, vì phiếu chứa văn bản giáo trình.
- **Lượt A và lượt B:** hai agent hoặc hai mô hình khác nhau, không thấy nhãn của nhau, mỗi lượt gán đủ mọi phiếu đúng một lần.
- Mỗi lượt tự chạy bộ kiểm định dạng trước khi trả. Lỗi thì tự sửa định dạng; không đổi nhãn vì bộ kiểm.
- Claude kiểm hai tệp và báo danh sách cặp lệch A–B. Lượt ba (agent khác) gán riêng các cặp lệch, không thấy nhãn A và B. Cặp vẫn không có đa số
  thì thành `khong_ro`.

## Nghiệm thu

- [x] Hai tệp nhãn A, B và tệp lượt ba đều qua được bộ kiểm định dạng.
- [x] Mỗi dòng nhãn ghi `nguoi_gan` (agent, mô hình, phiên bản) và `luot`. A và B khác agent hoặc khác mô hình.
- [x] Ghi chép của từng lượt (cách chia lô, số subagent, sự cố) được giao kèm.

## Kiểm hai lượt A, B (Claude, 2026-10-16)

- **A:** Codex / GPT-5, một tiến trình chính và ba tiến trình phụ, đọc đủ hướng dẫn. **B:** Gemini 3.8 Flash qua script `gan_nhan_b.py`
  (lô 10 phiếu, temperature 0). Cả hai qua bộ kiểm định dạng, đều in "HỢP LỆ". Tệp ở `tmp/goi-A/`, `tmp/goi-B/`.
- **Lượt B lệch quy trình ở hai chỗ.** Prompt hệ thống là bản tóm tắt bảy nhãn và các bước quyết định, không phải toàn văn hướng dẫn: thiếu mười ca
  khó và sáu ví dụ. Ngoài ra có 12 phiếu mô hình không trả nhãn; script tự điền `khong_tien_quyet` với lý do cố định "đoạn Y không cho thấy quan hệ".
  12 phiếu này coi là chưa gán và gửi sang lượt C.
- **Độ khớp:**
  - A–B: khớp 63,5% trên 7 nhãn (kappa 0,53); khớp 94,8% theo nhị phân `can_hoc_truoc` (kappa 0,48).
  - Tự nhất quán trên 65 phiếu lặp: A khớp 81,5% (kappa 0,76), B khớp 86,2% (kappa 0,79).
  - `khong_ro`: 0 ở cả hai lượt.
  - `can_hoc_truoc`: A 65 phiếu, B 78 phiếu, cả hai cùng gán 36.
- **Ô lệch lớn nhất:** A `du_tai_cho` → B `kien_thuc_nen`, 85 phiếu. Đây là ca khó 10 của hướng dẫn ("câu định nghĩa Y giải thích luôn X"), phần
  mà B không có trong prompt. Ô này không đổi nhị phân `can_hoc_truoc`.
- **Claude đọc 80 phiếu** (seed 4): 20 phiếu lệch nhị phân, 20 phiếu lệch nhãn khác, 20 phiếu đồng thuận `can_hoc_truoc`, 20 phiếu đồng thuận nhãn khác.
  - Đồng thuận `can_hoc_truoc`: 19/20 đúng. Phiếu còn lại ("Quy trình bón phân" với "Bón lót") ở biên.
  - Đồng thuận nhãn khác: 20/20 hợp lý.
  - 20 phiếu lệch nhị phân: A đúng khoảng 9, B đúng khoảng 3, còn khoảng 8 phiếu thật sự mơ hồ.
  - Lỗi hay gặp của B: coi thuật ngữ chuyên môn là nghĩa thường ("mâu thuẫn" hay "chất" trong triết học), và dùng `nguoc` sai.
  - Lỗi của A: dùng `du_tai_cho` cả khi câu được coi là giải thích chính là câu định nghĩa Y (96/192 phiếu có `cau_giai_thich` = `cau_y`).
- **Chỗ mơ hồ của hướng dẫn 1.0:** "X là một phần của Y" thì gán `nguoc`, nhưng "X là thành phần của định nghĩa Y" thì gán `can_hoc_truoc`. Hai luật
  này chọi nhau khi Y là một tổng thể được định nghĩa bằng cách kể các bộ phận, ví dụ "Điều khiển nhập/xuất" gồm "bộ quản lý ngắt". Lỗi này chỉ gây
  khoảng 9 phiếu lệch nhị phân. Không sửa hướng dẫn giữa chừng; lượt C dùng cùng bản 1.0.
- **Phán:** lệch giữa A và B không có hệ thống ở nhị phân `can_hoc_truoc`, nên dùng được cho D-04d sau khi phân xử.
- **Phạm vi lượt C:** chỉ gửi phiếu lệch nhị phân `can_hoc_truoc`, vì D-04d chỉ đo nhị phân này. Lệch giữa các nhãn khác không đổi nhị phân, nên
  không gửi. Gửi thêm các phiếu có nhãn giữ chỗ.
  - Tổng: 83 phiếu = 71 lệch nhị phân + 12 nhãn giữ chỗ.
  - Chọn bằng `scripts/pass-phu-ml/chon_luot_c_d04.py`.
  - Gói C nằm ngoài repo, ở `Desktop\d04-luot-C\`, gồm phiếu, hướng dẫn 1.0 và bộ kiểm. Không kèm nhãn A, B hay khoá.
- **Lượt C** (Antigravity / Argon, 2026-10-16): 83/83 phiếu, qua bộ kiểm định dạng. Không phiếu nào được gán `can_hoc_truoc`; lý do C hay nêu là
  "X đã giới thiệu ở mục trước". Với nhãn đa số, 0 phiếu thành `khong_ro`. Vì C nghiêng một phía, D-04d đo thêm độ nhạy trên nhãn từng lượt và
  trên A∪B.
