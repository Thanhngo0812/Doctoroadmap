# 05a — Sửa luật đề cương lặp của A2

Ngày 2026-10-17 · Nhân viên · Chi phí mô hình **0 USD**.

## Kết quả

Đã sửa đúng nhánh tiêu đề lặp của `assign_section_roles`. Tiêu đề vẫn phải là
mục con đầu tiên của ít nhất ba mục cha; cả nhóm chỉ bị khoá `de_cuong/structure`
khi độ phủ thân mục bởi tên các mục khác có trung vị ≥ 0,5. Không đủ bằng chứng
thì đi tiếp các nhánh cấu trúc sẵn có. Vì vậy "Cách giải" có `role_source` rỗng
và được gửi cho lớp nhãn LLM; `noi_dung` lúc này chỉ là giá trị mặc định chưa
được quyết, không phải nhãn cấu trúc mới.

Không sửa nhánh mục lục, cuối sách, mở đầu, bước neo, prompt nhãn vùng hay luật
lọc khái niệm ngoài nội dung. Không dùng danh sách từ khoá theo ngôn ngữ.

Chuẩn hoá NFC, casefold, dấu câu/khoảng trắng và số thứ tự đầu tiêu đề; khớp
ranh giới từ, bỏ tên dưới ba ký tự, không tính tên chính nhóm. Mỗi ký tự chữ/số
chỉ tính một lần kể cả khi tên mục khớp chồng. Mục không có ký tự chữ/số không
tham gia trung vị; cả nhóm rỗng thì không đạt. **Trung vị giữ quy ước của bảng
nghiên cứu: giá trị giữa phía trên khi có số lượng chẵn** (`sorted(values)[len(values)//2]`).
Do đó các số dưới đây khớp nguyên giá trị với mã nghiên cứu, không đổi quy ước
thống kê khi đưa luật vào sản phẩm.

## Cache và A3

- `CHUNK_ALGORITHM_ID` vẫn là `section-id-v11-document-structure`. Không thêm
  mã luật vai trò vào config `ingest`, không đổi ID chunk, văn bản hay offset.
- Thêm mã riêng `ROLE_ALGORITHM_ID = numbering-families-v1+repeated-outline-coverage-v1`.
  `label-roles` dùng mã này với hậu tố `+semantic-v3` trong
  `region_roles.algorithm_id`; `refresh_chunk_roles` dùng trong `chunk.role_algorithm_id`.
  Hai đường này không dùng nhầm cache vai trò cũ.
- Trước sửa đã đóng băng hash trên cây mục dựng tay có "Cách giải": config
  ingest `e55402903a795e9e8418ab6579c2869f582e97cb7c4fac7a2cc349f99c851147`,
  toàn bộ trường chunk trừ role
  `4f08fb3fbd078695f7d054d9bfc347e860d7ff68cf7a93f082495a12e9b3e31a`.
  Test sau sửa giữ đúng cả hai hash, tái dùng version ingest cũ, giữ nguyên bytes
  file chunk, và A3 tái dùng artifact ứng viên theo config chunk cũ. Nếu A3 mở
  phiên mô hình, test thất bại ngay.

## Kiểm kho thật, chỉ đọc

Script sản phẩm: `scripts/a2-de-cuong/kiem_05a.py`. Script đọc bản chunk mới nhất
của mỗi tài liệu, bỏ `d01-t01`, `d01-t02` và mọi tên bắt đầu bằng `smoke` trước
khi mở tệp. In đủ tài liệu, tiêu đề, số mục, độ phủ, vai trò theo luật cũ/mới;
`stored_roles` tách riêng nhãn đã có trong artifact vì nhãn lưu có thể thuộc một
phiên bản luật khác. Không tạo artifact mới.

Kết quả **26 tài liệu / 26 nhóm**, chỉ **doc-6 / Nội dung** được luật lặp nhận
là đề cương. Độ phủ khớp chính xác 26/26 giá trị với `norm`/`coverage` của script
nghiên cứu; hash của **384 tệp JSON artifact** trong 26 tài liệu không đổi trước
và sau lượt đối chiếu. Không mở tệp hai tài liệu T-01.

