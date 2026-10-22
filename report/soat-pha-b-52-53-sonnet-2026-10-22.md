**Trạng thái:** soát xong 2026-10-22: SA-52 đạt có ghi chú; SA-53 đạt có ghi chú.

# Soát độc lập SA-52 và SA-53 — 2026-10-22

Người soát: agent Sonnet 5.5. Chỉ đọc mã sản phẩm; thử sửa sai trong từng worktree rồi khôi phục bằng `git checkout -- <tệp>`, sau mỗi lần `git status --short src` rỗng. Không gọi mô hình, không chạm tập giữ lại. Mọi lệnh Python đặt `PYTHONPATH` vào worktree và đã in `doc2roadmap.__file__` để chắc nạp đúng mã.

## SA-52 (`work/sa52-cloze-quality`, 409e8a4)

**Phán xét: đạt có ghi chú.** Bốn lỗi gốc đã hết trên dữ liệu thật; mọi luật mới có test đỏ khi bỏ; có ba khe thiếu test và hai lỗ nhỏ trong luật dấu hai chấm (xem dưới), không chặn ghép.

### Lệnh đã chạy
- Bộ quiz theo danh sách của giao việc (6 tệp quiz + `tests/unit/test_architecture.py`), `--basetemp tmp/rev-a`: **57 đạt, 0 hỏng**.
- Phát lại 0 USD, tự viết (`tmp/replay52.py` của tôi, gọi thẳng `_cloze_bank` cho mọi khái niệm của mọi module, sáu cuốn: doc-1 v8, nhap-mon-ml v50, naive-bayes v49, doc-6 v29, xstk-ch3-1 v68, doc-4 v27), chạy trên `main` và trên nhánh. Đầu ra `tmp/rev-main.json`, `tmp/rev-branch.json` trong worktree.

### Đối chiếu tiêu chí
| Tiêu chí | Bằng chứng |
|---|---|
| Nhiễu theo từng câu; không đủ hai thì bỏ, mã `cloze.distractor_in_stem` | test 1, 2; đỏ khi bỏ lọc |
| Không khoét giữa thuật ngữ dài hơn, mã `cloze.blank_inside_longer_term` | test 3; đỏ khi `longer_terms=[]` |
| Q6: nhiễu ký hiệu bị bỏ, đáp án ký hiệu thì bỏ khái niệm (`cloze.notation_option`) | test 4, 5; đỏ khi bỏ từng nhánh |
| Câu kết bằng ":" bỏ (`cloze.incomplete_lead_in`) | test 6; đỏ khi bỏ |
| `LOCAL_RULES_VERSION` = v4 và test cache không monkeypatch khi tra | test 7; lùi về v3 thì đỏ (test chỉ monkeypatch để tính khoá cũ, khi tra dùng hằng số thật, đúng yêu cầu) |
| Giữ ngoại lệ "Hiệu" | bỏ ngoại lệ thì `test_cloze_does_not_blank_hiệu_inside_the_ký_hiệu_compound` đỏ |
| Phát lại 0 USD bốn số đếm về 0 | xác nhận độc lập, xem "Con số" |
| Test đỏ trước, xanh sau | tôi không chạy lại trên mã cũ từng test; bằng chứng gián tiếp là các mutation tương ứng đều đỏ |

