# DG-19 — (Tuỳ chọn) Tắt A2, tắt lọc trạng thái dạy A5

**Nguồn:** spec mục 11, 12; kế hoạch Q36 · **Ai:** agent · **Chi phí:** 0 khi cài · **Chặn bởi:** DG-08 · **Trạng thái:** chỉ làm nếu lịch 07–09/11 còn chỗ

## Làm được gì

Hai công tắc ablation, mặc định tắt. Khi tắt, đầu ra y hệt.
- **Tắt A2:** mọi mục coi là `noi_dung`.
- **Tắt lọc A5:** mọi khái niệm trích được đều vào dãy học, kể cả `mentioned_only` và `prior_knowledge`.

DG-08 nhận hai biến thể này.

## Tiêu chí

- [ ] Tắt thì artifact y hệt trên fixture.
- [ ] Bật thì đúng hành vi trên fixture.
- [ ] Cổng toàn repo xanh.
