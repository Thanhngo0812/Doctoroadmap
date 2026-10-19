# D-01 — Đặc tả dữ liệu huấn luyện cho pass phụ không LLM

**Nguồn chân lý:** [nghiên cứu vòng 1](../../report/nghien-cuu-pass-phu-khong-llm-vong-1-2026-10-05.md) ·
**Ai:** chủ dự án gom sách và gán nhãn bằng agentic; Claude xuất phiếu, kiểm và nạp nhãn ·
**Chi phí mô hình:** chạy luồng của dự án trên sách mới để có phiếu (A1 → A8 pass chính) tốn tiền Gemini; mỗi lượt dry-run và chờ duyệt như mọi
lượt trả tiền.

**Trạng thái:** soạn 2026-10-05; chủ dự án đề nghị tự làm dữ liệu cùng ngày.

**Cảnh báo cho chủ dự án (Claude, 2026-10-08): không đưa tệp này cho agentic.** Cả năm ví dụ ở mục "Ví dụ lấy từ dữ liệu dự án" trùng
đúng cặp của phiếu kiểm, đưa vào là lộ đáp án. Agentic chỉ nhận `phieu.jsonl`, [hướng dẫn gán](../../report/huong-dan-agentic-gan-nhan-d01.md)
và `scripts/pass-phu-ml/kiem_nhan_d01.py`; không nhận `khoa.jsonl`.

**Cập nhật gom sách — Codex, 2026-10-05:** theo yêu cầu mới của chủ dự án,
đã tải 16 cuốn học (8 lĩnh vực × 2) và 2 cuốn giữ lại vào
[`document-data/`](../../document-data/README.md), 3.195 trang / 54,03 MiB.
Kiểm PDF/lớp chữ/hash đạt; sách giữ lại chỉ kiểm máy, không đọc nội dung.
Chưa đóng toàn bộ điều kiện bước 1: 8 sách học chưa xác minh quyền nghiên cứu,
2 năm xuất bản chưa xác minh; metadata và quyền của 2 sách giữ lại chờ người giữ
tập kiểm bổ sung. Chưa chạy bước 2 hay gán nhãn. Xem manifest/checks và giới hạn
nghiệm thu trong README, không hiểu trạng thái tải đủ là duyệt quyền dùng mô hình.

## Vì sao (Claude, 2026-10-05)

Bộ kiểm cạnh cứng của vòng 1 học từ phán quyết của `gemini-3.1-flash-lite` trên bốn giáo trình tiếng Việt: đại số tuyến tính, nhập môn ML, xác
suất thống kê, triết học. Ba giới hạn đo được:
- **Ít lĩnh vực.** Văn liệu cho thấy mô hình tiên quyết tụt mạnh khi đổi miền.
- **Thầy nhiễu.** 19–44% cặp bị LLM hoãn, vì hai thứ tự trình bày lệch nhau hoặc phản hồi lỗi.
- **Trần là thầy.** Mô hình chỉ học được ranh giới của chính LLM.

Nhãn mới, nhiều lĩnh vực, theo một giao thức chặt, là đòn bẩy lớn nhất của vòng 2.

Nhãn do agentic tạo là **nhãn bạc**: dùng để học, **không** dùng làm vàng để đo. Đo cuối vẫn bằng vàng người trên tập giữ lại mới (vé T-01).

## Bước 1 — Gom sách (chủ dự án)

Tiêu chí:
- **Tiếng Việt**, giáo trình đại học hoặc cao đẳng. Cho phép xen thuật ngữ tiếng Anh.
- **PDF có lớp chữ**, chép chữ ra được (không phải ảnh quét), như doc-1 hay doc-4.
- Trọn cuốn, hoặc ít nhất 3 chương liền nhau có định nghĩa.
- **Đa lĩnh vực:** ít nhất 8 lĩnh vực, ví dụ toán, vật lý, hoá, sinh, CNTT, kinh tế, luật, y, kỹ thuật, khoa học xã hội.
- Không dùng lại tài liệu đã có trong dự án: doc-1…doc-6, naive-bayes, nhap-mon-ml, xstk-ch3-1, baocao-canhan.
- Ghi cho mỗi cuốn: tên, tác giả, nhà xuất bản và năm, lĩnh vực, số trang, nguồn, và quyền dùng cho nghiên cứu.

