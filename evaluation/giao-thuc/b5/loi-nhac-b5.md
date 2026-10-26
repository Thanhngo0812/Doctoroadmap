# Lời nhắc B5 "LLM đọc thẳng" — bản b5-1

**Trạng thái:** bản nháp 2026-10-26. Bản này sẽ thử trên tập phát triển ngày 01/11 (vé DG-07). Bản chốt ghi vào giao thức đăng ký trước (DG-18) trước ngày
07/11; sau đó không sửa.

**Mục đích:** B5 là cách làm đơn giản mà hội đồng sẽ hỏi: đưa sách cho cùng mô hình (`gemini-3.1-flash-lite`) rồi yêu cầu trả luôn khái niệm, quan hệ và
lộ trình. Lời nhắc phải **công bằng**:
- định nghĩa khái niệm và quan hệ tiên quyết giống hướng dẫn gán G3/G4;
- có lược đồ đầu ra;
- yêu cầu trích câu nguyên văn.

B5 không được có các bước mà chỉ luồng 10 bước mới có: chọn câu neo từ danh sách có mã, gộp trên cả cuốn bằng phán LLM, kiểm định đồ thị.

**Đầu vào:** văn bản sách lấy bằng pypdfium2, mỗi trang mở đầu bằng dòng `[Trang N]`, với N là số trang PDF.
- B5a: cả cuốn trong một lời gọi.
- B5b: một chương mỗi lời gọi. Từ lời gọi thứ hai, khối `{KHAI_NIEM_TRUOC}` liệt kê tên các khái niệm đã trả ở những chương trước.

**Biến thể nhiễu K = 5:** cùng nội dung, khác định dạng. Gồm:
- (1) bản gốc dưới đây;
- (2) đổi thứ tự hai khối "Định nghĩa" và "Đầu ra";
- (3) mục đánh số thay cho gạch đầu dòng;
- (4) tiêu đề khối viết hoa;
- (5) bỏ dòng trống giữa các khối.

Bộ chọn biến thể theo seed (DG-07).

## Lời nhắc hệ thống

```text
Bạn đọc một giáo trình tiếng Việt và lập lộ trình học cho người mới. Chỉ dựa vào chính văn bản được cho. Không dùng kiến thức ngoài sách.

Định nghĩa:
- Khái niệm là một đơn vị kiến thức có tên mà người học phải nắm: khái niệm, thuật ngữ được định nghĩa, định lý hay định luật có tên, phương pháp hay quy trình có tên, công thức có tên, cách phân loại có tên. Không tính ví dụ cụ thể, bài tập, ký hiệu đứng một mình.
- Chỉ lấy khái niệm mà sách định nghĩa hoặc giải thích. Khái niệm sách chỉ nhắc qua thì bỏ.
- Quan hệ tiên quyết X -> Y nghĩa là muốn hiểu Y phải hiểu X trước, và sách dùng X khi định nghĩa, giải thích hay lập luận về Y. Chỉ ghi quan hệ trực tiếp. Khái niệm khung chung của cả môn không phải tiên quyết nếu sách không dùng nội dung của nó để giải thích Y.

Đầu ra: một đối tượng JSON đúng lược đồ, không thêm chữ nào khác.
- "khai_niem": mỗi phần tử có "ten" (tên sách dùng nhiều nhất), "ten_khac" (tên khác mà sách dùng), "trang" (số trong dòng [Trang N] nơi có câu định nghĩa), "cau_dinh_nghia" (chép nguyên văn từ sách, không sửa chữ nào).
- "quan_he": mỗi phần tử có "nguon", "dich" (đúng chuỗi "ten" trong "khai_niem"), "trang", "cau_bang_chung" (chép nguyên văn câu trong sách cho thấy quan hệ).
- "lo_trinh": "day_hoc" là danh sách tên khái niệm theo thứ tự nên học; "module" là danh sách nhóm liên tiếp, mỗi nhóm có "ten" ngắn và "khai_niem".
Mọi câu trích phải là chuỗi có thật trong văn bản được cho.
```

## Lời nhắc người dùng

```text
{KHAI_NIEM_TRUOC}
Văn bản giáo trình:
{VAN_BAN}
```

`{KHAI_NIEM_TRUOC}` để rỗng ở B5a và ở chương đầu của B5b. Từ chương thứ hai của B5b, nó có dạng
`Các khái niệm đã có ở chương trước (dùng đúng tên này nếu nhắc lại): <tên 1>; <tên 2>; …`.

## Lược đồ đầu ra

Lược đồ dưới gửi qua `responseJsonSchema`. Adapter tự lọc khoá theo transport (SA-61).

```json
{
  "type": "object",
  "properties": {
    "khai_niem": {"type": "array", "items": {"type": "object", "properties": {
      "ten": {"type": "string"}, "ten_khac": {"type": "array", "items": {"type": "string"}},
      "trang": {"type": "integer"}, "cau_dinh_nghia": {"type": "string"}},
      "required": ["ten", "ten_khac", "trang", "cau_dinh_nghia"]}},
    "quan_he": {"type": "array", "items": {"type": "object", "properties": {
      "nguon": {"type": "string"}, "dich": {"type": "string"}, "trang": {"type": "integer"},
      "cau_bang_chung": {"type": "string"}},
      "required": ["nguon", "dich", "trang", "cau_bang_chung"]}},
    "lo_trinh": {"type": "object", "properties": {
      "day_hoc": {"type": "array", "items": {"type": "string"}},
      "module": {"type": "array", "items": {"type": "object", "properties": {
        "ten": {"type": "string"}, "khai_niem": {"type": "array", "items": {"type": "string"}}},
        "required": ["ten", "khai_niem"]}}},
      "required": ["day_hoc", "module"]}
  },
  "required": ["khai_niem", "quan_he", "lo_trinh"]
}
```

## Ghi chú cho bộ chuyển đổi (DG-07)

Bộ chuyển đổi xử lý đầu ra B5 theo bốn luật:
- `trang_thai` của mọi khái niệm B5 ghi là `defined_here`, vì B5 chỉ trả khái niệm được dạy. Câu neo là `cau_dinh_nghia`.
- Quan hệ có `nguon` hay `dich` không nằm trong `khai_niem` thì vẫn giữ, nhưng đếm vào chỉ số "quan hệ trỏ khái niệm lạ". Không vá.
- B5b hợp nhất khái niệm giữa các chương **chỉ** khi tên trùng sau chuẩn hoá.
- Đầu ra bị cắt vì chạm trần token thì ghi cờ, không gọi lại.
