# 00 — Kế hoạch: cụm chủ đề, mention map và suy luận tiên quyết (A6–A10)

**Nguồn chân lý:** [`doc/A6-A8-cum-chu-de-mention-map-va-tien-quyet-spec.md`](../../doc/A6-A8-cum-chu-de-mention-map-va-tien-quyet-spec.md)
· ADR [0008](../../doc/adr/0008-2b-pass-chinh-trich-mo-pass-phu-kiem-cap.md) và
[0009](../../doc/adr/0009-nhan-vang-tien-quyet-bam-van-ban.md) · ngôn ngữ chung ở
[`CONTEXT.md`](../../CONTEXT.md) · lý do từng luật ở
[`report/nghien-cuu-a6-a8-cum-chu-de-va-2b.md`](../../report/nghien-cuu-a6-a8-cum-chu-de-va-2b.md)

**Nơi làm:** nhánh riêng cho mỗi vé, gộp vào `main` khi qua review. Mốc so sánh: `cf8facf`.

## Đợt này làm gì

Biến bảng node canonical thành **đồ thị tiên quyết** rồi thành **lộ trình học**, và đo lại toàn bộ bằng một bộ
vàng do người gán. Đầu ra của đợt là hai thứ: sản phẩm chạy hết A1→A10 trên ba tài liệu mới, và một **báo cáo
thực nghiệm**.

**Phạm vi A10 (chủ dự án chốt 2026-09-17, hướng c):** A6–A8 là trọng tâm và là phần duy nhất vào tuyên bố khoa học.
A9 làm đầy đủ. A10 (vé 09) chỉ là **bản tối thiểu** cho sản phẩm có lộ trình xem được, không đưa vào phần khoa học. Thiết
kế A10 cần một đợt nghiên cứu riêng **sau** đợt này trước khi chốt. Xem đầu spec.

## Chia việc

| Ai | Vé |
|---|---|
| Nhân viên | 01, 02, 03, 06, 07, 08, 09, 10, 11, 16, 17, 18, **19, 20, 21** |
| Claude | 04, 05, 12, 13, 14, 15, **22** |

**Đợt vá A9–A10 (vé 19–22), cắt ngày 2026-09-22.** Nguồn chân lý:
[`doc/va-a9-a10-do-thi-tot-va-lo-trinh-dung-duoc-spec.md`](../../doc/va-a9-a10-do-thi-tot-va-lo-trinh-dung-duoc-spec.md),
căn cứ ở [`report/nghien-cuu-a9-a10-kiem-dinh-va-lo-trinh.md`](../../report/nghien-cuu-a9-a10-kiem-dinh-va-lo-trinh.md).
Đây chính là đợt nghiên cứu riêng cho A10 mà chủ dự án đã hẹn khi chốt phạm vi ngày 2026-09-17. Ba quyết định của
chủ dự án ngày 2026-09-22: **(1)** sửa cả hai chặn của chương vàng, giữ hai giáo trình `doc-1` và `doc-2` (mục 3C);
**(2)** stage vẫn là **nhóm học song song được**, đổi thuật toán chứ không đổi định nghĩa; **(3)** chu trình hai
cạnh được **gắn cờ nghi lỗi kiểu quan hệ và loại khỏi `requires`**, không giữ và cũng không gộp.

**Cùng ngày, `doc-1` được thay bằng PDF khác.** Bản cũ hỏng lớp text (0,06% ký tự có dấu); bản mới là một cuốn
khác — Đại học Hàng hải, 102 trang, 5 chương, 25,46% ký tự có dấu, 0 watermark. **Chương vàng của `doc-1` phải
chọn lại**; reviewer đề xuất Chương 3 — Không gian véc tơ, chi tiết ở vé 19.

**Vé 17 — xong ngày 2026-09-20:** chủ dự án cho phép sửa đúng ba điểm hẹp trong phase A3/A4. Bốn tài liệu cũ
`reused=true`; mốc `31/0/16` trong bản giao việc là baseline v1 cũ, còn baseline có thẩm quyền trên `main` sau khi
nhận quan hệ mở là **35/2/12** và vẫn giữ nguyên. Vé 11 đã chạy tiếp, rồi dừng ở `doc-1` vì 114 chunk còn watermark.