### Bảng thử sửa sai (tệp `quiz.py`)
| Chỗ đổi | Kết quả |
|---|---|
| bỏ lọc nhiễu theo câu (`unseen = distractors`) | BẮT (test 1 và 2) |
| `longer_terms = []` | BẮT (test 3) |
| đáp án ký hiệu được phép (`if False`) | BẮT (test 5) |
| nhiễu ký hiệu được phép | BẮT (test 4) |
| bỏ `or quote.endswith(":")` | BẮT (test 6) |
| `LOCAL_RULES_VERSION` về v3 | BẮT (test 7) |
| bỏ ký tự `×` khỏi regex ký hiệu | BẮT (test 4, 5) |
| bỏ ngoại lệ "Hiệu" | BẮT (test cũ) |
| `_term_in` bỏ ranh giới từ (`(?<!\w)`, `(?!\w)`) | **SỐNG SÓT. Thiếu test.** Bản sai làm nhiễu "Tam" bị coi là "có trong câu" khi câu chứa "Tam giác", và "hợp" khớp trong "tập hợp" |
| `distractor_terms.get(value,[value])` đổi thành `[value]` (bỏ alias của nhiễu) | **SỐNG SÓT. Thiếu test.** Vé nói "tên hay alias"; không test nào có nhiễu chỉ lộ qua alias |
| bỏ ghi `distractor_terms` ở nhánh dự phòng (nhiễu lấy từ toàn graph) | **SỐNG SÓT. Thiếu test** (cùng lý do) |
| bỏ ký tự `^` khỏi regex ký hiệu | **SỐNG SÓT. Thiếu test** cho `^` (các ký tự khác chỉ `×` được kiểm) |
| bỏ `normalized not in target_aliases` trong `_longer_concept_terms` | SỐNG SÓT. Chỉ khác khi hai nút chia sẻ alias; thiếu test, nguy cơ nhỏ |
| bỏ `if node_id == concept["node_id"]: continue` | SỐNG SÓT, gần tương đương: alias dài hơn của chính nút đáp án (ví dụ "phép hợp" của "Hợp") sẽ làm bỏ câu oan; chưa có test |

Sau mỗi lần thử, `git status --short src` rỗng.

### Lỗi hay rủi ro tìm thêm
1. **Luật dấu hai chấm chỉ nhận `:` thường** (`quiz.py` nhánh `quote.endswith(":")`). Ca tái hiện (đồ thị tổng hợp của test, câu "…sau đây："): dấu hai chấm toàn chiều rộng `：`, và `:…`, `:)` vẫn qua lưới (`status ready`). `:` kèm dấu cách, NBSP, đuôi trắng thì bị bắt đúng vì `strip()`. Trên sáu cuốn thật không có câu nào kết bằng `：`; rủi ro thấp.
2. **Luật tên dài hơn xét cả câu, không xét đúng vị trí chỗ khoét.** Câu có tên dài hơn ở chỗ khác bị bỏ oan; đổi lại luôn an toàn (không bao giờ khoét nhầm). Alias một từ của Pha A làm luật bỏ rộng: "Tập hợp" có alias `tập` (19 tên dài hơn), "Học" (19), "Mẫu" (33), "Vô/Hữu/Đạo" (10 đến 12). Khái niệm "Mẫu", "Vành", "Hợp", "Giao", "Tích" trong doc-1/xstk mất câu định nghĩa vì lý do này. Chấp nhận được, nhưng số khái niệm mất là cái giá thật; báo cáo người cài đã tính vào 672 → 634.
3. **Quy tắc ký hiệu chỉ xét tên khái niệm đáp án và tên nhiễu, không xét alias.** Ví dụ `Ma trận chuyển cơ sở` có alias `Ps→t`; alias này có thể bị khoét thành chỗ trống nhưng đáp án in ra là tên đầy đủ nên không phạm Q6. Không phải lỗi.
4. Đã xem, không lỗi: lọc nhiễu theo câu không làm hai nhiễu còn lại chứa nhau (đi qua `_balanced_distractors`, giữ nguyên luật chứa nhau); ngoại lệ "Hiệu" còn chạy; `_longer_concept_terms` quét cả graph chứ không chỉ module, an toàn hơn.

### Con số đã kiểm lại
Phát lại riêng (khác số đếm của người cài vì tôi đếm theo `_cloze_bank` tối đa 2 câu mỗi khái niệm, không qua chọn câu của `make_quiz`): main 1078 câu, nhánh 1006 câu.

| Số đếm | main | nhánh |
|---|---|---|
| nhiễu nằm trong câu | 296 | **0** |
| khoét giữa tên dài hơn (tính độc lập bằng thay alias vào tên dài hơn rồi tìm trong câu) | 22 | **0** |
| phương án có ký hiệu | 9 | **0** |
| câu kết bằng `:` hoặc `：` | 52 | **0** |

