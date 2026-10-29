# DG-08b — Lượt hệ chính chạy đúng đường của sản phẩm

**Nguồn:** spec mục 3, 11, 13; lượt phát triển 29/10 · **Ai:** agent · **Chi phí:** 0 khi cài (Claude chạy lượt thật) · **Chặn bởi:** DG-08, DG-18a ·
**Hạn:** 31/10 · **Trạng thái:** ready-for-agent

## Vì sao

Lượt chạy thật đầu tiên (29/10) cho thấy lệnh `luot` của DG-08 gọi các lệnh CLI phát triển từng bước (`ingest`, `label-roles`, `a3`, `a4`, `roadmap`).
Đường đó khác đường sản phẩm (`doc2roadmap.composition_build.DocumentPipeline`, mà web và lệnh `build` dùng) ở ít nhất hai chỗ:
- **A4:** CLI `a4` đòi `--gold` (bộ vàng A4 cũ) và `load_gold(require_complete=True)`. Hàm này dựng lại bảng gán mù từ artifact của các tài liệu cũ, nên kho mới
  của lượt luôn lỗi ("chưa có artifact canonical v2 cho tài liệu 'baocao-canhan'"). Sản phẩm gọi `Canonicalize.execute(..., a4_gold_coverage="none",
  gold_sheet_id=None)` và không có cổng vàng.
- **Cổng chất lượng chữ:** sản phẩm (`DocumentPipeline.read`) từ chối sách có bất kỳ cảnh báo chất lượng chữ nào (`BuildRejected("chu_loi")`). CLI phát triển cho
  vượt bằng `--allow-text-quality-reason` (`luot --ly-do-chu`).

Đánh giá phải đo **sản phẩm**. Số của hệ chính phải đến từ đúng mã mà người dùng chạy.

## Làm được gì

- Biến thể `chinh` (và `xao-k`, `pass-phu-llm`, vốn chỉ đổi cấu hình qua biến môi trường) chạy từng bước bằng phương thức của `DocumentPipeline`:
  `read` → `label_roles` → `a3` → `canonical(doc_id, "vi")` → `roadmap` (→ phần Pha B riêng như hiện có).
  - Giữ nguyên các thứ đã có: bản ghi lượt, chạy tiếp theo bước, đo giây và chi theo bước, dry-run dừng trước bước có chi đầu tiên.
  - Chi lấy từ `usage_meter` của pipeline, hoặc từ manifest artifact như hiện tại. Chọn cách khớp với sổ chi đang có, ghi rõ.
- **Bỏ `--vang-a4`** khỏi đường hệ chính, vì sản phẩm không có cổng vàng A4. Giữ tham số này nếu biến thể nào khác còn cần, không thì xoá cả test liên quan.
- **Cổng chất lượng chữ theo đúng sản phẩm:**
  - không có `--ly-do-chu` thì sách có cảnh báo bị từ chối ở bước `read`, đúng như sản phẩm. Bản ghi lượt ghi rõ lý do (`tu_choi_chu_loi`), lượt kết thúc
    với trạng thái riêng, không phải "lỗi chạy";
  - có `--ly-do-chu` thì đó là **đường vòng**, chỉ để phân tích phụ. Bản ghi mang cờ `duong_vong_chu: true` cộng lý do, và hai thứ này vào hash cấu hình.
    Bộ xuất ghi cờ này vào `dinh_danh` của hợp đồng (thêm khoá nếu lược đồ cần, kèm test lược đồ), để bộ chấm và bảng phân biệt được.
  - Trên tập thử, `--ly-do-chu` chỉ được dùng khi tên biến thể kết thúc bằng `-vong-chu`, ví dụ `chinh-vong-chu`. Biến thể này là biến thể riêng, không thay
    `chinh`. Tập phát triển dùng tự do, nhưng vẫn có cờ.
- **Biến thể docling:** sản phẩm luôn dùng bộ đọc nhẹ (`NheParser`) cho PDF, nên docling vẫn đi đường riêng (đặt lại parser). Ghi rõ trong mã và báo cáo đây là
  ablation, khác sản phẩm có chủ ý.
- **`oracle-a8`:** bước `roadmap` dùng `DocumentPipeline.roadmap` trên kho có canonical oracle.
- Báo cáo **đối chiếu từng bước** giữa CLI phát triển và `DocumentPipeline`: cùng use case, cùng tham số hay khác chỗ nào. Ví dụ `roadmap` của sản phẩm dựng
  `BuildLearningGraph` với `NameModulesB` và `NameConceptLabels`; CLI `roadmap` có y hệt không? Mọi khác biệt còn lại phải liệt kê.

## Tiêu chí

- [ ] Test bằng pipeline giả (thay `DocumentPipeline` bằng đối tượng giả ghi lại lời gọi):
  - thứ tự bước;
  - chạy tiếp sau ngắt;
  - dry-run không gọi bước có chi;
  - `canonical` được gọi với ngôn ngữ `vi` và không có vàng.
- [ ] Test cổng chữ:
  - sách có cảnh báo, không `--ly-do-chu`, thì lượt dừng ở `read` với trạng thái `tu_choi_chu_loi`, không gọi bước sau;
  - có `--ly-do-chu` thì `duong_vong_chu` nằm trong bản ghi, hash cấu hình và hợp đồng;
  - tập thử dùng `--ly-do-chu` với biến thể không có hậu tố `-vong-chu` thì bị từ chối.
- [ ] Một test tích hợp (không mạng, `allow_spend=False`, chỉ `read` trên PDF fixture nhỏ của repo): bước `read` của `luot` cho ra cùng phiên bản chunk và
  cùng nội dung như `DocumentPipeline.read` gọi trực tiếp.
- [ ] Bảng phá, tối thiểu:
  - gọi lại CLI `a4 --gold`;
  - bỏ cổng chữ;
  - đường vòng không vào hash;
  - đường vòng không có cờ trong hợp đồng;
  - chạy tiếp sau ngắt gọi lại bước đã xong.
