# Chạy lại doc-6 bằng chuỗi gộp (2026-10-18)

**Ai chạy:** Claude (phiên Pha B), chủ dự án duyệt ngày 2026-10-18 ("duyệt doc6 cho bạn luôn").
**Chi thật:** khoảng **0,007 USD** (gemini-3.1-flash-lite, temperature 0).

**Lý do chạy:**
- Đồ thị doc-6 v17 thuộc chuỗi v3 và không có câu neo ở 28/28 khái niệm.
- Hệ quả: quiz điền khuyết ra 0 câu, và bài giảng thiếu câu định nghĩa ([báo cáo kiểm thử](kiem-thu-pha-b-2026-10-18.md), mục 3.5, 6).
- Phải chạy trước khi xuất gói cho bộ câu hỏi thử (vé 19a), để `chunk_id` không đổi sau khi agentic đã soạn câu.

## Mã và lệnh

- **Commit mã:** `bbcfcc6`, chạy từ worktree sạch `tmp/pha-b-doc6/ma`, qua `scripts/pha-b/doc6/chay_tu_commit.py`.
  - Script dừng nếu worktree bẩn, sai commit, hay import nhầm mã của thư mục làm việc.
  - Gốc lệnh là repo chính, để dùng kho `artifacts/` và `.env`.
- **Lệnh:** theo khuôn cổng 19l; chuỗi gộp nay là mặc định nên không cần cờ `--upstream-chain`.
  - `a4 --doc-id doc-6 --gold artifacts/a4-gold.json --no-gold-for-doc --language vi`: dry-run trước, rồi `--allow-spend`;
  - `roadmap --doc-id doc-6`: dry-run trước, rồi `--allow-spend`.
- **Không gán lại nhãn vùng theo luật 05a.** Canonical dùng chunk v4, như ở cổng 19l. Phía pha A chỉ áp 05a cho xstk và doc-4 (vé 05b).
- **Nhật ký:** `tmp/pha-b-doc6/` (tệp `a4.json`, `roadmap.json`, `*.err`, và các dry-run).

| Bước | Kết quả | Lời gọi mô hình | USD | Giây |
|---|---|---:|---:|---:|
| `a4` | canonical v3: 38 nút, 27 nút chữ | 0. Neo, gộp, mô tả, kiểm đều tái dùng cache | ≈ 0, chỉ embedding 31 tên | 11 |
| `roadmap` | đồ thị v18–v25 | pass chính: 12.706 token vào, 902 ra | 0,0045 | 21 |
| tên module (trong `roadmap`) | 2 module, cả 2 tên do LLM đặt | 2 | 0,0015 | |
| **Tổng** | | | **≈ 0,007** | 32 |

Embedding hai stage cụm và mention dùng 3.895 token, dưới 0,001 USD.

## So với đồ thị cũ

| | v17 (chuỗi v3) | **v25 (chuỗi gộp)** |
|---|---:|---:|
| Module | 4 | 2 |
| Khái niệm học | 28 | 11 |
| Khái niệm có câu neo | 0 | 11 |
| Nút chỉ được nhắc tới | 0 | 16 |
| Cạnh `requires` | 24 | 4 |
| Câu điền khuyết (quiz không LLM, 0 USD) | 0 | 3 |
| Bài giảng có câu định nghĩa (đường không LLM, 0 USD) | 14/28 | 11/11 |

**Đọc tận nơi:**
- 16 nút chuyển sang "chỉ được nhắc tới" phần lớn là các mục trong đề cương môn học ở slide đầu. Ví dụ "Ngôn ngữ SQL", "Phụ thuộc hàm" là chương sau
  của môn học, nhưng cuốn slide này không dạy. Vì vậy cách xếp mới đúng hơn.
- Module 1: "Cơ sở dữ liệu và quản trị", gồm Dữ liệu, Hệ thống tập tin, Cơ sở dữ liệu, Giảm trùng lắp thông tin, Người dùng cuối, Quản trị viên.
- Module 2: "Mức quan niệm và Mức ngoài", gồm Xây dựng, Hệ Quản Trị CSDL, Mức ngoài, Mức quan niệm, Mức trong.
  - Tên lệch trọng tâm: module có cả "Mức trong" và "Hệ Quản Trị CSDL".
  - "Xây dựng" là khái niệm lạ.

  Vé 28 xử lý phần tên; phần khái niệm báo phía pha A.

## Ảnh hưởng tới Pha B

- **Đồ thị mặc định của doc-6 nay là v25.** `load_learning_graph` lấy bản A10 hoàn tất mới nhất.
- **Cache bài giảng và quiz của v17 không dùng lại cho v25,** vì khoá băm theo nút và ngữ cảnh.
- **Bộ câu hỏi thử (19a) xuất gói từ v25.** Còn nhap-mon-ml và naive-bayes ở chuỗi v3.
- **Sổ chi Pha B** (`artifacts/phase_b/live.json`) có thêm 2 dòng `module_title` của doc-6.
