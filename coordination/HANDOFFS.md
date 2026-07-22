# Handoffs

Nhật ký append-only, mục mới đặt ngay dưới phần hướng dẫn này.

## TASK-20260722-009 — 2026-07-22T14:29:27Z — Codex / GPT-5

- **Trạng thái:** DONE
- **Mục tiêu:** Lưu raw snapshot theo content hash để pipeline idempotent và có thể tái xử lý.
- **Đã thay đổi:** `agents/scraper/raw_store.py`, `agents/scraper/__init__.py`, `tests/unit/test_raw_store.py`, `README.md`, `coordination/**`.
- **Hành vi/API/schema:** `RawSnapshotStore.save()` ghi JSON một lần bằng exclusive create; `load()` chống path traversal và xác minh schema/source/hash.
- **Kiểm tra:** Ruff lint/format đạt; mypy strict đạt; pytest 25 passed.
- **Blocker/rủi ro:** Local filesystem store phù hợp MVP một máy; khi chạy nhiều worker cần object storage hoặc database-backed locking.
- **Việc tiếp theo:** Gemini thực hiện `TASK-20260722-008`; sau đó nối fetch → snapshot → extract thành pipeline command.

---

## TASK-20260722-007 — 2026-07-22T14:27:09Z — Codex / GPT-5

- **Trạng thái:** DONE
- **Mục tiêu:** Đưa dự án lên repository GitHub do người dùng cung cấp.
- **Đã thay đổi:** Khởi tạo remote `origin` và tracking branch `main`.
- **Hành vi/API/schema:** Không đổi mã nguồn.
- **Kiểm tra:** Push commit `d090c2a` thành công tới `hai-dep-try/HACKATHON_DATA`.
- **Blocker/rủi ro:** Không có.
- **Việc tiếp theo:** Codex làm `TASK-20260722-009`; Gemini có thể làm song song `TASK-20260722-008`.

---

## TASK-20260722-006 — 2026-07-22T14:23:48Z — Codex / GPT-5

- **Trạng thái:** DONE
- **Mục tiêu:** Dùng bài VnExpress về FPT FutureTech Talents làm source thật đầu tiên.
- **Đã thay đổi:** `config/sources.json`, `agents/extractor/core.py`, `tests/unit/test_extractor.py`, `scripts/smoke_source.py`, `README.md`, `coordination/**`.
- **Hành vi/API/schema:** Thêm source VnExpress đã bật; extractor nhận diện talent program từ bằng chứng, đối tượng sinh viên và link đăng ký; smoke script in UTF-8 và không lưu raw HTML.
- **Kiểm tra:** Smoke test mạng thật thành công; Ruff lint/format đạt; mypy strict đạt; pytest 21 passed.
- **Blocker/rủi ro:** Deadline, ngành học/công nghệ và scholarship value trong bài chưa được parse; source hiện là một discovery URL cụ thể, chưa phải crawler chuyên mục.
- **Việc tiếp theo:** `TASK-20260722-007` chờ URL Git remote để push dự án.

---

## TASK-20260722-005 — 2026-07-22T14:17:08Z — Codex / GPT-5

- **Trạng thái:** DONE
- **Mục tiêu:** Tạo HTTP scraper an toàn để nối source registry với extractor Gemini.
- **Đã thay đổi:** `agents/scraper/http_scraper.py`, `agents/scraper/source_registry.py`, `agents/scraper/__init__.py`, `tests/unit/test_http_scraper.py`, `README.md`; format `agents/extractor/core.py` và `tests/unit/test_extractor.py`.
- **Hành vi/API/schema:** `HttpScraper` chỉ crawl source `enabled`, kiểm allowlist, fail closed khi không đọc được `robots.txt`, áp dụng rate limit theo source và chỉ tạo `RawDocument` cho phản hồi HTML 2xx.
- **Kiểm tra:** Ruff lint/format đạt; mypy strict đạt; pytest 20 passed.
- **Blocker/rủi ro:** Chưa có nguồn thực được bật và chưa có persistence của raw snapshot; không gọi mạng thật trong unit test.
- **Việc tiếp theo:** Chọn nguồn công khai đầu tiên, xác minh robots/terms, tạo fixture local và cấu hình source đã bật.

---

## TASK-20260722-004 — 2026-07-22T14:14:00Z — Gemini / 3.1 Pro (Low)

