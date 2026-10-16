# 17c — Chuỗi đồ thị gộp chạy tới A10

**Nguồn chân lý:** [spec gộp khâu trước A8](../../doc/gop-khau-truoc-a8-spec.md), mục 2, 5 và 6.
**Ai:** nhân viên · **Chi phí mô hình:** 0 USD (test bằng mô hình giả) · **Chặn bởi:** 17b · **Trạng thái:** chờ 17b

## Vì sao

Vé này nối canonical đã có neo (vé 17b) với lệnh `roadmap`. Xong vé này, chuỗi gộp chạy đầu-cuối ra lộ trình, không còn ba stage provenance, neo
và danh tính.

## Cần làm

**Chọn chuỗi**
- Lệnh `roadmap` chạy theo chuỗi của canonical đang dùng. Chuỗi được ghi vào config của các stage đồ thị, nên nằm trong khoá cache.
- Nếu tuỳ chọn chuỗi và canonical không cùng chuỗi thì dừng với thông báo rõ. Hai chuỗi không bao giờ dùng lẫn artifact của nhau.

**Thứ tự stage của chuỗi gộp**

```
clusters (A6–A7) → mentions → main_edges → secondary_edges → validated (A9) → concept_labels → stages (A10) → module_titles
```

- Trường neo và trạng thái dạy của node canonical phải tới được A8, A9 và A10 nguyên vẹn.
- Mention map, viện dẫn và cặp nghi tiên quyết dựng trên tập node canonical, với chunk định nghĩa đã có chunk neo.

**A8**
- Pass chính nhận upstream `mentions` của chuỗi gộp.
- Hợp đồng cạnh theo định nghĩa và yêu cầu kiểu tiên quyết bật khi **canonical khai báo đã có neo**, không dựa vào tên stage. Hiện nay pass chính bật
  hợp đồng này khi upstream là stage `identity`; chuỗi v3 giữ nguyên hành vi đó.
- Pass phụ chạy được trên chuỗi gộp ở cả hai chế độ `llm` và `ml`.

**Các stage sau và bộ chấm**
- A9, đặt tên nhãn, A10 và bộ chấm A8 nhận được artifact của chuỗi gộp.
- Thiếu `identity_map` được hiểu là bản đồ rỗng.

**CLI**
- Trong chuỗi gộp, `--stop-after provenance|teaching|identity` báo lỗi kèm gợi ý "đã nằm trong stage canonical".
- `--dry-run` liệt kê đúng các stage của chuỗi gộp, không gọi mô hình hay embedding.
- `--identity-review` bị từ chối trong chuỗi gộp, kèm gợi ý nạp quyết định người duyệt ở A4 (vé 17g).

## Nghiệm thu

- [ ] Test điều phối với stage giả: thứ tự stage của chuỗi gộp và của chuỗi v3; `--stop-after` hợp lệ và không hợp lệ; `--dry-run` không gọi
      mô hình hay embedding.
- [ ] Test hợp đồng pass chính:
  - với upstream chuỗi gộp có khai báo neo, hợp đồng theo định nghĩa được bật;
  - với cùng upstream nhưng bỏ khai báo neo, hợp đồng không bật;
  - với upstream chuỗi v3, hành vi như cũ.
- [ ] Test đầu-cuối trên fixture tài liệu thật, với mô hình giả: canonical chuỗi gộp → `roadmap` ra artifact `stages` và lộ trình. Khái niệm có
      trạng thái `taught` vào dãy học. Không artifact nào có stage `provenance`, `teaching` hay `identity`.
- [ ] Chuỗi gộp chạy được với pass phụ `ml` và với pass phụ `llm`.
- [ ] A10 và bộ chấm A8 chạy được trên artifact không có `identity_map`.
- [ ] Tuỳ chọn chuỗi không khớp canonical thì dừng với thông báo rõ. `--identity-review` trong chuỗi gộp bị từ chối.
- [ ] Hồi quy: artifact chuỗi v3 trong fixture vẫn qua A8, A10 và bộ chấm; chuỗi v3 vẫn là mặc định. Toàn bộ test qua.
