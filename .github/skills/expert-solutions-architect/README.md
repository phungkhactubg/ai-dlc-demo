# Expert Solutions Architect Skill

Skill chuyên biệt dành cho việc nghiên cứu công nghệ, thiết kế kiến trúc phần mềm và lập kế hoạch triển khai cho các hệ thống backend sử dụng Go.

## 🚀 Tổng quan

Role này đóng vai trò là một **Expert Solutions Architect, Technical Lead, và Product Strategist** với mục tiêu tạo ra các bản thiết kế (blueprints) chất lượng cao, giúp các Developer (hoặc các AI Agent khác) có thể thực thi chính xác và hiệu quả.

## ✨ Chức năng chính

1.  **Nghiên cứu (Research)**: Phân tích công nghệ, so sánh các giải pháp và đề xuất phương án tối ưu.
2.  **Thiết kế (Design)**: Tạo cấu trúc hệ thống dựa trên Clean Architecture, DDD, Event-Driven, hoặc Hexagonal Architecture.
3.  **Lập kế hoạch (Plan)**: Tạo Implementation Plan chi tiết, Technical Spec, API Contract và Database Schema.
4.  **Khởi tạo (Scaffold)**: Tự động tạo khung dự án Go (Skeleton) với đầy đủ các driver (MongoDB, Redis, NATS, Kafka...) và các module tính năng theo chuẩn Clean Architecture.

## 🛠 Slash Commands

Sử dụng các lệnh sau trong khung chat để kích hoạt các workflow tương ứng:

| Lệnh | Mô tả |
| :--- | :--- |
| `/design <feature>` | Bắt đầu workflow thiết kế kiến trúc cho một tính năng mới. |
| `/research <topic>` | Nghiên cứu sâu về một công nghệ hoặc giải pháp cụ thể. |
| `/adr <title>` | Tạo một bản ghi quyết định kiến trúc (Architecture Decision Record). |
| `/new-go-project <name>` | Khởi tạo một dự án Go mới từ template chuẩn với đầy đủ drivers. |
| `/add-feature <name>` | Thêm một module tính năng mới theo Clean Architecture vào dự án hiện tại. |
| `/validate-project` | Kiểm tra tính tuân thủ kiến trúc của dự án hiện tại. |

## 📁 Cấu trúc thư mục

*   `SKILL.md`: Hướng dẫn chi tiết cho AI Agent về vai trò và quy tắc.
*   `ARCHITECTURE.md`: Thư viện các mẫu kiến trúc (Clean, Hexagonal, Event-Driven...).
*   `scripts/`: Bộ công cụ tự động hóa (nghiên cứu, tạo diagram, scaffold code, validate plan).
*   `skeleton/`: Các template tài liệu và khung dự án Go mẫu.
*   `examples/`: Các ví dụ thực tế về thiết kế kiến trúc.
*   `templates/`: Các mẫu Implementation Plan, Tech Spec, API Contract.

## 🚀 Quy trình làm việc (Workflow)

1.  **Discovery**: Làm rõ yêu cầu và ràng buộc kỹ thuật.
2.  **Research**: Sử dụng `scripts/research_tech.py` để tìm kiếm và đánh giá giải pháp.
3.  **Design**: Chọn kiến trúc phù hợp (tham khảo `ARCHITECTURE.md`) và tạo diagram bằng `scripts/generate_architecture.py`.
4.  **Contract-First**: Định nghĩa API Contract và Database Schema bằng các template trong `templates/`.
5.  **Planning**: Tạo Implementation Plan chi tiết và kiểm chứng bằng `scripts/validate_plan.py`.
6.  **Scaffolding**: Sử dụng `/new-go-project` hoặc `/add-feature` để tạo code block ban đầu.

## 🐍 Các Script quan trọng

| Script | Công dụng |
| :--- | :--- |
| `generate_project.py` | Tạo khung dự án Go với 7+ drivers tích hợp sẵn. |
| `generate_feature.py` | Tạo module CRUD hoàn chỉnh (Model, Service, Repo, Controller, Router). |
| `research_tech.py` | Tìm kiếm các thư viện/framework từ GitHub và phân tích độ phổ biến. |
| `validate_plan.py` | Kiểm tra kế hoạch triển khai có thiếu sót gì không (Multi-tenancy, JSON tags, Error wrapping...). |
| `generate_api_contract.py` | Tự động sinh tài liệu API Contract từ yêu cầu. |

---
**Lưu ý**: Skill này tập trung vào việc tạo ra tài liệu và cấu trúc chuẩn. Việc thực hiện chi tiết logic kinh doanh sẽ được bàn giao cho **Expert Go Backend Developer**.
