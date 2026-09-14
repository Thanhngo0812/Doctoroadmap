# 02 — Schema `relations` và kiểm từng quan hệ

**What to build:** Đầu ra phân hoạch đổi trường `subtype_edges` thành `relations`, mỗi quan hệ mang `edge_type` tự do.
Code kiểm từng quan hệ và chỉ loại quan hệ sai, không làm mất phân hoạch hợp lệ (nguyên tắc F61).

## Vì sao loại riêng từng quan hệ

Một quan hệ sai không được làm mất quyết định gộp đúng trong cùng đầu ra. Bài học F61: bản đầu bỏ cả cụm vì một cạnh
`subtype_of` sai, và mất cụm Naive Bayes.

**Blocked by:** 01 — Spec và ADR 0007

**Status:** done

- [x] `PARTITION_SCHEMA` (`application/canonical_prompt.py`): `relations` là mảng
      `{source, target, edge_type, chunk_ids, reason}`, cả năm trường đều bắt buộc. Bỏ `subtype_edges`.
- [x] `validate_partition` (`domain/canonical_decisions.py`) đòi đúng các khoá `{"nodes", "relations", "deferred"}`, và
      mỗi quan hệ đúng năm khoá. Sai khoá tính là lỗi định dạng như hiện nay (thử lại một lần, rồi hoãn cả cụm).
- [x] `split_relation_edges(value, source)` thay `split_subtype_edges`. Nó loại riêng một quan hệ, ghi lỗi cụ thể kèm
      tập chunk hợp lệ, khi rơi vào một trong các trường hợp:
  - `source` hoặc `target` không thuộc cụm, hoặc là nhóm `deferred`;
  - `source` và `target` cùng một node trong phân hoạch;
  - `chunk_ids` rỗng, hoặc có chunk ngoài nguồn của hai nhóm;
  - `reason` rỗng;
  - `edge_type` rỗng, là `requires`, đồng nghĩa với `requires` (dùng `validate_llm_edge_type`), hoặc là kiểu dành cho
    media (`illustrates`, `tabulates`).
- [x] `edge_type` được chuẩn hoá đúng như A4 đang làm với cạnh A3: casefold, gộp khoảng trắng (`domain/canonical.py`,
      `remap_edges`). Tách thành một hàm dùng chung, không viết lại.
- [x] Hai quan hệ trùng hệt (cùng source, target, kiểu) trong một đầu ra thì giữ một, hợp `chunk_ids`.
- [x] Nhật ký ghi `relation_rejected`, chỉ số là `relation_rejected`. Bỏ tên cũ `subtype_rejected`.
- [x] **Test.** Mỗi test phải hỏng khi bỏ đúng guard của nó; nộp danh sách đột biến đã thử:
  - quan hệ hợp lệ được giữ, kiểu đã chuẩn hoá (`Uses` thành `uses`);
  - mỗi trường hợp loại ở trên có một test;
  - loại hết mọi quan hệ thì phân hoạch vẫn được áp;
  - trọng tài giả trả quan hệ `requires` thì bị loại, và artifact không có cạnh `requires` từ 2a. Test này giữ ý của
    test cũ ở ticket A4/A5 07;
  - quan hệ tới nhóm `deferred` thì bị loại.
- [x] Sửa các test cũ đang dùng `subtype_edges` (test pipeline A4 và test `canonical_decisions`), giữ nguyên ý kiểm.
- [x] Toàn bộ test xanh, chặn mạng.

## Bằng chứng đột biến

- Bỏ guard đầu mút/deferred/cùng node: đúng 4 ca `unknown-source`, `unknown-target`, `deferred-target`, `same-node` đỏ.
- Bỏ guard nguồn chunk: đúng 2 ca `empty-chunks`, `foreign-chunk` đỏ.
- Bỏ guard lý do: ca `empty-reason` đỏ.
- Bỏ `validate_llm_edge_type`: hai ca `empty-type`, `requires-alias` đỏ.
- Bỏ guard loại dành riêng: ba ca `requires`, `illustrates`, `tabulates` đỏ.
- Bỏ chuẩn hoá và bỏ khử trùng: test hợp `chunk_ids`/giữ lý do đầu tiên đỏ ở cả hai đột biến.
- Sau khi khôi phục code thật: 20 test validator và seam `requires` đều xanh.