Câu mới xuất hiện sau sửa (không có trong main): 12, đều là câu thay thế. Rơi thêm ở nhánh: câu kết ":" (doc-1 39 lượt loại, xstk 30), khoét tên dài hơn (doc-1 15, doc-4 22, nhap-mon-ml 4, xstk 4), nhiễu trong câu 4 (xstk).

### Đọc tận đầu ra, 10 câu ngẫu nhiên (seed 5)
Tốt: "Bệnh giáo điều" (nhiễu "Nhận thức kinh nghiệm", "Tri thức kinh nghiệm", không nằm trong câu); "Mâu thuẫn bên ngoài" (nhiễu "Mâu thuẫn bên trong", "Mâu thuẫn không cơ bản"); "Phương pháp luận chung" (nhiễu "Phương pháp luận ngành", cùng họ, hợp lý); "Ý thức tôn giáo".
Còn khuyết điểm, không phạm các luật vé này:
- "Quan hệ sản xuất tàn dư": ba phương án dài ngắn lệch rất xa (nhiễu thứ hai dài hơn đáp án nhiều lần), người học đoán theo độ dài (Q? về cân bằng, có từ trước SA-52).
- "Thuộc tính cơ bản": nhiễu "Thuộc tính không cơ bản" là phủ định của đáp án, gần như trắc nghiệm đối lập, dễ đoán nhưng hợp lệ.
- "Cơ sở dữ liệu": câu phủ định "không được xem là một ___", dễ gây nhầm nhưng đáp án vẫn đúng theo nguồn.
- "Nhận thức lý luận": nhiễu "Nhận thức luận" gần giống tên đáp án; hợp lệ.
- Không câu nào kết bằng dấu hai chấm, chứa ký hiệu hay có nhiễu nằm trong câu.


## SA-53 (`work/sa53-bridge-final-index`, 8ed2e54)

**Phán xét: đạt có ghi chú.** Sửa đúng gốc lỗi (chỉ số gốc của luồng), regression đỏ trên `main` rồi xanh, các nhánh chỉ số đều có mutation bắt được, không tìm thấy ca nào làm câu đã phát bị rút khỏi bản final. Ghi chú: một mutation sống sót là bản sai tương đương; phát lại SA-43 tôi không chạy lại (xem "Con số").

### Lệnh đã chạy
- Bộ bài giảng theo danh sách giao việc (10 tệp + `tests/unit/test_architecture.py`), `--basetemp tmp/rev-b`: **100 đạt, 0 hỏng**. `doc2roadmap.__file__` nằm trong worktree.
- Chạy riêng `test_phase_b_sa53_bridge_index.py` với `PYTHONPATH` trỏ vào mã `main`: **2 hỏng, 2 đạt**. Hỏng đúng hai test mong đợi: regression `[a, a-trùng, c]` và test cache v6. Hai test còn lại (đối chứng không câu trùng đứng trước; hai câu nối trùng không bật K6) đạt trên mã cũ, đúng như báo cáo người cài: lớp lọc trước K6 đã có từ SA-49, vé chỉ thêm test, mutation bắt.
- Với SA-52, 7/7 test mới hỏng trên mã `main` và đạt trên nhánh.

### Đối chiếu tiêu chí
| Tiêu chí | Bằng chứng |
|---|---|
| Regression `[a, a-trùng, c]`: đỏ trên mã cũ, xanh sau sửa; final, cache, `prerequisites[].bridge` bằng đúng câu đã phát | test 1; đỏ trên `main` (đã chạy) |
| Ca đối chứng không có câu trùng đứng trước | test 2, xanh cả hai |
| Hai câu nối trùng không làm thành "cắt ngắn" hay sửa; bỏ lớp lọc thì đỏ | test 3; mutation "bỏ lớp lọc" đỏ |
| Lùi `lecture_validator_version` về v6 thì test cache đỏ | test 4; mutation v6 đỏ; test đỏ cả trên mã cũ |
| `lecture-validator-7` | `phase_b_limits.py`; ghi chú: lùi về v5 thì test vẫn xanh (không bắt buộc theo vé) |
| Phát lại 0 USD SA-43 | **chưa kiểm độc lập**, xem dưới |
| Cổng toàn repo | tôi không chạy theo lệnh cấm; chấp nhận báo cáo người cài (2.118 đạt ở lần 2) |

