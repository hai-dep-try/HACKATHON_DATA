# Architecture Decision Log

Chỉ ghi quyết định ảnh hưởng nhiều module, data contract, dependency, hạ tầng hoặc cách phối hợp. Không xóa quyết định cũ; khi thay đổi, tạo ADR mới và đánh dấu ADR cũ là `SUPERSEDED`.

## ADR-001 — Phối hợp nhiều AI bằng artifact trong repository

- **Ngày:** 2026-07-22
- **Trạng thái:** ACCEPTED
- **Bối cảnh:** Dự án có thể được chỉnh sửa bằng Codex, Gemini và các model khác với lịch sử chat tách biệt.
- **Quyết định:** Dùng `coordination/BOARD.md`, `HANDOFFS.md` và `DECISIONS.md` làm nguồn trạng thái chung. Mỗi task khai báo owner và phạm vi file trước khi sửa.
- **Hệ quả:** Có thêm thao tác cập nhật Markdown, đổi lại các công cụ có thể tiếp tục công việc mà không cần truy cập lịch sử chat của nhau và giảm nguy cơ ghi đè.

## ADR-002 — PostgreSQL + pgvector là search stack mặc định của MVP

- **Ngày:** 2026-07-22
- **Trạng thái:** ACCEPTED
- **Bối cảnh:** Chạy đồng thời PostgreSQL, Meilisearch và Qdrant làm tăng độ phức tạp vận hành sớm.
- **Quyết định:** PostgreSQL + pgvector là nguồn dữ liệu và search stack mặc định. Meilisearch/Qdrant chỉ bật qua profile mở rộng khi có yêu cầu hoặc benchmark.
- **Hệ quả:** MVP nhẹ hơn; index mở rộng vẫn có thể bổ sung mà không đổi data contract chính.

## ADR-003 — Tổng quát hóa dữ liệu thành student opportunity

- **Ngày:** 2026-07-22
- **Trạng thái:** ACCEPTED
- **Bối cảnh:** Ngoài hackathon, sản phẩm cần tìm talent program, internship và các cơ hội phù hợp sinh viên chưa có kinh nghiệm.
- **Quyết định:** `OpportunityRecord` là data contract chính, với loại cơ hội, mức kinh nghiệm, eligibility và compensation. Giữ `HackathonRecord` làm type alias tương thích cho code ban đầu.
- **Hệ quả:** Scraper/index/API mới phải xử lý nhiều loại cơ hội; Repo Analyzer trở thành bước làm giàu có điều kiện thay vì bắt buộc cho mọi record.

---

## Mẫu quyết định

```markdown
## ADR-NNN — Tiêu đề

- **Ngày:** YYYY-MM-DD
- **Trạng thái:** PROPOSED | ACCEPTED | SUPERSEDED
- **Bối cảnh:** ...
- **Quyết định:** ...
- **Hệ quả:** ...
```
