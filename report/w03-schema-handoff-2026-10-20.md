# W-03 — Checkpoint schema cho nhóm lõi

**Trạng thái:** schema đạt kiểm local; toàn vé W-03 đang triển khai.

- Migration mới duy nhất: `w03_0004`, `down_revision=w02_0003`. Lõi nối `w06_0005` sau revision này.
- Thêm `email_token`: UUID/FK cascade, purpose verify_email/reset_password, token_hash BYTEA unique và dài đúng 32 byte, email lúc gửi, created/expires/used, index account-purpose-created và expires. Không đổi bảng khoá học/Pha B.
- **18 test schema/migration/auth-store đạt**, PostgreSQL bắt buộc, không skip. [XML](w03-evidence/schema-checkpoint.xml). Kiểm DB rỗng, nâng W-02 giữ dữ liệu account, metadata/schema, một head; kiểm W-01 và W-02 ở revision cũ vẫn được giữ.
- Lệnh: `.venv/Scripts/python.exe scripts/w05_run_tests.py src/web/backend/tests/test_w03_schema.py src/web/backend/tests/test_w03_migration.py src/web/backend/tests/test_auth_store.py src/web/backend/tests/test_database.py --basetemp=.tmp/w03-schema-checkpoint -q --junitxml=.tmp/w03-schema-checkpoint.xml`.
- Service/API/UI và nghiệm thu đầu-cuối chưa hoàn tất tại checkpoint này. Không coi checkpoint là toàn vé đạt.
