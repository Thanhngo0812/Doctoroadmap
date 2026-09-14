# 02 — Viên đạn vạch đường: lớp tên → bảng node canonical, lệnh `a4`

**What to build:** `doc2roadmap a4 --doc-id baocao-canhan` chạy trong vài giây, không gọi mạng, và ra một phiên bản
artifact tầng `canonical`: mỗi nhóm ứng viên **trùng tên khít** thành một node canonical có tên chuẩn, alias, ký
hiệu, kiểu, cờ `learnable` và id neo; media đi thẳng theo `media_id`. Lệnh in chỉ số.

Đây là viên đạn vạch đường của cả đợt. Nó dựng use case, artifact, manifest, lệnh CLI và seam test mà mọi ticket sau
làm dày thêm. Riêng lớp tên đã là một bảng node dùng được: gộp 377 → 279 ứng viên văn bản mà không gọi mô hình nào,
và soát tay 58 nhóm thì 56 nhóm đúng.

## Vì sao làm ngay các luật tên, không để tạm

Mọi ticket sau đều đứng trên node của ticket này. Tên chuẩn, kiểu và id chọn sai ở đây sẽ lan khắp: id là thứ tiến độ
người học bám vào (ADR 0005), còn luật tên cũ nếu áp nguyên văn thì `x` (325 lần) thành tên của *Trung bình mẫu*.
Các luật này nhỏ và thuần — viết đúng một lần, test kỹ ở seam domain.

**Blocked by:** None — can start immediately.

**Status:** done

**Cập nhật triển khai 2026-09-11:** Đã triển khai lớp tên và fixture thật; 377→279 node văn bản. Phân loại alias 89/12/27 lệch mốc, còn cần đối chiếu.
Chi tiết kiểm chứng và phần chưa hoàn tất: [feedback A4/A5](../../feedback/F18-a4-a5-hop-nhat.md).

- [x] Use case A4 đọc artifact `candidates` mới nhất của tài liệu, cùng chunk upstream của nó (để đếm tần suất tên);
      ghi artifact tầng `canonical` qua kho artifact hiện có. Lệnh CLI `a4 --doc-id` chạy use case và in chỉ số.
- [x] **Khoá tên** = chuẩn hoá B0 + casefold + gộp khoảng trắng + quy vị trí dấu thanh về một kiểu (`hoá` = `hóa`,
      `uỷ` = `ủy`, `thuý` = `thúy`). Không gộp `y`/`i` hay `thiết`/`thuyết`. Ứng viên cùng khoá ⇒ một **nhóm tên** ⇒
      một node.
- [x] **Phân loại alias** thành ba loại (spec D2), chỉ áp cho alias: tên gọi · viết tắt (toàn chữ hoa/số, có chữ cái,
      như `ML`, `JWT`, `E2E`) · ký hiệu (không chứa từ ngữ nào: chữ cái đơn, biểu thức có ký tự Hy Lạp/toán như `μ`,
      `x σ n`, `t α`, `P(A|B)`). Trên corpus: 128 alias = **89 tên gọi · 12 viết tắt · 27 ký hiệu**; `H`, `A` là
      ký hiệu vì là chữ cái đơn.
- [x] **Ký hiệu** lưu riêng trên node, **phân biệt hoa thường** (`F` và `f` là hai ký hiệu), không vào tập alias.
- [x] **Tên chuẩn** theo spec D6: ứng cử viên là **tên của các ứng viên** (alias không tranh); bỏ ký hiệu; viết tắt chỉ
      thắng khi không còn tên gọi; chọn dạng có tần suất cao nhất trong văn bản tài liệu (khớp theo ranh giới từ, trên
      văn bản đã chuẩn hoá); hoà ⇒ dạng xuất hiện sớm nhất.
- [x] **Alias của node** = hợp alias của thành viên (tên gọi + viết tắt) cộng tên của các ứng viên không được chọn làm
      tên chuẩn. Mỗi alias giữ câu bằng chứng và `candidate_id` gốc.
- [x] **Kiểu**: chuẩn hoá tối thiểu chuỗi `node_type` (casefold, khoảng trắng, ánh xạ theo sổ đăng ký kiểu đã duyệt)
      rồi bỏ phiếu đa số; hoà ⇒ kiểu cụ thể hơn `concept` ⇒ kiểu được dùng nhiều hơn trong cả tài liệu ⇒ thứ tự chữ
      cái. Luật đã dùng ghi vào nhật ký. Trên corpus: **12/60** nhóm nhiều ứng viên hoà phiếu, tất cả được giải và có
      dòng nhật ký.
- [x] **`learnable`**: bỏ phiếu lại chỉ trên ứng viên mang kiểu canonical, hoà chọn `true`. Cùng tên mà khác kiểu nằm
      hai phía `learnable` ⇒ vào hàng review trong artifact.
- [x] **Id node** theo ADR 0005: băm của doc và `candidate_id` của ứng viên neo — ứng viên có `first_order_index` của
      chính nó nhỏ nhất, hoà thì `candidate_id` nhỏ nhất.
- [x] Bảng thành viên node → ứng viên. Nhật ký ghi từng lần tự gộp theo tên (thành viên, khoá tên).
- [x] **Media**: mỗi `media_id` một node; mô tả và `caption_source` giữ nguyên từ A3; không qua các luật trên.
- [x] `first_order_index` tạm lấy nhỏ nhất trên mọi ứng viên, `first_mention_index` bằng cùng giá trị. Ticket 09 sẽ
      thay `first_order_index` bằng chunk định nghĩa/giảng.
- [x] **Config hash** gồm phiên bản và config hash của artifact `candidates` nguồn, cùng phiên bản thuật toán. Chạy
      lại cùng đầu vào thì dùng lại artifact cũ, không tạo phiên bản mới.
- [x] **Manifest**: số ứng viên, số nhóm tên, số node (văn bản, media), tỉ lệ gộp, số lần hoà kiểu,
      `single_chunk_ratio`.
- [x] Trên bốn tài liệu: **377 ứng viên văn bản → 279 node văn bản**, cộng **79 node media**. Lệch thì giải thích.
- [x] **Seam ①** dựng xong: fixture artifact `candidates` thật của `baocao-canhan` cùng chunk của nó; test use case
      chạy không chạm mạng.
- [x] **Seam ②** có test cho:
    - khoá tên: `hoá`/`hóa` gộp; `tỷ lệ`/`tỉ lệ` không gộp;
    - phân loại alias: `F` ≠ `f`; `ML` là viết tắt; `Học` là tên gọi; `Khoảng ước lượng của μ` là tên gọi;
    - luật tên chuẩn: thắng theo tần suất; hoà; viết tắt thua tên gọi; ký hiệu không bao giờ thắng; alias không
      tranh dù xuất hiện nhiều hơn;
    - bỏ phiếu kiểu và từng nhánh của luật hoà;
    - id không đổi khi tên chuẩn đổi (đảo tần suất trong văn bản dựng tay).
- [x] Toàn bộ test hiện có vẫn xanh.
