# W-27 — Hiện lý do xếp hàng khi hết trần dựng trong ngày

**Nguồn:** chủ dự án 2026-10-29, trả lời câu hỏi sau nghiệm thu W-26 ("lý do xếp hàng khi hết trần ngày chỉ hiện ở cửa sổ worker; muốn hiện trên web?"):
"có làm viết vé thêm".
**Ai:** subagent lõi (mốc 1, backend + hợp đồng) rồi subagent web (mốc 2, React, **bắt buộc taste-skill**) · **Chi phí:** 0 USD · **Chặn bởi:** W-26
(đã ghép `843c07ef`) · **Trạng thái:** ready-for-agent, xếp sau W-17.2.

## Vì sao

Khi tổng chi dựng hôm nay chạm `system_daily_build_max_usd` (máy chủ demo: 10 USD/ngày, giờ Việt Nam), worker không nhận việc mới; bản dựng nằm `queued`
tới 00:00 hôm sau. Hiện chỉ cửa sổ worker in lý do (`demo_local.waiting_reason`). Trên web người dùng chỉ thấy "đang chờ", không biết phải chờ tới mai.

## Mốc 1 — backend và hợp đồng (subagent lõi)

- Thêm vào DTO bản dựng (`BuildService._view`, hợp đồng `build-1`) một trường có thể null, ví dụ
  `waiting: {"reason": "daily_build_cap", "resumes_at": "<ISO, 00:00 giờ Việt Nam hôm sau>"}`, chỉ khác null khi `status == 'queued'`, không huỷ, và
  trần ngày đang chạm (`PostgresBuildStore.cap_reached`). Áp cho mọi máy chủ có đặt trần, không riêng demo.
- Đọc quy tắc phiên bản hợp đồng trong `doc/web-chuc-nang-spec.md`: trường thêm có thể null mà spec cho giữ `build-1` thì giữ; nếu spec đòi đổi
  phiên bản thì đổi và ghi lý do. Cập nhật OpenAPI xuất ra.
- Không lộ số tiền: người dùng thường chỉ biết hệ thống đã chạm giới hạn dựng hôm nay và giờ chạy lại; không có USD đã chi, trần, hay bản dựng người khác.
- Một nguồn sự thật: worker (`waiting_reason`) và DTO dùng chung một hàm tính "đang chờ vì trần ngày" và giờ chạy lại, không viết hai lần.
- Test (PostgreSQL, đỏ trước trên bản sai): chạm trần → trường có, `resumes_at` đúng 00:00 Asia/Ho_Chi_Minh kể cả khi giờ UTC đang ở ngày trước;
  chưa chạm, đã huỷ, đang chạy, không đặt trần → null; phản hồi không chứa số USD; phép phá bỏ điều kiện `queued`/bỏ múi giờ bị bắt.

## Mốc 2 — React (subagent web, sau khi mốc 1 đạt)

- Trang tiến trình bản dựng và thẻ khoá học: khi `waiting` khác null, hiện câu tiếng Việt rõ ràng (ví dụ "Hệ thống đã dùng hết lượt dựng hôm nay. Bản
  dựng sẽ tự chạy lúc 00:00 ngày 30/10.") theo giờ Việt Nam; vẫn polling, tự đổi khi worker nhận việc. Không đổi luồng huỷ.
- Áp taste-skill (`.agents/skills/` theo sổ tay mục 4b) và token/thiết kế hiện có; 390/768/1280, sáng/tối.
- Test React: hiện đúng câu và giờ, null thì không hiện, chuyển trạng thái thì câu biến mất; phép phá đổi múi giờ bị bắt.

## Tiêu chí nghiệm thu

- [ ] Mốc 1: test backend W-27 + `src/web/backend/tests` qua runner xanh (trừ ca thiếu fixture W-15 đã biết), OpenAPI cập nhật, bảng phá.
- [ ] Mốc 2: React toàn bộ + build xanh, ảnh ba khổ, bảng phá.
- [ ] Trên máy chủ demo: hạ trần tạm thời bằng DB thử (không chi tiền thật) để thấy câu chờ trên web.
