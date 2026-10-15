# D-04 — Đặc tả nhãn cạnh ngược thứ tự sách (cho E8)

**Nguồn chân lý:** [báo cáo vòng 2](../../report/nghien-cuu-pass-phu-vong-2-ke-hoach-2026-10-10.md), mục 8.12 và 8.13 ·
**Ai:** Claude soạn đặc tả, hướng dẫn gán, kiểm và đo; xuất phiếu theo vé; chủ dự án gán nhãn bằng agentic ·
**Chi phí mô hình:** 0 USD từ phía dự án. Phiếu dựng từ artifact và nhãn đã có, không chạy lại luồng.

**Trạng thái:** soạn 2026-10-15. Chủ dự án duyệt làm E8 và đặc tả này cùng ngày.

**Không đưa tệp này cho agentic.** Agentic chỉ nhận `phieu.jsonl`, hướng dẫn gán D-04 và script kiểm định dạng. Lý do: mục "Cách Claude dùng
nhãn" nêu các luật đang được đo, và đọc nó sẽ làm nhãn nghiêng về luật.

## Vì sao (Claude, 2026-10-15)

R17 (`soften_backward_edges` ở A10) làm mềm mọi cạnh tiên quyết X → Y mà X được dạy **sau** Y, để lộ trình giữ thứ tự sách. Làm mềm hết thì mất các
cạnh đúng. Bỏ hẳn R17 thì Q7 tăng khoảng 0,2, nhưng Q7b giảm 0,24–0,36 (mục 8.12).

E8 đã thử bốn luật giữ cứng có chọn lọc, nhưng bộ vàng phát triển không quyết được (mục 8.13):
- R17 chỉ tác động mạnh ở doc-4, khoảng 300 cạnh;
- vàng doc-4 chỉ phủ chương 8, nên chỉ 1–4 cạnh ngược có hai đầu là đích vàng;
- Q7 và Q7b đổi chủ yếu qua các chuỗi gián tiếp đi qua nút ngoài vàng.

Muốn chọn luật thì phải biết **chính từng cạnh ngược** đúng hay sai, và nếu đúng thì lộ trình có nên đảo thứ tự sách hay không. Đặc tả này
xin đúng hai điều đó, trên nhiều sách.

Nhãn agentic là **nhãn bạc**: dùng để chọn và so luật, không dùng làm vàng. Đo đầu cuối vẫn trên vàng người (doc-1, xstk, doc-4 và T-01).

## Bước 1 — Chọn cặp (theo vé xuất phiếu)

Một **cặp ngược** là (X, Y) mà:
- có đề xuất "X là tiên quyết của Y" (nguồn ở dưới);
- X và Y đều được dạy, có vị trí dạy, và X dạy **sau** Y theo đúng khoá vị trí của A10: chỉ số chunk dạy sớm nhất trong vùng nội dung. Cặp cùng
  chunk không tính, vì R17 không làm mềm chúng.

**Nguồn 1 — ba tài liệu phát triển** (doc-1, xstk-ch3-1, doc-4): lấy **mọi** cạnh mà R17 làm mềm vì "ngược thứ tự sách", trong đồ thị của LLM v3 và
của E5 (`e5-a-hieu-chinh`). Gộp trùng theo (X, Y), ghi hệ nào đề xuất và cạnh đó từ pass chính hay pass phụ. Ước khoảng 350 cặp, phần lớn ở doc-4.

**Nguồn 2 — 16 sách học của D-01:** các cặp trong cửa sổ có nhãn agentic lượt A là `can_de_hieu`, hoặc có xác suất ngoài mẫu của E5 vượt ngưỡng
hiệu chỉnh, mà X dạy sau Y.
- Lấy mẫu tối đa 60 cặp mỗi sách. Chia đều hai tầng "cùng chương" và "khác chương"; tầng thiếu thì lấy bù từ tầng kia. Hạt giống cố định.
- D-01 không chạy A8 pass chính, nên nguồn này không đo được luật "pass chính".

**Không lấy** gì từ hai sách T-01 (`document-data/test/`).

**Phiếu kiểm và phiếu lặp:**
- 5% số phiếu được xuất lại lần hai, đổi thứ tự trình bày, để đo độ tự nhất quán;
- không có câu kiểm có đáp án, vì chưa có vàng cho câu hỏi này.

Sau khi xuất, báo số cặp theo nguồn, sách và tầng.

## Bước 2 — Phiếu (định dạng)

