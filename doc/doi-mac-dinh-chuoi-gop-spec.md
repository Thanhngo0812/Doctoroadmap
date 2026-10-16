# Spec — Đổi mặc định sang chuỗi gộp

**Status:** ready-for-agent · soạn 2026-10-17 (Claude) · chủ dự án quyết đổi mặc định ngày 2026-10-16 và chốt kế hoạch qua đợt soát ngày 2026-10-17.

**Nguồn:**
- [spec gộp khâu trước A8](gop-khau-truoc-a8-spec.md): vé 17a–17k đã cài;
- [nghiệm thu 17i](../report/v4-17i-nghiem-thu-chuoi-gop-luot-1-2026-10-16.md);
- [nghiên cứu cải thiện chuỗi gộp](../report/nghien-cuu-cai-thien-chuoi-gop-2026-10-16.md): mục 2–4, 6, 7, và mục 10 (các quyết định sau đợt soát).

## Problem Statement — Vấn đề

**Chuỗi v3 vẫn là mặc định.** Giữa A4/A5 và A8, mỗi cuốn sách phải đi qua ba stage LLM nối tiếp: provenance, neo C8 và danh tính.
- Ba stage này kéo dài thời gian mỗi cuốn.
- Chúng làm luồng khó trình bày: hai bước gộp thực thể, thêm các khâu phụ A9′ và A9″ chen giữa A1 và A10.

**Chuỗi gộp đã cài và đã nghiệm thu (vé 17i).**
- Neo và trạng thái dạy giữ được chất lượng của C8.
- Gộp sai mà vàng phát hiện được không tăng.
- E4 không tệ hơn quá mức nhiễu.
- Số lời gọi trước A8 giảm khoảng 45–60%.

**Nhưng chưa thể bật ngay. Lượt chạy thật còn lộ ra mấy điểm:**
- **A4 tốn lời phán sửa vô ích.**
  - Nguồn đề cử `same_evidence` chưa từng sinh lần gộp nào.
  - Cạnh cắt chỉ có nguồn `ngram` cũng vậy.
  - Hai loại này chiếm khoảng một nửa số lời phán sửa ở doc-4.
- **A4 sót một số gộp đúng**, theo hai cách:
  - Chỉ một cặp "khác" trong một thành phần là cả thành phần bị tách và hoãn.
  - Có những cặp chỉ khác cách viết vẫn bị phán tách, ví dụ "χα 2" với "χα^2", "Gram - Schmidt" với "Gram-Schmidt".
- **Chia cụm A4 không tái lập được giữa hai lần chạy.** Thứ tự nút phụ thuộc `PYTHONHASHSEED`.
- **Chạy chậm vì mấy chỗ thuần CPU.**
  - Dựng câu ứng viên neo quét lại toàn văn cho từng khái niệm: khoảng 200 giây trên doc-4.
  - Stage mention tính độ gần bằng Python thuần và embed lại tên: 400 giây.
  - Pass phụ ML chạy 592 giây trên doc-4, so với 18 giây trên d01-02.
  - Canonical chỉ chạy 4 lời gọi đồng thời.
- **Đổi mặc định ngây thơ sẽ làm gãy D-01.** D-01 gọi `a4 --names-only`, mà chuỗi gộp từ chối lệnh này.
- **Mã và cấu hình còn giữ ba tuỳ chọn đã đo là thua**, cùng ba stage cũ. Giữ lại thì phải giải thích khi trình bày.

## Solution — Giải pháp

Làm theo năm pha, đúng thứ tự đã chốt ở đợt soát:

1. **Sửa A4 của chuỗi gộp, và đổi cấu hình cùng CLI.**
   - Sửa A4:
     - bỏ nguồn `same_evidence`;
     - không phán sửa cạnh cắt chỉ có `ngram`;
     - giải mâu thuẫn bắc cầu theo kiểu bảo thủ;
     - chung tên sau chuẩn hoá thì buộc gộp;
     - chia cụm tất định;
     - R2 nhận thêm nhãn `coextensive_with`.
   - Mặc định mới: chuỗi gộp, neo "một khái niệm".
   - `--names-only` / `--prepare` tự dùng chuỗi v3.
2. **Tăng tốc**, không đổi khoá cache: dựng câu ứng viên neo, stage mention, chạy song song ở canonical, pass phụ ML, và đo thời gian đủ phần.
   Làm song song với pha 1, và phải xong trước pha 3.
