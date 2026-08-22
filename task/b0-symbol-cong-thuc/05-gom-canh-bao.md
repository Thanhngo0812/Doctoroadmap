# 05 — Gom cảnh báo trùng lặp

**What to build:** Người vận hành mở danh sách cảnh báo và **đọc được nó trong một màn hình**, thay vì cuộn qua
264 dòng giống hệt nhau.

## Cơ chế cảnh báo đang tự đánh bại chính nó

Tài liệu thứ hai sinh ra danh sách như thế này:

```
"empty_node: dropped formula"
"empty_node: dropped formula"
… (264 lần)
"orphan_caption: Chú ý . Với mẫu hai chiều như sau:"     <- lọt giữa đống này
"empty_node: dropped formula"
"orphan_caption: Trong đó: m j = n 1j + n 2j + ..."      <- và cái này
```

Hai cảnh báo **chú thích mồ côi** — đúng loại lỗi mà một đợt trước đã bỏ công vá, và đã dựng cả một cơ chế
thống kê để phát hiện — nằm lẫn giữa 264 dòng lặp và **không ai nhìn thấy**.

Một cảnh báo không đọc được thì bằng không có cảnh báo. Đây là lần thứ tư dự án gặp hình dạng lỗi *"một thứ
trông như đang bảo vệ nhưng không bảo vệ gì"*.

## Gom theo loại, không gom theo chuỗi

Cảnh báo chú thích mồ côi **kèm nguyên văn** chú thích, nên hai cái đó khác chuỗi nhau. Gom theo chuỗi sẽ không
gộp được gì cả với cảnh báo công thức, mà lại làm mất nguyên văn nếu hai chú thích trùng nhau.

Gom theo **loại** thì 264 dòng công thức thành một, còn hai cảnh báo chú thích giữ nguyên văn của từng ca.

**Blocked by:** 02 — cần phiên bản mới, nếu không artifact cũ với danh sách chưa gom bị dùng lại im lặng.

**Status:** completed — 2026-08-22

- [x] Cảnh báo cùng **loại** được gom thành một dòng kèm **số đếm**
- [x] Cảnh báo có kèm nguyên văn — như chú thích mồ côi — vẫn giữ được nguyên văn của từng ca
- [x] Thứ tự các loại trong danh sách ổn định giữa hai lần chạy trên cùng đầu vào
- [x] Danh sách đã gom được ghi vào manifest và in ra ở dòng lệnh
- [x] Có test: 300 cảnh báo cùng loại ⇒ **một** dòng kèm số đếm đúng
- [x] Có test: một cảnh báo hiếm lẫn giữa 300 cảnh báo thường ⇒ **vẫn nhìn thấy** sau khi gom
- [x] Có test: hai cảnh báo cùng loại nhưng khác nguyên văn ⇒ **không** mất nguyên văn nào
- [x] Có test: tài liệu không có cảnh báo nào ⇒ danh sách rỗng, không phải một dòng "0 cảnh báo"
- [x] Ingest lại tài liệu hai: danh sách cảnh báo đọc được trong một màn hình