- **Trạng thái:** DONE
- **Mục tiêu:** Xây extractor deterministic-first chuyển HTML trong `RawDocument` thành `OpportunityRecord`, chưa gọi LLM thật.
- **Đã thay đổi:** `agents/extractor/core.py`, `agents/prompts/opportunity_extraction.md`, `tests/unit/test_extractor.py`, `coordination/BOARD.md`, `coordination/HANDOFFS.md`.
- **Hành vi/API/schema:** Viết hàm `extract_opportunity` trích xuất thông tin qua `JSON-LD`, OpenGraph và HTML fallback, đảm bảo không đoán bừa (`unknown over guessing`).
- **Kiểm tra:** `ruff check . --fix`, `mypy agents backend`, `pytest` đều passed thành công.
- **Blocker/rủi ro:** Fallback hiện tại chỉ lấy mỗi title từ thẻ H1/title, chưa lấy location, deadline. Cần có thêm logic để gọi LLM extraction dựa trên prompt ở file markdown.
- **Việc tiếp theo:** Tích hợp gọi LLM extraction API cho các trường còn lại.

---

## TASK-20260722-003 — 2026-07-22T14:11:10Z — Codex / GPT-5

- **Trạng thái:** DONE
- **Mục tiêu:** Tạo source registry an toàn và data contract cho dữ liệu scraper bàn giao sang extractor.
- **Đã thay đổi:** `agents/common/models.py`, `agents/common/__init__.py`, `agents/scraper/__init__.py`, `agents/scraper/source_registry.py`, `config/sources.example.json`, `tests/unit/test_source_registry.py`, `README.md`, `coordination/**`.
- **Hành vi/API/schema:** Thêm immutable `RawDocument.from_text(...)`; registry kiểm tra source ID, domain allowlist, URL discovery, rate/concurrency và bắt buộc `respect_robots_txt=True`.
- **Kiểm tra:** Ruff đạt; mypy strict đạt; pytest 11 passed.
- **Blocker/rủi ro:** Registry hiện chỉ có nguồn minh họa bị tắt; chưa xác minh và bật nguồn thật.
- **Việc tiếp theo:** Gemini nhận `TASK-20260722-004` theo `coordination/GEMINI_TASK_004.md`.

---

## TASK-20260722-002 — 2026-07-22T14:07:54Z — Codex / GPT-5

- **Trạng thái:** DONE
- **Mục tiêu:** Mở rộng hệ thống từ hackathon sang các cơ hội phù hợp sinh viên/người chưa có kinh nghiệm.
- **Đã thay đổi:** `AGENTS.md`, `README.md`, `docs/architecture.md`, `agents/common/models.py`, `agents/common/__init__.py`, `tests/unit/test_models.py`, `coordination/BOARD.md`, `coordination/HANDOFFS.md`, `coordination/DECISIONS.md`.
- **Hành vi/API/schema:** Thêm `OpportunityRecord`, `OpportunityType`, `ExperienceLevel` và các trường eligibility/compensation; giữ `HackathonRecord` làm alias tương thích.
- **Kiểm tra:** Ruff lint/format đạt; mypy strict đạt; pytest 6 passed.
- **Blocker/rủi ro:** Chưa có scraper nguồn career page; classification cần bám nội dung nguồn, không suy diễn internship đồng nghĩa no-experience.
- **Việc tiếp theo:** Thiết kế source registry và scraper đầu tiên cho career page/talent program.

---

## TASK-20260722-001 — 2026-07-22T14:01:43Z — Codex / GPT-5

- **Trạng thái:** DONE
- **Mục tiêu:** Tạo nơi trao đổi chung để nhiều AI không làm lại, xóa hoặc xung đột công việc.
- **Đã thay đổi:** `AGENTS.md`, `README.md`, `coordination/README.md`, `coordination/BOARD.md`, `coordination/HANDOFFS.md`, `coordination/DECISIONS.md`.
- **Quyết định:** Dùng Markdown trong repository làm nguồn trạng thái trung lập giữa các công cụ; ownership theo file/task.
- **Kiểm tra:** Rà soát liên kết và cấu trúc tài liệu.
- **Việc tiếp theo:** Mọi AI phải nhận task trên board trước khi sửa code và ghi handoff khi kết thúc phiên.

---

## Mẫu bàn giao

```markdown
## TASK-ID — YYYY-MM-DDTHH:MM:SSZ — Owner / Model

- **Trạng thái:** REVIEW | DONE | BLOCKED
- **Mục tiêu:** ...
- **Đã thay đổi:** ...
- **Hành vi/API/schema:** ...
- **Kiểm tra:** lệnh và kết quả
- **Blocker/rủi ro:** ...
- **Việc tiếp theo:** ...
```