3. **Thí nghiệm và cổng (Claude).**
   - Đo nhiễu pass chính, ra dải nhiễu E4.
   - Thử cho pass chính chạy song song. Nhận thì vào pha 1b.
   - Chạy cổng trên 6 tài liệu phát triển; lượt này kiêm dựng lại artifact chuẩn. Trần 10 USD cho cả đợt.
4. **Bật mặc định**, cùng commit với tài liệu: ADR 0016, ADR 0004, `CONTEXT.md`, spec-addendum, và dòng "Lịch" của spec gộp khâu.
5. **Dọn dẹp, ngay sau cổng:** gỡ ba stage cũ, nhánh A4/A5 v3, và ba tuỳ chọn thua. Vẫn đọc và chấm được artifact v3 cũ.

Sau khi xong, luồng chỉ còn A1 → A2 → A3/A3′ → A4 (gộp thực thể, kiêm danh tính) → A5 (mô tả, câu neo, trạng thái dạy) → A6–A7 → A8 (pass chính LLM,
pass phụ ML) → A9 → A10.

## User Stories

1. Là chủ dự án, tôi muốn chuỗi gộp là mặc định, để mỗi cuốn bớt ba stage LLM nối tiếp và luồng trình bày được trong một sơ đồ A1 → A10.
2. Là chủ dự án, tôi muốn số lời gọi và USD trước A8 giảm thêm sau khi bỏ các lời phán sửa vô ích, để phút/cuốn và USD/cuốn tốt hơn chuỗi v3.
3. Là chủ dự án, tôi muốn số phút/cuốn thật của luồng mới, đo sau các vé tăng tốc, để đưa vào báo cáo.
4. Là chủ dự án, tôi muốn một cổng nghiệm thu với tiêu chí đặt trước, để việc bật mặc định có căn cứ.
5. Là chủ dự án, tôi muốn cổng trượt về chất lượng thì chưa bật, còn trượt về tiền hay thời gian thì vẫn bật và mở vé tối ưu.
6. Là chủ dự án, tôi muốn mỗi lượt có chi đều chạy dry-run trước và nằm trong trần 10 USD của đợt.
7. Là chủ dự án, tôi muốn mã sau đợt này không còn ba stage cũ và ba tuỳ chọn thua, để người đọc mã và hội đồng không phải hiểu nhánh chết.
8. Là chủ dự án, tôi muốn tài liệu (ADR, `CONTEXT.md`, spec-addendum) đổi cùng commit bật mặc định, để tài liệu không nói ngược mã.
9. Là người học, tôi muốn một khái niệm có hai cách viết (ví dụ "Gram - Schmidt" và "Gram-Schmidt") chỉ hiện một lần trong lộ trình.
10. Là người học, tôi muốn các khái niệm đồng nghĩa không bị tách ra chỉ vì một cặp khác trong cùng nhóm bị phán "khác".
11. Là người học, tôi muốn lộ trình không thêm khái niệm chỉ được nhắc qua. Neo "một khái niệm" giữ cách phán của C8.
12. Là Claude (nghiên cứu), tôi muốn chia cụm A4 tất định, để chạy lại cùng đầu vào thì tái dùng được cache và so được hai cấu hình.
13. Là Claude, tôi muốn biết nhiễu thuần của pass chính khi đầu vào phiên cố định, để đặt ngưỡng E4 cho cổng.
14. Là Claude, tôi muốn thử cho các phiên pass chính chạy song song, để biết có rút ngắn thời gian mà không hại chất lượng hay không.
15. Là Claude, tôi muốn số đo thời gian phủ cả các đoạn CPU của canonical và của stage đặt tên module, để không còn 45% thời gian nằm ngoài phép đo.
16. Là Claude, tôi muốn đo E4 của pass phụ ML trên đồ thị chuỗi gộp so với mốc 18d, để biết có phải học lại mô hình E5 hay không.
17. Là nhân viên, tôi muốn mỗi sửa đổi A4 có tuỳ chọn và mục config riêng, để test được từng cái và khoá cache đổi đúng chỗ.
18. Là nhân viên, tôi muốn các vé tăng tốc có test chứng minh đầu ra giống hệt, cụ thể là câu ứng viên và mention map.
19. Là nhân viên, tôi muốn danh sách các hàm dùng chung phải giữ khi gỡ stage cũ, để không xoá nhầm.
20. Là người chạy D-01, tôi muốn `a4 --names-only` vẫn chạy được khi mặc định là chuỗi gộp.
21. Là người đọc artifact cũ, tôi muốn A8, A10, bộ chấm và Pha B vẫn đọc được artifact v3 có `identity_map` sau khi gỡ stage.
22. Là phiên Pha B, tôi muốn được báo trước rằng id node đổi và cache bài giảng cũ mất hiệu lực, và muốn có một test nạp đồ thị chuỗi gộp qua bộ nạp
    Pha B.
