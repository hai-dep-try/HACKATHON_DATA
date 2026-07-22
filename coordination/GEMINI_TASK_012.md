# Task brief cho Gemini — TASK-20260722-012

## Mục tiêu

Mở rộng FastAPI bằng endpoint liệt kê và lọc `OpportunityRecord`, dùng repository được inject để sau này đổi sang PostgreSQL mà không sửa route.

## Trước khi làm

1. Đọc `AGENTS.md`, `coordination/README.md` và handoff mới nhất.
2. Chuyển `TASK-20260722-012` sang `IN_PROGRESS`, ghi model và thời gian UTC.
3. Không sửa `agents/**`, `scripts/**`, `config/**`, dependency hoặc test ngoài phạm vi.

## Phạm vi được phép

- `backend/**`
- `tests/unit/test_api.py`
- Dòng task của mình trong `coordination/BOARD.md`
- Handoff của mình trong `coordination/HANDOFFS.md`

## Yêu cầu

- Tạo repository protocol/abstraction và implementation in-memory dùng cho test/dev.
- Inject repository qua FastAPI dependency; không dùng global mutable list trực tiếp trong route.
- `GET /opportunities` hỗ trợ filter tùy chọn: `opportunity_type`, `experience_level`, `location_type`.
- `GET /opportunities/{content_hash}` trả 404 nếu không có.
- Response dùng schema `OpportunityRecord`; không tạo schema trùng trong backend.
- Validate query enum bằng FastAPI/Pydantic.
- Giữ endpoint `/health` hiện tại.
- Không gọi database hoặc network trong unit test.

## Acceptance criteria

- Test danh sách rỗng, danh sách có dữ liệu, từng filter, lookup thành công và 404.
- Repository có thể thay thế trong test qua dependency override.
- Ruff lint/format, mypy strict và pytest đều đạt.
- Ghi handoff và không commit file ngoài scope.
