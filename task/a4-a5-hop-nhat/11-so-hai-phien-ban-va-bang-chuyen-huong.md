# 11 — So hai phiên bản canonical, và bảng chuyển hướng id

**What to build:** `a4-compare --doc-id … --first … --second …` in Jaccard node và Jaccard thành viên giữa hai phiên
bản `canonical`. Mỗi lần `a4` tạo phiên bản mới, manifest ghi `jaccard_previous` và **bảng chuyển hướng**: id nào của
phiên bản trước không còn thì trỏ sang node mới chứa phần lớn thành viên cũ của nó.

## Vì sao

- Id node là thứ tiến độ người học bám vào (B1 lưu `concept_mastery` theo id). ADR 0005 giữ id đứng yên khi tên hay mô
  tả đổi, nhưng khi neo đổi — gộp, tách, hoặc ứng viên neo biến mất ở lần trích sau — thì cần bảng chuyển hướng để
  tham chiếu cũ vẫn tìm được node.
- Độ tái lập phải đo như đã đo ở A3: vòng 18 thấy node A3 tái lập 1,000 mà cạnh chỉ 0,321 — chưa đo thì không biết
  merge ổn định tới đâu.

**Blocked by:** 02 — Viên đạn vạch đường: lớp tên → bảng node canonical, lệnh `a4`

**Status:** done

**Cập nhật triển khai 2026-09-11:** Đã có loader/compare/redirect/restore; test merge, tách theo đa số thành viên, mất hết, nhận lại id và nối chuỗi chuyển hướng.
Chi tiết kiểm chứng và phần chưa hoàn tất: [feedback A4/A5](../../feedback/F18-a4-a5-hop-nhat.md).

- [x] Kho artifact nạp được một phiên bản `canonical` cụ thể và phiên bản mới nhất, theo khuôn nạp `candidates` sẵn có.
- [x] **Jaccard node** trên tập id node. **Jaccard thành viên** trên tập cặp ứng viên chung node — phép so chuẩn cho kết
      quả gom cụm, không phụ thuộc id.
- [x] **Bảng chuyển hướng**: id có ở phiên bản trước mà không còn ở phiên bản mới ⇒ trỏ sang node mới chứa nhiều thành
      viên cũ nhất; không còn thành viên nào ⇒ ghi *đã mất*.
- [x] Id đã nằm trong bảng chuyển hướng mà lần sau lại được tính ra — ứng viên neo xuất hiện trở lại, tức cùng tên cùng
      section, cùng thực thể — thì node đó **nhận lại id cũ**, bản ghi chuyển hướng bị gỡ và ghi nhật ký. Bất biến có
      test: không bao giờ có hai node cùng id, và không id nào vừa là node vừa là chuyển hướng (ADR 0005).
- [x] Manifest: `jaccard_previous` (node, thành viên) và số id được chuyển hướng.
- [x] `a4-compare` in hai số Jaccard, số node chỉ có ở từng bên, số id chuyển hướng.
- [x] Test với hai phiên bản dựng tay:
    - gộp hai node ⇒ id của node mất neo chuyển hướng sang node gộp;
    - tách một node ⇒ id cũ trỏ sang phần chứa nhiều thành viên cũ nhất;
    - hai phiên bản giống hệt ⇒ Jaccard 1,000 và không có chuyển hướng.
- [x] Toàn bộ test hiện có vẫn xanh.
