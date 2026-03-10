# Hướng dẫn sử dụng Expert PM & BA Orchestrator Skill

Skill `expert-pm-ba-orchestrator` đóng vai trò là "Tổng chỉ huy" (Main Brain) cho quy trình phát triển phần mềm (SDLC), quản lý từ khâu phân tích yêu cầu đến khi hoàn thiện sản phẩm.

## 1. Các chế độ hoạt động chính

### A. Chế độ Tự động (Autonomous Mode) - `/full-cycle`
Dùng khi bạn muốn giao trọn gói một yêu cầu và để AI tự động chạy qua các bước: Phân tích PRD -> Thiết kế Kiến trúc -> Lập kế hoạch -> Thực thi.

*   **Lệnh**: `/full-cycle <file_yêu_cầu hoặc nội_dung_text>`
*   **Ví dụ**: 
    - `/full-cycle yêu cầu: xây dựng tính năng đăng nhập bằng Google OAuth`
    - `/full-cycle @requirements.txt`

### B. Chế độ Từng bước (Interactive Mode)
Dùng khi bạn muốn kiểm soát từng giai đoạn của dự án.

1.  **Phân tích Yêu cầu (Giai đoạn 1)**
    *   **Lệnh**: `/analyze-req <yêu_cầu>`
    *   **Tác dụng**: Phân tích yêu cầu thô sơ thành tài liệu PRD chi tiết, tạo file `project-documentation/PRD.md`.

2.  **Liên kết Kiến trúc (Giai đoạn 2)**
    *   **Lệnh**: `/link-arch`
    *   **Tác dụng**: Gọi skill Solutions Architect để thiết kế hệ thống dựa trên PRD, tạo `ARCHITECTURE_SPEC.md`.

3.  **Lập Kế hoạch Tổng thể (Giai đoạn 3)**
    *   **Lệnh**: `/plan-master`
    *   **Tác dụng**: Tạo lộ trình triển khai chi tiết (`MASTER_PLAN.md`), phân chia công việc thành các "Work Package" (WP-XXX) rõ ràng.

4.  **Phân rã SRS chi tiết (Giai đoạn 4)**
    *   **Lệnh**: `/gen-srs`
    *   **Tác dụng**: Chuyển đổi các Work Package từ Master Plan thành các yêu cầu chi tiết (SRS) cho từng module. Mỗi SRS sẽ được liên kết chặt chẽ với một ID `WP-XXX`.

5.  **Lập Kế hoạch Chi tiết (Giai đoạn 5)**
    *   **Lệnh**: `/plan-detail`
    *   **Tác dụng**: Phân rã SRS thành các task nguyên tử (Atomic Task) tuân thủ quy tắc 2 giờ. Thiết lập cầu nối traceability giữa Task -> SRS -> Master Plan.

6.  **Điều phối Thực thi (Giai đoạn 6)**
    *   **Lệnh**: `/orchestrate-exec`
    *   **Tác dụng**: Bắt đầu gọi các Developer Agent (Go, React, AI) để code theo các Detail Plans đã lập.

7.  **Quản lý Thay đổi (Change Request) (Giai đoạn 7)**
    *   **Lệnh**: `/change-request <mô_tả_thay_đổi>`
    *   **Tác dụng**: Phân tích ảnh hưởng của thay đổi mới, cập nhật lại toàn bộ tài liệu và kế hoạch mà không làm vỡ hệ thống.

## 2. Cấu trúc Tài liệu Quản lý

Skill này sẽ tự động tạo và duy trì các tài liệu trong thư mục `project-documentation/`:

*   `OVERVIEW.md`: Tổng quan dự án, tiến độ chung.
*   `PRD.md`: Chi tiết yêu cầu chức năng và nghiệp vụ.
*   `MASTER_PLAN.md`: Kế hoạch thực hiện chi tiết từng bước.
*   `ARCHITECTURE_SPEC.md`: Thiết kế kỹ thuật hệ thống.