### Bảng thử sửa sai (`lectures.py`, `phase_b_limits.py`)
| Chỗ đổi | Kết quả |
|---|---|
| `stream_indexed` luôn `enumerate` (hoàn nguyên sửa chỉ số) | BẮT (regression) |
| nhánh K6 dùng `enumerate` | BẮT (regression) |
| nhánh cắt đuôi dùng `enumerate` | **SỐNG SÓT, bản sai tương đương về đầu ra.** Tôi dựng ca cắt đuôi thật (câu nối `[a, a-trùng, c]` cộng giải thích thứ ba trùng giải thích đầu, nên K6 mở sau cổng, `cat_ngan`), chạy với và không có mutation: stream, final, cache giống hệt vì `_merge_emitted` bù lại đúng các câu đã phát. Vậy sửa ở nhánh này là phòng thủ chồng, chưa có test riêng |
| bỏ `continue` của lọc trùng tiên quyết | BẮT (test 3) |
| `bridge_raw_indices.append(raw_index + 1)` | BẮT (test 1, 2) |
| ghi vị trí đã lọc thay vì vị trí gốc | BẮT (test 1) |
| `lecture-validator-7` đổi về v6 | BẮT |
| đổi về v5 | sống sót, ngoài yêu cầu vé (chỉ cần v6) |

Sau mỗi lần thử, `git status --short src` rỗng. Lưu ý: tập `phase_b_limits.py` dùng CRLF, script thử của tôi ghi lại làm `git status` hiện `M` tạm thời (không có khác biệt nội dung, `git diff --stat` rỗng); đã `git checkout -- src` và status sạch.

### Lỗi hay rủi ro tìm thêm
1. **Không có ca câu đã phát bị rút khỏi final.** Tôi thử riêng ca ngược với vé: câu nối đầu của tiên quyết a bị K6 loại ở stream, câu nối thứ hai của a được phát. Bộ lọc trùng ở final giữ câu đầu (hợp lệ) và bỏ câu thứ hai, rồi K6 loại câu đầu; không có sửa chữa thì tiên quyết a mất. Thực tế (`tmp/probe53.py`, hai kịch bản): stream, final, cache và `prerequisites[].bridge` giống nhau, vì `_merge_emitted` đưa câu đã phát về. Tuy nhiên, kết quả này dựa vào cơ chế bù, không có test khoá cho kịch bản "câu a đầu bị K6, câu a sau được phát". **Khe thiếu test**, chưa phải lỗi.
2. **`zip(bridge_raw_indices, items)` không cắt cụt.** `bridge_raw_indices` và `filtered_bridges` được thêm cùng lúc trong cùng vòng lặp nên luôn dài bằng nhau; sau đó `output["bridges"] = filtered_bridges` nên `items` cùng độ dài. Nếu `bridges` không phải list, các dòng `enumerate(output.get("bridges", []))` đã ném lỗi hoặc đi từng ký tự từ trước SA-53 (không do SA-53 gây ra), và `zip` vẫn đủ độ dài.
3. **Các trường khác `bridges`** vẫn dùng `enumerate(items)`, nên cắt đuôi và K6 cho `explanation`, `example`, `contrasts` giữ nguyên hành vi cũ. Đúng vì lọc trùng chỉ chạm `bridges`.
4. **Tên hằng/vị trí**: `stream_indexed` định nghĩa lại như hàm lồng trong mỗi vòng thử (một lần mỗi lượt); không ảnh hưởng.