**Số lượng:** ít nhất 12 cuốn.
- **2 cuốn để riêng làm tập giữ lại (T-01):** người gán vàng theo giao thức vàng hiện có; **không** đưa vào agentic, không cho Claude xem trước
  khi khoá cấu hình.
- 10 cuốn còn lại dùng để học.

## Bước 2 — Chạy luồng và xuất phiếu (Claude)

1. Chạy A1 → A8 pass chính trên 10 cuốn học. Cần nút, câu neo, cửa sổ định nghĩa, mention map, cặp ứng viên, cạnh pass chính. Không chạy pass
   phụ LLM. Dry-run trước, báo dự toán, chờ duyệt.
2. Xuất **phiếu**: mỗi khái niệm được dạy Y là một dòng JSONL. Ứng viên gồm:
   - **mọi** khái niệm X có tên trong cửa sổ định nghĩa của Y, khớp theo ranh giới từ tiếng Việt;
   - tối đa 5 khái niệm X **không** có tên trong cửa sổ, lấy từ cặp ứng viên của luồng; phục vụ nghiên cứu cạnh không nguyên văn (`trong_cua_so: false`).
3. Chèn câu kiểm và câu lặp (mục "Kiểm chất lượng"), xáo thứ tự.

Định dạng phiếu (Claude ghi, agentic đọc):

```json
{"phieu": "D-01", "doc_id": "sach-07", "linh_vuc": "kinh tế vi mô", "y_id": "node_…", "y_ten": "Độ co giãn của cầu",
 "y_bi_danh": ["độ co dãn của cầu theo giá"], "muc": ["Chương 2", "2.3 Độ co giãn"],
 "cau": [{"i": 0, "text": "…"}, {"i": 1, "text": "…"}, {"i": 2, "text": "…"}],
 "cau_neo": 2,
 "ung_vien": [
   {"x_id": "node_…", "x_ten": "Cầu", "x_bi_danh": [], "x_dinh_nghia": "câu định nghĩa của X trong sách, hoặc null",
    "cau_co_ten": [1, 2], "trong_cua_so": true}
 ]}
```

- `cau` là cửa sổ định nghĩa của Y: tối đa bốn câu trước câu neo, câu neo, hai câu sau. Cùng cửa sổ mà hợp đồng vé 12 dùng.
- `cau_neo` là chỉ số câu luồng chọn làm câu định nghĩa.
- `cau_co_ten` là các câu có tên X.

## Bước 3 — Gán nhãn (chủ dự án, agentic)

Với **mỗi** ứng viên X của **mỗi** phiếu, chọn đúng một nhãn:

| nhãn | nghĩa | phép thử |
|---|---|---|
| `can_de_hieu` | X là **thành phần của định nghĩa** Y như sách viết: Y được định nghĩa qua X, Y là một loại X, Y là thuộc tính hay phép toán trên X, hoặc câu bối cảnh của định nghĩa đặt X làm đối tượng | người học chưa biết X thì **không hiểu được câu định nghĩa Y** |
| `cong_cu` | X có mặt trong phần trình bày Y như công cụ, phương pháp tính, ví dụ, ký hiệu, nhưng không cần để hiểu Y là gì | chưa biết X vẫn hiểu Y là gì; cần X để làm bài, chứng minh hay áp dụng |
| `khong` | không có quan hệ tiên quyết **trực tiếp**: nhắc thoáng qua; hai khái niệm "anh em" được định nghĩa hay liệt kê cạnh nhau; X dùng để so sánh hay đối lập; X là khuôn khổ chung không thuộc định nghĩa (kiểu "theo phép biện chứng duy vật…"); hoặc chỉ gián tiếp qua khái niệm khác | — |
| `nguoc` | Y mới là tiên quyết của X: X được định nghĩa qua Y | — |
| `khop_nham` | tên X xuất hiện nhưng **không chỉ khái niệm X**: nằm trong một từ khác hoặc mang nghĩa thường | "chất" trong "vật chất", "hợp" trong "trường hợp" |
| `khong_ro` | đoạn văn không đủ để quyết | — |

