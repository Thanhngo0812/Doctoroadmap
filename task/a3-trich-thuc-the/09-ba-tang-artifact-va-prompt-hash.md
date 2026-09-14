# 09 — Ba tầng artifact và `prompt_hash`

**What to build:** Chỉnh prompt suy luận cạnh ở đợt sau **không phải trích lại 116 section**. Vòng lặp
thử nghiệm tính bằng phút thay vì bằng giờ — đúng thứ kiến trúc đóng băng của B0 đã trả lương (cắt lại
chunk không phải parse lại).

```
candidates/{doc}/v{n}   <- đổi prompt trích      ⇒ chỉ nhích tầng này
canonical/{doc}/v{n}    <- đổi ngưỡng merge      ⇒ chỉ nhích tầng này   [đợt sau]
graph/{doc}/v{n}        <- đổi prompt suy cạnh   ⇒ chỉ nhích tầng này   [đợt sau]
```

Đợt này dựng **khung ba tầng** và cài đặt đầy đủ tầng `candidates`; hai tầng sau để đợt merge và đợt
suy luận cạnh dùng.

## `prompt_hash` — và cái bẫy đã biết

Hash gồm: template + **ví dụ few-shot** + `model_id` + tham số sinh + định nghĩa schema + danh sách
kiểu mồi.

**Ví dụ few-shot bắt buộc phải vào hash.** Chúng là **núm vặn độ hạt** (ticket 10). Sửa ví dụ mà hash
không thấy thì artifact cũ được tái dùng im lặng, và người sửa tưởng ví dụ không có tác dụng — đúng lỗi
`adapter_version` mà B0 đã trả giá để học.

Nguyên tắc: **mọi thứ có thể đổi output đều phải nằm trong hash.**

**Blocked by:** 08 — cần đầu ra toàn tài liệu và cờ `coverage_incomplete` để quyết định có đóng băng không.

**Status:** done

- [x] Khung ba tầng khai báo trong cổng kho artifact, theo khuôn `find_parse`/`find_chunks` đang có
- [x] Tầng `candidates` cài đặt đủ: tìm thấy artifact khớp hash ⇒ **không chạy lại**
- [x] `prompt_hash` gồm đủ sáu thành phần; **có test**: đổi một ví dụ few-shot ⇒ hash đổi ⇒ chạy lại
- [x] Có test: đổi `model_id` ⇒ hash đổi · đổi tham số sinh ⇒ hash đổi
- [x] Manifest ghi `model_id`, `prompt_hash`, sổ đăng ký kiểu, và toàn bộ thống kê của ticket 08
- [x] **`coverage_incomplete` ⇒ TỪ CHỐI đóng băng artifact**, báo rõ section nào thiếu
- [x] API key **không** vào hash, không vào manifest, không vào log
- [x] Có test: chạy hai lần cùng cấu hình ⇒ lần hai không gọi mô hình lần nào