23. Là người gán T-01, tôi muốn T-01 chạy trên chuỗi gộp khi vàng đã có, với vàng quy id qua bảng chuyển hướng, và giữ mù tập giữ lại.

## Implementation Decisions

### Pha 1a. Sửa A4 của chuỗi gộp

Mọi sửa đổi chỉ áp ở chuỗi `gop`. Mỗi sửa đổi có mục riêng trong config, nên nằm trong khoá cache. Băm config của chuỗi v3 giữ nguyên.

**1. Bỏ nguồn đề cử `same_evidence`.**
- Trên 13 canonical chuỗi gộp, nguồn này chưa sinh lần gộp nào, mà tốn khoảng 112 lời phán sửa trên doc-4.
- Nguồn này không còn sinh cạnh đề cử. Số đếm trong `stats` là 0, hoặc không có mục.

**2. Cạnh cắt chỉ có nguồn `ngram` không sinh lời phán sửa.**
- Cạnh `ngram` vẫn dùng để chia cụm.
- Ở bước phán sửa, cặp bị cắt mà nguồn duy nhất là `ngram` thì giữ tách, không gọi mô hình. Nhật ký ghi lý do riêng; số đếm vào `stats`.
- Đo được: 0 gộp mất ở cấu hình mặc định; doc-4 bớt 116 lời phán sửa.

**3. Giải mâu thuẫn bắc cầu theo kiểu bảo thủ.**
- Hiện nay, chỉ một cặp "khác" trong thành phần là cả thành phần bị tách thành đơn lẻ và hoãn.
- Cách mới: trong thành phần mâu thuẫn, chỉ giữ gộp cho các cặp **chung tên sau chuẩn hoá**. Các nhóm còn lại tách và hoãn như hiện nay.
- Nhật ký `transitive_conflict` ghi thêm các cặp được giữ.
- Mô phỏng: phục hồi 2 gộp đúng ở doc-1, 0 gộp sai.
- Biến thể "tham lam" bị loại, vì kéo lại một gộp sai đã biết ở xstk.

**4. Chung tên sau chuẩn hoá thì buộc gộp.**
- Áp cho hai nhóm có **tên** trùng nhau sau chuẩn hoá: NFKC, bỏ dấu LaTeX, gộp gạch nối và khoảng trắng quanh gạch nối. Không áp cho alias, vì nhiều alias
  của A3 sai.
- Đây là ràng buộc "cùng" khi dựng thành phần gộp, đi qua cơ chế ràng buộc sẵn có. Quyết định người duyệt "khác" vẫn thắng.
- Mô phỏng: thêm 4 gộp đúng (χα 2 = χα^2, χ0 2 = χ0^2, Gram-Schmidt, Véctơ tọa độ), 0 gộp sai.

**5. Chia cụm A4 tất định.**
- Trước khi chạy thuật toán chia cụm, đổi id node thành số nguyên theo thứ tự đã sắp, rồi đổi ngược kết quả.
- Cùng đầu vào và cùng seed thì ra cùng cụm, bất kể `PYTHONHASHSEED`.
- Thuật toán hiện nay là Louvain, giữ nguyên. Spec gộp khâu gọi nhầm là Leiden.

**6. R2 của chuỗi gộp nhận thêm nhãn `coextensive_with`.**
- So đúng nhãn sau chuẩn hoá, như các nhãn của vé 17j.
- Đổi mã luật kiểm trong config chuỗi `gop`.

### Pha 1b. Cấu hình, CLI và (nếu nhận) pass chính song song

**Mặc định mới:**
- chuỗi thượng nguồn: `gop`;
- chế độ neo: `single`, cả trong cấu hình lẫn mặc định của hàm dựng stage canonical;
- `merge_description_enabled=false` và cỡ lô phán sửa 1: đã đúng, giữ nguyên.

