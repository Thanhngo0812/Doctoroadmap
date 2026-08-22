# 01 — Ba tham số trần vào cấu hình và bump

**What to build:** Người vận hành nhìn manifest và thấy **ba** trần token thay vì một, chỉnh được cả ba qua cấu
hình, và đổi bất kỳ trần nào cũng sinh phiên bản chunk mới. Hành vi cắt **chưa đổi** trong ticket này — hai
trần mới còn chưa ai dùng tới.

Đây là **prefactor**: nó giữ cho hai nhánh sau không chặn nhau vì cái bump.

## Ba trần, mỗi trần một câu hỏi

| Tham số | Mặc định | Trả lời câu hỏi |
|---|---:|---|
| trần văn xuôi | 512 | bao nhiêu chữ thành một đơn vị truy hồi tốt |
| **trần bảng** | **2048** | bảng lớn cỡ nào thì vẫn nên nằm gọn một chỗ |
| **trần cứng** | **6000** | ngưỡng nào chắc chắn an toàn với mô hình nhúng |

## Vì sao trần cứng là tham số chứ không phải hằng số

Đổi mô hình nhúng là đổi giới hạn, và bắt sửa mã cho một con số vận hành là sai chỗ. Bù lại mặc định phải đặt
đủ thấp để không ai vô tình nâng nó lên sát giới hạn thật — giới hạn của mô hình dự kiến là **8192**, và ta đếm
bằng tokenizer **Gemma** chứ không phải của Gemini, nên sai số giữa hai bộ đếm không đo được.

**Blocked by:** Không — bắt đầu ngay.

**Status:** completed — 2026-08-21

- [x] Cấu hình có thêm trần bảng và trần cứng, cả hai có mặc định như bảng trên
- [x] Cả ba trần **tham gia hash cấu hình** — đổi một trần là sinh phiên bản chunk mới
- [x] Cả ba trần được ghi vào manifest tầng chunk
- [x] Cả ba trần đi từ cấu hình xuống tới tầng cắt, kể cả qua lệnh dòng lệnh
- [x] Phiên bản thuật toán tăng đúng **một** bậc
- [x] Phiên bản adapter **không** đổi — đợt này không chạm cây parse
- [x] Hành vi cắt **không đổi một chút nào** trong ticket này
- [x] Có test: đổi trần bảng làm hash cấu hình đổi theo
- [x] Có test: đổi trần cứng làm hash cấu hình đổi theo
- [x] Toàn bộ bộ test vẫn xanh, **không bài nào phải sửa khẳng định**
- [x] **Ingest lại tài liệu thử nghiệm và khẳng định tập định danh chunk giống hệt trước ticket này**
