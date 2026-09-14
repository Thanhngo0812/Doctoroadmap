# 08 — Chạy toàn tài liệu: song song, cổng chặn, chính sách lỗi

**What to build:** Một lệnh chạy A3 trên **cả tài liệu** — 116 section song song — và khi có gì bất
thường thì **hệ thống kêu lên** thay vì chạy xong rồi trả kết quả thủng.

## Ba luật hỏng-thì-kêu

| Tình huống | Hành động |
|---|---|
| Section trích ra 0 thực thể | Cảnh báo `empty_extraction` kèm tên section, gom theo khuôn cảnh báo B0 |
| **> 40% section rỗng** | **DỪNG pipeline** — prompt hỏng hoặc tài liệu không phải giáo trình |
| JSON hỏng | **1 lượt sửa** kèm thông báo lỗi cụ thể, đúng khuôn executor 2b |
| Lỗi mạng / hạn mức | Lùi theo cấp số nhân |
| Section lỗi dai dẳng | Thử lại ở **cuối**; vẫn lỗi ⇒ ghi `coverage_incomplete` |

**Luật quan trọng nhất là luật cuối.** Bỏ qua section lỗi rồi vẫn đóng băng artifact nghĩa là lần chạy
sau thấy hash khớp, **tái dùng bản thủng, không ai biết**. Artifact có lỗ tệ hơn không có artifact. Đây
là lần thứ năm dự án gặp hình dạng *"một thứ trông như đang chạy nhưng không sinh ra gì"*.

Cổng 40% cũng vậy: phát hiện muộn thì **đã chạy hết 116 section**.

## Quy mô

```
116 section song song · ~460 lượt gọi (xấu nhất 812)
dự kiến 390–730 thực thể học được · 79 media
```

**Blocked by:** 03 — cần luồng một section chạy đúng trước khi nhân lên 116.

**Status:** done

- [x] Một lệnh chạy A3 trên cả tài liệu; section chạy **song song**, độ song song cấu hình được
- [x] Cảnh báo `empty_extraction` kèm tên section, gom trùng lặp theo khuôn B0 (`×N`)
- [x] Vượt **40%** section rỗng ⇒ dừng, báo rõ lý do, **không** ghi artifact
- [x] JSON hỏng ⇒ đúng **một** lượt sửa kèm thông báo lỗi; hỏng tiếp ⇒ tính là section lỗi
- [x] Section lỗi được **thử lại ở cuối** trước khi kết luận
- [x] Còn section lỗi ⇒ `coverage_incomplete` trong kết quả (ticket 09 dùng cờ này để chặn đóng băng)
- [x] Có test: 50% section rỗng ⇒ dừng · 30% rỗng ⇒ chạy tiếp kèm cảnh báo
- [x] Có test: một section lỗi dai dẳng ⇒ `coverage_incomplete`, các section khác vẫn ra kết quả
- [x] Chạy thật bốn tài liệu, ghi số: thực thể theo kiểu, số lượt gọi, section rỗng, section lỗi
