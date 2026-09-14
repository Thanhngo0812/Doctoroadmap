# 05 — Mô tả media: ảnh vào prompt đa phương thức, bảng đọc từ nội dung

**What to build:** **Mọi node media đều có mô tả** — 11 hình và 60 bảng hiện không chú thích đều được
mô tả. Section có hình thì **ảnh đi kèm ngay trong lời gọi trích**, cùng văn bản; mô hình vừa nhìn vừa
đọc, và trích được cả khái niệm **hình dạy mà văn bản không nói**.

## Hình và bảng đi hai đường, vì chúng khác nhau về bản chất

| | `figure` | `table` |
|---|---|---|
| Nội dung trong `text` chunk | chỉ dấu `[figure]` | **toàn bộ markdown của bảng** |
| Mô hình lúc trích đọc được? | **Không** — phải đính ảnh | **Có — đang đọc rồi** |
| Có chú thích | 8/19 | **4/64** |
| Cần đa phương thức? | có, 11 hình | **không** |
| `caption_source` khi tự sinh | `generated_multimodal` | `generated_from_content` |

**Bảng không tốn thêm lời gọi nào** — mô hình đã thấy toàn bộ markdown khi trích section, chỉ cần hỏi
thêm một trường trong đúng lượt đang chạy. Đừng dựng lượt riêng cho bảng.

## Vì sao không tách thành bước mô tả riêng

Đường tách hai bước — mô tả ảnh mù rồi kiểm sau — thua ở ba chỗ:

- **Neo ngữ cảnh xảy ra trong lúc mô tả**, không phải kiểm sau. Không cho ảo giác sinh ra, thay vì sinh
  ra rồi lọc.
- Bước mô tả mù **không biết khái niệm nào đáng chú ý**, nên không moi được nội dung hình dạy mà văn bản
  bỏ qua. Bài giáo dục đa phương thức 08/2026 ghi nhận đúng hiện tượng này.
- Chi phí gần bằng không: **chỉ 13/129 section (10%) mang ảnh**.

## Chốt chặn bắt buộc: chống neo ngược vào văn bản

Thấy cả chữ lẫn ảnh, mô hình dễ **chép lại ý văn bản rồi gọi đó là mô tả ảnh** — mô tả thành thừa,
không thêm gì. Prompt phải hỏi **cái nhìn thấy được**: *trục ghi gì, mấy đường, nhãn nào, hình dạng ra
sao*. **Không** hỏi *"hình này nói về gì"*.

**Ảnh có chú thích vẫn phải đưa vào ngữ cảnh** — chú thích làm `description`, nhưng ảnh vẫn có mặt vì nó
có thể dạy thứ chú thích không nói. 8/19 hình có chú thích, 11 không.

**Hệ quả:** mô hình trích phải là mô hình **đa phương thức**.

## Hai thứ mô hình giao ra, không phải một

Mô hình **đang nhìn ảnh** — vứt đi phán đoán của nó về việc hình minh hoạ **cái gì** là phí. Cùng một
lượt, nó giao hai thứ:

```
1. MÔ TẢ      — cái nhìn thấy được (bắt buộc, xem bất biến dưới)
2. XÁC NHẬN   — trong các thực thể của chunk này, hình minh hoạ NHỮNG cái nào?
                trả về TẬP CON, được phép rỗng
```

Cạnh vẫn do **ticket 04 sinh bằng đồng vị trí** — mô hình chỉ **xác nhận**, không tạo và không xoá.
Cạnh được xác nhận mang `confirmed: true`.

## Vì sao cần `confirmed`, và vì sao là tập con

**Người tiêu thụ cụ thể: `get_media_for_concept` ở pha B.** Không có nhãn thì người học hỏi về *"Mô
hình"* sẽ nhận về bức ảnh lưới mèo/chó — chỉ vì nó tình cờ nằm cùng chunk. Nhiễu ở đây không phải nhiễu
thống kê, nó là **ảnh sai hiện ra trước mặt người học**.

Đo trên ca thật: chunk `c_36332bd4` có 2 ảnh × 4 thực thể = **8 cạnh đồng vị trí**, có nghĩa chắc **2**.

**Tập con, không phải "nhiều nhất một".** Một hình hoàn toàn có thể minh hoạ hai khái niệm thật — ép
chọn một là bắt mô hình nói dối. Rỗng, một, hay ba đều hợp lệ.

**Tên là `confirmed` chứ không phải `primary`**: cái đang xảy ra là **xác nhận**, không phải xếp hạng.

**Không có đường nào để tầng này làm mất cạnh.** Xác nhận sai ⇒ thừa một nhãn. Bỏ sót ⇒ cạnh vẫn còn
nguyên nhờ sàn đồng vị trí. Cùng bất đối xứng đã dùng cho ngưỡng blocking ở 2a.