**CLI:**
- `a4 --names-only` và `a4 --prepare` mà không có `--upstream-chain` tường minh thì tự dùng chuỗi `v3`. Có `--upstream-chain gop` tường minh thì vẫn báo lỗi
  như hiện nay.
- Lệnh `roadmap` giữ cách chọn chuỗi theo canonical đang dùng. README ghi rõ: chạy `a4` mặc định trên tài liệu cũ sẽ đổi chuỗi của lần `roadmap` sau.

**Pass chính song song — chờ kết quả thí nghiệm của Claude ở pha 3:**
- Nếu thí nghiệm cho thấy bỏ "cạnh đã có của các phiên trước trong chương" khỏi đầu vào phiên không làm E4 tụt quá dải nhiễu, thì:
  - thêm tuỳ chọn này vào pass chính, nằm trong khoá cache;
  - các phiên của một chương chạy song song.
- Nếu không đạt, mục này bị bỏ. Claude ghi kết quả vào spec này trước khi giao vé.

### Pha 2. Tăng tốc (không đổi khoá cache)

1. **Dựng câu ứng viên neo:** chuẩn hoá các chunk **một lần** cho cả tài liệu, thay vì cho từng khái niệm. Câu ứng viên phải giống hệt trước.
2. **Đo thời gian:**
   - thêm đo phần cho các đoạn CPU của canonical: dựng node, dựng đồ thị đề cử, đề cử thêm, chuẩn bị neo;
   - stage đặt tên module ghi `stats` thời gian.
3. **Stage mention:**
   - tính độ gần ngữ nghĩa bằng thư viện số học vector;
   - khớp tên chính xác một lần cho cả tài liệu;
   - không embed lại các tên đã embed ở stage cụm.
   Mention map phải giống hệt trước.
4. **Chạy song song ở canonical:**
   - nâng số lời gọi đồng thời mặc định lên khoảng 16, vẫn đi qua bộ giới hạn tốc độ hiện có;
   - bỏ rào chia lô 8 khái niệm ở đường neo của canonical;
   - xoá mục cấu hình `vertex_concurrency`, vì không nơi nào đọc nó.
5. **Pass phụ ML:** tìm vì sao doc-4 mất 592 giây và sửa nút cổ chai. Đặc trưng và điểm phải giống hệt trước.

### Pha 3. Thí nghiệm và cổng (Claude, có chi)

**Thứ tự:** (15) đo nhiễu → (14) pass chính song song → quyết pha 1b → cổng. Trước mỗi lượt có chi đều chạy dry-run và báo số. Trần 10 USD cho cả đợt.

**(15) Đo nhiễu pass chính.**
- Phát lại một số phiên pass chính với đầu vào cố định, lấy từ nhật ký của 17i, vài lần mỗi phiên.
- Đo độ ổn định của cạnh, rồi suy ra dải nhiễu của E4.
- Ước khoảng 0,93 USD.

**(14) Pass chính song song.**
- Chạy bằng script nghiên cứu, không sửa mã sản phẩm, trên doc-1 và xstk: khoảng 0,55 USD. Thêm doc-4 nếu kết quả hứa hẹn: khoảng 2,2 USD.

**Cổng, kiêm dựng lại artifact chuẩn.**
- **Phạm vi:**
  - canonical chuỗi gộp với cấu hình sau pha 1 cho doc-1, xstk, doc-4, nhap-mon-ml, naive-bayes, doc-6;
  - chuỗi đồ thị cho 3 tài liệu có vàng;
  - chạy ở kho chính.
- **Tiêu chí:**
  - neo ở đích vàng không kém 17i: doc-1 25/26, xstk 26/26, doc-4 47/47 cùng trạng thái;
  - gộp sai mà vàng phát hiện không quá 3;
  - E4 nằm trong dải nhiễu của (15) so với các lượt 17i;
  - lời gọi và USD trước A8 không vượt mức ước của nghiên cứu (doc-4 khoảng 1.230 lời, khoảng 1,0 USD);
  - E4 của pass phụ ML không tụt rõ so với 18d.
