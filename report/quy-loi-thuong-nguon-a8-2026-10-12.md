# Quy lỗi cạnh vàng về thượng nguồn của A8: trạng thái dạy, neo, danh tính (2026-10-12)

Chủ dự án hỏi trạng thái dạy, neo và danh tính có quan trọng với A8 (pass chính, pass phụ) hay không. Nếu nghiên cứu chỉ ra là cần, chủ dự án sẽ
duyệt kế hoạch bỏ LLM ở ba khâu này. Báo cáo này đo câu trả lời trên ba tài liệu phát triển có vàng người (doc-1, xstk-ch3-1, doc-4), tổng cộng
172 cạnh vàng. Chi phí: 0 USD, không gọi mô hình.

## Tóm tắt

- **Một phần ba số cạnh vàng bị thiếu là do thượng nguồn.** Hai pass phụ LLM v3 và LightGBM E5 đều tìm được 73/172 cạnh. Trong 99 cạnh thiếu, 36
  cạnh do thượng nguồn: 32 do trạng thái dạy, 3 do danh tính, 1 do Y không có cửa sổ định nghĩa. Mô hình A8 có giỏi hơn đến mấy cũng không lấy lại
  được 36 cạnh này.
- **Trạng thái dạy mất nhiều nhất, nhưng dồn vào một cuốn và gốc không ở LLM của C8.** 29/32 cạnh thuộc xstk. Ở đó 8/24 đích vàng bị coi là
  "chỉ nhắc", trong đó 7 khái niệm có chunk định nghĩa bị A2 gán vai trò `de_cuong`. Luật của C8 bỏ qua khái niệm chỉ có căn cứ ngoài vùng nội
  dung, hoặc chỉ cho LLM xem phần bị gán sai. doc-4 không mất cạnh nào, doc-1 mất 3.
- **Câu neo phần lớn đúng.** Claude đọc 84 câu neo của đích vàng, thấy 79 câu đúng chỗ (khoảng 94%). Năm câu neo đáng ngờ, tức 6% số đích, lại hút
  7/34 cạnh thừa của LLM v3 (21%) và 4/26 cạnh thừa của E5.
- **Giới hạn lớn hơn là thiết kế cửa sổ định nghĩa.** Trong 136 cạnh vàng có hai đầu qua được cổng trạng thái dạy và Y có cửa sổ, 49 cạnh (36%)
  có tên X không nằm trong cửa sổ của Y. Khi X có trong cửa sổ, LLM v3 tìm được 67% số cạnh và E5 tìm được 75%. Khi X nằm ngoài, LLM v3 chỉ tìm được 31% và E5
  16%.
- **Danh tính ít ảnh hưởng tới phép đo.** Ba lần gộp sai làm mất 3 cạnh vàng (2%). Số cặp đáng gộp mà bị bỏ sót thì bộ vàng này không đo được.
- **Ba khâu tốn khoảng 0,76 USD trên doc-4 trọn cuốn**, gồm provenance, C8 (neo và trạng thái dạy) và danh tính, khoảng 1.600 lời gọi. Con số này
  bằng khoảng một phần sáu phần chi LLM còn lại của một cuốn, sau khi pass phụ chuyển sang ML.
- **Kết luận:** lý do bỏ LLM ở ba khâu là phạm vi (seminar, đích dài hạn của đồ án) và chi phí, không phải chất lượng.
  - LLM ở khâu neo đang làm tốt, nên đổi khâu này là rủi ro: phải có vàng neo và cổng "không kém hơn" trước khi thay.
  - Lợi chất lượng lớn nhất là sửa chuỗi A2 → C8 (vé 05). Việc này độc lập với chuyện có LLM hay không.

## 1. Cách làm

Thượng nguồn lấy từ artifact pass phụ v3 của từng tài liệu. Artifact này chứa nút sau danh tính, trạng thái dạy, câu neo và chunk, và giống nhau
cho mọi hệ. Mỗi hệ là một payload A10 do bộ phát lại E4 (`phat_lai_e4.py`) lưu lại, trên cùng thượng nguồn đó. Ba hệ được so:
- `khong`: chỉ pass chính;
- `llm-v3`: pass chính và pass phụ LLM v3, tức luồng sản phẩm v3;
- `e5-a-hieu-chinh`: pass chính và pass phụ LightGBM đã chọn ở E5 (nhãn A, ngưỡng hiệu chỉnh).

Cạnh vàng X→Y (đã quy về nút đại diện qua `identity_map`) được tính là **có** khi đồ thị cạnh cứng của A10 có đường đi từ X tới Y. Mỗi cạnh thiếu
được gán **một** nguyên nhân, xét lần lượt theo thứ tự sau:

