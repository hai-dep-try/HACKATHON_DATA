# Work board

Đọc `coordination/README.md` trước khi cập nhật. Giữ một dòng cho mỗi task; không tái sử dụng task ID.

| ID | Status | Owner | Updated (UTC) | Scope / files | Depends on | Summary |
|---|---|---|---|---|---|---|
| TASK-20260722-010 | DONE | Codex / GPT-5 | 2026-07-22T14:34:14Z | `agents/extractor/**`, `tests/unit/test_extractor.py`, `coordination/**` | TASK-20260722-008 | Review và tích hợp extractor Gemini theo nguyên tắc evidence-only |
| TASK-20260722-009 | DONE | Codex / GPT-5 | 2026-07-22T14:29:27Z | `agents/scraper/raw_store.py`, `agents/scraper/__init__.py`, `tests/unit/test_raw_store.py`, `README.md`, `coordination/**` | TASK-20260722-006 | Lưu raw snapshot theo content hash, idempotent và có thể load lại |
| TASK-20260722-008 | DONE | Gemini / 3.1 Pro (Low) | 2026-07-22T14:32:00Z | `agents/extractor/**`, `tests/unit/test_extractor.py`, `agents/prompts/**`, `coordination/BOARD.md`, `coordination/HANDOFFS.md` | TASK-20260722-006 | Parse deadline, technologies, eligibility và compensation; xem `coordination/GEMINI_TASK_008.md` |
| TASK-20260722-007 | DONE | Codex / GPT-5 | 2026-07-22T14:27:09Z | Git repository / remote | TASK-20260722-006 | Push nhánh main lên GitHub `hai-dep-try/HACKATHON_DATA` |
| TASK-20260722-006 | DONE | Codex / GPT-5 | 2026-07-22T14:23:48Z | `config/sources.json`, `agents/extractor/**`, `tests/unit/test_extractor.py`, `scripts/smoke_source.py`, `README.md`, `coordination/**` | TASK-20260722-005 | Tích hợp và smoke-test nguồn VnExpress thực tế |
| TASK-20260722-005 | DONE | Codex / GPT-5 | 2026-07-22T14:17:08Z | `agents/scraper/**`, `tests/unit/test_http_scraper.py`, `README.md`, `agents/extractor/core.py`, `tests/unit/test_extractor.py`, `coordination/**` | TASK-20260722-004 | Xây HTTP scraper tôn trọng robots/allowlist và chuẩn hóa format extractor |
| TASK-20260722-004 | DONE | Gemini | 2026-07-22T14:14:00Z | `agents/extractor/**`, `agents/prompts/**`, `tests/unit/test_extractor.py` | TASK-20260722-003 | Xây extractor deterministic-first từ RawDocument sang OpportunityRecord; xem `coordination/GEMINI_TASK_004.md` |
| TASK-20260722-003 | DONE | Codex / GPT-5 | 2026-07-22T14:11:10Z | `agents/common/models.py`, `agents/common/__init__.py`, `agents/scraper/**`, `config/sources.example.json`, `tests/unit/test_source_registry.py`, `README.md`, `coordination/**` | TASK-20260722-002 | Tạo source registry và RawDocument contract |
| TASK-20260722-002 | DONE | Codex / GPT-5 | 2026-07-22T14:07:54Z | `AGENTS.md`, `README.md`, `docs/architecture.md`, `agents/common/**`, `tests/unit/test_models.py`, `coordination/**` | TASK-20260722-001 | Mở rộng domain sang cơ hội sinh viên và chương trình entry-level |
| TASK-20260722-001 | DONE | Codex / GPT-5 | 2026-07-22T14:01:43Z | `AGENTS.md`, `README.md`, `coordination/**` | — | Thiết lập giao thức phối hợp nhiều AI |

## Trạng thái hợp lệ

`TODO` · `IN_PROGRESS` · `BLOCKED` · `REVIEW` · `DONE`

## Mẫu dòng mới

```text
| TASK-YYYYMMDD-NNN | TODO | Unassigned | YYYY-MM-DDTHH:MM:SSZ | `path/**` | — | Mô tả ngắn |
```
