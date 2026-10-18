# Bàn giao cho phiên Pha B: sau 19n/19o, 05a–05c và T-01b (2026-10-18)

**Từ:** phiên pha A (Claude). **Gửi:** phiên Pha B (sau A10).

Bản này nối tiếp [bàn giao 2026-10-17](ban-giao-pha-b-chuoi-gop-2026-10-17.md).

Đọc kèm:
- [báo cáo T-01b](v4-T01b-2026-10-18.md);
- [vé 05c](../task/v4/05c-nhan-vung-moi-toi-canonical.md);
- [báo cáo 05b](v4-05b-chay-lai-xstk-doc4-2026-10-17.md).

## Tóm tắt

- **Không phải sửa mã.** 110 test Pha B (`test_phase_b_*`) qua trên mã hiện tại `da15192`.
- **Phải làm:** giữ mù hai cuốn T-01 (mục 4). Kho `artifacts/phase_b/live.json` nay có tiêu đề và mô tả module của hai cuốn này.
- **Nên biết:**
  - chuỗi gộp đã nghiệm thu trên tập giữ lại, sẽ không quay lại v3;
  - đồ thị mới nhất của xstk đổi từ v56 sang v64.

## 1. Chuỗi gộp đã nghiệm thu; mã v3 đã gỡ

- **19n và 19o đã vào ở commit `36b81ff`.**
  - Pha A không còn dựng đồ thị v3, và `roadmap` từ chối canonical v3.
  - Artifact v3 cũ vẫn đọc được: hợp đồng đọc giữ nguyên.
- **`quote_is_verbatim` nay nằm ở `domain.quotes`.** Nhân viên 19n đã đổi một dòng import trong `application/phase_b/common.py`. Tệp này đã được
  track, nên đây là tệp của Pha B được sửa từ phía pha A.
- **T-01b đạt (2026-10-18):** trên hai cuốn giữ lại, chuỗi gộp không kém v3.
  - Đích vàng trong dãy học bằng nhau.
  - Gộp sai mà vàng phát hiện: 0 ở cả hai chuỗi.
  - E4 lệch xấu nhất −0,07.

  Từ giờ coi hợp đồng đồ thị chuỗi gộp là ổn định.
- **Manifest đồ thị mới vẫn ghi `config.upstream_chain = "gop"`** (đã kiểm trên xstk v64). Vẫn dùng trường này để ghi đồ thị thuộc chuỗi nào khi
  đo đánh giá.

## 2. Đồ thị mới nhất của xstk đổi

Vé 05b chạy lại xstk theo luật A2 mới (05a). Hàm `load_learning_graph` khi không truyền `graph_version` sẽ lấy đồ thị A10 hoàn tất mới nhất.

| Tài liệu | Đồ thị | Khái niệm | Id mất / id mới | Module | Module giữ nguyên tập khái niệm |
|---|---|---|---|---|---|
| xstk-ch3-1 | v56 → **v64** | 73 → 82 | 1 / 10 | 13 → 14 | 6 |
| doc-1 | v53, không đổi | | | | |
| doc-4 | v23, không đổi | | | | |
| nhap-mon-ml, naive-bayes, doc-6 | v46, v45, v17, không đổi (vẫn là đồ thị v3) | | | | |

- **Id mất ở xstk** không quy được qua `redirects`. Khái niệm đó rời dãy học vì trạng thái dạy đổi, không phải vì bị gộp.
- **Cache bài giảng và quiz** của xstk v56 không dùng lại được cho v64, vì khoá băm theo `node_id` và ngữ cảnh.
- **Test hoặc demo cần số cố định** thì truyền `graph_version`, như hai test quiz đã ghim doc-1 v45.
- **Ba tài liệu còn đồ thị v3:** muốn có đồ thị chuỗi gộp thì phải chạy luồng pha A, có chi tiền. Báo chủ dự án trước, không tự chạy.

## 3. Vai trò chunk (05a) và bộ nạp nhãn vùng (05c)

