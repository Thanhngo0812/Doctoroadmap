# 10 — A5: kiểm draft của node đơn lẻ

**What to build:** Node chỉ có một ứng viên — 219/279 nhóm tên trên corpus — được **kiểm draft theo lô**. Draft được
câu bằng chứng hỗ trợ **và** đúng ngôn ngữ chủ đạo thì giữ nguyên; ngược lại thì viết lại, chỉ từ bằng chứng. Sau
ticket này, mọi node trừ media đều có mô tả thoả cùng một bất biến: mỗi câu kèm `chunk_id`.

## Vì sao không giữ nguyên draft như GraphRAG/LightRAG

Giữ nguyên draft cho node đơn lẻ không miễn phí trên dữ liệu này: draft là câu vai trò, có draft sai hẳn
(`Prior probability` → *"The probability distribution on A, denoted as P(B)"*), và ngôn ngữ trôi theo tên thuật ngữ —
`baocao-canhan` có 82% chữ tiếng Việt mà 32/57 draft viết tiếng Anh. Cũng không viết lại tất cả: không có lý do thì
viết lại chỉ mở thêm đường cho mô hình bịa (Q15).

**Blocked by:** 09 — A5: mô tả chuẩn cho node nhiều ứng viên

**Status:** done

**Cập nhật triển khai 2026-09-11:** Đã triển khai kiểm theo lô; test giữ draft, viết lại sai ngôn ngữ dù model trả giữ, viết lại thiếu hỗ trợ.
Chi tiết kiểm chứng và phần chưa hoàn tất: [feedback A4/A5](../../feedback/F18-a4-a5-hop-nhat.md).

- [x] **Lô kiểm**: mỗi lời gọi xử lý nhiều node đơn lẻ, cỡ lô cấu hình được. Đầu vào mỗi node: tên chuẩn, kiểu, draft,
      câu bằng chứng cộng chunk nguồn.
- [x] Đầu ra mỗi node: *giữ* hoặc *viết lại*. Viết lại thì theo **đúng hợp đồng đầu ra ticket 09**: 1–4 câu, trích
      dẫn, `defining_chunk_ids`, kiểm như ticket 09.
- [x] **Code quyết phần ngôn ngữ, không phải mô hình**: draft khác ngôn ngữ chủ đạo ⇒ bắt buộc viết lại, kể cả khi mô
      hình trả *giữ*.
- [x] Draft được giữ nhận trích dẫn là chunk bằng chứng của chính ứng viên đó, để mọi mô tả cùng thoả bất biến "mỗi câu
      kèm `chunk_id`"; `defining_chunk_ids` = chunk đó.
- [x] Sai định dạng hai lần ⇒ giữ draft, gắn cờ, ghi nhật ký — như ticket 09.
- [x] **Manifest**: số node giữ draft / viết lại vì không được hỗ trợ / viết lại vì sai ngôn ngữ.
- [x] **Seam ①**, người kiểm giả, không chạm mạng:
    - draft tiếng Anh trong tài liệu tiếng Việt ⇒ bị viết lại dù người kiểm giả trả *giữ* (thấy hỏng khi bỏ luật);
    - draft được hỗ trợ và đúng ngôn ngữ ⇒ giữ, không phát sinh lời gọi viết lại (test đếm lời gọi);
    - draft bị trả *không được hỗ trợ* ⇒ viết lại, mô tả mới có trích dẫn hợp lệ.
- [x] Toàn bộ test hiện có vẫn xanh.
