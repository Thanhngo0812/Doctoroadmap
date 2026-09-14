# 03 — Lắp cạnh, nguồn gốc và chỉ số của quan hệ 2a

**What to build:** Quan hệ hợp lệ thành cạnh node–node trong artifact canonical. Mỗi cạnh ghi rõ nguồn: A3, 2a, hay
cả hai. Chỉ số cho biết kênh mới đem thêm được gì so với A3.

## Vì sao cần `origins`

Hiện nay, cạnh 2a trùng bộ ba với cạnh A3 bị gộp vào cạnh A3 mà không để lại dấu vết. Khi kiểu cạnh mở, trùng bộ ba sẽ
thường xuyên hơn: cả A3 lẫn 2a cùng nói `uses`. 2b cần biết một đề xuất có hai nguồn độc lập cùng nêu, vì như vậy mạnh
hơn một nguồn.

**Blocked by:** 02 — Schema `relations` và kiểm từng quan hệ

**Status:** done

- [x] **Map về node.** Chỉ map quan hệ về node sau khi đã chốt nhóm → node, tức là sau lượt vá và chặn bắc cầu. Hai đầu
      rơi vào cùng node thì bỏ, đếm vào `relation_self_removed`.
- [x] **Gộp trùng.** Quan hệ trùng bộ ba (source, target, `edge_type`) từ nhiều cụm và lượt vá gộp làm một: hợp
      `chunk_ids`, giữ `reason` đầu tiên theo thứ tự xử lý (các cụm theo thứ tự, rồi tới lượt vá). Kết quả phải tất định.
- [x] **Nguồn gốc.** Mọi cạnh trong artifact có `origins`, là danh sách đã sắp xếp, lấy trong {`"2a"`, `"a3"`}.
  - Cạnh 2a trùng bộ ba với cạnh A3 thì thành một cạnh, `origins: ["2a", "a3"]`. Hợp `chunk_ids`, giữ nguyên các trường
    của A3 (`evidence`, `source_refs`, `confirmed`), và thêm `reason` của 2a.
  - Cạnh chỉ có từ 2a mang `proposal: true`, `confirmed: false`, như `subtype_of` hiện nay.
- [x] **F75.** `find_subtype_conflicts` chỉ nhận cạnh 2a có `edge_type == "subtype_of"`. Test: cạnh 2a `uses` trùng cặp
      với cạnh A3 `uses` không bị ghi là xung đột subtype.
- [x] **Config** thêm `"relation_rule": "open-v1"`. Đổi cách lắp cạnh về sau thì tăng số phiên bản, để cache không trả
      artifact cũ.
- [x] **Chỉ số** (test khẳng định chỉ số khớp payload):

  | Chỉ số | Nghĩa |
  |---|---|
  | `relation_edges` | số cạnh 2a sau khi gộp trùng |
  | `relation_types` | đếm cạnh 2a theo kiểu |
  | `relation_same_as_a3` | cạnh 2a trùng bộ ba với cạnh A3 |
  | `relation_other_type_than_a3` | cặp đã có cạnh A3, nhưng khác kiểu |
  | `relation_new_pair` | cặp chưa có cạnh A3 nào, xét cả hai chiều |
  | `relation_self_removed` | quan hệ bị bỏ vì hai đầu thành một node |

  Giữ `subtype_conflicts_a3`. Trường `edge_types` của payload đếm cả kiểu từ 2a.
- [x] `scripts/run_a4_arm.py` in thêm các chỉ số trên.
- [x] **Test seam** với trọng tài giả:
  - quan hệ `uses` giữa hai node thành cạnh `uses` với `origins: ["2a"]`;
  - quan hệ trùng bộ ba A3 thành một cạnh, `origins: ["2a", "a3"]`;
  - quan hệ giữa hai nhóm mà lượt vá sau đó gộp thì bị bỏ và được đếm;
  - hai cụm cùng đề xuất một bộ ba thì chỉ ra một cạnh.
- [x] Toàn bộ test xanh, chặn mạng.

Arm v3 sinh 73 cạnh 2a: 5 trùng bộ ba A3, 15 cùng cặp khác kiểu, 53 cặp mới; loại 2 self-edge sau map và 14 quan hệ sai ở validator.