Mỗi cặp là một dòng JSONL. Phiếu **không** ghi hệ đề xuất, điểm, confidence hay nhãn D-01, để người gán không bị dẫn.

```json
{"phieu": "D-04", "phieu_id": "p_…", "doc_id": "d01-07", "linh_vuc": "kinh tế vi mô",
 "y": {"ten": "Độ co giãn của cầu", "bi_danh": [], "muc": ["Chương 2", "2.3 Độ co giãn"],
       "cau": [{"i": 0, "text": "…"}, {"i": 1, "text": "…"}], "cau_neo": 1, "cau_co_ten_x": [1]},
 "x": {"ten": "Hàm cầu", "bi_danh": [], "muc": ["Chương 4", "4.1 Hàm cầu"],
       "cau": [{"i": 0, "text": "…"}, {"i": 1, "text": "…"}], "cau_neo": 0}}
```

- `y.cau` là cửa sổ định nghĩa của Y, đúng cửa sổ của hợp đồng vé 12 và phiếu D-01: tối đa bốn câu trước câu neo, câu neo và hai câu sau.
- `x.cau` là cửa sổ định nghĩa của X, dựng cùng cách, tại chỗ X được dạy (về sau trong sách).
- `cau_co_ten_x` là các câu trong cửa sổ Y có tên hay bí danh của X. Mảng có thể rỗng, vì cạnh của LLM không bắt buộc nhắc tên X.
- `muc` là chuỗi tiêu đề mục từ cấp 1 xuống.
- Khoảng cách (`cung_chuong`; `so_muc_giua`, tức số mục lá nằm giữa chỗ dạy Y và chỗ dạy X) chỉ ghi ở khoá, không ghi trên phiếu. Lý do: cấp 1 của
  cây mục có khi là cả một phần sách, như ở doc-4, nên `cung_chuong` dễ đọc sai; và một số đo độ xa có thể kéo nhãn theo nó. Sửa 2026-10-15,
  sau khi đọc phiếu mẫu.

## Bước 3 — Gán nhãn (agentic)

Câu hỏi: **sách dạy Y trước X. Người học có phải học X trước rồi mới học Y không?**

Chọn đúng một nhãn:

| nhãn | nghĩa | phép thử |
|---|---|---|
| `can_hoc_truoc` | X là thành phần của định nghĩa Y, và cửa sổ Y **không** tự giải thích X đủ để hiểu Y. Lộ trình nên đưa X lên trước Y | che phần sau của sách đi: chỉ đọc tới Y thì người học không hiểu được câu định nghĩa Y |
| `du_tai_cho` | X là thành phần của định nghĩa Y, nhưng chỗ Y đã nói đủ về X để hiểu Y, qua một định nghĩa sơ bộ, chú thích, ví dụ hay "xem mục sau". Phần sau chỉ trình bày X đầy đủ hơn | hiểu được Y mà chưa đọc tới chỗ dạy X; đọc X sau giúp hiểu sâu hơn |
| `kien_thuc_nen` | Y dùng X, nhưng giáo trình mặc nhiên coi người đọc đã biết X ở mức đủ hiểu Y (kiến thức phổ thông hay môn trước); chỗ dạy X về sau chỉ ôn lại hoặc chính thức hoá | người đọc đúng đối tượng của giáo trình hiểu được Y mà không cần chỗ dạy X |
| `nghia_khac` | chữ X ở chỗ Y mang nghĩa thường, hoặc một nghĩa khác với khái niệm X được định nghĩa về sau | "lượng" theo nghĩa thường ở Y, còn "Lượng" về sau là phạm trù triết học |
| `khong_tien_quyet` | không có quan hệ tiên quyết trực tiếp: nhắc thoáng qua, hai khái niệm anh em, so sánh hay đối lập, khuôn khổ chung, hoặc chỉ gián tiếp qua khái niệm khác | — |
| `nguoc` | Y mới là tiên quyết của X: X được định nghĩa qua Y | — |
| `khong_ro` | hai đoạn văn không đủ để quyết | — |

Luật chung (giống D-01):
- **Căn cứ vào đoạn văn được cho.** Hiểu biết môn học chỉ dùng để hiểu đoạn văn và để xét `kien_thuc_nen` ở mức đối tượng của giáo trình. Không dùng
  hiểu biết môn học để thêm quan hệ mà đoạn văn không thể hiện.
- **Chỉ quan hệ trực tiếp.**
- Với `can_hoc_truoc`, `du_tai_cho`, `kien_thuc_nen`, `nghia_khac`: ghi `cau_y` là chỉ số câu trong `y.cau` làm căn cứ.
- Với `du_tai_cho`: ghi thêm `cau_giai_thich`, là chỉ số câu trong `y.cau` đã giải thích X.
- Không chắc thì chọn `khong_ro`, **không đoán**.

