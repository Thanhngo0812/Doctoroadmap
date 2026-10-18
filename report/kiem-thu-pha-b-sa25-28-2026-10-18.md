# Soát độc lập vé SA-25–28 (2026-10-18)

**Người soát:** Claude (phiên Pha B). **Đầu vào:**
- [bàn giao của nhân viên](pha-b-sa25-28-ban-giao-2026-10-18.md);
- bốn báo cáo `pha-b-sa25…28-2026-10-18.md`;
- commit `352cca9`.

**Chi phí lượt soát:** 0 USD. Mọi phép đo là phát lại phản hồi đã ghi.

**Phạm vi:** chỉ sáu cuốn phát triển. Không mở T-01, không đọc `cache` của `live.json`.

## Kết luận

| Vé | Phán xét | Việc tiếp |
|---|---|---|
| 25 Hậu kiểm theo câu, bảng giá chung | **đạt** | trình bày tài liệu sau hậu kiểm → SA-30 |
| 26 Bài giảng: chống lặp, lý do hỏng, `usage`, `used_later` | **đạt**; phát hiện K6 dò sai | → SA-30 |
| 27 Quiz LLM: mã lý do loại, luật tên có điều kiện | **đạt**; Claude đồng ý luật tên có điều kiện | vé 22 đánh giá chất lượng |
| 28 Tên module: mô tả thành câu | **chưa đạt**: đường lùi tăng từ 8/160 lên 135/160 | → SA-29 |

## 1. SA-25: đạt

**Đọc cả 6 tài liệu sau hậu kiểm (`tmp/phaseb-sa25-documents/`):** không còn câu khẳng định nào thiếu nguồn. Nhãn ghép được kiểm từng nhãn, tiêu đề H1 không còn lặp.

**Ba vấn đề trình bày, đưa sang SA-30:**
- **Tiêu đề rỗng còn sót.** Khi mọi câu dưới một tiêu đề bị bỏ, tiêu đề vẫn còn. Ví dụ "## Hạn chế", "### Ghi chú thêm", và cả bài doc-1 chỉ còn hai tiêu đề.
  Bài naive-bayes còn một dòng chỉ có dấu ".".
- **2/6 tài liệu `failed`.** Lý do là mô hình không chép được câu trích nguyên văn vào `citations`, nên gần hết câu bị bỏ. Trợ lý xử lý khác: khi nhãn
  hợp lệ mà thiếu câu trích, mã tự chọn câu của nguồn trùng nhiều từ nhất.
- **Khối "ngoài tài liệu" vẫn là câu sáo rỗng hay lời dặn ôn thi,** không phải ví dụ. Luật hiện chỉ chặn định nghĩa. Phần này thuộc prompt, chờ spec mới.

## 2. SA-26: đạt; phát hiện K6 dò sai

**Phần đạt:**
- lọc ý trùng;
- `usage` cộng đủ mọi lần sinh;
- chẩn đoán theo từng lần sinh;
- `used_later` đúng chiều.

Phát lại 12 bài: `ready` tăng từ 7 lên 9.

**Phát hiện mới của lượt soát.**
- K6 dò "cụm 8 từ lặp ≥ 3 lần" trên **toàn bộ JSON đầu ra**, gồm cả câu trích nguyên văn và tên trường.
- Kiểm trên 18 lần sinh đã ghi của nhóm 2:

| Dò K6 trên | Số lần sinh bị coi là lặp |
|---|---:|
| toàn bộ JSON (hiện tại) | 9/18 |
| chỉ chữ của các ý | **0/18** |
| chỉ các câu trích | 3/18 |

- Vậy cả 9 lần hỏng vì K6 đều là **dò sai**: ý không lặp, chỉ có câu trích và khung JSON lặp lại. Đây là nguyên nhân hỏng lớn nhất của bài giảng.

**Ba lỗi khác** do báo cáo nghiên cứu bài giảng phát hiện; Claude kiểm lại đúng:
- `single_flight` ghi mọi kết quả vào cache, kể cả bài `fallback`. Bài hỏng một lần thì bị lưu vĩnh viễn và trả cho mọi người học.
- `ttft_ms` bằng 0 ở cả 18/18 dòng sổ chi bài giảng, tức chưa đo được thời gian tới chữ đầu.
- `_bounded_quote` cắt câu trích ở 120 ký tự, ngắn hơn trần chung `quote_max_chars` (200).

## 3. SA-27: đạt

**Chẩn đoán:**
- Mỗi câu ứng viên bị loại có một mã lý do.
- Ở V1 và V2, lý do chính là nhãn nguồn sai khuôn hay `from` không khớp nguồn. Đây là lỗi prompt cũ, các luật loại đúng.

