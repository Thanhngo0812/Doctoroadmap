# 12 — Đo Jaccard: tầng này ổn định tới đâu

**What to build:** Manifest đồ thị trả lời được câu **"chạy lại có ra kết quả như cũ không, và giống bao
nhiêu phần trăm?"**

## Vì sao đây không phải chỉ số tuỳ chọn

Frontiers in Immunology 2026: bốn LLM, **cùng corpus, cùng schema** → Jaccard từng cặp **0,06–0,11**,
66–75% cạnh chỉ một mô hình có. Kết luận nguyên văn: *"mô hình, chứ không phải tài liệu, đã viết ra phần
lớn đồ thị."*

`temperature = 0` **không cứu được** chuyện này — nó chỉ giữ ổn định trong cùng một mô hình. Mà đổi mô
hình là việc sẽ xảy ra: nhà cung cấp ra bản mới, bản cũ bị khai tử.

Dự án đã dựng cả kiến trúc tất định cho B0 — ghim tokenizer, ghim adapter, băm config — rồi sẽ đặt lên
trên nó một tầng mà **đổi mô hình là đổi hai phần ba nội dung**. Không thể làm tầng đó tất định, nhưng
**bắt buộc phải làm nó khai báo được**.

## Khoá so

```
Jaccard(A,B) = |A ∩ B| / |A ∪ B|
```

**Khoá: tên chuẩn hoá (thường hoá + bỏ dấu câu) cộng giao tập alias.** Hai thực thể là một nếu tập alias
giao nhau.

**Không dùng embedding để khớp** — đó là dùng chính thứ đang bị nghi ngờ để chấm điểm sự ổn định, vòng
luẩn quẩn làm đẹp số một cách giả tạo.

**Blocked by:** 09 — cần artifact có phiên bản để so hai lần chạy.

**Status:** done

- [x] `model_id` ghim trong manifest **ngang hàng** `tokenizer_id` của B0 — không phải chi tiết cấu hình
- [x] Lệnh so hai phiên bản artifact, in **hai số riêng: Jaccard thực thể và Jaccard cạnh**
- [x] Khoá so là tên chuẩn hoá + giao alias; **không** dùng embedding
- [x] Manifest ghi Jaccard so với lần chạy trước của cùng tài liệu
- [x] Có test: hai tập giống hệt ⇒ 1,0 · không giao ⇒ 0 · ví dụ dựng tay ra đúng phân số
- [x] Có test: hai thực thể khác tên nhưng **giao alias** ⇒ tính là một
- [x] Chạy thật hai lần trên cùng tài liệu cùng mô hình, ghi lại Jaccard — **đây là số đo đầu tiên
      của dự án về độ ổn định tầng LLM**, ghi vào báo cáo dù kết quả có xấu