Toàn bộ vai trò theo nhánh lặp cũ là `de_cuong`; các nhánh mở đầu/cuối sách vẫn
được ưu tiên như trước. Trong bốn nhóm có mục mở đầu, một số mục giữ nhãn cấu
trúc đó sau khi rời luật lặp, đúng yêu cầu đi tiếp các nhánh còn lại.

| Tài liệu | Tiêu đề | Số mục | Độ phủ | Vai trò mới |
|---|---|---:|---:|---|
| d01-02 | I. Định nghĩa | 3 | 0.16 | chờ LLM |
| d01-03 | ≅& CÂU HỎI VÀ BÀI TẬP | 4 | 0.08 | chờ LLM |
| d01-03 | a. Vị trí trong bảng tuần hoàn | 3 | 0.00 | chờ LLM |
| d01-04 | CÂU HỎI ÔN TẬP | 6 | — | chờ LLM |
| d01-05 | 1.1. Nguyên liệu, hóа сhất, ԁụng сụ và thiết bị: | 5 | 0.00 | chờ LLM |
| d01-05 | 2.1. Nguyên liệu, hóа сhất, ԁụng сụ và thiết bị: | 5 | 0.00 | chờ LLM |
| d01-05 | Giới thiệu։ | 5 | 0.00 | mở đầu theo cấu trúc; phần còn lại chờ LLM |
| d01-05 | 3.1. Nguyên liệu, hóа сhất, ԁụng сụ và thiết bị: | 5 | 0.00 | chờ LLM |
| d01-05 | 4.1. Nguyên liệu, hóа сhất, ԁụng сụ và thiết bị: | 3 | 0.00 | chờ LLM |
| d01-08 | IX Tóm tắt | 5 | 0.03 | mở đầu theo cấu trúc; phần còn lại chờ LLM |
| d01-10 | THUẬT NGỮ | 6 | 0.29 | chờ LLM |
| d01-10 | 1.1. Khái niệm | 3 | 0.02 | chờ LLM |
| d01-10 | TRẮC NGHIỆM | 7 | 0.09 | chờ LLM |
| d01-11 | Mục tiêu: | 4 | 0.00 | mở đầu theo cấu trúc; phần còn lại chờ LLM |
| d01-12 | CÂU HỎI | 7 | 0.44 | chờ LLM |
| d01-13 | Mục tiêu: | 6 | 0.00 | chờ LLM |
| d01-13 | Đáp án: | 30 | 0.12 | chờ LLM |
| d01-15 | Giới thiệu: | 4 | 0.13 | mở đầu theo cấu trúc; phần còn lại chờ LLM |
| d01-15 | Phương pháp bón: | 3 | 0.10 | chờ LLM |
| d01-15 | * Bón theo cách 1: | 6 | 0.12 | chờ LLM |
| d01-16 | Giới thiệu: | 4 | 0.00 | chờ LLM |
| d01-16 | Câu hỏi ôn tập | 3 | 0.00 | chờ LLM |
| doc-2 | Step 1 | 3 | 0.00 | chờ LLM |
| doc-4 | Câu hỏi ôn tập | 10 | 0.31 | chờ LLM |
| doc-6 | Nội dung | 6 | 0.62 | đề cương / structure |
| xstk-ch3-1 | Cách giải | 13 | 0.00 | chờ LLM |

Dữ liệu máy đọc: [bảng kiểm JSON](v4-05a-kiem-kho-2026-10-17.json).

## Dry-run nhãn vùng

| Tài liệu / đầu vào | Mục chờ LLM | Lô dự kiến | USD ước, chưa retry |
|---|---:|---:|---:|
| xstk-ch3-1, chunk v3 | 43 | 2 | 0,003611 |
| doc-4, mặc định hiện tại quy về chunk v3 từ artifact nhãn v6 | 285 | 8 | 0,033083 |