| thứ tự | nguyên nhân | ý nghĩa |
|---|---|---|
| 1 | danh tính gộp hai đầu | X và Y bị gộp làm một nút |
| 2 | trạng thái dạy của Y | Y là `mentioned_only`, `unchecked`, `prior_knowledge` hoặc `not_subject_matter`. Bộ kiểm loại mọi cạnh vào Y |
| 3 | trạng thái dạy của X | X có một trong các trạng thái trên, nên không vào dãy học |
| 4 | Y không có cửa sổ | Y được dạy nhưng không dựng được cửa sổ định nghĩa, nên không cạnh cứng nào vào Y qua được bộ kiểm |
| 5 | X ngoài cửa sổ | tên X không có trong cửa sổ của Y, khớp theo ranh giới từ như ứng viên của E5. Tách hai trường hợp: tên X có trong chunk neo hay chunk dạy của Y nhưng ngoài cửa sổ, hoặc không được nhắc gần Y |
| 6 | mô hình | X có trong cửa sổ mà vẫn thiếu. Tách ba trường hợp: chỉ có đường đi qua cạnh mềm, bị gỡ khi phá chu trình, hoặc không tạo |

Mức 5 là chặn cứng với pass phụ ML, vì ứng viên đòi tên X nằm trong cửa sổ. Với LLM thì không chặn: bộ kiểm chỉ đòi câu trích nằm trong cửa sổ
và có trích chunk neo, không đòi tên X. Mức 4 chặn cả hai.

**Cạnh thừa** là cạnh cứng của rút gọn bắc cầu, tức đúng các cạnh hiện ở dòng "cần:", có hai đầu là đích vàng, mà X không phải tổ tiên vàng của Y.

## 2. Kết quả chung

Bảng dưới cộng cả ba tài liệu, 172 cạnh vàng.

| | chỉ pass chính | pass phụ LLM v3 | pass phụ LightGBM (E5) |
|---|---:|---:|---:|
| **có** | 46 | **73** | **73** |
| thiếu: danh tính gộp hai đầu | 3 | 3 | 3 |
| thiếu: trạng thái dạy (Y hoặc X) | 32 | 32 | 32 |
| thiếu: Y không có cửa sổ | 1 | 1 | 1 |
| thiếu: X ngoài cửa sổ (trong chunk dạy Y / không nhắc gần Y) | 42 (12 / 30) | 34 (10 / 24) | 41 (12 / 29) |
| thiếu: mô hình (chỉ có đường mềm / không tạo) | 48 (5 / 43) | 29 (22 / 7) | 22 (11 / 11) |
| có, khi X trong cửa sổ | 39/87 | 58/87 | 65/87 |
| có, khi X ngoài cửa sổ | 7/49 | 15/49 | 8/49 |
| cạnh hiện ở "cần:" sai / tổng | 7/53 | 34/93 | 26/90 |

Bảng sau tách theo tài liệu, với hệ LLM v3:

| | doc-1 | xstk-ch3-1 | doc-4 |
|---|---:|---:|---:|
| cạnh vàng | 40 | 62 | 70 |
| có (LLM v3 / E5) | 22 / 21 | 16 / 13 | 35 / 39 |
| thiếu do trạng thái dạy | 3 | 29 | 0 |
| thiếu do danh tính | 1 | 2 | 0 |
| thiếu do Y không có cửa sổ | 0 | 1 | 0 |
| thiếu do X ngoài cửa sổ | 12 | 7 | 15 |
| thiếu do mô hình | 2 | 7 | 20 (17 chỉ có đường mềm) |

`[CHÈN HÌNH – cột chồng cho từng hệ: phần "có" và năm nhóm nguyên nhân thiếu, cộng ba tài liệu; màu riêng cho nhóm thượng nguồn (danh tính, dạy,
neo), nhóm cửa sổ và nhóm mô hình. Số liệu ở bảng trên.]`

## 3. Từng khâu

### 3.1 Trạng thái dạy

Trạng thái của đích vàng trên từng tài liệu:
- doc-1: 24/25 được dạy, 1 "chỉ nhắc";
- xstk: 15 được dạy, 1 `uncertain`, **8 "chỉ nhắc"**, trên tổng 24;
- doc-4: 45/45 được dạy.

Ở xstk, 7/8 khái niệm "chỉ nhắc" có chunk định nghĩa bị A2 gán vai trò `de_cuong`. Đây là lỗi đã ghi từ tập giữ lại v3: mục "Cách giải" bị gán
đề cương. C8 xử lý 8 khái niệm này như sau:
- 4 khái niệm không được hỏi gì (không có bản ghi C8), vì luật bỏ qua khái niệm chỉ có căn cứ ngoài vùng nội dung;
- 3 khái niệm có chunk định nghĩa bị gán đề cương, toàn bộ hoặc một phần; C8 có hỏi LLM và LLM kết luận "chỉ nhắc";
- 1 khái niệm ("Bài toán tìm kích thước mẫu") có chunk định nghĩa thuộc nội dung, nhưng LLM vẫn kết luận "chỉ nhắc".

