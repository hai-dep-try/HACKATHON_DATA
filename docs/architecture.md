# Kiến trúc hệ thống

## Mục tiêu

Hệ thống tạo một tập dữ liệu cơ hội cho sinh viên/người mới bắt đầu có nguồn gốc rõ ràng, có thể tái xử lý và tìm kiếm bằng từ khóa hoặc ngữ nghĩa. Phạm vi gồm hackathon, internship, talent/trainee program, fellowship, scholarship, competition và bootcamp. Pipeline phải idempotent và tiếp tục hoạt động có kiểm soát khi một nguồn thay đổi cấu trúc.

## Thành phần

1. **Scraper** lấy nội dung công khai, canonicalize URL, tính `content_hash` và lưu raw snapshot.
2. **Extractor** tạo `OpportunityRecord`, chuẩn hóa loại cơ hội, yêu cầu kinh nghiệm, đối tượng, thời gian/địa điểm và ghi confidence.
3. **Repo Analyzer** chỉ chạy khi cơ hội có repository GitHub (thường là hackathon/competition), thu thập metadata bằng token read-only.
4. **Indexer** upsert bản ghi vào PostgreSQL. Full-text/vector index là dữ liệu dẫn xuất và có thể dựng lại.
5. **API** truy vấn dữ liệu; route handler gọi service/repository thay vì gọi scraper trực tiếp.

## Data flow và idempotency

```text
source URL
   │ canonicalize
   ▼
raw snapshot + SHA-256 content_hash
   │ changed?
   ├─ no  → cập nhật last_seen_at
   └─ yes → extract → validate → enrich → upsert → index
```

Khóa tự nhiên ưu tiên là canonical URL. Khi một sự kiện có nhiều nguồn, một bước entity resolution riêng sẽ liên kết các source record; không gộp chỉ dựa trên tiêu đề.

## Nguồn theo loại cơ hội

- **Hackathon/competition:** Devpost, trang cuộc thi và website trường/CLB công khai.
- **Internship/trainee/talent program:** career page chính thức của doanh nghiệp và cổng tuyển dụng công khai.
- **Fellowship/scholarship/bootcamp:** website của đơn vị tổ chức, trường, quỹ hoặc cộng đồng chuyên môn.

Nguồn chính thức được ưu tiên hơn trang tổng hợp. Mỗi record phải giữ URL nguồn và URL ứng tuyển riêng nếu có.

## Phân loại eligibility

`opportunity_type` mô tả chương trình; `experience_level` mô tả kinh nghiệm mong đợi. Extractor không được suy ra `no_experience` chỉ từ từ “internship”. Các trường `target_audiences`, `eligible_majors`, `eligibility_text`, `paid` và `compensation_text` phải bám sát nội dung nguồn; thông tin không rõ được giữ ở trạng thái chưa xác định.

## Lưu trữ và tìm kiếm

- **PostgreSQL + pgvector (MVP):** dữ liệu chuẩn, filter, full-text cơ bản và embedding.
- **Meilisearch (tùy chọn):** typo tolerance và trải nghiệm full-text nâng cao.
- **Qdrant (tùy chọn):** vector workload lớn hoặc cần vector filtering chuyên biệt.

Chỉ bật dịch vụ tùy chọn khi có benchmark hoặc yêu cầu sản phẩm rõ ràng.

## Xử lý lỗi

- Network error: retry hữu hạn với exponential backoff và jitter.
- HTTP 429: tôn trọng `Retry-After`; giảm concurrency.
- Parser error: lưu trạng thái và raw snapshot để debug; không xuất record không hợp lệ.
- LLM output sai schema: validate bằng Pydantic, retry hữu hạn, sau đó chuyển dead-letter queue.
- Index failure: dữ liệu PostgreSQL vẫn là nguồn chuẩn; job index có thể chạy lại.

## Bảo mật và tuân thủ

Secret chỉ đi qua environment/secret manager. Log phải che token và dữ liệu cá nhân. Không vượt cơ chế truy cập, CAPTCHA hoặc thu thập nội dung không công khai. Retention của raw data cần được cấu hình theo nguồn.

## Quan sát hệ thống

Mỗi lần chạy nên có `run_id` và structured log. Chỉ số tối thiểu gồm số URL đã xem, snapshot mới, record hợp lệ, lỗi theo nguồn, latency, token LLM và GitHub rate-limit còn lại.