**Luật tên trong đề:** nhân viên đổi thành có điều kiện, đúng đề xuất của vé. Chỉ loại khi đáp án đúng chính là tên hay bí danh của khái niệm. Claude đồng
ý. Các luật nguồn và lời gọi kiểm mù giữ nguyên. Test M10 bắt được ca lời gọi kiểm chọn sai đáp án.

**Lượt thật 2 module (0,078 USD):**
- 11/15 khái niệm có câu: 8 câu LLM và 3 câu điền khuyết.
- 13 biến thể được lời gọi kiểm chấp nhận.

**Claude đọc cả 13 biến thể:**
- 13/13 đúng đáp án và khớp nguồn.
- **Điểm yếu, để vé 22 đánh giá:**
  - 4/13 câu cùng một khuôn "ký hiệu nào biểu diễn phép…", với phương án là ký hiệu;
  - vài câu nhiễu khó tin, như "A ∪ B" cho câu hỏi về tập rỗng, hay "Lượng từ phổ biến" cho câu hỏi về phần tử.
- **Thời gian:**
  - doc-1 mất 21,3 giây tới câu đầu;
  - doc-4 mất 6,2 giây.

  Cần đo lại ở vé 22 để biết lý do là tuần tự hay bị bóp quota.

## 4. SA-28: chưa đạt; Claude quyết hướng sửa

**Kết quả lượt thật:**
- chỉ 25/160 đầu ra LLM qua kiểm;
- 122 module rơi đường lùi vì cờ `vocabulary`;
- tên và mô tả rơi cùng nhau, nên mất cả những tên LLM tốt.

Các đồ thị mới (doc-1 v54, nhap-mon-ml v47, naive-bayes v46, doc-6 v26, xstk v65, doc-4 v24) đang là bản mặc định.

**Đo bằng phát lại 160 phản hồi đã ghi, 0 USD**, script `scripts/pha-b/kiem_lai_tu_vung_sa28.py`:

| Tập từ vựng của luật 1 | Đạt |
|---|---:|
| hiện tại: tên, bí danh, mô tả A5, tiêu đề mục, 1% âm tiết thường gặp nhất | 25 |
| + âm tiết của các đoạn dạy khái niệm trong module | 31 |
| + đoạn dạy + âm tiết có ở ≥ max(3, 2% số đoạn) của chính cuốn | **82** |
| + đoạn dạy + âm tiết có ở ≥ 4/6 cuốn | 77 |
| **chỉ kiểm riêng tên** (luật tên, từ vựng hiện tại) | **144** |

**Âm tiết vẫn thiếu sau khi mở rộng** là các chữ mô tả tự xưng: "module" (42 lần), "nội dung" (31), "rõ", "dạy". Prompt cấm tự xưng là hết.

**Quyết định của Claude** (vé 28 giao Claude quyết khi luật từ vựng làm rơi đường lùi nhiều):
1. **Tách kiểm tên khỏi kiểm mô tả.** Tên đạt luật tên thì giữ, dù mô tả hỏng. Mô tả hỏng thì dùng khuôn, cờ `description_vocabulary`. Làm lại từ cache,
   0 USD; tên LLM lên khoảng 144/160.
2. **Mở rộng từ vựng của mô tả** bằng hai nguồn đều lấy từ chính cuốn sách, không dùng danh sách viết tay:
   - âm tiết của các đoạn dạy khái niệm trong module;
   - âm tiết có ở ít nhất max(3, 2% số đoạn) của cuốn.

   Từ vựng của tên giữ như cũ.
3. **Thêm luật "không mượn từ module kề" bằng mã.** Hiện luật này chỉ có trong prompt. Âm tiết thuộc tên khái niệm của module ±1 mà không có trong tên,
   mô tả A5 hay đoạn dạy của module đích thì câu đó bị loại. Luật này cần vì từ vựng đã rộng hơn.
4. **Prompt cấm mô tả tự xưng** ("module này", "chương này", "bài này", "nội dung"). Mô tả bắt đầu thẳng bằng điều được dạy.
5. **Chạy lại sáu cuốn:** có tiền, ước 0,15–0,25 USD. Dry-run trước, chủ dự án duyệt.

Spec Pha B mục 2, luật 1 và luật 2, sửa theo quyết định này.

## 5. Việc tiếp

- **SA-29:** tên module theo mục 4.
- **SA-30:** các sửa nhỏ sau soát:
  - K6 chỉ dò trên chữ của ý;
  - không cache bài hỏng;
  - đo TTFT;
  - câu trích cạnh không cụt;
  - bỏ tiêu đề rỗng sau hậu kiểm;
  - tài liệu dùng câu trích do mã chọn như trợ lý, đo bằng phát lại.
- **Thiết kế lớn chờ đợt tra hỏi:** giao diện hai tầng, bài giảng gợi lại và gợi mở, xử lý bài hỏng hẳn. Câu hỏi mở ở hai báo cáo nghiên cứu ngày
  2026-10-18.