Như vậy gốc của 29 cạnh mất ở xstk là nhãn vai trò của A2 cộng một luật của C8. LLM của C8 phán sai trên đúng dữ liệu được thấy chỉ là ca hiếm.
Hai lỗi này nằm sẵn trong [vé 05](../task/v4/00-ke-hoach.md) ("A2 'Cách giải'", "C8 bỏ qua khái niệm ngoài nội dung"); nay có số đo: 29/62 cạnh vàng
của xstk.

Có cả lỗi theo chiều ngược lại. "Phân phối chuẩn" bị coi là được dạy, trong khi xstk-ch3-1 chỉ *dùng* khái niệm này (kiến thức nền từ chương
trước), và câu neo của nó là một câu dùng chứ không phải câu dạy.

### 3.2 Neo

Hầu như mọi đích được dạy đều dựng được cửa sổ: 84/85, riêng xstk 15/16.

Claude đọc câu neo của 84 đích được dạy và phán từng câu. Đây là phán của Claude, không phải vàng người. 79 câu đúng chỗ khái niệm được định
nghĩa hoặc giới thiệu: doc-1 24/24, xstk 13/15, doc-4 42/45. Năm câu đáng ngờ:

| tài liệu | khái niệm | vấn đề |
|---|---|---|
| xstk | Ước lượng tỉ lệ | neo vào một dòng tiêu đề gạch đầu dòng ở mục 2.3, không phải chỗ dạy |
| xstk | Phân phối chuẩn | neo vào câu dùng khái niệm; trạng thái dạy cũng sai (mục 3.1) |
| doc-4 | Tính khách quan | neo vào câu về tính khách quan của không gian, thời gian, một nghĩa hẹp hơn |
| doc-4 | Quy luật chuyển hóa lượng–chất | neo vào câu tóm tắt ba quy luật, không vào mục dạy riêng |
| doc-4 | Kết cấu | câu chủ yếu nói về "Chất"; đây là nguồn của cạnh ngược "Chất → Kết cấu" ở tập giữ lại v3 |

Năm đích này chỉ chiếm 6% số đích nhưng nhận 7/34 cạnh thừa của LLM v3 (21%) và 4/26 cạnh thừa của E5 (15%). Chúng làm mất ít cạnh vàng: 4/6 cạnh
vàng vào chúng bị thiếu với LLM v3, cả bốn do X nằm ngoài cửa sổ.

**Giới hạn của cửa sổ là thiết kế, không phải lỗi neo.** Xét 136 cạnh vàng có hai đầu qua được cổng trạng thái dạy và Y có cửa sổ. Trong đó 49
cạnh (36%) có tên X không nằm trong cửa sổ định nghĩa của Y:
- 12 cạnh có tên X trong chunk neo hoặc chunk dạy của Y nhưng ngoài cửa sổ, tức cửa sổ quá hẹp hoặc lệch chỗ;
- các cạnh còn lại không có tên X ở gần Y. Đây là tiên quyết ngầm, giáo trình không nói ra cạnh định nghĩa.

E5 chỉ lấy được 8/49 cạnh loại này, nhờ bắc cầu qua cạnh khác. Đây đúng là phần mà E7 (ứng viên không nguyên văn) nhắm tới, với trần là 49 cạnh.

### 3.3 Danh tính

Bảng dưới đếm số lần gộp của danh tính, số nhóm gộp chạm khái niệm vàng, và số lần gộp sai làm mất cạnh vàng.

| | doc-1 | xstk | doc-4 |
|---|---:|---:|---:|
| nút bị gộp | 11 | 5 | 4 |
| nhóm chạm khái niệm vàng | 5 | 3 | 2 |
| gộp sai làm cạnh vàng thành tự nối | 1 ("Tọa độ") | 2 ("Độ tin cậy"; "Xác định kích thước mẫu trong ước lượng trung bình") | 0 |

Một cạnh vàng giữa hai khái niệm bị gộp nghĩa là người gán coi chúng là hai khái niệm khác nhau, có quan hệ tiên quyết với nhau, nên đó là gộp
sai. Số cặp đáng gộp mà bị bỏ sót thì bộ vàng này không đo được.

**Vì sao danh tính tách khỏi A4.** Về bản chất, danh tính cũng là gộp thực thể, cùng việc với A4. Nó chạy muộn hơn vì cần ba thứ chưa có lúc chạy
A4:
- câu neo, vì tiêu chí R8b đòi hai khái niệm cùng ngoại diên;
- trạng thái dạy, để chọn đại diện là khái niệm được dạy sớm nhất;
- vector mô tả của A6, để đề cử ứng viên.

Nếu làm bản không LLM, có thể dời bước tìm neo lên ngay sau A5 rồi gộp hai khâu làm một.

