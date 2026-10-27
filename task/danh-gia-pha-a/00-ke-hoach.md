# Đánh giá Pha A — kế hoạch vé DG-01…DG-19

**Nguồn:**
- spec `doc/danh-gia-pha-a-spec.md`, chuẩn của mọi vé; ADR 0029;
- kế hoạch `report/ke-hoach-danh-gia-pha-a-2026-10-26.md`, gồm 39 quyết định Q1–Q39 ở mục 15;
- văn liệu `report/nghien-cuu-phuong-phap-danh-gia-pha-a-2026-10-26.md`;
- bản hội đồng `evaluation/trinh-bay-hoi-dong.md`.

**Bảo vệ:** 2026-11-14. Vàng đóng băng 06/11, mã và giao thức đóng băng 07/11, chạy tập thử 07–09/11.

**Cách làm:** hai agent Sonnet do Claude quản lý, chạy theo hai làn. Claude tự làm DG-01, DG-05, DG-18, viết hướng dẫn gán và lời nhắc B5, rồi nghiệm thu mọi vé.
Mỗi vé có worktree `tmp/dg-NN` và nhánh `work/dg-NN-<tên>`. Claude ghép trên main local, **không push**.

## Bảng vé

| Vé | Việc | Ai | Chặn bởi | Hạn | Trạng thái |
|---|---|---|---|---|---|
| [01](01-manifest-va-boc-chuong.md) | Manifest sách, bốc chương theo seed, kiểm PDF gốc | Claude | — | 28/10 | **đã ghép** (34a7920, 27/10); manifest tập phát triển xong; tập thử: 4/8 cuốn đã bốc theo boc-1 (lý, kinh tế, luật, văn), 4 cuốn chờ sách thay |
| [02](02-phieu-g3-kho-khai-niem.md) | Hướng dẫn và phiếu G3 trọn vòng, tới kho chốt | Claude (hướng dẫn) + agent A | lược đồ manifest của 01 | 28/10 | **đã ghép** (123ca21, 27/10); hướng dẫn g3-1 chủ dự án duyệt 27/10 |
| [03](03-phieu-g4-quan-he.md) | Hướng dẫn và phiếu G4 trọn vòng, tới vàng chính/hợp/giao | Claude (hướng dẫn) + agent A | 02 | 29/10 | **đã ghép** (123ca21, 27/10); hướng dẫn g4-1 chủ dự án duyệt 27/10 |
| [04](04-hop-dong-xuat-cham-a8-a10.md) | Hợp đồng đánh giá, bộ xuất hệ chính, chấm A8/A10, đối chiếu bộ chấm cũ | agent B | — | 29/10 | **đã ghép** (da64233, 27/10); đối chiếu bộ chấm cũ lệch 0 |
| [05](05-thong-ke-va-dong-thuan.md) | Thống kê và đồng thuận | Claude, agent soát | — | 31/10 | **đã ghép** (34a7920, 27/10); agent soát xong, sửa theo soát |
| [06](06-cong-tac-pipeline.md) | Công tắc pipeline mặc định tắt: giây chờ embedding, seed xáo pass chính, lọc cặp pass phụ | agent B | 04 | 30/10 | nghiệm thu trên `work/dg-06-cong-tac` (561aaaa); **chờ cổng toàn repo** rồi ghép |
| [07](07-b5-llm-doc-thang.md) | B5 "LLM đọc thẳng" | Claude (lời nhắc) + agent B | 04 | 31/10 | agent B đang cài (27/10) |
| [08](08-dieu-phoi-luot-chay.md) | Điều phối lượt chạy, chạy một khoảng chương phát triển tới bảng điểm | agent B | 04, 06 | 31/10 | chưa làm |
| [09](09-can-khai-niem.md) | Căn khái niệm: luật tự động, phiếu căn tay mù, nhật ký, phiếu kiểm 20% | agent A | 02, 04 | 01/11 | chưa làm |
| [10](10-thuoc-khai-niem-va-truy-nguyen.md) | Thước A3/A4/A5 và truy nguyên | agent A | 09 | 01/11 | chưa làm |
| [11](11-baseline-va-phat-lai.md) | Baseline B1–B4, bộ phát lại A9 → A10 và các biến thể | agent B | 04 | 01/11 | chưa làm |
| [12](12-nhap-g1-g2-va-phieu-duyet.md) | Gói nháp G1/G2, lỗi cài, phiếu duyệt | agent A | lược đồ manifest của 01 | 31/10 | agent A đang cài (27/10) |
| [13](13-cham-a1-a2.md) | Chấm A1/A2 | agent A | 04, 12 | 02/11 | chưa làm |
| [14](14-oracle-a8.md) | Oracle A8 trên kho chốt G3 | agent B | 02, 08 | 02/11 | chưa làm |
| [15](15-quy-loi-theo-khau.md) | Quy lỗi 7 bậc, xếp loại cạnh ngoài vàng | agent B | 10, 13 | 03/11 | chưa làm |
| [16](16-phieu-g5.md) | Phiếu G5 mù, câu đối chứng, precision hiệu chỉnh, rubric | agent A | 07, 09, 11 | 03/11 | chưa làm |
| [17](17-bang-hinh-datasheet-allowlist.md) | Bảng, hình, datasheet, cổng allowlist | agent A | 05, 15, 16 | 04/11 | chưa làm |
| [18](18-giao-thuc-dang-ky-truoc.md) | Giao thức đăng ký trước, mô phỏng công suất, danh sách đóng băng | Claude | 05, 07, 08, 10 | 06/11 | chưa làm |
| [19](19-tat-a2-tat-loc-a5.md) | *(tuỳ chọn)* Tắt A2, tắt lọc A5 | agent | 08 | — | chỉ làm nếu lịch còn chỗ |

