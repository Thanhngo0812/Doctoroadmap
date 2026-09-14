# 02 — Bằng chứng: mô hình chép, code xác minh

**What to build:** Mở một thực thể vừa trích ra và **tra ngược được** — nó đến từ câu nào, ở vị trí ký
tự nào trong chunk nào. Thực thể mà mô hình không chép được câu bằng chứng có thật thì **bị loại tự
động**, không cần người soi.

## Vì sao

Spec cũ bắt buộc bằng chứng cho **cạnh** nhưng không cho **khái niệm** — bất đối xứng vô lý, vì khái
niệm bịa sinh ra node mà mọi thứ khác bám vào. Đây là mở rộng của bất biến **I9** ở B0
(`normalized_full_text[span] == chunk.text`) từ chunk sang node.

## Luật

```
LLM chép câu nguyên văn
  -> code chuẩn hoá bằng ĐÚNG bộ chuẩn hoá B0 (NFC · gộp khoảng trắng · bỏ phân biệt hoa thường)
  -> dò trong chunk nguồn
  -> thấy    : tính span, lưu cùng thực thể
  -> KHÔNG thấy: LOẠI thực thể, đếm vào thống kê
```

**Không so mờ.** So mờ mở cửa cho ảo giác một phần — mô hình bịa một câu na ná câu thật vẫn lọt, mà đó
đúng là thứ luật này sinh ra để chặn.

**Blocked by:** 01 — cần có đầu ra thô của mô hình để xác minh.

**Status:** done

- [x] Tái dùng hàm chuẩn hoá của B0, **không** viết bộ chuẩn hoá thứ hai
- [x] Thực thể qua được mang `chunk_id` + span ký tự, cùng hệ toạ độ với `image_refs`/`table_refs`
- [x] Có test: câu chép **chính xác** ⇒ giữ, span đúng vị trí
- [x] Có test: câu chép khác **hoa thường và khoảng trắng** ⇒ vẫn khớp sau chuẩn hoá
- [x] Có test: câu mô hình **viết lại theo ý mình** (không có trong chunk) ⇒ **bị loại**
- [x] Có test: câu na ná nhưng khác vài từ ⇒ **bị loại** — khẳng định không có so mờ
- [x] Số thực thể bị loại vì thiếu bằng chứng được đếm vào thống kê, không nuốt im lặng
- [x] Luật áp cho **cả** thực thể **lẫn** cạnh đề xuất **lẫn** alias
