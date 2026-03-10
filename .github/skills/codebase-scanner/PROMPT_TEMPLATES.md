# 📋 AI Agent Prompt Templates

Sử dụng các templates này để yêu cầu AI Agent thực hiện các nhiệm vụ cụ thể một cách hiệu quả nhất đối với codebase lớn.

---

## 1. Onboarding & Hiểu Dự Án

**Prompt:**
> `/load-overview`
> Hãy tóm tắt cho tôi kiến trúc tổng thể của dự án này, liệt kê các công nghệ chính và cách các module giao tiếp với nhau. Sau đó hãy chỉ ra module quan trọng nhất.

---

## 2. Tìm Hiểu Tính Năng Cụ Thể

**Prompt:**
> `/load-domain <tên_domain>` (Ví dụ: `workflow`)
> Tôi cần sửa logic trong domain `<tên_domain>`. Hãy liệt kê cho tôi các API chính, các data models quan trọng và các services liên quan mà tôi cần chú ý.

---

## 3. Tìm Code / Logic Theo Business Rule

**Prompt:**
> `/load-semantic business` và `/find-logic <tên_tính_năng>`
> Tôi cần tìm logic xử lý business rule liên quan đến `<mô_tả_tính_năng>`. Hãy tìm trong index các file liên quan và giải thích cách nó được triển khai.

---

## 4. Kiểm Tra Bảo Mật Trước Khi Submit

**Prompt:**
> `/load-semantic security`
> Tôi vừa thay đổi code liên quan đến `<phần_vừa_sửa>`. Hãy kiểm tra xem thay đổi này có vi phạm các rủi ro bảo mật đã được cảnh báo trong security report không? Đặc biệt là check SQL injection và XSS.

---

## 5. Lên Kế Hoạch Task Mới (Verify Architecture)

**Prompt:**
> `/verify-arch Tôi muốn thêm tính năng <mô_tả_task>`
> Dựa trên kiến trúc hiện tại (L0/L1) và domain liên quan (L2), hãy đề xuất phương án triển khai tính năng này sao cho đúng design pattern hiện có. Đừng code ngay, hãy lên plan trước.

---

## 6. Audit & Refactor Code

**Prompt:**
> `/load-semantic tech-debt`
> Liệt kê các file có độ phức tạp cao hoặc hàm quá dài trong module `<tên_module>`. Hãy đề xuất kế hoạch refactor cho file `<tên_file>` dựa trên tech debt report.

---

## 7. Tìm Kiếm Symbol Khổng Lồ

**Prompt:**
> Tôi đang tìm struct/function tên là `<tên_symbol>`.
> Hãy dùng `grep_search` trên `.github/codebase-docs/SEARCH_INDEX.json` để tìm file chứa nó, sau đó đọc file đó và giải thích cho tôi.

---

## 💡 Lưu ý cho người dùng:
- Các lệnh `/load-*` là tín hiệu để AI Agent biết phải đọc file documentation nào trước.
- Luôn yêu cầu Agent "lên kế hoạch" (plan) trước khi thay đổi code trong codebase lớn.
- Nếu Agent nói "tôi không thấy code đó", hãy nhắc nó dùng **SEARCH_INDEX.json**.
