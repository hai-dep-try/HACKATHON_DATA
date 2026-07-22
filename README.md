# hackathon_data

Pipeline multi-agent để thu thập, chuẩn hóa, làm giàu và tìm kiếm cơ hội dành cho sinh viên/người chưa có kinh nghiệm: hackathon, internship, talent/trainee program, fellowship, scholarship, competition và bootcamp.

## Kiến trúc

```text
Devpost / YBOX / career pages / website công khai
                 │
                 ▼
             Scraper ───────► data/raw
                 │
                 ▼
             Extractor ─────► OpportunityRecord
                 │
                 ▼
          Repo Analyzer ────► metadata GitHub
                 │
                 ▼
              Indexer ──────► PostgreSQL / search
                 │
                 ▼
             FastAPI / UI
```

PostgreSQL là nguồn dữ liệu chính. MVP dùng PostgreSQL và `pgvector`; Meilisearch và Qdrant là profile mở rộng, không bắt buộc để bắt đầu.

Mỗi cơ hội được phân loại theo `opportunity_type` và `experience_level`, đồng thời lưu đối tượng phù hợp, ngành học, yêu cầu ứng tuyển, hình thức trả lương/trợ cấp và URL nộp đơn nếu nguồn cung cấp.

## Quickstart trên PowerShell

Yêu cầu: Python 3.11–3.13. Docker chỉ cần khi chạy hạ tầng local.

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -U pip
python -m pip install -e ".[dev]"
Copy-Item .env.example .env
pytest
uvicorn backend.main:app --reload
```

Nếu cần scraper dùng trình duyệt:

```powershell
python -m playwright install chromium
```

Khởi động PostgreSQL/pgvector:

```powershell
docker compose -f docker/docker-compose.yml up -d postgres
```

## Quickstart trên Bash

```bash
python3.11 -m venv .venv
source .venv/bin/activate
python -m pip install -U pip
python -m pip install -e '.[dev]'
cp .env.example .env
pytest
uvicorn backend.main:app --reload
```

## Cấu trúc

```text
agents/              Các agent và model dùng chung
backend/             FastAPI
data/raw/            Snapshot nguồn, không commit nội dung thực tế
data/processed/      Dữ liệu chuẩn hóa, không commit nội dung thực tế
data/fixtures/       Fixture nhỏ, đã làm sạch, dùng cho test
docker/              Hạ tầng local
docs/                Kiến trúc và quyết định kỹ thuật
scripts/             Entry point cho pipeline định kỳ
tests/unit/           Test không gọi dịch vụ ngoài
tests/integration/    Test cần dịch vụ ngoài, chạy tách biệt
coordination/         Bảng task, quyết định và bàn giao giữa các AI
config/               Source registry và cấu hình không chứa secret
```

Source mới phải được khai báo theo mẫu [sources.example.json](config/sources.example.json). Registry mặc định tắt các nguồn ví dụ; chỉ bật một nguồn thật sau khi kiểm tra URL, điều khoản, `robots.txt` và parser fixture.

`HttpScraper` chỉ lấy HTML từ source đã bật, URL nằm trong allowlist và được `robots.txt` cho phép. Nó trả `RawDocument`; extractor sau đó chuyển tiếp thành `OpportunityRecord`.

`RawSnapshotStore` lưu snapshot theo `data/raw/<source_id>/<content_hash>.json`. Cùng một nội dung chỉ được tạo một lần; khi đọc lại, schema, source ID và hash đều được xác minh.

Smoke-test một source thật mà không lưu raw HTML:

```powershell
.\.venv\Scripts\python.exe scripts\smoke_source.py --source vnexpress-education
```

Chạy pipeline MVP đầy đủ cho tất cả source đang bật:

```powershell
.\.venv\Scripts\python.exe scripts\run_pipeline.py
```

Lệnh này tải discovery page, lưu raw snapshot idempotent và trả JSON `OpportunityRecord`. Có thể giới hạn một source bằng `--source <source-id>`.

## Làm việc với nhiều AI

Codex, Gemini, Claude hoặc người phát triển đều dùng cùng một quy trình trong
[coordination/README.md](coordination/README.md). Trước khi sửa code, hãy nhận task trên
`coordination/BOARD.md` và khai báo các file dự kiến chạm tới. Khi kết thúc phiên, cập nhật trạng
thái và thêm một mục bàn giao để AI tiếp theo không làm lại hoặc ghi đè công việc.

## Kiểm tra chất lượng

```powershell
ruff check .
ruff format --check .
mypy agents backend
pytest
```

Xem [docs/architecture.md](docs/architecture.md) để biết data flow, idempotency và ranh giới trách nhiệm.
