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
| Nhân viên | 01, 02, 03, 06, 07, 08, 09, 10, 11 |
| Claude | 04, 05, 12, 13, 14 |

**Cập nhật 2026-09-19:** nhân viên đã hoàn tất code và chạy thật các vé 01, 02, 03, 06, 07, 08, 09, 10. Vé 16
được thêm sau mention map; code/test/cache/precision đã đạt, còn thiếu bảng E1 vì file nhãn thử tìm được là template
trống. Vé 11 đã có đủ ba PDF nhưng bị vé 16 chặn.
Số đo thật, chi phí và danh sách mutation nằm trong feedback của từng vé.

## Thứ tự và cạnh chặn

```text
01 prefactor ─┐
02 clusters ──┴─> 03 mentions ─> 16 provenance ─┬─> 06 pass chính ─> 07 pass phụ ─> 10 fixture ─┐
                                               │              └──> 08 tầng 3 ─> 09 A10         │
04 excel vàng ─────────────────┴─> 05 bộ chấm ─┐                               │
16 ─> 11 nạp tài liệu mới ─────────────────────┴─> 12 chạy E1/E2 ──────────────┴─> 13 chạy 2b + E3/E4/E6 ─> 14 báo cáo
```

Vé **01, 02 và 04 không chặn bởi gì cả**. Vé 11 bị chặn bởi vé 16; vé 04 nằm trên đường găng vì việc gán nhãn tốn
người.

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