Các việc chạy song song theo ba làn:
- **Làn A, phiếu:** 02 → 03 → 12 → 09 → 10 → 16 → 17.
- **Làn B, chấm và chạy:** 04 → 06 → 07 → 08 → 11 → 14 → 13 → 15.
- **Claude:** 01, 05, hướng dẫn gán, lời nhắc B5, 18; nghiệm thu.

## Luật chung cho mọi vé

**Bố cục mã** (spec mục 1):
- Gói Python `danhgia` nằm trong `evaluation/`. Chạy bằng `python -m danhgia <lệnh>` với `PYTHONPATH` gồm `evaluation` và `src`.
- Chỉ **seam xuất** được nhập mã pipeline: kho artifact, use case phát lại. **Seam chấm** và **seam phiếu** không nhập `doc2roadmap`. Test kiến trúc của gói phải
  khẳng định điều này.
- Test nằm trong `tests/evaluation/`, để cổng toàn repo chạy chúng. Một `conftest` đưa `evaluation` vào đường dẫn.
- Dữ liệu phát triển được commit (manifest, vàng gán thử, fixture) nằm trong `evaluation/`.
- Thư viện: dùng thư viện chuẩn, `openpyxl` và `numpy` có sẵn trong `.venv`. Không cài gói mới. Hình xuất SVG bằng mã, không dùng matplotlib.

**Worktree và test:** như mẫu lời giao `tmp/claude-tools/prompt-cai-sa61.md`:
- `copy_bundles.py` phải in `bundles ok: copied 3145`;
- `PYTHONPATH` trỏ vào worktree;
- pytest luôn có `--basetemp`.

**Cổng:**
- vé có sửa `src/` chạy cổng toàn repo qua `scripts/w05_run_tests.py`, cần Docker `wayfinder-db-test-1` healthy;
- vé chỉ sửa `evaluation/` và `tests/evaluation/` chạy nhóm `tests/evaluation` cộng `tests/unit/test_architecture.py`; Claude chạy cổng toàn repo khi ghép;
- hai agent không chạy cổng PostgreSQL cùng lúc.

**Bằng chứng:**
- mọi test phải thấy **đỏ trước khi cài**;
- mỗi vé có **bảng phá**: thử làm hỏng mã, test phải bắt được;
- báo cáo `report/danh-gia-pha-a/DG-NN-<ngày>.md`, lưu dần, có dòng `**Trạng thái:**`.

**Luật cấm:**
- Không gọi mô hình, không chạy lượt có tiền. Vé có lượt thật thì Claude chạy.
- Không mở tập giữ lại: `d01-t01`, `d01-t02`, `document-data/test/`, `Desktop\d02-tap-khoa`, `khoa.jsonl`.
- Không đọc `artifacts/phase_b/live.json` hay `.env`.
- Không ghi vào `artifacts/` của thư mục chung.
- **Không đụng tập thử của đợt này**: nó nằm ở sổ người giữ ngoài repo, agent không được biết đường dẫn.
- Không sửa `src/web/`.
- Không xoá hay gỡ worktree; không đụng `tmp/t01a-clean-ff797eb`.
- Commit chỉ đường dẫn của mình (`git commit -m … -- <tệp>`), không `git add -A`. Dòng cuối message:
  `Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>`.
- Không ghép, không đẩy. Không sửa spec, vé, kế hoạch hay bản hội đồng. Spec sai thì ghi vào mục "Câu hỏi" của báo cáo.
