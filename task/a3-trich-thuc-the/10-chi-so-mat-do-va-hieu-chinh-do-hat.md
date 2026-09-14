# 10 — Chỉ số mật độ: biến độ hạt thành số đo được

**What to build:** Người chỉnh prompt **nhìn số biết mình đang trích thô hay mịn**, thay vì đoán.

## Độ hạt là thứ được đo, không phải thứ được khai

Không có tham số `granularity`. Núm vặn thật là **ví dụ few-shot** — và núm mạnh nhất là **ví dụ phủ
định**, vì ranh giới nằm ở ca biên chứ không ở ca rõ:

```
TRÍCH        : Overfitting · Regularization L2 · Laplace Smoothing
KHÔNG TRÍCH  : "tập dữ liệu"  — thuật ngữ chung, không được giảng ở đây
               "α = 1"         — tham số của một kỹ thuật, không phải khái niệm
               "Chương 3"      — cấu trúc tài liệu
```

## Bộ chỉ số

| Chỉ số | Thô | **Đích** | Mịn |
|---|---|---|---|
| Thực thể `learnable` / 1000 token | 3–5 | **8–15** | 20+ |
| Trên corpus 48.694 token | 146–243 | **390–730** | 970+ |
| Trên mỗi section | 1–2 | **3–6** | 8+ |
| Tỉ lệ ứng viên có tên trùng xuyên section | cao | vừa | thấp |

**Đếm phải tách `learnable` khỏi tổng** — kiểu mở làm tổng phồng lên trông như mịn trong khi mật độ
khái niệm học được vẫn thô.

Chỉ số cuối là dấu hiệu ngầm hay bị bỏ qua: khái niệm thô **lặp lại xuyên tài liệu**, khái niệm mịn chỉ
xuất hiện một lần. Trước merge, mỗi ứng viên vốn chỉ thuộc một section nên `single_chunk_ratio` luôn
bằng 1 và không có giá trị. Thay vào đó, dùng chuẩn hoá so node A3 (B0 + casefold + bỏ dấu câu), tìm tên có mặt ở ít nhất hai section,
rồi chia số ứng viên mang các tên đó cho tổng ứng viên `learnable`. `single_chunk_ratio` chỉ đo ở đợt 2a
sau khi các nguồn đã được hợp nhất.

**Blocked by:** 08 — cần chạy toàn tài liệu mới có mẫu đủ để đo.

**Status:** done

- [x] Lệnh báo cáo in đủ bốn chỉ số cho mỗi tài liệu và cho toàn corpus
- [x] Thước đo trước merge là `cross_section_duplicate_name_ratio`; không báo
      `single_chunk_ratio` vô nghĩa ở A3
- [x] Mật độ đếm **chỉ** thực thể `learnable`; tổng thực thể báo riêng
- [x] Thêm cột A3 vào **bộ số vàng bốn tài liệu** đang có: thực thể theo kiểu, thực thể học được, mật độ,
      tỉ lệ có bằng chứng, số kiểu phân biệt
- [x] Giữ nguyên luật đã có: **đổi số vàng phải kèm giải thích trong cùng commit**
- [x] Có test: bộ chỉ số tính đúng trên đầu vào dựng tay
- [x] Chạy thật, ghi mật độ hiện tại của bốn tài liệu và **kết luận đang thô hay vừa hay mịn**
- [x] Nếu lệch dải 8–15, chỉnh ví dụ few-shot và ghi lại số trước/sau — đây là vòng hiệu chỉnh, làm
      trong ticket này chứ không hoãn