Định dạng trả về: mỗi phiếu một dòng, mỗi lượt gán trả đủ mọi phiếu đúng một lần.

```json
{"phieu_id": "p_…", "nhan": "du_tai_cho", "cau_y": 1, "cau_giai_thich": 0, "ly_do": "tối đa 30 từ",
 "nguoi_gan": "tên agent + mô hình + phiên bản", "luot": "A"}
```

**Hai lượt độc lập (A, B).** Hai agent hoặc hai mô hình khác nhau, không thấy nhãn của nhau. D-01 cho thấy một lượt có kappa chỉ 0,43 với chính nó
ở ngữ cảnh khác, nên một lượt là không đủ cho phép đo này. Cặp lệch nhau thì để lượt thứ ba quyết, hoặc ghi `khong_ro`.

## Kiểm chất lượng (Claude)

- **Định dạng:** mọi dòng hợp lệ; mỗi phiếu có đúng một nhãn mỗi lượt; chỉ số câu nằm trong danh sách câu; `cau_giai_thich` có mặt khi và chỉ khi nhãn
  là `du_tai_cho`. Lỗi định dạng thì trả lại, không tự sửa nhãn.
- **Báo cáo:** độ tự nhất quán trên phiếu lặp; kappa A–B theo nhãn, và theo nhị phân `can_hoc_truoc` hay không; tỉ lệ `khong_ro`.
- **Claude đọc** một mẫu 40 cặp lệch nhau và 40 cặp đồng thuận, rồi ghi kiểu lỗi. Nếu nhãn lệch có hệ thống thì sửa hướng dẫn trước khi dùng nhãn.

## Cách Claude dùng nhãn

Từ nhãn ra hành vi đúng của A10:

| nhãn | A10 nên làm |
|---|---|
| `can_hoc_truoc` | giữ cạnh cứng, đảo thứ tự sách |
| `du_tai_cho`, `kien_thuc_nen` | cạnh mềm, giữ thứ tự sách. Đây là hành vi của R17 hiện tại |
| `nghia_khac`, `khong_tien_quyet` | bỏ cạnh |
| `nguoc` | cạnh Y → X, xuôi thứ tự sách |

Phép đo, dùng nhãn đồng thuận A∩B; nhãn của từng lượt chỉ dùng để đo độ nhạy:
- **Mỗi luật giữ cứng** của E8, gồm `tat`, `cung-chuong`, `pass-chinh` (chỉ nguồn 1), `tin-chac` và khoảng cách `so_muc_giua` ≤ k: tính độ chính xác
  (tỉ lệ `can_hoc_truoc` trong các cạnh luật giữ cứng) và độ phủ (tỉ lệ `can_hoc_truoc` được giữ cứng). Báo theo nguồn, lĩnh vực và hệ.
- **Mô hình học**, nếu không luật đơn nào đủ: LightGBM trên đặc trưng cấu trúc (khoảng cách, cùng chương, `cau_co_ten_x` rỗng hay không, xác suất
  E5, nhãn D-01), chia theo sách như E5.
- **Tiêu chí soạn vé sửa A10, chốt trước khi có nhãn:**
  - độ chính xác giữ cứng ≥ 0,70 với khoảng Wilson dưới ≥ 0,60, và độ phủ ≥ 0,30;
  - và trên ba tài liệu vàng, phát lại bằng `thi_nghiem_e8.py`, Q7b giảm không quá 0,05 và bao đóng P giảm không quá 0,03 so với R17.
- **Phụ phẩm:**
  - tỉ lệ `nghia_khac` và `khong_tien_quyet` là độ chính xác thật của cạnh ngược, đo ngay trên chính các cạnh mà vàng không chấm được;
  - `kien_thuc_nen` là tín hiệu cho phân loại `prior_knowledge` của C8, và cho vé gộp khâu (vé 17).

## Lưu ý

- Phiếu chứa văn bản giáo trình. Gửi phiếu cho dịch vụ nào là quyết định của chủ dự án, như D-01.
- Nhãn agentic là nhãn bạc, kể cả khi hai lượt đồng thuận. Không gộp vào vàng, không dùng để chấm tập giữ lại.
- Đổi luật của A10 là đổi `src/`, nên phải qua vé của nhân viên, và chỉ soạn vé khi tiêu chí trên đạt.
