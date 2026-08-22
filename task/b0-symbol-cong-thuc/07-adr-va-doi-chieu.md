# 07 — ADR 0002, từ điển và đối chiếu hai tài liệu

**What to build:** Quyết định kiến trúc nói đúng phạm vi nó đang chi phối, từ điển có chỗ cho công thức, và
toàn bộ đợt được kiểm trên **cả hai** tài liệu thật.

Đây là đợt đầu tiên có hai tài liệu để đối chiếu, và chúng bù khuyết nhau: tài liệu một không có ký tự hỏng mã
nào, tài liệu hai có 653; tài liệu một có một công thức, tài liệu hai có 264.

**Blocked by:** 03, 04, 05, 06 — mọi thay đổi phải nằm đủ trước khi đối chiếu mới có nghĩa.

**Status:** completed — 2026-08-22

## ADR 0002

- [x] Mở rộng phạm vi từ "hình và bảng" sang "**hình, bảng và công thức**": quyết định *tham chiếu đứng ngoài
      khoá băm chunk* nay chi phối cả ba
- [x] Ghi quyết định **dấu vết vào văn bản, nội dung ra chỗ khác** như một khuôn dùng chung — nó đã áp cho hình
      không có chú thích, nay áp cho công thức, và sẽ áp cho bất kỳ nội dung nào tồn tại nhưng không phải chữ
      đọc được
- [x] Ghi quyết định **dấu hiệu trong văn bản là mã trung tính ngôn ngữ**, không phải câu của một ngôn ngữ cụ thể
- [x] Ghi rằng bảng tra Symbol là một **phỏng đoán** — thư viện parse không cho biết font — và vì sao vẫn chấp
      nhận được: ký tự vùng dùng riêng không có nghĩa hợp lệ nào, nên để nguyên là sai chắc chắn

## Từ điển thuật ngữ

- [x] Thêm **công thức** và **tham chiếu công thức**, theo đúng khuôn các mục sẵn có, mỗi mục kèm phần *tránh dùng*
- [x] Rà mục **Chunk**: nó nay có thể chứa cả văn bản, hình, bảng lẫn công thức

## Đối chiếu trên tài liệu một — tiêu chí mạnh nhất của đợt

Tài liệu này có **0** ký tự vùng dùng riêng và **0** tiêu đề lặp ≥2 lần. Nên chỉ **hai nhóm chunk** được phép
đổi định danh.

- [x] Nhóm chứa **một công thức được khôi phục** — đổi
- [x] Nhóm chứa **dấu hiệu hình không có chú thích** — đổi, vì dấu hiệu chuyển sang dạng trung tính ngôn ngữ
- [x] **Mọi chunk còn lại giữ nguyên định danh.** Đổi nhiều hơn thế ⇒ **dừng và tìm ra vì sao** trước khi đóng đợt
- [x] Không thoái lui: cây section vẫn bốn cấp, năm chỗ nối câu qua trang còn nguyên, 9 tham chiếu hình vẫn
      resolve đủ, vị trí ký tự vẫn đúng với mọi chunk

## Đối chiếu trên tài liệu hai

- [x] **Không** ký tự vùng dùng riêng còn sót mà không có cảnh báo
- [x] **263** công thức có mặt, mỗi cái có tham chiếu trỏ đúng vị trí
- [x] `Trong đó:` và `Chú ý .` **không** còn trong danh sách section
- [x] **Không** section nào bắt đầu bằng dấu liệt kê
- [x] Danh sách cảnh báo **đọc được trong một màn hình**
- [x] 51 bảng và 51 tham chiếu bảng **vẫn còn nguyên**
- [x] Vị trí ký tự đúng với mọi chunk; không chunk nào vượt trần cứng

## Đóng đợt

- [x] Toàn bộ bộ test xanh
- [x] Ghi lại số đo sau đợt cho **cả hai** tài liệu, để lần sau còn đối chiếu

> **Hai việc nên ghi vào tài liệu hướng dẫn của dự án**, vì cả hai đã lặp lại đủ nhiều lần:
>
> **Một.** Cả hai lỗi nặng đợt này đều là *"đọc sai thứ thư viện đưa cho"* — ký tự vùng dùng riêng là đọc đúng
> mã nhưng không diễn giải; công thức là đọc đúng đối tượng nhưng sai trường. Cùng dạng với thông báo lỗi ảnh
> lọt vào nội dung ở đợt hình. Ba lần rồi: **khi một thư viện trả về thứ trông rỗng hoặc trông lạ, kiểm mọi
> trường của nó trước khi kết luận là không có gì.**
>
> **Hai.** Công thức bị bỏ đã được ghi nhận từ vòng review thứ hai và xếp mức thấp — vì tài liệu đó có đúng một
> công thức. Tài liệu thứ hai có 264. **Một tài liệu chỉ cho một con số, và con số quyết định mức độ.**
