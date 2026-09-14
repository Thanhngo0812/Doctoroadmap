# 03 — Ánh xạ cạnh A3 về node canonical

**What to build:** Artifact `canonical` mang theo cạnh đề xuất của A3 đã ánh xạ về node — sẵn làm đầu vào cho 2b.
Cạnh giữa hai ứng viên nay đã chung một node thì bỏ; cạnh trùng thì gộp; cạnh media nối lại về node và trạng thái mồ
côi của media được tính lại. Chạy `a4` là thấy số cạnh trước và sau ánh xạ.

## Vì sao tách khỏi ticket 02

Ánh xạ cạnh phải chạy **lại** mỗi khi bảng node đổi — sau lượt phán cụm (07) và bước vá (08) sẽ có thêm node gộp.
Viết nó thành một hàm thuần nhận "bảng thành viên + cạnh A3" thì ba ticket dùng chung được, không gắn chết vào lớp tên.

**Blocked by:** 02 — Viên đạn vạch đường: lớp tên → bảng node canonical, lệnh `a4`

**Status:** done

**Cập nhật triển khai 2026-09-11:** Đã triển khai hàm remap dùng lại sau merge; corpus lớp tên 219→213, test tự nối/trùng cạnh.
Chi tiết kiểm chứng và phần chưa hoàn tất: [feedback A4/A5](../../feedback/F18-a4-a5-hop-nhat.md).

- [x] Mỗi cạnh A3 ánh xạ hai đầu `candidate_id` → id node canonical; đầu là media thì trỏ về node media.
- [x] Hai đầu rơi vào cùng một node ⇒ bỏ cạnh, đếm vào manifest.
- [x] Nhiều cạnh cùng kiểu (khoá kiểu cạnh chuẩn hoá) giữa cùng một cặp node ⇒ gộp thành một, hợp bằng chứng (không
      lặp), `confirmed` lấy OR.
- [x] Cạnh `illustrates` / `tabulates` theo cùng luật; sau ánh xạ tính lại `orphan_reason` của node media (I-G2) —
      media có cạnh thì hết mồ côi.
- [x] `requires` do A3 đề xuất giữ nguyên là **đề xuất**; 2b mới xác minh (§726).
- [x] Sổ đăng ký kiểu cạnh trong artifact `canonical` đếm lại theo cạnh sau ánh xạ (I-G3).
- [x] Manifest: số cạnh A3, số cạnh tự nối bị bỏ, số cạnh trùng đã gộp, số cạnh còn lại.
- [x] Trên bốn tài liệu, sau lớp tên: **219 cạnh A3 → 0 cạnh tự nối, 6 cạnh trùng gộp, còn 213**. Lệch thì giải
      thích.
- [x] Ánh xạ là hàm thuần nhận bảng thành viên bất kỳ, để ticket 07 và 08 gọi lại sau khi gộp thêm node.
- [x] Test domain đi **cả hai nhánh**, dựng tay: hai ứng viên chung node có cạnh giữa chúng ⇒ cạnh bị bỏ (trên corpus
      hiện tại nhánh này không kích hoạt, nên chỉ test tay mới bảo vệ được nó); hai cạnh cùng kiểu cùng cặp node ⇒ một
      cạnh, bằng chứng hợp, `confirmed` OR. Mỗi test phải thấy hỏng khi bỏ luật tương ứng.
- [x] Toàn bộ test hiện có vẫn xanh.
