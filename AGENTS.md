# AGENTS.md — Quy tắc làm việc trong `hackathon_data`

## 1. Phạm vi dự án

Repository này xây dựng pipeline thu thập, chuẩn hóa, phân tích và tìm kiếm cơ hội cho sinh viên/người chưa có kinh nghiệm, gồm hackathon, internship, talent/trainee program, fellowship, scholarship, competition và bootcamp:

```text
Nguồn công khai → Scraper → Extractor → Repo Analyzer → Indexer → API/UI
```

- `agents/scraper/`: thu thập nội dung công khai và lưu raw snapshot.
- `agents/extractor/`: chuyển nội dung thô thành `OpportunityRecord`.
- `agents/repo_analyzer/`: làm giàu dữ liệu repository GitHub.
- `agents/indexer/`: đồng bộ dữ liệu sang PostgreSQL/search backend.
- `agents/common/`: model, cấu hình và tiện ích dùng chung.
- `backend/`: FastAPI; không đặt logic scraping trong route handler.
- `frontend/`: giao diện web.
- `data/`: dữ liệu local; chỉ fixture nhỏ, không nhạy cảm được phép commit.
- `tests/`: unit test và integration test.

## 2. Nguyên tắc dành cho coding agent

1. Trước khi sửa, đọc `coordination/README.md`, `coordination/BOARD.md`, `coordination/DECISIONS.md`, file liên quan và test hiện có.
2. Nhận việc trên `coordination/BOARD.md` và khai báo chính xác file/thư mục dự kiến sửa. Không bắt đầu nếu phạm vi đó đang do AI khác giữ.
3. Giữ thay đổi nhỏ, đúng phạm vi yêu cầu; không sửa hoặc xóa thay đổi của người dùng hay AI khác.
4. Không tự ý thay schema dữ liệu công khai, database migration hoặc thêm dependency lớn. Nếu cần, ghi đề xuất/decision trước.
5. Dùng `OpportunityRecord` trong `agents/common/models.py` làm data contract giữa các agent. `HackathonRecord` chỉ là alias tương thích cho code cũ.
6. Mọi thao tác ghi dữ liệu phải idempotent: ưu tiên upsert, canonical URL và `content_hash`.
7. Không hard-code secret. Dùng biến môi trường được mô tả trong `.env.example`.
8. Không commit `.env`, token, raw HTML thực tế, dữ liệu cá nhân hoặc database dump.
9. Chạy kiểm tra phù hợp trước khi hoàn tất: `ruff check .`, `mypy agents backend`, `pytest`.
10. Trước khi rời task, cập nhật trạng thái và ghi bàn giao vào `coordination/HANDOFFS.md`, kể cả khi task chưa hoàn tất.
11. Nếu không chạy được kiểm tra do thiếu công cụ/dịch vụ, nêu rõ kiểm tra nào chưa chạy và lý do.

## 3. Phối hợp nhiều AI

Các AI trao đổi qua thư mục `coordination/`; đây là nguồn trạng thái chung, không dựa vào lịch sử chat riêng của bất kỳ công cụ nào.

- Mỗi task có ID dạng `TASK-YYYYMMDD-NNN`, một owner và phạm vi file không chồng lấn.
- `coordination/BOARD.md` là trạng thái hiện tại: `TODO`, `IN_PROGRESS`, `BLOCKED`, `REVIEW`, `DONE`.
- `coordination/HANDOFFS.md` là nhật ký append-only. Không viết lại hoặc xóa bàn giao cũ.
- `coordination/DECISIONS.md` lưu quyết định kiến trúc ảnh hưởng từ hai module trở lên.
- Khi phát hiện sửa đổi ngoài phạm vi đã nhận, giữ nguyên và phối hợp qua board; không revert, reset hoặc format hàng loạt.
- Không giữ task `IN_PROGRESS` khi kết thúc phiên. Chuyển sang `REVIEW`, `DONE`, hoặc `BLOCKED` và ghi next step.
- Nếu hai task cần cùng một file, tách thứ tự thực hiện hoặc để một owner duy nhất tích hợp thay đổi.

## 4. Quy tắc thu thập dữ liệu

- Chỉ thu thập trang/API công khai; ưu tiên API, RSS hoặc feed chính thức.
- Tôn trọng điều khoản dịch vụ, `robots.txt`, rate limit và chính sách của từng nguồn.
- Không vượt CAPTCHA, đăng nhập, paywall hoặc cơ chế chống bot.
- Dùng timeout, retry có exponential backoff và giới hạn concurrency theo domain.
- Ghi `source_url`, `source_name`, `scraped_at`, `content_hash` và trạng thái lỗi.
- Parser phải thất bại có kiểm soát khi HTML thay đổi; không âm thầm tạo bản ghi sai.
- Test parser bằng fixture local. Unit test mặc định không gọi mạng, LLM hay GitHub API thật.

## 5. Quy ước dữ liệu

- Thời gian lưu theo UTC và phải có timezone; timezone hiển thị mặc định là `Asia/Ho_Chi_Minh`.
- Giá trị chưa xác định dùng `None`/`unknown`, không suy đoán.
- Phải phân biệt loại cơ hội (`opportunity_type`) với yêu cầu kinh nghiệm (`experience_level`); không mặc định mọi internship đều không yêu cầu kinh nghiệm.
- Chỉ đặt `paid=True/False` khi nguồn nói rõ; nếu không, giữ `None`.
- `priority_score` nằm trong `[0, 100]` và phản ánh mức độ đáng quan tâm.
- `extraction_confidence` nằm trong `[0, 1]` và phản ánh độ tin cậy của việc trích xuất; không trộn hai loại điểm.
- Mỗi payload có `schema_version`. Thay đổi breaking phải tăng major version và có migration.
- Raw snapshot là nguồn để tái xử lý; processed data có thể tái tạo từ raw data.

## 6. Priority score mặc định

Khi chưa có cấu hình riêng, tổng điểm 100 gồm:

- 30 điểm: phù hợp địa lý (Hà Nội, TP.HCM hoặc online).
- 25 điểm: còn hạn đăng ký và thời gian hợp lệ.
- 20 điểm: phù hợp ngành học, chủ đề hoặc công nghệ mục tiêu.
- 15 điểm: phù hợp người chưa có kinh nghiệm, có trợ cấp/giải thưởng, mentor hoặc cơ hội tuyển dụng.
- 10 điểm: độ tin cậy và độ đầy đủ của nguồn.

Extractor phải lưu các thành phần điểm để kết quả có thể giải thích được.

## 7. Definition of Done

Một thay đổi được coi là hoàn tất khi:

- Code đã format/lint và type-check trong phạm vi liên quan.
- Unit test mới bao phủ đường chạy chính và ít nhất một trường hợp thiếu/sai dữ liệu.
- Không chứa secret hoặc dữ liệu nhạy cảm.
- Tài liệu và `.env.example` được cập nhật nếu hành vi/cấu hình thay đổi.
- Với thay đổi database/index: có migration hoặc kế hoạch tương thích ngược rõ ràng.
- Board, decision và handoff đã được cập nhật nếu task có thay đổi material.

## 8. Lệnh phát triển chuẩn

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -U pip
python -m pip install -e ".[dev]"
python -m playwright install chromium
pytest
```

Xem `README.md` để biết quickstart đầy đủ và `docs/architecture.md` để biết kiến trúc hệ thống.