**Vì sao xác nhận ở đây chứ không để agent lọc lúc truy vấn:** lúc trích, mô hình **đang nhìn bức ảnh**;
lúc truy vấn, agent chỉ có chuỗi mô tả. Phán đoán này rẻ hơn và chính xác hơn khi còn nhìn thấy ảnh, và
chỉ trả tiền **một lần** thay vì mỗi lần hỏi.

Cạnh **xuyên chunk** — hình ở chương 3 minh hoạ khái niệm chương 7 — **hoãn tới sau merge**: khái niệm
phải canonical trước đã, nếu không sẽ nối vào một biến thể sắp bị gộp mất.

## Vị trí ref phải bơm tường minh — không trông chờ dấu `[figure]`

Đo trên corpus: **6/16 chunk chứa media không có dấu `[figure]` nào**. Lý do là hành vi đúng của B0 —
**ảnh có chú thích thì chú thích đứng thay chỗ dấu**:

```
ref 33ded2e2 @10248 -> trỏ vào "Hình 3: Ví dụ về…"   ← CÓ chú thích, không có dấu
ref faa71862 @10365 -> trỏ vào "[figure]"            ← KHÔNG chú thích
```

Nên prompt phải liệt kê **từng ref kèm vị trí ký tự và tình trạng chú thích**, không để mô hình tự dò
dấu trong văn bản.

## Bất biến: mọi node media phải có mô tả

Áp cho **cả `figure` lẫn `table`**. `caption_source: none` **không phải trạng thái bình thường** — nó
là **trạng thái hỏng**: mô hình từ chối, lỗi gọi, hoặc nội dung không đọc được. Phải đếm và báo, không
nuốt im lặng.

**Blocked by:** 03 — cần hình dạng hội thoại ba giai đoạn. 04 — cần ứng viên media và cạnh đồng vị trí
tồn tại để gắn mô tả và nhãn.

**Status:** done

- [x] Section mang ảnh ⇒ ảnh đính kèm trong lời gọi trích, cùng văn bản và tiêu đề tổ tiên
- [x] Prompt hỏi đặc điểm **nhìn thấy được**, không hỏi ý nghĩa
- [x] Ảnh có chú thích: `description` = chú thích, `caption_source: original`, nhưng ảnh **vẫn** vào ngữ cảnh
- [x] Ảnh không chú thích: `description` = mô tả sinh ra, `caption_source: generated_multimodal`
- [x] **Bảng** không chú thích: `description` = mô tả sinh **từ markdown đã có trong chunk**,
      `caption_source: generated_from_content` — **không** thêm lời gọi, **không** cần ảnh
- [x] **Bất biến: mọi node `figure` và `table` có `description` khác rỗng.** `caption_source: none` là
      **hỏng** — đếm riêng, báo ra, không im lặng
- [x] Prompt liệt kê **từng ref kèm vị trí ký tự và tình trạng chú thích** — không trông chờ mô hình
      tự dò dấu `[figure]` trong văn bản (6/16 chunk không có dấu nào)
- [x] Mô hình trả về **tập con** các thực thể mà media thật sự minh hoạ; cạnh tương ứng mang
      `confirmed: true`. Tập con **rỗng, một, hay nhiều** đều hợp lệ
- [x] Có test: mô hình xác nhận **hai** thực thể ⇒ **hai** cạnh `confirmed`, các cạnh khác vẫn còn
- [x] Có test: mô hình trả tập **rỗng** ⇒ mọi cạnh đồng vị trí **giữ nguyên**, không cạnh nào `confirmed`
- [x] Có test: mô hình xác nhận thực thể **không thuộc chunk này** ⇒ **từ chối nhãn**, cạnh không đổi
- [x] **Không có đường nào để bước này xoá hoặc tạo cạnh** — có test khẳng định số cạnh trước/sau bằng nhau
- [x] Có test: section không ảnh ⇒ lời gọi **không** mang phần ảnh, không phí token
- [x] Có test: section chỉ có bảng, không hình ⇒ **không** đi đường đa phương thức, mô tả vẫn sinh ra
- [x] Có test: chunk có media nhưng **0 thực thể** ⇒ vẫn có mô tả, không có cạnh, không có `confirmed`
- [x] Ghi vào thống kê: **tỉ lệ cạnh `illustrates`/`tabulates` được xác nhận** — quá thấp nghĩa là đồng
      vị trí đang sinh phần lớn là nhiễu, đáng nhìn
- [x] Trên bốn fixture: **11 hình** + **60 bảng** nhận mô tả sinh ra · **8 hình** + **4 bảng** giữ chú
      thích gốc · **0** node `caption_source: none`
- [x] Fixture hội thoại ghi lại cả phần ảnh để phát lại được, không cần gọi lại
