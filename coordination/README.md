# Quy trình phối hợp giữa người và nhiều AI

Thư mục này là kênh trao đổi bền vững giữa Codex, Gemini, Claude và người phát triển. Nội dung ở đây được ưu tiên hơn trạng thái được nhớ riêng trong từng cuộc chat.

## Khi bắt đầu một phiên

1. Đọc `AGENTS.md`, `BOARD.md`, `DECISIONS.md` và các handoff mới nhất.
2. Kiểm tra thay đổi hiện có bằng `git status --short` nếu repository đã dùng Git.
3. Tìm task phù hợp hoặc tạo một dòng mới trong `BOARD.md` với ID duy nhất.
4. Chuyển task sang `IN_PROGRESS`, ghi owner/model, thời gian UTC và các file dự kiến sửa.
5. Nếu file đã nằm trong task `IN_PROGRESS` khác, không sửa file đó. Ghi dependency hoặc yêu cầu bàn giao.

## Trong khi làm

- Chỉ sửa các file đã khai báo. Nếu cần mở rộng phạm vi, cập nhật board trước.
- Không chạy format toàn repository khi đang có nhiều task song song.
- Không revert, reset, xóa hoặc ghi đè thay đổi chưa rõ chủ sở hữu.
- Quyết định ảnh hưởng nhiều module phải được ghi vào `DECISIONS.md`.
- Có thể thêm ghi chú ngắn vào task để AI khác biết blocker hoặc interface đang thay đổi.

## Khi kết thúc phiên

1. Chạy kiểm tra phù hợp và ghi kết quả.
2. Cập nhật trạng thái thành:
   - `REVIEW`: code đã xong, cần người/AI khác review.
   - `DONE`: hoàn tất và đã xác minh.
   - `BLOCKED`: chưa thể tiếp tục; phải ghi blocker và next step.
3. Thêm mục mới ở đầu `HANDOFFS.md`; không sửa hoặc xóa mục cũ.
4. Liệt kê file đã đổi, hành vi đã hoàn thành, kiểm tra đã chạy và việc còn lại.

## Quy tắc ownership

- Ownership là theo task và phạm vi file, không phải toàn bộ repository.
- Một file chỉ có một owner đang hoạt động tại một thời điểm.
- Task `IN_PROGRESS` quá 24 giờ mà không có handoff được xem là stale, nhưng không tự ý chiếm lại. Chuyển nó sang `BLOCKED` với ghi chú trước khi nhận tiếp.
- File chung như `pyproject.toml`, schema, migration và data contract nên do một integration task riêng sở hữu.

## ID và thời gian

- Task ID: `TASK-YYYYMMDD-NNN`, ví dụ `TASK-20260722-001`.
- Decision ID: `ADR-NNN`, ví dụ `ADR-001`.
- Thời gian: ISO 8601 UTC, ví dụ `2026-07-22T08:30:00Z`.
- Owner: tên người/công cụ và model nếu biết, ví dụ `Codex / GPT-5` hoặc `Gemini / 2.5 Pro`.

## Xử lý xung đột

Khi phát hiện hai bên đã sửa cùng file:

1. Dừng sửa file xung đột.
2. Giữ cả hai thay đổi; không tự động chọn một phía.
3. Tạo task tích hợp với một owner duy nhất.
4. Ghi rõ ý định của từng phía trong handoff.
5. Owner tích hợp chạy lại test và ghi kết quả cuối cùng.
