# 04 — Bộ tách câu toàn cầu

**What to build:** Bộ tách câu thôi chỉ biết tiếng Việt. Nó nhận dấu kết câu của mọi chữ viết chính, không đòi
khoảng trắng ở nơi chữ viết không dùng khoảng trắng, và không cắt bừa tại các viết tắt thông dụng.

Và nó **thôi mang tên một ngôn ngữ**, vì nó phục vụ mọi tài liệu.

## Hiện trạng đo được

```
CJK    khối 800 token · tách được   1 câu · ra 1 chunk 800 token   (vượt trần 56%)
Hindi  khối 961 token · tách được   1 câu · ra 1 chunk 960 token   (vượt trần 87%)
EN     khối 641 token · tách  240 câu · nhưng cắt sai tại 'Dr.' và 'Mr.'
```

Hai lỗi ngược chiều nhau. Với chữ viết không phải Latin, bộ tách là **no-op**: các dấu kết câu của những chữ
viết đó vô hình với biểu thức hiện tại, và phần lớn chúng vốn không dùng khoảng trắng giữa câu — mà biểu thức
lại **đòi có khoảng trắng ngay sau** dấu. Kết quả là một câu duy nhất bao trọn khối, nên khối quá dài không bao
giờ được cắt.

Với chữ Latin không phải tiếng Việt thì ngược lại — cắt **quá tay**, vì danh sách viết tắt chỉ có năm mục tiếng
Việt.

## Ba thay đổi

**Lớp dấu kết câu** mở rộng theo Unicode: ngoài dấu chấm, chấm than, chấm hỏi hiện có, thêm ít nhất dấu chấm
lửng, dấu chấm ngang của chữ Hán, dạng toàn rộng của chấm than và chấm hỏi, dấu danda của chữ Devanagari, dấu
chấm hỏi và dấu chấm của chữ Ả Rập, dấu kết câu của chữ Khmer.

**Yêu cầu khoảng trắng phía sau** chỉ áp cho dấu thuộc chữ viết có dùng khoảng trắng. Với dấu thuộc chữ viết
không dùng khoảng trắng, ranh giới nằm ngay sau dấu.

**Danh sách viết tắt** trở thành **dữ liệu**, không còn viết cứng trong biểu thức: một bộ dùng chung cho chữ
Latin, cộng các bộ theo ngôn ngữ. Bộ tiếng Việt hiện có chuyển nguyên vẹn vào bộ theo ngôn ngữ.

## Không thêm phụ thuộc

Đã cân nhắc và loại thư viện tách câu ngoài: bộ phổ biến nhất **không hỗ trợ tiếng Việt** và sẽ rơi về luật
tiếng Anh, làm hỏng đúng ngôn ngữ duy nhất đang chạy đúng. Bộ tách hiện tại đã là một biểu thức tất định; làm
nó biết nhiều chữ viết hơn là mở rộng thứ đang có, không phải thay bằng một tầng mới khó gỡ lỗi.

## Bảng ca kiểm — lấy từ phép đo thật, bản hiện tại trượt phần lớn

| Đầu vào | Hiện tại | Mong muốn |
|---|---|---|
| `TS. An đo 3.14 đơn vị. PGS. Bình nói "đồng ý!" Câu cuối?` | 3 câu ✅ | **vẫn 3 câu** |
| `Dr. Smith met Mr. Jones. They agreed.` | **4 câu** ❌ | 2 câu |
| `Use a model, e.g. logistic regression. Then evaluate.` | **3 câu** ❌ | 2 câu |
| `See Goodfellow et al. 2016 for details. It is standard.` | **3 câu** ❌ | 2 câu |
| `As shown in Fig. 3 the loss drops. We then stop.` | **3 câu** ❌ | 2 câu |
| `这是第一句。这是第二句。第三句。` | **1 câu** ❌ | 3 câu |
| `これは最初の文です。これは二番目です。` | **1 câu** ❌ | 2 câu |
| `यह पहला वाक्य है। यह दूसरा है।` | **1 câu** ❌ | 2 câu |
| `هذه الجملة الأولى؟ وهذه الثانية.` | **1 câu** ❌ | 2 câu |
| `テスト！次の文？終わり。` | **1 câu** ❌ | 3 câu |

**Dòng đầu là ca hồi quy.** Nó đang đúng và không được phép hỏng — đó là ngôn ngữ duy nhất hiện chạy tốt.

**Blocked by:** Không — bắt đầu ngay. Hoàn toàn độc lập với nhánh bảng.

**Status:** completed — 2026-08-21

- [x] Bộ tách câu không còn mang tên một ngôn ngữ
- [x] Lớp dấu kết câu mở rộng theo Unicode như mô tả trên
- [x] Ranh giới không đòi khoảng trắng phía sau với dấu thuộc chữ viết không dùng khoảng trắng
- [x] Danh sách viết tắt là **dữ liệu**: một bộ chung cho chữ Latin, cộng các bộ theo ngôn ngữ
- [x] Thêm một mục viết tắt **không** phải sửa biểu thức chính quy
- [x] Cơ chế che tạm cho số thập phân được giữ nguyên
- [x] **Không thêm phụ thuộc nào**
- [x] Có test cho **cả mười** ca ở bảng trên
- [x] Ca tiếng Việt là **test hồi quy**, phải xanh trước và sau
- [x] Vị trí ký tự trả về vẫn trỏ vào chuỗi **gốc**, không phải chuỗi đã che tạm
- [x] Có test: chuỗi không có dấu kết câu nào ⇒ trả về đúng một ranh giới bao trọn chuỗi
- [x] Tăng phiên bản thuật toán **không** cần thiết ở ticket này — ticket `01` đã bump; nếu bạn thấy cần bump 
      tiếp thì **dừng và báo**, vì nó có nghĩa là hành vi đổi ngoài dự kiến
