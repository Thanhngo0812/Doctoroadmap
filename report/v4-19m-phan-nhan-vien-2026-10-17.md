# 19m — Phần nhân viên

Ngày 2026-10-17. Cổng 19l đã qua. Chỉ sửa phần cấu hình, README và kiểm thử được giao trong vé 19m; không chạy lại pipeline hoặc gọi mô hình trả phí. **Chi phí API: 0 USD.**

## Thay đổi

- `Settings.upstream_chain` và `DOC2ROADMAP_UPSTREAM_CHAIN` trong `.env.example` mặc định `gop`. Đọc `Settings()` thực tế trên máy cũng ra `gop`; không sửa `.env`.
- README hướng dẫn chọn lại `v3` bằng CLI hoặc môi trường, giữ ngoại lệ `--names-only`/`--prepare`, và cảnh báo chạy `a4` mặc định trên tài liệu cũ sẽ chuyển chuỗi của lần `roadmap` sau. Nếu giữ canonical v3 cũ thì roadmap vẫn dùng v3.
- Test mặc định trong `test_canonical_defaults_19d.py` chuyển theo 19m. Test mới thực thi CLI A4 và composition thật với fixture A3, embedding lưu sẵn và mô hình giả: canonical v3 → A4 mặc định → canonical có neo gop; roadmap sau đó đi qua danh sách stage gop. Chọn `--upstream-chain v3` tường minh giữ danh sách stage v3. Các stage roadmap dùng mô hình giả để quan sát thứ tự, không dựng đồ thị có trả phí.
- Stub `build_canonical` ở test ngoại lệ vàng của CLI nhận các keyword theo chữ ký hiện có; giữ toàn bộ assertion về kiểm vàng.

## Kiểm thử

Trước sửa: test mặc định mới và test CLI không chỉ định chuỗi cùng đỏ vì còn `v3`; nhánh chọn v3 tường minh xanh. Sau sửa: nhóm 19d/CLI gop/đồ thị/17k **51 test qua**; bộ CLI sau sửa stub **11 test qua**. Không cộng các số này vào kết quả toàn kho vì có giao nhau.

Lượt toàn kho đầu: **1.636 qua, 2 lỗi**, 303,75 giây. Hai lỗi thuộc test quiz Pha B đọc `load_learning_graph(..., "doc-1")` mới nhất nhưng cố định `module_023` và đòi 5 câu. Đối chiếu cùng artifact với config từ HEAD (mặc định v3) vẫn lỗi y hệt. Chẩn đoán offline: graph v45 sinh 5 câu, graph v53 sau cổng sinh 4 câu; module đã đổi theo bàn giao Pha B.

Chỉ ghim hai lời nạp trong `test_phase_b_quiz.py` vào `graph_version=45`, là đầu vào v3 của hai phép kiểm cũ. Không đổi logic quiz hoặc nới assertion 5 câu. Hai ca đã xanh sau sửa. Tệp test Pha B này có sẵn nhưng chưa được theo dõi trong Git; patch riêng cho hai lời nạp và một dòng giải thích nằm ở `tmp/19m/quiz-fixture.patch`, để người commit phân biệt với phần Pha B có sẵn.

Lượt hồi quy cuối: **1.638 test qua**, 0 lỗi, 0 bỏ qua; mã thoát 0, **243,95 giây**. `git diff --check` qua. Đây là kết quả toàn workspace hiện tại, gồm cả các test Pha B chưa được theo dõi trong Git.

```powershell
$env:HF_HUB_OFFLINE='1'
$env:TRANSFORMERS_OFFLINE='1'
.venv\Scripts\python.exe -m pytest -p no:cacheprovider --basetemp=tmp/pytest-19m-full-final --junitxml=tmp/pytest-19m-full-final.xml --tb=short
```

## Bàn giao commit

Theo vé 19m, Claude kiểm nghiệm thu rồi commit tài liệu và cấu hình cùng một đợt. Phần nhân viên chưa stage/commit riêng. Các tài liệu ADR, `CONTEXT.md`, spec và bàn giao Pha B đã có của Claude được giữ nguyên để commit chung.
