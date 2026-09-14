# 14 — Lần chạy thật đầu tiên: ghi hợp đồng mô hình, chấm, chốt tham số

**What to build:** Sau khi bộ vàng đã đóng băng, chạy `a4` thật trên bốn tài liệu, chấm bằng `a4-evaluate`, A/B model cho
bước phán, chốt tham số, và ghi các fixture một lời gọi để giữ hợp đồng với mô hình thật. Kết quả là một báo cáo số đo
trong `report/`, và artifact `canonical` của bốn tài liệu sẵn cho 2b.

## Vì sao là ticket riêng, cuối cùng

Đây là lần đầu có quyết định mô hình thật, nên nó phải đến **sau** khi người dùng gán mù xong (ticket 06). Và nó là chỗ
duy nhất chốt được những gì spec cố tình để mở: model của bước phán, tham số đồ thị, và giữ hay bỏ kênh mô tả.

**Blocked by:** 06 — [Người dùng] Gán mù bộ vàng A4; 03 — Ánh xạ cạnh A3 về node canonical; 08 — Vá cặp bị chia hai
cụm, và mâu thuẫn bắc cầu; 10 — A5: kiểm draft của node đơn lẻ; 11 — So hai phiên bản canonical, và bảng chuyển hướng
id; 12 — Cache quyết định theo băm đầu vào; 13 — Lệnh chấm `a4-evaluate`

**Status:** done

**Kết quả hoàn tất 2026-09-12:** đã chạy thật cả bốn tài liệu bằng flash-lite, chấm trên bộ 416 nhãn AI, A/B với
`gemini-3.1-pro-preview`, chốt flash-lite và bộ tham số hiện tại. Chạy lặp 0 lời gọi mới, Jaccard node/membership
1,000. Bốn fixture contract v2 đã ghi và phát lại offline thành công.
[Báo cáo kết quả, lỗi và giới hạn](../../report/a4-a5-lan-chay-that-dau-tien.md).
Các ghi chú chưa chạy bên dưới là lịch sử.

**Lịch sử 2026-09-11:** khi đó chưa chạy và còn chờ bộ vàng mù task 06. CLI yêu cầu `--gold` đúng nguồn và đủ mục
trước khi tạo model merge/A5. Chỉ vector tên đã gọi thật, không có quyết định LLM thật trên corpus.
Theo chủ dự án, thời điểm đó tạm dùng `gemini-3.1-flash-lite` cho cả merge/A5.
[Trạng thái chi tiết](../../feedback/F18-a4-a5-hop-nhat.md).

**Cập nhật 2026-09-11, sau đó:** 06 đã có bộ vàng, `--gold artifacts/a4-gold.json`, nên hết chặn. Người gán là Claude,
gán thay chủ dự án. Mục đồng thuận hai người gán chưa có người thứ hai độc lập, vì phụ lục A cùng người gán; báo cáo
ghi rõ điều này, không trình κ với bộ bạc như đồng thuận hai người. Xem [ticket 06](06-nguoi-dung-gan-mu-bo-vang.md).

- [x] **Bốn fixture một lời gọi**, ghi từ mô hình thật trên `baocao-canhan`: một cụm, một cụm vá, một lời gọi A5 tổng
      hợp, một lô A5 kiểm node đơn lẻ. Dùng nguyên cơ chế ghi–phát lại hội thoại của A3, không sửa hạ tầng. Test chỉ
      khẳng định **hình dạng**: schema hợp lệ, trích dẫn hợp lệ, không nhóm nào mất.
- [x] `prompt_hash` dùng để chọn fixture được **tính từ mã sản phẩm**, không đọc từ chính fixture — bài học F57. Có test
      chứng minh: đổi khung prompt thì test phát lại hỏng.
- [x] Chạy `a4` thật trên bốn tài liệu; manifest đủ chỉ số; ghi số thật, không ước lượng.
- [x] `a4-evaluate` trên bộ vàng: P/R/F1 theo cặp, recall đồ thị đề cử, `subtype_of`, đồng âm, đồng thuận hai người gán.
- [x] **A/B ít nhất hai model** cho bước phán trên bộ vàng; chốt model bằng số, ghi lý do.
- [x] **Quyết định kênh mô tả**: đếm cặp *cùng* của bộ vàng nằm ngoài đồ thị đề cử mà vector `description_draft` đề cử
      được. Có ⇒ đề xuất thêm kênh; không ⇒ ghi quyết định bỏ, kèm số.
- [x] Chốt tham số k, ngưỡng n-gram, độ phân giải, trần cụm theo bộ vàng; tham số nào đổi so với spec thì ghi lý do và
      sửa spec.
- [x] Chạy lại lần hai ngay sau đó ⇒ **0 lời gọi mô hình** (ticket 12) và `a4-compare` cho Jaccard 1,000.
- [x] Báo cáo trong `report/`: bảng số theo tài liệu (node, tỉ lệ gộp, `deferred`, cạnh bị cắt, cặp vá, mâu thuẫn bắc cầu,
      cờ `nghi_gop_nham`, node A5 giữ / viết lại); các ca gộp nhầm và bỏ sót tiêu biểu, có trích bằng chứng; đề xuất
      chỉnh tham số hoặc prompt.
- [x] Toàn bộ test xanh; không test nào gọi mạng.