### 3.4 Chi phí

Bảng dưới là chi của từng khâu trên doc-4 trọn cuốn (616 khái niệm), đọc từ nhật ký phán đã ghi, theo giá trong mã (0,25 USD mỗi triệu token vào,
1,50 USD mỗi triệu token ra).

| khâu | lời gọi | token vào | token ra | USD |
|---|---:|---:|---:|---:|
| provenance | 89 | 279.209 | 11.074 | 0,086 |
| C8 (neo, trạng thái dạy) | 618 | 1.141.338 | 77.522 | 0,402 |
| danh tính (phán và xác minh) | 907 | 694.063 | 64.075 | 0,270 |
| **cộng ba khâu** | **1.614** | | | **0,758** |
| để so: pass chính | | | | 2,206 |
| để so: pass phụ LLM v3 | | | | 45,916 (thành 0 với pass phụ ML) |

## 4. Trả lời câu hỏi

**Ba khâu này quan trọng.**
- Chúng chặn 36% số cạnh vàng bị thiếu.
- Neo quyết định văn bản mà cả hai pass được đọc. Năm câu neo đáng ngờ, chỉ 6% số đích, đã gây 15–21% số cạnh thừa.

**Nhưng số liệu không cho thấy LLM là chỗ yếu của ba khâu.**
- LLM chọn câu neo đúng khoảng 94%.
- Cạnh mất do trạng thái dạy đến từ nhãn vai trò của A2 cộng một luật của C8.
- Danh tính gộp sai ít.

Vì vậy lý do bỏ LLM ở ba khâu là phạm vi và chi phí:
- seminar đòi Pha A không LLM;
- đích dài hạn của đồ án là chỉ giữ LLM ở A3 và A8 pass chính;
- ba khâu tốn khoảng 0,76 USD và 1.600 lời gọi mỗi cuốn cỡ doc-4.

Bản không LLM phải **không kém hơn** bản LLM trên các số ở trên.

Nếu chủ dự án duyệt lập kế hoạch, thứ tự đề xuất như sau:
1. **Sửa chuỗi A2 → C8 trước (vé 05).** Đây là lợi chất lượng lớn nhất, gồm nhận đúng "Cách giải" là nội dung và để C8 xét cả khái niệm có căn cứ
   ngoài nội dung. Việc này độc lập với chuyện có LLM hay không. Đo lại bằng chính script này và trên vàng T-01.
2. **Danh tính không LLM**, rủi ro thấp nhất. Dùng luật dè dặt (chuẩn hoá, viết tắt, ký hiệu ↔ chữ) và không gộp khi không chắc, vì lỗi đo được
   là gộp sai chứ không phải gộp thiếu. Cân nhắc gộp chung với A4 sau khi dời neo lên sớm.
3. **Trạng thái dạy không LLM**, làm cùng vai trò vùng A2, vì A2 cũng gọi LLM và là gốc lỗi.
4. **Neo không LLM sau cùng**, rủi ro cao nhất.
   - Trước hết cần một bộ vàng neo do người duyệt; 84 câu Claude đã đọc dùng làm hạt giống.
   - Cổng: độ đúng không thấp hơn bản LLM, và E4 của cả hai pass không giảm.

Dữ liệu học có sẵn: nhật ký phán LLM của C8 và danh tính trên 16 cuốn D-01 (đã chạy tới danh tính) và các tài liệu phát triển, dùng làm nhãn bạc
để chưng cất như cách làm với pass phụ.

## 5. Giới hạn

- Ba tài liệu, mỗi tài liệu một chương vàng, 172 cạnh. Mất mát do trạng thái dạy dồn gần hết vào một cuốn. Cần xác nhận trên vàng T-01.
- Phép phán câu neo là của Claude, chưa phải vàng người.
- Mỗi cạnh chỉ nhận một nguyên nhân, theo thứ tự ở mục 1. Một cạnh có thể có nhiều nguyên nhân cùng lúc.
- "Tên X trong cửa sổ" khớp theo ranh giới từ (underthesea), như ứng viên E5. Khớp như kênh exact thì số có thể lệch nhẹ.
- Số cặp đáng gộp mà bị bỏ sót chưa đo được.

## 6. Chạy lại

```
tmp/venv-ml/Scripts/python.exe scripts/pass-phu-ml/quy_loi_thuong_nguon.py --tach-tu
```

Script đọc payload A10 đã lưu trong `tmp/pass-phu-ml/e4/<hệ>/` (sinh bằng `phat_lai_e4.py` hoặc `lap_canh.py`). Đầu ra:
- `tmp/pass-phu-ml/ket-qua/quy-loi-tach-tu.json`;
- bảng chi tiết có tên khái niệm ở `tmp/pass-phu-ml/quy-loi/`.

Chạy khoảng 20 giây.
