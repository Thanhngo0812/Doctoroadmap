# 12 — Cache quyết định theo băm đầu vào

**What to build:** Chạy lại `a4` khi đầu vào không đổi thì **không gọi mô hình lần nào**. Đổi luật ngôn ngữ thì chỉ A5
bị gọi lại; lượt phán cụm và bước vá dùng lại toàn bộ. Sửa một section rồi trích lại thì chỉ những cụm chứa ứng viên
của section đó bị gọi lại.

## Vì sao cache nằm trong nhật ký, không phải hạ tầng riêng

Mỗi quyết định đã được ghi vào nhật ký gộp kèm băm dữ liệu gửi đi (tickets 07–10). Nhật ký của phiên bản trước chính
là cache: tra theo băm, trùng thì dùng lại. Không thêm kho nào, và cache kiểm được bằng cùng những con số manifest đã
ghi (Q6, spec D9).

**Blocked by:** 08 — Vá cặp bị chia hai cụm, và mâu thuẫn bắc cầu; 10 — A5: kiểm draft của node đơn lẻ

**Status:** done

**Cập nhật triển khai 2026-09-11:** Test offline đã xác nhận cache lần hai, đổi phiên bản luật ngôn ngữ chỉ A5, đổi evidence chỉ cụm merge ảnh hưởng.
Chi tiết kiểm chứng và phần chưa hoàn tất: [feedback A4/A5](../../feedback/F18-a4-a5-hop-nhat.md).

- [x] Mỗi quyết định — phán cụm, cụm vá, A5 tổng hợp, lô A5 kiểm đơn lẻ — mang băm của (model, `prompt_hash`, dữ liệu
      gửi đi).
- [x] Lần chạy mới đọc nhật ký của phiên bản `canonical` gần nhất; quyết định có băm trùng ⇒ dùng lại, không gọi mô
      hình. Quyết định dùng lại được ghi rõ là *dùng lại* trong nhật ký mới, kèm phiên bản gốc.
- [x] Manifest: số quyết định dùng lại và số lời gọi mới, tách theo bước.
- [x] Đổi luật ngôn ngữ (config hash phần A5 đổi, phần merge không đổi) ⇒ lượt cụm và lượt vá dùng lại 100%, chỉ A5 gọi
      lại.
- [x] Quyết định dùng lại **không bao giờ** áp cho dữ liệu khác băm: đổi một câu bằng chứng của một ứng viên ⇒ cụm chứa
      nó bị gọi lại, các cụm khác thì không.
- [x] HTTP/timeout/lỗi đường truyền dừng lượt chạy và không ghi artifact `complete`; đầu ra sai schema vẫn được giữ
      trong `attempts` để chẩn đoán.
- [x] **Seam ①**, trọng tài và người viết giả có đếm lời gọi:
    - chạy hai lần liền ⇒ lần hai **0 lời gọi**;
    - đổi luật ngôn ngữ ⇒ chỉ người viết A5 bị gọi;
    - sửa bằng chứng của một ứng viên ⇒ chỉ cụm chứa nó và node của nó ở A5 bị gọi lại;
    - mỗi test phải thấy hỏng khi tắt cache.
- [x] Toàn bộ test hiện có vẫn xanh.