Luật chung:
- **Căn cứ vào đoạn văn được cho.** Hiểu biết môn học chỉ dùng để hiểu đoạn văn, không dùng để thêm quan hệ mà đoạn văn không thể hiện. Giao
  thức này giống giao thức vàng của dự án, vốn bám câu chữ giáo trình.
- **Chỉ quan hệ trực tiếp.** Nếu X cần cho Y chỉ vì Y cần Z và Z cần X, mà Z cũng là ứng viên, thì chọn `khong` và ghi Z vào `trung_gian`.
- Với `can_de_hieu`, `cong_cu`: ghi `cau` là chỉ số câu làm căn cứ, lấy trong danh sách câu đã cho. Với `nguoc`: chỉ số câu, hoặc `null` khi
  căn cứ chỉ nằm trong `x_dinh_nghia` (bổ sung 2026-10-08).
- Không chắc thì chọn `khong_ro`, **không đoán**.

Định dạng trả về: mỗi cặp (phiếu, X) một dòng JSONL, mỗi lượt gán trả đủ mọi cặp đúng một lần.
- **`phieu_id` bắt buộc** (bổ sung 2026-10-08). Phiếu lặp có cùng `doc_id`, `y_id` với phiếu gốc, nên thiếu `phieu_id` thì không tách được
  hai lần gán.
- Luật đầy đủ của `cau` và `trung_gian` ở mục 8 của [hướng dẫn gán](../../report/huong-dan-agentic-gan-nhan-d01.md).
- `scripts/pass-phu-ml/kiem_nhan_d01.py` kiểm định dạng.

```json
{"phieu_id": "p_…", "doc_id": "sach-…", "y_id": "node_…", "x_id": "node_…", "nhan": "can_de_hieu", "cau": 2, "trung_gian": null,
 "ly_do": "tối đa 30 từ", "nguoi_gan": "tên agent + mô hình + phiên bản", "luot": "A"}
```

## Ví dụ lấy từ dữ liệu dự án (chỉ cho người đọc đặc tả; trùng phiếu kiểm, không đưa cho agentic)

Các ví dụ này đã có nhãn vàng người hoặc đã được đọc lại:

- **`can_de_hieu`.** Y = "Số chiều", X = "Không gian véc tơ hữu hạn sinh" (doc-1).
  Câu: "Số phần tử của mỗi cơ sở của không gian véc tơ hữu hạn sinh V ≠ {θ} được gọi là số chiều của V". Bản trích chữ của sách ghi lệch
  "≠" thành "= { θ }"; phiếu thật sẽ có những lỗi trích như vậy.
  Định nghĩa Y đặt trên X. Vàng có cạnh này.
- **`can_de_hieu`, căn cứ là câu bối cảnh trước câu neo.** Y = "Vô hướng", X = "Trường" (doc-1).
  Câu [0] của cửa sổ: "Giả sử K là một trường." Câu neo [2] định nghĩa không gian véc tơ trên K, với "phép nhân véc tơ với vô hướng": vô hướng
  lấy từ K. Vàng có cạnh này.