### Con số đã kiểm lại
- 4 test mới, 100 đạt tổng, regression đỏ trên `main`: đã chạy độc lập.
- Phát lại SA-43 (8 cặp bài–tiên quyết, 16 nhánh): **tôi không phát lại được độc lập** vì wrapper phát lại của người cài (đánh số lại bản ghi) không được commit; chạy thẳng `sa43_acceptance.py --replay` cần cả doc-1@57 (đã mất) và ghi vào kho trong worktree. Tôi chỉ đọc `tmp/sa53-replay/subset-summary.json` của người cài: 16 nhánh, 13 câu nối, 8 cặp (bài, tiên quyết) riêng biệt, 13 ready và 3 failed (1 lệch fixture ở nhiệt độ 1), khớp với "15/16 khớp fixture" và "không nhánh nào có hai câu nối cùng tiên quyết". Vì không nhánh nào có hai câu nối cùng tiên quyết, đoạn lọc trùng (nơi sửa) không bị kích hoạt trên dữ liệu thật, nên phát lại này không phải bằng chứng cho đúng sửa; bằng chứng đến từ test tổng hợp.

## Tóm tắt cho Claude
- SA-52: đạt có ghi chú. Ba khe thiếu test (ranh giới từ của `_term_in`, alias của nhiễu, ký tự `^`) và luật dấu hai chấm bỏ sót `：` và `:…`.
- SA-53: đạt có ghi chú. Sửa chỉ số đúng; nhánh cắt đuôi là bản sai tương đương nhờ `_merge_emitted`; thiếu test khoá kịch bản "câu a đầu bị K6, câu a sau được phát"; phát lại SA-43 không phải bằng chứng cho đúng sửa.

## Nghiệm thu của Claude (2026-10-22)

**Kết luận:** nhận phán xét của người soát. SA-52 và SA-53 **đạt có ghi chú**, được ghép.

**Kiểm lại một nhận định của người soát.** Mục 2 phần SA-52 cho rằng luật tên dài hơn "xét cả câu, không xét vị trí chỗ khoét", nên bỏ oan những câu có tên
dài hơn ở chỗ khác. Nhận định này **không đúng** với mã hiện hành. `_blank_concept_aliases` khoét **mọi** lần xuất hiện của tên và alias của đáp án.
Tên dài hơn lại chứa alias đó theo ranh giới từ, nên hễ tên dài hơn có trong câu thì luôn có một chỗ khoét nằm trong nó. Như vậy, xét cả câu cho cùng
kết quả với xét vị trí. Kiểm trên sáu cuốn (`tmp/sa52-cloze-quality/tmp/claude_longer_pos.py`): **45/45** câu bị loại vì `cloze.blank_inside_longer_term`
có chỗ khoét nằm trong tên dài hơn, 0 câu chỉ có tên dài hơn ở chỗ khác.

Khái niệm mất câu (Mẫu, Hợp, Phân loại, Phương pháp luận…) là do khoét mọi lần xuất hiện, cộng với alias một từ của Pha A. Cách đổi duy nhất là không
khoét lần xuất hiện nằm trong tên dài hơn; đổi vậy thì câu để lộ một phần đáp án. Tôi không làm ở đây: câu điền khuyết chỉ là đường lùi, và SA-22 sẽ
đo chất lượng quiz bằng người chấm.

**Các khe người soát tìm thấy:**

| khe | xử lý |
|---|---|
| ranh giới từ của `_term_in`; nhiễu chỉ lộ qua alias (cả nhánh dự phòng); ký tự `^` | thêm test ở **SA-54** |
| SA-53: chưa có test khoá kịch bản "câu nối đầu của tiên quyết a bị K6 loại, câu nối sau được phát" | thêm test ở **SA-54** |
| SA-53: nhánh cắt đuôi dùng `enumerate` là bản sai tương đương nhờ `_merge_emitted` | ghi nhận, không cần test riêng: đầu ra giống hệt, sửa ở đó là phòng thủ chồng |
| luật dấu hai chấm không bắt `：` (toàn chiều rộng), `:…`, `:)` | ghi nhận giới hạn; sáu cuốn không có câu nào như vậy. Sửa thì phải lên `LOCAL_RULES_VERSION` và sinh lại ngân hàng, không đáng ở lúc này |
| phát lại SA-43 không chạm đoạn lọc trùng | đồng ý; bằng chứng của SA-53 là test tổng hợp và regression đỏ trên main |

**Ghép:** mỗi nhánh nhận main mới nhất rồi chạy lại cổng toàn repo, sau đó mới ghép. Hash ghép và kết quả cổng ghi trong bảng kế hoạch.