## 3. Quy trình làm việc đề xuất

1.  **Khởi tạo**: Bắt đầu bằng `/analyze-req` để làm rõ yêu cầu.
2.  **Review**: Kiểm tra `PRD.md` mà AI tạo ra. Nếu cần sửa, hãy chat để yêu cầu chỉnh sửa.
3.  **Thiết kế**: Chạy `/link-arch` để có thiết kế kỹ thuật.
4.  **Kế hoạch**: Chạy `/plan-master` để chia nhỏ thành các gói công việc lớn (Work Package).
5.  **Chi tiết hóa**: Chạy `/gen-srs` để làm rõ yêu cầu cho từng module từ Master Plan.
6.  **Lập task**: Chạy `/plan-detail` để tạo danh sách task nguyên tử (2-hour tasks).
7.  **Thực thi (Giai đoạn 6)**: Chạy `/orchestrate-exec` để bắt đầu code.
    - **Lưu ý Đặc biệt cho Dự án MỚI**: Tại bước này, PM sẽ yêu cầu Architect copy toàn bộ mã nguồn mẫu (Skeleton) vào thư mục gốc (Root) của dự án và điều chỉnh tên package. Đây là bước bắt buộc trước khi code tính năng.

## 4. Quy định Đọc kĩ lưỡng (Anti-Fraud Protocol - KIỂM TOÁN BẮT BUỘC)
**QUAN TRỌNG**: Bạn đang ở trạng thái **KIỂM TOÁN TÀI LIỆU**. Mọi nỗ lực bỏ qua việc đọc bằng cách "hiểu cấu trúc" đều là vi phạm nghiêm trọng.

1.  **CẤM GOM NHÓM TRONG MANIFEST**:
    - Tuyệt đối CẤM gộp các file trong bảng Manifest (ví dụ: không được ghi `srs/*.md` hay `Files 9-14`).
    - **MỌI** file bắt buộc phải có một dòng riêng biệt trong bảng.
2.  **CÁC TRẠNG THÁI BỊ CẤM**:
    - CẤM các trạng thái: "Structure understood", "Pattern clear", "Group read", "Partially read", "Estimated".
    - Trạng thái duy nhất được chấp nhận: **"100% Ingested (Verified via view_file)"**.
3.  **CHỈ SỐ DÒNG CHÍNH XÁC**:
    - CẤM sử dụng dấu `~` hoặc ghi "ước tính" (estimated) cho số dòng.
    - Bạn BẮT BUỘC phải ghi chính xác số dòng mà tool `view_file` báo cáo.
4.  **KIỂM TOÁN LỢI GỌI TOOL (LOGIC GATE AUDIT)**:
    - Trước khi tuyên bố file đã đọc, bạn phải tự kiểm tra: "Mình đã thực sự gọi lệnh `view_file` cho đường dẫn cụ thể này trong lượt này chưa?". Việc tuyên bố đã đọc mà không có lệnh gọi tool tương ứng được coi là **Gian lận kỹ thuật**.
5.  **GIỚI HẠN CONTEXT = TĂNG LƯỢT CHAT**:
    - "Hiệu quả context" không phải là lý do để bỏ qua file. Nếu hết context, hãy tóm tắt các phân tích cũ và **TIẾP TỤC GỌI TOOL TUẦN TỰ**.
6.  **CẤM NGÔN THỰC THI**:
    - Mọi việc nhắc đến "Implementation", "Scaffolding" hay "Task Execution" trước khi bảng Manifest chi tiết đạt 100% đều dẫn đến thất bại nhiệm vụ ngay lập tức.

> **Lưu ý**: Trong quá trình thực thi, nếu bạn có yêu cầu mới, hãy dùng lệnh `/change-request` thay vì ra lệnh trực tiếp để đảm bảo tính nhất quán của tài liệu.