- **Ca biên `can_de_hieu` / `cong_cu`.** Y = "Bài toán thuận", X = "Khoảng ước lượng" (xstk).
  Câu: "Bài toán tìm khoảng ước lượng có thể coi là bài toán thuận…". Định nghĩa Y gọi thẳng tên X, nên chọn `can_de_hieu`. LLM chọn `cong_cu` ở
  một thứ tự và `can_de_hieu` ở thứ tự kia; vàng có cạnh.
- **`khong`, hai khái niệm anh em.** Y = "Không gian véc tơ vô hạn chiều", X = "Số chiều" (doc-1).
  Hai định nghĩa (a), (b) nằm cạnh nhau trong cùng Định nghĩa 6; không cái nào cần cái kia để hiểu. Vàng không có cạnh.
- **`khong`, liệt kê.** Y = "Bài toán tìm độ tin cậy", X = "Bài toán tìm kích thước mẫu" (xstk).
  Câu: "…hai bài toán ngược: Bài toán tìm độ tin cậy … và bài toán tìm kích thước mẫu…". Vàng không có cạnh.
- **`khong`, khuôn khổ.** Câu định nghĩa trong giáo trình triết học mở đầu bằng "theo phép biện chứng duy vật…" (doc-4). "Phép biện chứng duy vật"
  là khuôn khổ, không là thành phần của định nghĩa, trừ khi định nghĩa thật sự xây trên nó. Tập giữ lại v3 đã đếm loại lỗi này của LLM.
- **`khop_nham`.** X = "Chất" mà câu chỉ có "vật chất", "bản chất"; X = "Hợp" trong "trường hợp", "tập hợp"; X = "Hiệu" trong "kí hiệu". Luồng
  đã khớp theo ranh giới từ, nhưng bộ tách từ vẫn có lúc sai. Nhãn này cho biết lỗi còn lại.

## Kiểm chất lượng (Claude chèn và chấm)

- **Câu kiểm (5% phiếu):** cặp đã có nhãn vàng người từ doc-1, xstk, doc-4, trộn lẫn không đánh dấu. Báo độ đúng của agentic trên các câu này;
  độ đúng thấp thì xem lại hướng dẫn trước khi dùng nhãn.
- **Câu lặp (5% phiếu):** cùng phiếu xuất hai lần, thứ tự ứng viên khác nhau. Báo độ tự nhất quán.
- **Hai lượt độc lập (A, B)** nếu làm được: hai agent hoặc hai mô hình khác nhau, không thấy nhãn của nhau. Báo Cohen's kappa theo nhãn và theo
  lĩnh vực. Cặp lệch nhau được gán lượt thứ ba, hoặc để `khong_ro`.
- Claude kiểm định dạng: mọi dòng hợp lệ; mỗi cặp của phiếu có đúng một nhãn mỗi lượt; `cau` nằm trong danh sách câu. Lỗi định dạng thì trả lại,
  không tự sửa nhãn.

## Cách Claude dùng nhãn

- **Chia theo sách:** cặp của một cuốn không bao giờ vừa ở tập học vừa ở tập đo. Báo kết quả theo từng lĩnh vực.
- Học bộ kiểm cạnh cứng với nhãn `can_de_hieu` là dương; `cong_cu` thành cạnh mềm cho danh sách công cụ; `khop_nham` dùng để đo và sửa bộ khớp tên.
- Ứng viên `trong_cua_so: false` dùng cho nghiên cứu cạnh cứng không nguyên văn.
- So ba nguồn nhãn trên cùng phép đo đầu cuối (bộ E4) và trên vàng người: LLM v3, agentic lượt A, agentic đồng thuận A và B.

## Lưu ý

- Phiếu chứa văn bản giáo trình. Quy ước cũ của dự án chỉ gửi nội dung giáo trình tới Gemini. **Gửi phiếu cho dịch vụ nào là quyết định của chủ
  dự án.**
- Nhãn agentic là nhãn bạc, kể cả khi hai lượt đồng thuận. Không gộp vào vàng, không dùng để chấm tập giữ lại.