**Cập nhật 2026-09-19:** nhân viên đã hoàn tất code và chạy thật các vé 01, 02, 03, 06, 07, 08, 09, 10. Vé 16
được thêm sau mention map và đã qua đủ code/test/cache/precision cùng cổng E1. Chủ dự án đã mở Vé 11; lượt chạy
`doc-3` hoàn tất ingest, A3 và chỉ mục nhưng phát hiện ba chặn mới F107–F109: biến ký hiệu lọt A3 làm A4 dừng, A3
không lưu token usage, và gold guard A4 chưa có luật cho tài liệu mới. Chưa chạy `doc-1`/`doc-2` để giữ đúng thứ tự.
Số đo thật, chi phí và danh sách mutation nằm trong feedback của từng vé.

## Thứ tự và cạnh chặn

```text
01 prefactor ─┐
02 clusters ──┴─> 03 mentions ─> 16 provenance ─┬─> 06 pass chính ─> 07 pass phụ ─> 10 fixture
                                                └─> 08 tầng 3 ─> 09 A10
04 excel vàng ─> 05 bộ chấm

17 ─> 18 watermark ─> 19 mở khoá chương vàng ─> 11 nạp tài liệu ─> 12 E1/E2 ─> 13 2b + E3/E4/E6 ─┬─> 14 báo cáo
                                                                                                 └─> 15 luồng 2b
20 A9 v2 ─> 21 A10 v2 ─> 22 chỉ số lộ trình ───────────────────────────────────────────────────────┘
```

Vé **01, 02 và 04 không chặn bởi gì cả**. Vé 17 và 18 đã xong.

**Vé 19 là đường găng duy nhất của cả đợt.** Cả hai chương vàng đang bị chặn: `doc-2` mục 3C mất `ℒ(V,W)`,
`𝐅^{m,n}`, `ℳ` vì guard tên ký hiệu (36 tên phân biệt bị loại), còn `doc-1` bị A5 đoán `document_language=en` nên
61/98 mô tả viết bằng tiếng Anh cho một giáo trình tiếng Việt. Người gán nhãn không ngồi xuống được cho tới khi vé
19 xong, và việc gán nhãn tốn người chứ không tốn máy.

**Vé 20 và 21 chạy song song với 19** vì chúng đo trên artifact đã có. Nhưng 21 chặn bởi 20 (A10 chỉ đúng khi A9
giao cho nó một DAG thật), và 22 chặn bởi 21 (đo τ trên lộ trình còn phá hoà theo thứ tự chương thì đối chứng đã
nhiễm).

## Luật chung cho mọi vé

- **Mọi khâu LLM dùng `gemini-3.1-flash-lite`, `temperature` 0.** Không chạy mô hình mạnh hơn.
- **Trần chi phí cả giai đoạn: 50 USD.** Mỗi lượt chạy thật ghi số lời gọi, token và chi phí cộng dồn vào vé.
- **Test chạy khi chặn mạng**, không ghi lại fixture nào trừ vé 10. Toàn bộ test hiện có phải xanh.
- **Test chỉ được nhận khi nó đỏ lúc phá đúng thứ nó giữ.** Mỗi vé nộp danh sách đột biến đã thử và test nào bắt.
- **Không sửa bộ vàng đã đóng băng**, gồm `tests/fixtures/a4/gold-blind.json`.
- **Đổi prompt là đổi hành vi:** phải ghi lại fixture hợp đồng, chạy lại, và chấm theo luật viết trước
  (`src/doc2roadmap/application/prompts/README.md`).
- **Chất lượng trên hạn chót.** Mốc là 2026-10-03 nhưng chủ dự án sẽ dời nếu cần; không cắt phương pháp để kịp lịch.
- Số đo thật của vé dán thẳng vào vé, không để trong chat.