- **Luật khi trượt:**
  - trượt về chất lượng thì chưa bật; sửa rồi chạy lại phần hỏng;
  - E4 lệch trong dải nhiễu thì coi là qua;
  - vượt tiền hay thời gian mà chất lượng đạt thì vẫn bật và mở vé tối ưu.
- **Đầu ra:** một báo cáo cổng có số phút/cuốn, USD/cuốn, lời gọi theo phần, và các chỗ đã đọc.

### Pha 4. Bật mặc định và tài liệu (cùng commit)

- **ADR 0016:**
  - danh tính là một phần của gộp thực thể ở A4;
  - neo và trạng thái dạy quyết ở A5, mỗi khái niệm một lời;
  - provenance rời chuỗi;
  - vì sao bỏ chế độ neo gom vào A5, bỏ đề cử theo mô tả, và bỏ gom lô lời phán sửa (số đo của 17i và nghiên cứu).
- **ADR 0004:** thêm mục cập nhật: vector mô tả nháp không còn dùng để đề cử ở A4.
- **`CONTEXT.md`:**
  - "Cặp nghi trùng" ghi các nguồn đề cử còn lại;
  - "Xác minh danh tính" đổi thành xác minh cặp gộp khác tên ở A4;
  - "Bản đồ danh tính" chỉ còn ở artifact v3;
  - thêm "Câu neo" và "Trạng thái dạy".
- **Spec-addendum:** sơ đồ pha A theo luồng mới.
- **Spec gộp khâu:** sửa dòng "Lịch" theo quyết định 2026-10-16.
- **Bàn giao Pha B** (tệp bàn giao của phiên Pha B): id node đổi theo bảng chuyển hướng, cache bài giảng và quiz cũ mất hiệu lực.

### Pha 5. Dọn dẹp (vé riêng, ngay sau cổng)

**Gỡ:**
- stage provenance, stage `teaching` (C8) và stage danh tính;
- nhánh A4/A5 v3 có gọi mô hình;
- các giá trị `--stop-after provenance|teaching|identity` và cờ `--identity-review`;
- ba tuỳ chọn thua: chế độ neo `a5`, nguồn đề cử theo mô tả, gom lô lời phán sửa;
- tuỳ chọn chọn chuỗi `upstream_chain` thôi nhận `gop` / `v3` cho đường chạy mới.

**Giữ đường canonical chỉ lớp tên** cho D-01 (D-01 đã đóng băng): `--names-only`, `--prepare`.

**Phải giữ, vì mã khác đang dùng.** Chuyển sang module trung tính nếu module chứa chúng bị gỡ:
- hàm kiểm câu trích nguyên văn (Pha B dùng);
- schema xác minh và bộ nạp tệp duyệt (canonical dùng);
- miền danh tính (đề cử và duyệt ở canonical dùng);
- lõi neo (canonical dùng).

**Hợp đồng đọc artifact cũ:** A8, A10, bộ chấm và Pha B vẫn đọc được artifact v3 có `identity_map`.

### Quyết định khác

- **D-01:** đóng băng, không thêm cuốn mới. Học lại E5 trên đặc trưng chuỗi gộp là việc sau, nếu cần.
- **E5:** chỉ đo bản 0 USD trong cổng. Bản trả phí và việc học lại chỉ làm khi E4 tụt rõ.
- **T-01:**
  - chờ có vàng của hai người gán rồi mới dựng canonical chuỗi gộp cho hai cuốn giữ lại;
  - chấm bằng tuỳ chọn quy id vàng (vé 17h);
  - script kiểm chỉ in trường số trong allowlist;
  - là số đưa vào báo cáo, không phải cổng.
- **Luật neo L8b** không thuộc spec này. Để làm nghiên cứu sau, phục vụ hướng bỏ LLM của seminar.

## Testing Decisions

**Một test tốt** kiểm hành vi nhìn từ ngoài: hợp đồng artifact, số lời gọi mô hình, việc tái dùng cache, việc từ chối có thông báo. Không kiểm chi tiết
cài đặt bên trong. Mỗi luật chặn phải được thấy đỏ ít nhất một lần (AGENTS.md mục 5).

**Seam dùng lại, không thêm seam mới**, trừ test tích hợp Pha B:

