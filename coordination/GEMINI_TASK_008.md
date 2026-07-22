# Task brief cho Gemini — TASK-20260722-008

## Mục tiêu

Nâng cấp deterministic extractor để lấy thêm deadline, technologies, eligibility và compensation từ dữ liệu có bằng chứng rõ ràng, đặc biệt cho bài VnExpress/FPT FutureTech Talents đã cấu hình.

## Trước khi làm

1. Đọc `AGENTS.md`, `coordination/README.md` và handoff mới nhất.
2. Chuyển `TASK-20260722-008` sang `IN_PROGRESS`, ghi model và thời gian UTC.
3. Không sửa `agents/scraper/**`, `agents/common/models.py`, `config/**`, `scripts/**` hoặc test ngoài phạm vi.

## Phạm vi được phép

- `agents/extractor/**`
- `agents/prompts/**`
- `tests/unit/test_extractor.py`
- Dòng task của mình trong `coordination/BOARD.md`
- Handoff của mình trong `coordination/HANDOFFS.md`

## Yêu cầu

- Ưu tiên JSON-LD trước, sau đó mới phân tích text có bằng chứng.
- Parse `registration_deadline` thành datetime timezone-aware khi ngày/tháng/năm đủ rõ. Nếu bài chỉ ghi ngày/tháng, chỉ dùng năm từ metadata xuất bản khi quan hệ thời gian không mơ hồ và phải có test.
- Chuẩn hóa technology được nhắc rõ: `AI`, `Cloud`, `Cyber Security`, `Quantum`.
- Lưu câu eligibility ngắn vào `eligibility_text`; không suy ra ngành/đối tượng ngoài nội dung.
- Lưu mô tả học bổng/trợ cấp vào `compensation_text`; `paid` chỉ đặt khi nguồn nói rõ đó là lương/trợ cấp cho người tham gia.
- Không gọi LLM hoặc network trong unit test.
- Không hard-code riêng URL VnExpress hay tên FPT trong logic; dùng rule dựa trên schema/evidence.

## Acceptance criteria

- Fixture tổng hợp tương đương bài FPT parse được deadline năm 2026, bốn technologies và eligibility sinh viên năm 3–5.
- Trường thiếu hoặc ngày mơ hồ vẫn là `None`.
- Không làm hỏng các test extractor hiện tại.
- Ruff lint/format, mypy strict và pytest đều đạt.
- Ghi rõ giới hạn parser trong handoff.
