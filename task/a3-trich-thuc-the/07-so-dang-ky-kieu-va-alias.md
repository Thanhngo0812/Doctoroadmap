# 07 — Sổ đăng ký kiểu mở, tên song ngữ và alias

**What to build:** Mô hình được **tự đặt kiểu node mới** (`theorem`, `algorithm`, `definition`…) và mọi
kiểu nó nghĩ ra được ghi vào **sổ đăng ký kèm số lần dùng** — kiểu lạ xuất hiện một lần thì bị soi, kiểu
dùng nhiều thì được công nhận.

## Kiểu mở, mồi bằng ví dụ

Prompt mồi **5–6 kiểu mẫu** rồi nói rõ **được đặt kiểu mới**. Không mồi `dataset`: đây là kiểu bối cảnh
điển hình, không phải mục học. Không đưa danh sách đóng: bài giáo dục
08/2026 dùng **tám loại cạnh** và hơn SOTA trước 14–31% — ép về vài loại là tự bịt.

Ví dụ mồi kéo phần lớn output về một từ vựng chung **mà không đóng cửa**, giảm tải cho pha chuẩn hoá ở
tầng 3 sau này.

`figure`/`table` là tên dành riêng do code giữ — LLM không được dùng.

## Tên và alias

- Tên chuẩn = **dạng xuất hiện nhiều nhất trong tài liệu**; alias gom cả hai ngôn ngữ.
- Alias đến từ **cả hai nguồn**: LLM đề xuất lúc trích, và hợp nhất tên khi merge (đợt sau).
- LLM chỉ được đề xuất alias **có mặt trong văn bản** — cùng kỷ luật bằng chứng ticket 02.
- **Cấm tự sinh viết tắt**: `NB` suy từ *Naive Bayes* sẽ đụng với mọi thứ viết tắt `NB` khác.

Vì sao alias phải có nguồn LLM chứ không chỉ nguồn merge: alias xuất hiện **cùng câu** với tên chính —
*"quá khớp (overfitting)"* — không bao giờ thành hai ứng viên riêng để merge phát hiện.

**Blocked by:** 03 — cần đầu ra có `node_type` và alias để ghi sổ.

**Status:** done

- [x] Prompt mồi 5–6 kiểu, nói rõ được đặt kiểu mới; **không** danh sách đóng
- [x] Schema bắt buộc LLM trả `learnable`; prompt hỏi node là mục người học phải hoàn thành hay chỉ là
      bối cảnh; thiếu trường ở artifact cũ vẫn mặc định `true`
- [x] Nói rõ `edge_type` cũng là hệ mở và mồi quan hệ ngoài `requires` (`example_of`,
      `contrasts_with`, `component_of`, `computed_by`, `uses`)
- [x] Sổ đăng ký kiểu ghi mọi `node_type` và loại cạnh xuất hiện, kèm **số lần dùng**
- [x] Thống kê riêng số/tên loại cạnh do LLM sinh, không tính `illustrates`/`tabulates` do code sinh
- [x] `learnable` mâu thuẫn trong một kiểu được bỏ phiếu đa số, hoà mới ưu tiên `true`; cùng tên khác
      kiểu mà cờ trái nhau sinh cảnh báo để 2a quyết định tường minh
- [x] Sổ đăng ký là artifact có phiên bản, ghi cùng manifest (bất biến **I-G3**)
- [x] Kiểu mới **không phải lỗi** — chấp nhận, ghi sổ, tăng bộ đếm
- [x] LLM dùng `figure`/`table` ⇒ **từ chối**, báo tên dành riêng
- [x] LLM sinh tên cạnh đồng nghĩa `requires` (`prerequisite_of`, `depends_on`…) ⇒ **từ chối**, báo dùng
      `requires` hoặc đặt tên khác hẳn
- [x] Alias không có mặt trong văn bản ⇒ **loại** (qua luật ticket 02)
- [x] Có test: alias trong cùng câu với tên chính ⇒ được nhận
- [x] Chỉ số canh bùng nổ kiểu: **số kiểu phân biệt / số node**, ghi vào thống kê