1. **Stage canonical chạy trên fixture tài liệu thật, với mô hình giả.** Mẫu sẵn có là các test canonical chuỗi gộp của vé 17b, 17e, 17f, 17g, 17j, 17k.
   - **Mục 1:** không cặp nào mang nguồn `same_evidence`.
   - **Mục 2:** cặp cắt chỉ có `ngram` không sinh lời gọi, giữ tách, và được đếm. Cặp cắt có thêm nguồn khác vẫn được phán sửa.
   - **Mục 3:** thành phần có một cặp "khác" vẫn giữ gộp cho cặp chung tên sau chuẩn hoá. Cặp không chung tên trong thành phần đó bị tách và hoãn.
   - **Mục 4:** hai nhóm chỉ khác cách viết gạch nối hay LaTeX thì gộp, kể cả khi mô hình phán "khác". Quyết định người duyệt "khác" thắng. Hai nhóm chỉ
     chung alias thì không bị buộc gộp.
   - **Mục 5:** chạy hai tiến trình con với `PYTHONHASHSEED` khác nhau, ra cùng cụm và cùng băm payload.
   - **Mục 6:** `coextensive_with` nối hai node tách rời thì bị phán lại.
   - **Mọi mục:** đổi tuỳ chọn thì khoá cache đổi; băm config v3 giữ nguyên.
2. **Cấu hình và CLI.** Mẫu sẵn có là test CLI chuỗi gộp.
   - Mặc định là `gop` và `single`.
   - `--names-only` và `--prepare` không có `--upstream-chain` thì chạy chuỗi v3. Có `--upstream-chain gop` thì báo lỗi.
3. **Tăng tốc:** test giống hệt trên fixture thật. Câu ứng viên, mention map, đặc trưng và điểm pass phụ đều so băm trước và sau. Số đo phần có mặt
   trong manifest.
4. **Dọn dẹp:**
   - import toàn bộ gói sau khi gỡ;
   - artifact v3 trong fixture vẫn qua A8, A10, bộ chấm và bộ nạp Pha B;
   - các giá trị `--stop-after` cũ báo lỗi rõ.
5. **Test tích hợp Pha B (mới):** nạp đồ thị `stages` của chuỗi gộp qua bộ nạp đồ thị Pha B. Node có câu neo và chunk dạy đúng dạng mà bài giảng đọc.

**Nghiệm thu nghiên cứu** là pha 3, do Claude làm với chi phí đã duyệt.

## Out of Scope

- Luật neo L8b và mọi hướng bỏ LLM ở A4/A5 (seminar).
- Sửa luật A2 "Cách giải" và luật bỏ qua của C8 (vé 05).
- Học lại mô hình pass phụ ML, trừ khi cổng thấy tụt rõ.
- Đường lớp tên cho chuỗi gộp (D-01 mở rộng).
- Đợt dựng baseline chỉ số đánh giá cho mọi khâu. Thí nghiệm (15) cung cấp số cho đợt đó.
- Luật chống lật chiều cạnh trục; luật ký hiệu trong câu bằng chứng; xác minh mù cho cặp `subtype_of`. Nghiên cứu đã cho thấy không có ích ổn định hoặc
  rủi ro cao.
- Pha B và web, ngoài một test tích hợp và tệp bàn giao.

## Further Notes

**Ước lợi trên doc-4, trước A8** (nghiên cứu mục 7):

| Cấu hình | Lời gọi | USD |
|---|---|---|
| sau pha 1 | khoảng 1.230 | khoảng 1,0 |
| neo "một khái niệm" chưa sửa | khoảng 1.550 | khoảng 1,26 |
| chuỗi v3 | 2.295 | 1,367 |

Cộng pha 2, canonical doc-4 có thể từ 14,7 phút còn khoảng 4–6 phút. Số thật đo ở cổng.

**Rủi ro chính:**
- gộp nhiều sửa đổi A4 vào một lượt nghiệm thu thì khó quy công từng sửa đổi; mỗi sửa đổi đã có mô phỏng 0 USD riêng;
- E4 một lượt nhiễu khoảng ±0,15 Q7; (15) đo trước để đặt ngưỡng;
- xoá nhầm hàm dùng chung khi dọn dẹp; đã liệt kê ở pha 5.

**Thứ tự giao vé:**
- pha 1a và pha 2 song song;
- (15) và (14) của Claude chạy song song với pha 1a;
- pha 1b sau (14);
- cổng sau cả pha 1 và pha 2;
- pha 4 sau cổng;
- pha 5 ngay sau pha 4.