- **05a đổi luật A2.** Tiêu đề lặp chỉ thành đề cương khi tên các mục khác phủ đủ thân mục.
  - Ở xstk, đồ thị v64 ghim chunk v7. So với v5 (đồ thị v56), `de_cuong` từ 48 xuống 0, tất cả thành `noi_dung`.
  - `bai_tap` giữ đúng 21 chunk cũ.
  - Pha B chỉ đọc vai trò `bai_tap` (quiz chọn bài tập, bài giảng lọc ví dụ). Mã Pha B không đọc `de_cuong` ở đâu, nên không phải sửa.
- **05c đổi `load_role_chunks`, hàm mà khâu tên module của Pha B dùng.**
  - Hàm này nay trả bản nhãn mới nhất từ cùng bản chunk gốc, khi bản ghim trong đồ thị tự nó là bản nhãn.
  - Trên kho hiện tại, chỉ doc-4 bị ảnh hưởng: đồ thị v23 ghim chunk v6, nay khâu tên nhận v8.
  - v6 và v8 giống hệt nhau trừ vai trò (đã kiểm id, văn bản, offset, thứ tự và mục cha của cả 671 chunk). Khâu tên lại không đọc vai trò, nên tên
    module doc-4 không đổi.
- **Bài giảng và quiz nạp chunk bằng `load_chunks`** với version ghim trong đồ thị, nên không đổi.
  - Lưu ý: ở doc-4, khâu tên và bài giảng hiện đọc hai bản nhãn khác nhau (25/671 chunk khác vai trò).
  - Nếu sau này khâu tên dùng tới vai trò thì phải thống nhất đường nạp.

## 4. Giữ mù T-01 (phải làm)

`d01-t01` và `d01-t02` là tập giữ lại.
- Số đo trên hai cuốn này là số báo cáo cuối của pha A, và vẫn chưa mở mù.
- Hai cuốn nay đã có đồ thị chuỗi gộp: d01-t01 v19; d01-t02 v19 (nhánh B) và v27 (nhánh C, mới nhất).

Trừ khi chủ dự án cho phép, Pha B **không** được:
- mở hay in nội dung hai cuốn: chunk, tên khái niệm, tiêu đề và mô tả module, bài giảng, quiz;
- chạy lệnh Pha B có chi trên hai cuốn;
- đưa hai cuốn vào bộ nghiệm thu Pha B (`artifacts/phase_b/acceptance-*.json`). Nếu sau này cần tập giữ lại cho Pha B, dùng hai cuốn này theo đúng
  cách: đặt tiêu chí trước, script chỉ in trường số.

**Kho Pha B đã có dữ liệu T-01.**
- A10 của `roadmap` gọi khâu tên module Pha B, với kho `artifacts/phase_b/live.json`.
- Lượt T-01b ghi vào đó 177 dòng `usage` (`purpose = module_title`, `doc_id` là `d01-t01` hoặc `d01-t02`, 0,17 USD), cùng các mục `cache` tương ứng.
  Các mục cache này chứa `title` và `description` của module T-01.
- Khoá cache là hash, nên không lọc được theo tài liệu.

Vì vậy:
- **Không in giá trị `cache`** của tệp này. Khi thống kê `usage`, bỏ các dòng có `doc_id` bắt đầu bằng `d01-t0`.
- **Không xoá các mục đó**, vì chúng là cache hợp lệ của đồ thị v19 và v27.
- **Script hay test đọc `live.json` thật** mà in tiêu đề module thì phải lọc trước khi in.

## 5. Ghi chú chi phí

- **Chi của khâu tên module chỉ được ghi trong `usage` của kho Pha B.** `stats` trong manifest đồ thị (các bản `stages`) ghi 0 token.
- Tính USD/cuốn của `roadmap` chỉ từ manifest đồ thị thì thiếu khoản này. Ở T-01, khoản này khoảng 0,03–0,06 USD/cuốn mỗi lượt.
- Pha A đã sửa báo cáo T-01b. Khi Pha B báo chi phí cả luồng, cộng thêm từ `usage`.