Đây là dự toán, **không phải chi phí đã chi**. `remaining_items` của CLI tính
theo lô; số mục ở cột thứ hai lấy từ `note` của plan. Chưa thực hiện chuyển
nhãn xstk từ v3 sang v2. Không chạy nhãn thật, A4 hay roadmap, không chạy lại
16 cuốn D-01. Phần chạy/đo thật thuộc 05b của Claude.

Lệnh đã chạy từ gốc repo:

```powershell
$env:PYTHONIOENCODING='utf-8'
.venv\Scripts\python.exe scripts/a2-de-cuong/kiem_05a.py
.venv\Scripts\doc2roadmap.exe label-roles --doc-id xstk-ch3-1 --chunks-version 3 --dry-run --allow-text-quality-reason "Tái lập T10 trên văn bản xstk đã khóa; chấp nhận lỗi chữ VNI đã ghi nhận ở trang 3, không làm sạch hoặc đổi bộ đọc"
.venv\Scripts\doc2roadmap.exe label-roles --doc-id doc-4 --dry-run
```

## Kiểm thử

Trước khi sửa production: **6 failed, 5 passed** ở
`tmp/pytest-05a-red.xml`. Hai assertion riêng của "Cách giải" đều đỏ:

- `test_repeated_heading_needs_body_evidence_before_structural_lock[Cách giải-None-False]`:
  mã cũ gán `de_cuong/structure` thay vì để trống nguồn.
- `test_cach_giai_reaches_label_roles_model_instead_of_being_silently_excluded`:
  mã cũ gửi **0/3** mục cho mô hình giả.

Hai guard cache cũng đã thấy đỏ: `label-roles` tái dùng cache cũ và
`refresh_chunk_roles` trả lại version cũ. Sau sửa, cả hai tạo cấu hình vai trò
mới và tái dùng được chính kết quả mới ở lần kế tiếp.

Test mới ở `tests/unit/application/test_repeated_outline_05a.py`: **19 ca**,
gồm các hình dạng "Cách giải", "Nội dung", thân rỗng, câu hỏi ôn tập, ngôn ngữ
khác; chuẩn hoá/ranh giới/ngưỡng/chồng tên; cache vai trò; config/ID/offset/bytes
ingest và cache A3; script chỉ đọc và bỏ mọi thư mục smoke/T-01.
Nhóm hồi quy A2/A3 cùng bốn tài liệu mẫu: **109 passed**, 18,70 giây,
`tmp/pytest-05a-regression.xml`. Không cập nhật các hash chunk vàng của bốn tài liệu.

Toàn kho: **1.555 passed, 7 cảnh báo deprecation**, 242,10 giây, exit 0;
JUnit `tmp/pytest-05a-full.xml`. Chạy offline:

```powershell
$env:HF_HUB_OFFLINE='1'
$env:TRANSFORMERS_OFFLINE='1'
.venv\Scripts\python.exe -m pytest -p no:cacheprovider --basetemp=tmp/pytest-05a-full --junitxml=tmp/pytest-05a-full.xml --tb=short
```

`git diff --check` qua. Không thêm dependency. Phần production chỉ sửa ba file:
`domain/chunking.py`, `application/use_cases/label_chunk_roles.py` và
`application/use_cases/ingest_document.py`; assertion mã luật vai trò ở test
ingest được sửa tương ứng.

## Bàn giao 05b

Mã 05a đang nằm trong workspace, chưa có commit riêng. HEAD nền `3637d94` không
chứa bản sửa này; không dùng SHA đó làm nguồn gốc artifact mới. Trước khi chạy
05b, cần commit mã 05a và ghim checkout sạch theo vé 05b. Workspace hiện còn
các thay đổi 19n–19o và A1/D-01/Pha B có sẵn; kết quả toàn kho cần hiểu là kiểm
workspace kết hợp, không phải nghiệm thu một commit triển khai riêng.
