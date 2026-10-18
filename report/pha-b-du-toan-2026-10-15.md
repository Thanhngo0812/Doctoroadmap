# Dự toán Pha B trên sáu A10 ghim — 2026-10-15

Dry-run trên sáu đồ thị A10 ghim trong `DEVELOPMENT_DOCS`, không đọc `.env`, không gọi mạng/API/embedding, không tạo artifact naming và không ghi artifact sản phẩm. Runtime chạy `mode=gemini`, `allow_spend=False`; mọi use case dùng Phase B store trong bộ nhớ. Usage thực tế sau lượt chạy: 0; quiz attempt: 0; chi thực tế: **$0.00**. Mỗi đồ thị có 159/159 tên module hợp lệ.

Mỗi tài liệu được ước lượng hai bài giảng, một quiz ở module đầu có khái niệm học được, một trợ lý với trần 5 lượt, một tài liệu cho khái niệm đầu, một concept index và một naming StagePlan trên toàn bộ module.

| Tài liệu | A10 | Module có tên | Names StagePlan | Bài giảng ×2 | Quiz | Trợ lý tối đa 5 lượt | Tài liệu | Concept index | Tổng dự toán |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| doc-1 | v37 | 39/39 | $0.044577 | $0.007115 | $0.064161 | $0.009886 | $0.005572 | $0.003221 | $0.134532 |
| nhap-mon-ml | v37 | 15/15 | $0.017145 | $0.006706 | $0.051586 | $0.009873 | $0.005953 | $0.001251 | $0.092513 |
| naive-bayes | v37 | 5/5 | $0.005715 | $0.006572 | $0.050011 | $0.009885 | $0.005314 | $0.000777 | $0.078274 |
| doc-6 | v8 | 4/4 | $0.004572 | $0.006493 | $0.049887 | $0.009879 | $0.005059 | $0.000378 | $0.076268 |
| xstk-ch3-1 | v46 | 9/9 | $0.010287 | $0.007366 | $0.067461 | $0.009898 | $0.006017 | $0.001436 | $0.102464 |
| doc-4 | v12 | 87/87 | $0.099441 | $0.007189 | $0.070273 | $0.009892 | $0.006429 | $0.010840 | $0.204064 |

Chi phí theo loại: names $0.181737; lecture $0.041441; quiz $0.353379; assistant_upper_bound $0.059312; document $0.034343; concept_index $0.017903. **Tổng upper bound $0.688115**.

Quiz dùng context thực tế dựng bởi `_context`/generation prompt, 4 lượt tối đa mỗi concept chưa cache (2 generate + 2 blind verifier), thêm biên một output generation tối đa cho input repair và mỗi verifier; output caps lấy từ `BSettings` (1200/400). Tính tiền theo `PRICING_USD_PER_MILLION` dùng chung. Đây là bound theo caps, không phải dự báo giá trị trung bình.

Assistant lấy dry-run 1-call làm nền, nhân số lượt tối đa (5) và chặn ở `assistant_max_usd` cho từng câu hỏi. Naming lấy nguyên `NameModulesB.plan()`/`StagePlan` trên 159 module; không gọi generation hoặc lưu graph. Concept index giữ ước tính bảo thủ input-token tại mức giá chung.

## Graph ghim và hash

| Tài liệu | Graph | Stage | Source hash | Config hash | Payload SHA-256 |
|---|---:|---|---|---|---|
| doc-1 | v37 | stages | `6615daf62a01f7f445170d9d9ed261a9c9cda8a2d5a91f69f97cb74ad9e194e0` | `83964a953784891936ac1f857623e563a419a813b3d840d904a6b13631ac5d29` | `3571ffabd45a7d41a0b584f8676491f9521a771cda160b81307a3812128f9839` |
| nhap-mon-ml | v37 | stages | `f4d5936c5d804ae60e78251f26684fc9d14538f83b7a640102b5837bbf8de114` | `3717282b2daf32055e5f5509919f6545a737585a1ce25f6ca1b755212287c34a` | `09171bc61a22d76fe7ef052e986f8c4e955e05aeeca90e236ed81e01741f6589` |
| naive-bayes | v37 | stages | `7ec87ad7c90547fbdf1633ebd2b210b4ae821c85a94a9a5db2e2b972e13964bf` | `e7a0fabea0ef598e7ca430184a1d8664bd0bb8a190643c9bbd94ecb8a10a34b6` | `e586191d71c6bae8e06cef68508ca89b8f1ba544c089a2b1e4643b1f2878f289` |
| doc-6 | v8 | stages | `5f8204a92925a010adaa0f8139cbb7ed2c0880791a09d0d5618c1edc1b7f4fc6` | `86ea0539915d09ba0f250757a77f16b63b22215c447c1d651ad332529ef3ea7e` | `875566a71d8e49eb35b6402ad948c0b2d527d261ea3118a791692a572ded6fd7` |
| xstk-ch3-1 | v46 | stages | `b8172a250ac6722353957afaa7edda50c290c39821eb08bdd3990edda55e22c7` | `4c3a7a96ac2e986a20a3cff6d862822a475ab559cb281ce5ad44770c35299b2f` | `578d21d056f08ee4651f1f74c5389a3de92a079f5ce6c62825ceec84cccc0e5c` |
| doc-4 | v12 | stages | `5d3c34876635662842e96de72646b7ccea6a696f6203f92952b6316cb0a5cb16` | `889a21f0d4a7cbb7c501c1150bbb33f979ef5102c63e3f9880f457dee905d740` | `64ca1d8c4fd4821d8161135ca0e97e5c7a61a15d9c1a24a3eedf39ba9a251fdd` |

## Phạm vi và thời gian

| Tài liệu | Bài giảng ms ×2 | Names ms | Quiz concept/call/ms | Assistant calls/ms | Document ms | Index concept/token/ms |
|---|---|---:|---|---|---:|---|
| doc-1 | 20, 23 | 329 | 8/32/36 | 5/19 | 32 | 218/12885/104 |
| nhap-mon-ml | 1, 1 | 85 | 7/28/4 | 5/11 | 6 | 75/5003/20 |
| naive-bayes | 1, 1 | 36 | 7/28/2 | 5/3 | 2 | 33/3107/7 |
| doc-6 | 1, 1 | 28 | 7/28/2 | 5/3 | 2 | 28/1514/7 |
| xstk-ch3-1 | 6, 5 | 249 | 8/32/17 | 5/7 | 13 | 72/5743/36 |
| doc-4 | 31, 26 | 2186 | 7/28/294 | 5/330 | 79 | 489/43358/544 |

Các số ms là thời gian dựng context/plans tại máy này, không phải latency mạng. Names StagePlan ước số gọi cho toàn bộ 159 tên. Quiz, assistant, document, lecture là sáu lượt mỗi loại theo phạm vi trên.

Chi tiết calls, token bounds, report, hashes và thời gian nằm trong [`tmp/phaseb-dry-run-plan.json`](../tmp/phaseb-dry-run-plan.json). **Tổng estimate $0.688115 vượt ngưỡng $0.50. Không có paid calls trong lượt dry-run này.**
