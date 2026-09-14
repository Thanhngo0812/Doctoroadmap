# 04 — Đồ thị đề cử và gom cụm ứng viên

**What to build:** `a4` dựng đồ thị **cặp nghi trùng** giữa các nhóm tên từ ba kênh — alias chung, tên gần giống, tên
gần nghĩa — rồi gom thành **cụm ứng viên** không quá 9 nhóm. Chưa gọi mô hình nên bảng node chưa đổi; cụm và danh sách
cạnh bị cắt được ghi vào artifact, là thứ bảng gán bộ vàng (05) và lượt phán cụm (07) đứng lên. Manifest in số cạnh
theo kênh, số cụm, cụm lớn nhất, số cạnh bị cắt.

## Vì sao không dùng ngưỡng cosine

Đo trên bốn tài liệu (báo cáo mục 2): cosine giữa hai thực thể bất kỳ đã là 0,80, nên đồ thị ngưỡng 0,75 biến mỗi tài
liệu thành đúng một cụm; connected components xích lại dù dựng theo kNN. Embedding **mô tả** là tín hiệu *liên quan*,
không phải *đồng nhất* — embed **tên** cho 58% trùng thật ở top các cặp, mô tả chỉ 24%. Vì vậy: láng giềng gần nhất
trên vector **tên**, cộng hai kênh từ vựng, rồi Louvain có trần (ADR 0006, spec D3).

**Blocked by:** 02 — Viên đạn vạch đường: lớp tên → bảng node canonical, lệnh `a4`

**Status:** done

**Cập nhật hoàn tất 2026-09-12:** Đã ghi vector tên thật và triển khai 3 kênh/Louvain; chốt k=3, n-gram=0,5,
resolution=2, seed=42, cap=9 sau quét 13 cấu hình trên 47 cặp vàng.
Chi tiết kiểm chứng và phần chưa hoàn tất: [feedback A4/A5](../../feedback/F18-a4-a5-hop-nhat.md).

- [x] **Embedding tên** do A4 tự tính qua cổng embedding hiện có, `SEMANTIC_SIMILARITY`, model và số chiều theo cấu
      hình hiện hành. Vector nhóm = trung bình vector tên các thành viên, đã chuẩn hoá. Model, số chiều và công thức
      văn bản embed vào config hash của A4 (ADR 0004).
- [x] Fixture phát lại vector tên cho `baocao-canhan`, ghi bằng cơ chế ghi–phát lại embedding sẵn có; kịch bản ghi
      chạy lại được.
- [x] **Kênh alias**: alias không phải ký hiệu của nhóm này trùng khoá tên hoặc alias của nhóm kia ⇒ cạnh, trọng số 1.
- [x] **Kênh tên gần giống**: Jaccard 3-gram ký tự không đệm biên trên tên đã bỏ dấu và dấu câu ≥ 0,5 ⇒ cạnh, trọng số
      max(cosine tên, 0,5).
- [x] **Kênh tên gần nghĩa**: mutual-3NN trên vector nhóm ⇒ cạnh, trọng số cosine tên.
- [x] **Ký hiệu không bao giờ tạo cạnh**: hai nhóm chỉ chung `f`/`F` hay `x` thì không có cạnh nào (test).
- [x] **Gom cụm**: Louvain có trọng số, **seed cố định**, độ phân giải 2. Cụm vượt **9 nhóm** thì chia lại ở độ phân giải
      cao hơn cho tới khi ≤ 9. Nhóm không có cạnh nào không vào cụm nào.
- [x] Liệt kê **cạnh bị cắt** — hai đầu nằm ở hai cụm khác nhau — để ticket 08 dùng.
- [x] Tham số đồ thị (k, ngưỡng n-gram, độ phân giải, seed, trần cụm) nằm trong cấu hình và config hash.
- [x] `networkx` khai báo là **phụ thuộc trực tiếp**, ghim phiên bản. Không dùng hàm Leiden của `networkx` — nó chỉ là
      API chuyển tiếp, không có cài đặt.
- [x] Cụm và cạnh bị cắt được ghi vào artifact `canonical`. Manifest: số cạnh theo từng kênh và hợp, số cụm cần gọi
      mô hình, cụm lớn nhất, số cạnh bị cắt.
- [x] Trên bốn tài liệu: **alias 9 · n-gram 95 · tên 222 · hợp 256 cạnh; 63 cụm cần gọi mô hình, cụm lớn nhất 7;
      38 cạnh bị cắt** với seed 42; dải 36–42 trên bảy seed đã đo.
- [x] **Seam ②**: mutual-kNN; n-gram; ký hiệu không tạo cạnh; chia lại khi vượt trần (đồ thị dựng tay có cụm 12 nhóm ⇒
      mọi cụm ≤ 9); cùng seed ⇒ cùng cụm qua hai lần chạy.
- [x] **Seam ①** trên fixture `baocao-canhan`: cặp `WebSocket`/`WebSockets`, `Tranh chấp dữ liệu`/`Race Condition` và
      `Kiến trúc Hub - Client`/`Mô hình Hub - Client` đều có cạnh; không cụm nào vượt 9 nhóm; không test nào chạm mạng.
- [x] Toàn bộ test hiện có vẫn xanh.
