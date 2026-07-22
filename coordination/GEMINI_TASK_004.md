# Task brief cho Gemini — TASK-20260722-004

## Mục tiêu

Xây extractor deterministic-first chuyển HTML trong `RawDocument` thành `OpportunityRecord`, chưa gọi LLM thật. Ưu tiên dữ liệu có cấu trúc và không suy diễn điều kiện ứng tuyển.

## Trước khi làm

1. Đọc `AGENTS.md` và `coordination/README.md`.
2. Chuyển `TASK-20260722-004` trên board sang `IN_PROGRESS`, cập nhật model và thời gian UTC.
3. Không sửa file thuộc task khác. Không sửa `agents/common/models.py`, `agents/scraper/**`, `pyproject.toml` hoặc test hiện có.

## Phạm vi file được phép

- `agents/extractor/**`
- `agents/prompts/**`
- `tests/unit/test_extractor.py`
- Cập nhật trạng thái của chính task trong `coordination/BOARD.md`
- Thêm handoff của chính task vào `coordination/HANDOFFS.md`

## Interface đã có

- Input: `agents.common.models.RawDocument`
- Source metadata: `agents.scraper.source_registry.SourceDefinition`
- Output: `agents.common.models.OpportunityRecord`

Extractor nên nhận cả `RawDocument` và `SourceDefinition`, đồng thời từ chối khi `document.source_id != source.id`.

## Thứ tự extraction

1. JSON-LD `JobPosting` hoặc `Event` nếu hợp lệ.
2. OpenGraph/meta tags.
3. HTML heading/text fallback tối thiểu.

Chỉ map dữ liệu có bằng chứng trong document. Không mặc định internship là `no_experience`, không đoán `paid`, deadline hoặc location. `content_hash` và `scraped_at` của output phải lấy nguyên từ input.

## Acceptance criteria

- Parse được fixture HTML có JSON-LD `JobPosting` thành internship.
- Parse được fixture HTML có JSON-LD `Event` thành hackathon/competition.
- Fallback lấy được title nhưng để trường không rõ ở `unknown`/`None`.
- JSON-LD hỏng không làm crash nếu vẫn có title fallback.
- Mismatch source ID bị từ chối rõ ràng.
- Không gọi network hoặc LLM trong unit test.
- `ruff check .`, `mypy agents backend`, `pytest` đều đạt.
- Ghi handoff với file đã đổi, test và giới hạn còn lại.

## Prompt chuẩn bị cho giai đoạn sau

Có thể tạo `agents/prompts/opportunity_extraction.md` mô tả schema và nguyên tắc “unknown over guessing”, nhưng không tích hợp API/model provider trong task này.
