# Product Requirements Document (PRD)
# Nền Tảng Cung Cấp Dịch Vụ Dùng Chung (Services Provider) cho AV & UAV
## VNPT AV Platform — Services Provider Group

**Document Version**: 1.0.0  
**Status**: Draft  
**Created**: 2026-03-06  
**Owner**: VNPT AV Platform — Product Team  

---

## 1. Executive Summary

- **Objective**: Xây dựng nhóm phân hệ **Services Provider** cho VNPT AV Platform — một nền tảng PaaS (Platform-as-a-Service) cung cấp dịch vụ gọi xe tự hành (Autonomous Vehicle / AV) và máy bay không người lái (UAV). Nhóm Services Provider chịu trách nhiệm toàn bộ logic kinh doanh từ đặt chuyến xe, định giá, thanh toán, quản lý doanh nghiệp (Tenant), thông báo, phân tích và hệ sinh thái tích hợp.
- **Target Audience**:
  - **Người dùng cuối (Passengers/Riders)**: Hành khách đặt xe AV thông qua ứng dụng di động.
  - **Khách hàng doanh nghiệp (Enterprise Tenants/B2B)**: Các công ty thuê hạ tầng nền tảng để xây dựng ứng dụng gọi xe riêng.
  - **Quản trị nền tảng (Platform Admins)**: Nhóm vận hành VNPT AV Platform.
  - **Đối tác tích hợp (3rd Party Partners)**: Nhà cung cấp dịch vụ bảo hiểm, bản đồ, thanh toán, v.v.
- **Success Metrics**:
  - Average ETA Accuracy: chênh lệch < 2 phút
  - Ride Completion Rate: > 95%
  - Average Wait Time: < 5 phút
  - Fleet Utilization: > 70% xe đang chạy
  - Safety Intervention Rate: < 1 lần / 1.000 chuyến
  - API P95 Latency: < 500ms
  - Payment Success Rate: > 99.5%
  - System Uptime: ≥ 99.9%
- **Key Constraints**:
  - Backend Service: Java 17+ / Spring Boot 3.x (các phân hệ SP)
  - Database: MongoDB (primary), Redis (cache), InfluxDB (time-series), Elasticsearch (analytics)
  - Event Streaming: Kafka (async), NATS (real-time push)
  - Multi-tenant: Bắt buộc cô lập dữ liệu theo `tenant_id`
  - Security: JWT/OAuth2, RBAC, PCI-DSS compliance (PAY)

---

## 2. Problem Statement

- **Context**: VNPT AV Platform đang mở rộng từ hệ thống quản lý đội xe (VMS/AOC) sang mô hình kinh doanh trực tiếp và B2B. Để vận hành như một nền tảng thương mại, cần phải có nhóm phân hệ Services Provider chuyên xử lý các nghiệp vụ tạo ra doanh thu.
- **Current Limitations**:
  - Chưa có phân hệ đặt xe thương mại cho xe tự hành (AV-aware matching, trip lifecycle).
  - Chưa có hệ thống định giá động (surge pricing, upfront pricing).
  - Chưa có nền tảng quản lý doanh nghiệp B2B (multi-tenant onboarding, white-labeling).
  - Chưa có hệ thống thanh toán tích hợp đa cổng (Stripe, VNPay, MoMo, v.v.).
  - Thiếu hệ thống phân tích và báo cáo tập trung.
  - Chưa có hệ sinh thái marketplace cho đối tác tích hợp.

---

## 3. User Personas

| Persona | Mô tả | Nhu cầu chính |
|---------|-------|---------------|
| **Passenger (Rider)** | Người dùng cuối đặt xe AV qua app mobile | Đặt xe nhanh, biết ETA chính xác, thanh toán dễ dàng, nhận thông báo real-time |
| **Enterprise Admin (Tenant Admin)** | Quản trị viên của công ty B2B thuê nền tảng | Onboarding tự động, white-label brand, quản lý hóa đơn và hạn ngạch, xem dashboard |
| **Platform Admin (VNPT)** | Nhóm vận hành nền tảng VNPT | Quản lý tất cả tenants, xem báo cáo doanh thu, quản lý đối tác marketplace |
| **3rd Party Partner** | Nhà cung cấp plugin/service (bảo hiểm, bản đồ...)  | Đăng ký, publish plugin lên marketplace, nhận thanh toán hoa hồng |
| **Safety Monitor** | Giám sát viên an toàn vận hành xe AV | Nhận cảnh báo khẩn cấp ngay lập tức khi xe gặp sự cố |

---

## 4. Functional Requirements

### 4.1 RHS Service — Ride-Hailing Service (Dịch Vụ Đặt Xe Tự Hành)

#### 4.1.1 Quản lý vòng đời chuyến đi (Trip Lifecycle Management)

- **FR-RHS-001**: Hệ thống PHẢI hỗ trợ hành khách yêu cầu đặt xe ngay (on-demand) và đặt lịch trước (scheduled rides).
- **FR-RHS-002**: Hệ thống PHẢI quản lý trạng thái chuyến đi theo Trip State Machine gồm các trạng thái sau (theo thứ tự vòng đời bình thường):
  ```
  Requested → Matched → Vehicle_Enroute → Arrived → Boarding → In_Progress → Alighting → Completed
  ```
  Các trạng thái ngoại lệ:
  ```
  Remote_Intervention | Safety_Stop | Cancelled
  ```
- **FR-RHS-003**: Hệ thống PHẢI cho phép hành khách huỷ chuyến đi trước khi xe đến điểm đón, tùy theo chính sách huỷ của từng tenant.
- **FR-RHS-004**: Hệ thống PHẢI lưu và cung cấp API tra cứu lịch sử chuyến đi của hành khách.
- **FR-RHS-005**: Hệ thống PHẢI publish sự kiện thay đổi trạng thái chuyến đi lên **Kafka** để các phân hệ khác (PAY, ABI) consume, đồng thời push real-time update qua **NATS** tới ứng dụng mobile của hành khách.

#### 4.1.2 AV-Aware Matching (Ghép xe thông minh)

- **FR-RHS-010**: Thuật toán ghép xe PHẢI đánh giá dựa trên các yếu tố sau (không chỉ gần nhất):
  - Khoảng cách địa lý (proximity).
  - Mức pin hiện tại của xe AV (vehicle battery level).
  - Loại xe (vehicle type) phù hợp yêu cầu.
  - Tính tương thích ODD (Operational Design Domain): xe PHẢI được cấp phép chạy trong khu vực mà hành khách yêu cầu.
- **FR-RHS-011**: Hệ thống PHẢI cache kết quả ghép xe tạm thời trên **Redis** để đảm bảo phản hồi nhanh.

#### 4.1.3 ETA Engine (Dự đoán thời gian chính xác)

- **FR-RHS-020**: Hệ thống PHẢI tính ETA bằng mô hình ML (LSTM hoặc GBM) dựa trên:
  - Dữ liệu lịch sử chuyến đi.
  - Bản đồ HD từ phân hệ HML.
  - Lưu lượng giao thông thực tế.
  - Hồ sơ tốc độ (speed profile) của xe AV.
- **FR-RHS-021**: ETA PHẢI cập nhật liên tục trong quá trình xe di chuyển và đẩy về app mobile qua NATS.

#### 4.1.4 Ride Pooling (Đi chung xe)

- **FR-RHS-030**: Hệ thống PHẢI hỗ trợ tính năng ghép nhiều hành khách có cùng tuyến đường vào một chuyến xe.
- **FR-RHS-031**: Thuật toán Pooling Optimizer PHẢI tối thiểu hóa quãng đường đi vòng (detour) trong khi vẫn tuân thủ ràng buộc thời gian của từng hành khách.

#### 4.1.5 Rating Service (Đánh giá chất lượng xe)

- **FR-RHS-040**: Sau mỗi chuyến đi hoàn thành, hệ thống PHẢI thu thập đánh giá từ hành khách về các tiêu chí: độ sạch sẽ, mức độ an toàn, sự thoải mái.
- **FR-RHS-041**: Điểm đánh giá PHẢI được tổng hợp để chấm điểm chất lượng cho từng chiếc xe trong hệ thống VMS.

---

### 4.2 FPE Service — Fare & Pricing Engine (Hệ Thống Định Giá & Cước Phí)

#### 4.2.1 Dynamic & Upfront Pricing

- **FR-FPE-001**: Hệ thống PHẢI tính giá cước theo công thức: `Fare = Base Fee + (Distance Rate × km) + (Time Rate × phút)`, kết hợp với phân cấp theo loại xe (vehicle-type tier).
- **FR-FPE-002**: Hệ thống PHẢI hỗ trợ Upfront Pricing: chốt giá cố định ngay khi hành khách đặt xe, giá này KHÔNG thay đổi dù lộ trình thực tế có sai lệch.
- **FR-FPE-003**: Hệ thống PHẢI cache giá ước tính trên **Redis** để đảm bảo phản hồi siêu tốc (< 200ms).

#### 4.2.2 Surge Pricing (Giá tăng theo nhu cầu)

- **FR-FPE-010**: Hệ thống PHẢI tính hệ số nhân giá (surge multiplier) trong khoảng **1.0x đến 3.0x** dựa trên tỷ lệ cung-cầu thực tế.
- **FR-FPE-011**: Hệ thống PHẢI tích hợp dữ liệu nhu cầu dự đoán từ Fleet Optimization để điều chỉnh surge thông minh.
- **FR-FPE-012**: Hệ thống PHẢI hỗ trợ cấu hình trần surge (configurable caps) theo từng tenant để bảo vệ người dùng cuối.

#### 4.2.3 Enterprise Rate Cards (Bảng giá doanh nghiệp)

- **FR-FPE-020**: Hệ thống PHẢI cho phép Platform Admin tạo Rate Card riêng cho từng tenant với các mô hình:
  - Flat rates (giá đồng giá).
  - Volume discounts (chiết khấu theo sản lượng).
  - Monthly caps (giới hạn chi tiêu hàng tháng).

#### 4.2.4 Promotion Management (Quản lý khuyến mãi)

- **FR-FPE-030**: Hệ thống PHẢI hỗ trợ tạo và quản lý (CRUD) các chiến dịch khuyến mãi:
  - Mã giảm giá (coupons).
  - Giảm giá chuyến đi đầu tiên (first-ride discount).
  - Khuyến mãi theo khu vực địa lý (zone promotions).
  - Điểm thưởng giới thiệu (referral credits).

#### 4.2.5 Fare Split & Revenue Share

- **FR-FPE-040**: Hệ thống PHẢI hỗ trợ chia tiền cước giữa nhiều hành khách đi chung xe (Fare Split) với tỷ lệ tùy chỉnh.
- **FR-FPE-041**: Hệ thống PHẢI tự động tính toán tỷ lệ chia sẻ doanh thu giữa VNPT Platform và tenant (Revenue Share) dựa trên cấu hình linh hoạt.
- **FR-FPE-042**: FPE PHẢI publish sự kiện thay đổi giá và surge pricing lên **Kafka**.

---

### 4.3 BMS Service — Billing & Subscription Management (Quản Lý Thanh Toán & Gói Dịch Vụ)

#### 4.3.1 Subscription & Plan Management

- **FR-BMS-001**: Hệ thống PHẢI quản lý vòng đời các gói dịch vụ (ví dụ: Starter, Growth, Enterprise) bao gồm:
  - Chu kỳ thanh toán: hàng tháng / hàng năm.
  - Bản dùng thử (Trial periods).
- **FR-BMS-002**: Mỗi gói dịch vụ PHẢI quản lý danh sách Feature Flags và quyền lợi đi kèm riêng.

#### 4.3.2 Metering & Quota Management

- **FR-BMS-010**: Hệ thống PHẢI theo dõi và đo lường các chỉ số sử dụng của từng tenant:
  - Số lượng API calls.
  - Số chuyến đi (rides).
  - Số km di chuyển.
  - Dung lượng lưu trữ (storage GB).
- **FR-BMS-011**: Hệ thống PHẢI thực thi giới hạn tài nguyên (quota enforcement): chặn các yêu cầu vượt quá hạn ngạch được cấp phép.
- **FR-BMS-012**: Metering counters PHẢI được cache trên **Redis** để kiểm tra quota siêu nhanh (< 10ms).
- **FR-BMS-013**: Dữ liệu đo lường theo thời gian PHẢI được lưu vào **InfluxDB** và **MongoDB**.

#### 4.3.3 Invoicing & Tax Calculation

- **FR-BMS-020**: Hệ thống PHẢI tự động xuất hóa đơn định kỳ với bảng kê chi tiết từng khoản mục (line-item breakdown).
- **FR-BMS-021**: Hệ thống PHẢI tự động tính thuế (VAT, GST) dựa trên quy định pháp lý theo khu vực của tenant.
- **FR-BMS-022**: Khi có hóa đơn mới, BMS PHẢI gửi tín hiệu tới **NCS Service** để thông báo cho doanh nghiệp qua email/webhook.

#### 4.3.4 Cost Explorer & Credit System

- **FR-BMS-030**: Hệ thống PHẢI cung cấp dashboard phân tích chi tiêu, dự báo chi phí và gửi cảnh báo tự động khi tenant vượt ngân sách.
- **FR-BMS-031**: Hệ thống PHẢI quản lý ví tín dụng (Credits) bao gồm: pre-paid, promotional credits, trial credits.
- **FR-BMS-032**: BMS PHẢI gọi **PAY Service** để thực hiện trừ tiền hóa đơn doanh nghiệp định kỳ.
- **FR-BMS-033**: BMS PHẢI publish billing events và metering events lên **Kafka** để ABI Service tiêu thụ.

---

### 4.4 PAY Service — Payment Processing (Hệ Thống Xử Lý Thanh Toán)

#### 4.4.1 Core Payment Processing

- **FR-PAY-001**: Hệ thống PHẢI hỗ trợ định tuyến giao dịch đến các cổng thanh toán: tính phí (charge), ủy quyền (authorize), và ghi nhận giao dịch (capture).
- **FR-PAY-002**: Hệ thống PHẢI tích hợp sẵn adapter kết nối tới: **Stripe**, **VNPay**, **VNPT Money**, **Viettel Money**, **MoMo**.
- **FR-PAY-003**: Hệ thống PHẢI hỗ trợ cơ chế **Escrow**: pre-authorize khi đặt xe → capture khi hoàn thành chuyến đi.
- **FR-PAY-004**: Hệ thống PHẢI sử dụng **Idempotency Key** (lưu trên Redis) để ngăn chặn trừ tiền trùng lặp.

#### 4.4.2 Wallet Management (Ví điện tử)

- **FR-PAY-010**: Hệ thống PHẢI cung cấp ví điện tử nội bộ cho người dùng: nạp tiền (top-up), kiểm tra số dư, nạp tự động.
- **FR-PAY-011**: Dữ liệu số dư ví PHẢI được lưu an toàn trên **MongoDB** (tokenized card data).

#### 4.4.3 Refund & Payouts

- **FR-PAY-020**: Hệ thống PHẢI xử lý hoàn tiền toàn phần hoặc một phần dựa trên chính sách linh hoạt (ví dụ: tự động hoàn tiền nếu xe đến trễ > 10 phút).
- **FR-PAY-021**: Hệ thống PHẢI quản lý lịch chi trả doanh thu (scheduled payouts) cho đối tác doanh nghiệp theo tỷ lệ Revenue Share từ FPE.

#### 4.4.4 Fraud Detection (Chống gian lận)

- **FR-PAY-030**: Hệ thống PHẢI tích hợp cơ chế chống gian lận kết hợp:
  - Rule-based: các quy tắc cứng (blacklist, velocity checks).
  - ML fraud scoring: mô hình học máy chấm điểm rủi ro.
- **FR-PAY-031**: Giao dịch có điểm rủi ro cao PHẢI bị giữ lại để xem xét thủ công hoặc tự động từ chối.

#### 4.4.5 Multi-Currency

- **FR-PAY-040**: Hệ thống PHẢI tự động chuyển đổi ngoại tệ và hỗ trợ các phương thức thanh toán đặc thù theo khu vực địa lý.
- **FR-PAY-041**: PAY PHẢI publish payment events và audit logs lên **Kafka**.

---

### 4.5 TMS Service — Tenant & Organization Management (Quản Lý Doanh Nghiệp)

#### 4.5.1 Enterprise Onboarding (Tự động hóa khởi tạo)

- **FR-TMS-001**: Hệ thống PHẢI cung cấp quy trình thiết lập tự động đa bước (multi-step provisioning) cho khách hàng doanh nghiệp mới, bao gồm:
  - Tạo `tenant_id` duy nhất.
  - Thiết lập không gian dữ liệu riêng biệt.
- **FR-TMS-002**: TMS PHẢI đóng vai trò "nhạc trưởng" gọi tuần tự các phân hệ sau khi onboarding:
  1. **SSC**: Tạo tài khoản Admin + thiết lập RBAC.
  2. **BMS**: Thiết lập gói cước (subscription).
  3. **DPE**: Sinh API Keys.
  4. **VMS**: Phân bổ đội xe.

#### 4.5.2 White-labeling & Branding

- **FR-TMS-010**: Mỗi tenant PHẢI được phép tùy chỉnh:
  - Logo (upload lên S3/MinIO).
  - Bảng màu (color scheme).
  - Email template.
  - Custom domain (domain mapping).

#### 4.5.3 Data Isolation & Resource Quota

- **FR-TMS-020**: Hệ thống PHẢI đảm bảo cô lập dữ liệu hoàn toàn giữa các tenant (cross-tenant data leakage prevention) bằng cơ chế lọc theo `tenant_id` ở tất cả các lớp.
- **FR-TMS-021**: Hệ thống PHẢI thực thi giới hạn tài nguyên (số xe tối đa, lưu lượng API, storage) theo gói dịch vụ đã đăng ký.

#### 4.5.4 Tenant Configuration & Feature Flags

- **FR-TMS-030**: Hệ thống PHẢI quản lý các thiết lập đặc thù và Feature Flags riêng cho từng tenant.
- **FR-TMS-031**: Thông tin ngữ cảnh tenant PHẢI được cache trên **Redis** để truy xuất siêu nhanh.

#### 4.5.5 Rider Identity Management (B2C)

- **FR-TMS-040**: Hệ thống PHẢI cung cấp dịch vụ quản lý hồ sơ người dùng cuối (hành khách) với khả năng:
  - Đăng ký / Đăng nhập bằng mạng xã hội (Google, Apple).
  - Xác thực số điện thoại bằng OTP.
- **FR-TMS-041**: Hệ thống CÓ THỂ tích hợp với **Keycloak** (v26+) như nền tảng xác thực và phân quyền tập trung.
- **FR-TMS-042**: Rider Identity PHẢI tách biệt hoàn toàn khỏi IAM (Identity & Access Management) vận hành đội xe.
- **FR-TMS-043**: TMS PHẢI publish tenant lifecycle events (tenant created, tenant suspended) lên **Kafka**.

---

### 4.6 NCS Service — Notification & Communication (Hệ Thống Thông Báo)

#### 4.6.1 Multi-channel Routing (Định tuyến đa kênh)

- **FR-NCS-001**: Hệ thống PHẢI hỗ trợ gửi thông báo qua các kênh: Push Notification (iOS/Android via FCM/APNs), SMS (Twilio), Email (SendGrid), In-app, Webhooks.
- **FR-NCS-002**: Hệ thống PHẢI tự động chọn kênh gửi tốt nhất dựa trên loại sự kiện và mức độ ưu tiên:
  - **Critical** (e.g., Safety Alert): Push Notification + SMS (gửi đồng thời).
  - **High** (e.g., Xe đã đến): Push Notification.
  - **Medium** (e.g., Biên lai thanh toán): Email + Push Notification.
  - **Low** (e.g., Thông tin khuyến mãi): Email hoặc In-app.

#### 4.6.2 Template Engine

- **FR-NCS-010**: Hệ thống PHẢI cho phép CRUD mẫu thông báo (notification templates) với hỗ trợ đa ngôn ngữ (i18n).
- **FR-NCS-011**: Hệ thống PHẢI hỗ trợ variable substitution (thay thế biến động) trong template.
- **FR-NCS-012**: Hệ thống PHẢI hỗ trợ A/B testing cho nội dung thông báo.

#### 4.6.3 User Preferences & Privacy

- **FR-NCS-020**: Người dùng PHẢI được phép cấu hình:
  - Kênh muốn nhận (opt-in/opt-out từng kênh).
  - Giờ yên tĩnh (quiet hours) — không nhận thông báo trong khoảng thời gian nhất định.
  - Giới hạn tần suất nhận thông báo (frequency caps).

#### 4.6.4 Reliable Delivery (Đảm bảo phân phối)

- **FR-NCS-030**: Hệ thống PHẢI retry với chiến lược exponential backoff khi dịch vụ gửi bên thứ 3 gặp sự cố.
- **FR-NCS-031**: Tin nhắn không thể gửi sau tất cả các lần retry PHẢI được đưa vào Dead Letter Queue (DLQ) để điều tra.
- **FR-NCS-032**: Hệ thống PHẢI sử dụng **Redis** để deduplication (loại bỏ thông báo gửi trùng) và rate limiting.

#### 4.6.5 Enterprise Webhooks

- **FR-NCS-040**: Hệ thống PHẢI cho phép tenant đăng ký subscribe sự kiện nền tảng (e.g., ride.completed, payment.success) qua Webhooks.
- **FR-NCS-041**: Webhook delivery PHẢI bao gồm signature verification (HMAC) để đảm bảo bảo mật.
- **FR-NCS-042**: NCS PHẢI sử dụng **Kafka** làm hàng đợi xử lý sự kiện bất đồng bộ.
- **FR-NCS-043**: NCS PHẢI lưu nhật ký phân phối (delivery status logs) vào **MongoDB**.

---

### 4.7 ABI Service — Analytics & Business Intelligence (Hệ Thống Phân Tích)

#### 4.7.1 Dashboards & KPI Monitoring

- **FR-ABI-001**: Hệ thống PHẢI cung cấp real-time dashboards với khả năng tùy chỉnh widget cho từng tenant.
- **FR-ABI-002**: Hệ thống PHẢI theo dõi và cảnh báo (threshold alerts) cho các KPI sau:
  - Average ETA Accuracy (target: < 2 phút lệch).
  - Ride Completion Rate (target: > 95%).
  - Average Wait Time (target: < 5 phút).
  - Fleet Utilization (target: > 70%).
  - Safety Intervention Rate (target: < 1/1000 chuyến).

#### 4.7.2 Demand & Revenue Analytics

- **FR-ABI-010**: Hệ thống PHẢI tạo bản đồ nhiệt (heatmaps) thể hiện khu vực nhu cầu cao.
- **FR-ABI-011**: Hệ thống PHẢI phân tích xu hướng doanh thu theo: tenant, khu vực địa lý, loại xe.
- **FR-ABI-012**: Hệ thống PHẢI phát hiện quy luật theo mùa vụ (seasonal patterns) và theo khung giờ.

#### 4.7.3 Regulatory Reporting

- **FR-ABI-020**: Hệ thống PHẢI tự động sinh báo cáo tuân thủ quy định bao gồm: dữ liệu an toàn vận hành, mức độ tiếp cận dịch vụ, lượng khí thải.
- **FR-ABI-021**: Báo cáo PHẢI được lưu trên **MinIO/S3** và hỗ trợ xuất PDF/CSV.

#### 4.7.4 ETL & Export

- **FR-ABI-030**: Hệ thống PHẢI có pipeline ETL để gom cụm dữ liệu thô thành dạng sẵn sàng phân tích.
- **FR-ABI-031**: Hệ thống PHẢI hỗ trợ lịch gửi báo cáo tự động (hàng ngày/tuần/tháng) qua API hoặc email.
- **FR-ABI-032**: ABI PHẢI consume events từ **Kafka**: ride-events (RHS), payment-events (PAY), billing-events (BMS).
- **FR-ABI-033**: ABI PHẢI sử dụng **Elasticsearch** cho aggregation queries và **InfluxDB** cho time-series analytics.

---

### 4.8 MKP Service — Marketplace & Integration Hub (Hệ Sinh Thái Tích Hợp)

#### 4.8.1 Catalog & Plugin Management

- **FR-MKP-001**: Hệ thống PHẢI cung cấp "chợ ứng dụng" cho phép doanh nghiệp duyệt, tìm kiếm, cài đặt và gỡ cài đặt plugin.
- **FR-MKP-002**: Mỗi tenant PHẢI được phép bật/tắt plugin một cách độc lập trong không gian của họ.
- **FR-MKP-003**: Danh mục marketplace PHẢI được cache trên **Redis** để tải siêu nhanh.

#### 4.8.2 Partner & Certification Service

- **FR-MKP-010**: Hệ thống PHẢI quản lý toàn bộ vòng đời đối tác: đăng ký → ký kết thỏa thuận → theo dõi hiệu suất.
- **FR-MKP-011**: Hệ thống PHẢI thực hiện đánh giá bảo mật (security audit) và kiểm thử hiệu năng (performance testing) trước khi duyệt đối tác lên Marketplace.

#### 4.8.3 Pre-built Connectors

- **FR-MKP-020**: Hệ thống PHẢI cung cấp sẵn các connector tới các lĩnh vực:
  - Bảo hiểm (Insurance): per-ride insurance, liability, tích hợp qua Webhook sự kiện `ride.started`.
  - Hỗ trợ tiếp cận (Accessibility): xe lăn, khiếm thính, tích hợp vào module ghép xe.
  - Du lịch doanh nghiệp (Corporate Travel): SAP Concur, TripActions qua OAuth + API.
  - Bản đồ & Phân tích (Mapping & Analytics): custom map providers, custom BI tools.

#### 4.8.4 Revenue Share (Chia sẻ doanh thu đối tác)

- **FR-MKP-030**: Hệ thống PHẢI tự động tính hoa hồng nền tảng và chi trả doanh thu cho đối tác.
- **FR-MKP-031**: MKP PHẢI gọi **PAY Service** để thực hiện payouts cho đối tác.
- **FR-MKP-032**: MKP PHẢI tương tác với **TMS** để kích hoạt/quản lý plugin theo tenant, và với **DPE** để cấu hình luồng API tích hợp.

---

### 4.9 Business Logic & Rules

| Rule ID | Rule | Service |
|---------|------|---------|
| BL-001 | Mỗi yêu cầu DB PHẢI bao gồm `tenant_id` trong điều kiện lọc để tránh cross-tenant data leak. | Tất cả |
| BL-002 | Surge multiplier tối đa là 3.0x. Configurable cap theo tenant. | FPE |
| BL-003 | Escrow pre-authorize → chỉ capture khi chuyến đi hoàn thành. Không capture khi trip bị cancel. | PAY |
| BL-004 | Idempotency key (UUID) PHẢI tồn tại trong Redis ≥ 24 giờ để ngăn duplicate charge. | PAY |
| BL-005 | Hoàn tiền tự động nếu xe đến trễ > 10 phút so với ETA cam kết (tính từ thời điểm Matched). | PAY, RHS |
| BL-006 | Khi quota API của tenant đạt 80%, NCS PHẢI gửi cảnh báo. Khi đạt 100%, yêu cầu PHẢI bị từ chối với HTTP 429. | BMS, NCS |
| BL-007 | Safety Alert (Critical) PHẢI gửi đồng thời qua cả Push + SMS trong vòng < 5 giây. | NCS |
| BL-008 | Mọi giao dịch tài chính PHẢI có audit log không thể xóa (immutable) trên MongoDB. | PAY |
| BL-009 | Plugin chỉ được xuất hiện trên Marketplace sau khi vượt qua security audit và performance test. | MKP |
| BL-010 | Feature Flag của tenant PHẢI ghi đè lên Feature Flag mặc định của Platform. | TMS |
| BL-011 | Onboarding tenant PHẢI là transactional: thất bại ở bất kỳ bước nào PHẢI rollback toàn bộ. | TMS |

---

### 4.10 Data Entities & Relations

```
Tenant (TMS)
  ├── has many → User (SSC/TMS)
  ├── has one → Subscription (BMS)
  ├── has many → RateCaRC (FPE)
  ├── has many → InstalledPlugin (MKP)
  └── has one → TenantConfig (TMS)

User/Rider (TMS)
  ├── has many → Trip (RHS)
  └── has one → Wallet (PAY)

Trip (RHS)
  ├── has one → Fare (FPE)
  ├── has one → Payment (PAY)
  └── has many → Rating (RHS)

Subscription (BMS)
  ├── has many → Invoice (BMS)
  ├── has many → UsageRecord (BMS)
  └── has one → Plan (BMS)

Invoice (BMS)
  └── has one → PaymentTransaction (PAY)

Partner (MKP)
  ├── has many → Plugin (MKP)
  └── has many → PartnerPayout (PAY)

Notification (NCS)
  ├── belongs to → Tenant
  └── has one → DeliveryLog (NCS)
```

---

## 5. Non-Functional Requirements

### 5.1 Performance

| Metric | Target |
|--------|--------|
| API P95 Latency (Read) | < 200ms |
| API P95 Latency (Write) | < 500ms |
| Fare Estimation Response | < 200ms (cached) |
| Quota Check | < 10ms (Redis) |
| Notification Delivery (Critical) | < 5 giây end-to-end |
| ETA Accuracy | Chênh lệch < 2 phút |
| Trip State Machine Transition | < 1 giây sau sự kiện |

### 5.2 Scalability

| Component | Target |
|-----------|--------|
| Concurrent Trips | ≥ 10.000 chuyến đồng thời |
| API Requests | ≥ 50.000 req/s (tổng hệ thống) |
| Kafka Events Throughput | ≥ 100.000 events/s |
| Tenants | ≥ 1.000 enterprise tenants |
| Users per Tenant | ≥ 100.000 users |

### 5.3 Security

| Requirement | Details |
|-------------|---------|
| Authentication | JWT / OAuth2 (Keycloak v26+) |
| Authorization | RBAC — mỗi action phải được map với role |
| Multi-tenancy Isolation | Tất cả queries PHẢI có `tenant_id` filter |
| Payment Security | PCI-DSS compliant; tokenized card data |
| API Security | API Key + Rate Limiting |
| Audit Trail | Mọi thay đổi tài chính có immutable audit log |
| Webhook Security | HMAC signature verification |
| Data Encryption | AES-256 at rest; TLS 1.3 in transit |
| Fraud Protection | Rule-based + ML scoring |

### 5.4 Reliability & Availability

- System Uptime: ≥ 99.9% (< 8.7 giờ downtime/năm)
- RTO (Recovery Time Objective): < 30 phút
- RPO (Recovery Point Objective): < 5 phút (zero critical data loss)
- Payment Duplicate Prevention: Idempotency key cơ chế bắt buộc
- Notification Retry: Exponential backoff + Dead Letter Queue
- Kafka: Replication Factor ≥ 3; Consumer Group retry

### 5.5 Observability

- Distributed tracing (Jaeger/OpenTelemetry) cho tất cả services
- Metrics: Prometheus + Grafana dashboard
- Centralized logging: ELK Stack (Elasticsearch, Logstash, Kibana)
- Alerting: PagerDuty / OpsGenie tích hợp cho Critical alerts

---

## 6. User Experience & Interaction

### 6.1 Hành khách đặt xe (End-to-End Ride Flow)

```
1. Passenger mở app → Nhập điểm đón/điểm đến
2. FPE tính Upfront Fare (< 200ms, cached)
3. Passenger xác nhận đặt xe
4. PAY pre-authorize (Escrow) ngay lập tức
5. RHS chạy AV-Aware Matching → assign xe tốt nhất
6. NATS push: "Xe đã được ghép, ETA X phút"
7. Xe AV di chuyển → ETA Engine cập nhật liên tục → NATS push
8. Trạng thái: Vehicle_Enroute → Arrived → Boarding → In_Progress → Alighting → Completed
9. PAY capture (trừ tiền) sau khi Completed
10. NCS gửi biên lai qua Email + Push
11. Hệ thống yêu cầu Passenger đánh giá chuyến xe
```

### 6.2 Enterprise Tenant Onboarding Flow

```
1. B2B Partner đăng ký qua Portal
2. TMS tạo tenant_id, thiết lập dữ liệu riêng
3. TMS gọi SSC → tạo Admin account + RBAC roles
4. TMS gọi BMS → chọn gói subscription
5. TMS gọi DPE → sinh API Keys
6. TMS gọi VMS → phân bổ đội xe
7. Tenant cấu hình branding: logo, màu, domain
8. NCS gửi email chào mừng với thông tin đăng nhập
```

### 6.3 Edge Cases

| Scenario | Business Rule | System Response |
|----------|---------------|-----------------|
| Không tìm được xe phù hợp (ODD/pin) | AV-Aware Matching thất bại | Trả về lỗi 503 với message "Không có xe phù hợp"; không trừ tiền |
| Xe AV gặp sự cố giữa chuyến | Safety_Stop state | NCS gửi Critical alert cho Safety Monitor; TMS dispatch Remote Intervention |
| Giao dịch trùng lặp (duplicate charge) | Idempotency check | Trả về HTTP 200 với response gốc; không trừ tiền lần 2 |
| Tenant vượt API quota | BL-006 | HTTP 429 Too Many Requests; NCS gửi cảnh báo khi đạt 80% |
| Surge > 3.0x | Cap enforcement | Giới hạn multiplier tại 3.0x hoặc cap của tenant |
| Token JWT hết hạn | Auth validation | HTTP 401; client phải refresh token |
| Passenger hủy sau khi xe đang đến | Cancel policy | Có thể charge phí hủy theo policy tenant; PAY release escrow (trừ phí nếu có) |
| Onboarding tenant thất bại giữa chừng | BL-011 | Rollback toàn bộ: xóa tenant_id, account, subscription đã tạo |
| Webhook delivery thất bại | Retry + DLQ | Exponential backoff 3 lần; sau đó vào DLQ |

---

## 7. Logic Validation Checklist (MANDATORY)

- [x] **RBAC**: Mọi action đều được map với user role. Rider chỉ xem trip của mình. Tenant Admin chỉ xem dữ liệu trong tenant của họ.
- [x] **Data Validation**: Tọa độ GPS phải trong range hợp lệ. Surge multiplier 1.0x–3.0x. Fare amount > 0. Phone number phải validate OTP.
- [x] **Error Handling**: HTTP 400 (validation), 401 (unauthenticated), 403 (unauthorized), 404 (not found), 409 (conflict/duplicate), 422 (business logic), 429 (quota exceeded), 500 (internal), 503 (service unavailable).
- [x] **Multi-tenancy**: Tất cả queries PHẢI có `tenant_id` filter. Không có cross-tenant data access.
- [x] **Audit Trail**: Tất cả giao dịch tài chính (charge, refund, payout) có immutable audit log với actor + timestamp.
- [x] **Idempotency**: PAY Service bắt buộc idempotency key cho mọi mutation operation.
- [x] **Escrow**: PAY không capture tiền nếu trip chưa ở trạng thái Completed.
- [x] **Quota Enforcement**: BMS chặn request khi tenant vượt 100% quota.

---

## 8. Edge Case Matrix

| ID | Scenario | Business Rule | System Response |
|----|----------|---------------|-----------------|
| EC-001 | JWT token expired | Session integrity | HTTP 401; redirect to login |
| EC-002 | Concurrent booking same vehicle | Last-write wins + optimistic lock | HTTP 409 Conflict; retry matching |
| EC-003 | Payment gateway down | Fail-safe | Queue transaction; notify user; retry with backup gateway |
| EC-004 | ML model timeout (ETA) | Fallback | Use rule-based ETA; log degradation |
| EC-005 | Kafka consumer lag spike | Backpressure | Scale consumer group; alert ops team |
| EC-006 | Tenant suspended mid-trip | Graceful shutdown | Complete ongoing trips; block new requests |
| EC-007 | Invalid ODD zone request | Safety rule | Reject booking; suggest nearest valid pickup point |
| EC-008 | Credit balance depleted | Pre-payment check | Block trip booking; redirect to top-up |

---

## 9. Acceptance Criteria (Definition of Done)

### RHS Service
- [ ] Passenger có thể đặt xe và hủy xe thành công.
- [ ] Trip State Machine chuyển đúng trạng thái theo vòng đời.
- [ ] AV-Aware Matching ghép xe dựa trên pin, ODD, loại xe.
- [ ] ETA được cập nhật real-time qua NATS.
- [ ] Ride Pooling hoạt động với ≥ 2 passengers.
- [ ] Rating được ghi nhận sau chuyến đi.

### FPE Service
- [ ] Fare tính đúng theo công thức base + distance + time.
- [ ] Upfront Pricing chốt giá cố định trước chuyến đi.
- [ ] Surge Multiplier hoạt động trong range 1.0x–3.0x.
- [ ] Rate Card áp dụng đúng cho tenant tương ứng.
- [ ] Promotion code giảm giá đúng.

### BMS Service
- [ ] Subscription lifecycle hoạt động: trial → active → expired.
- [ ] Metering counters tăng đúng theo usage thực tế.
- [ ] Invoice tự động tạo cuối kỳ.
- [ ] Quota enforcement chặn đúng khi đạt 100%.
- [ ] Tax tính đúng theo khu vực.

### PAY Service
- [ ] Escrow pre-authorize thành công khi đặt xe.
- [ ] Capture thành công sau khi trip Completed.
- [ ] Duplicate charge bị ngăn bởi idempotency key.
- [ ] Hoàn tiền tự động khi xe trễ > 10 phút.
- [ ] Fraud scoring từ chối/giữ giao dịch rủi ro cao.
- [ ] Multi-gateway routing hoạt động (Stripe, VNPay, MoMo).

### TMS Service
- [ ] Onboarding tự động thành công từ đầu đến cuối.
- [ ] White-label branding áp dụng đúng cho tenant.
- [ ] Cross-tenant data isolation được kiểm chứng.
- [ ] Keycloak SSO hoạt động cho Rider login.
- [ ] Rollback onboarding khi thất bại.

### NCS Service
- [ ] Push Notification gửi thành công qua FCM/APNs.
- [ ] SMS gửi qua Twilio thành công.
- [ ] Critical alert gửi trong < 5 giây.
- [ ] Retry với exponential backoff hoạt động.
- [ ] DLQ chứa đúng message thất bại.
- [ ] Webhook với HMAC signature gửi thành công.

### ABI Service
- [ ] Dashboard hiển thị KPI real-time.
- [ ] Threshold alert kích hoạt đúng khi vi phạm.
- [ ] Heatmap nhu cầu được tạo.
- [ ] Báo cáo PDF/CSV xuất thành công.
- [ ] Scheduled reports gửi đúng lịch.

### MKP Service
- [ ] Plugin được duyệt sau security + performance audit.
- [ ] Tenant cài đặt/gỡ plugin thành công.
- [ ] Revenue share được tính và payout thực hiện.
- [ ] Pre-built connectors (Insurance, Corporate Travel) hoạt động.

---

## 10. Out of Scope (Version 1.0)

- VMS (Vehicle Management System) và AOC (Autonomous Operations Center) — các phân hệ quản lý đội xe (thuộc nhóm khác).
- HML (HD Map & Location) Service — cung cấp bản đồ (phân hệ riêng).
- DPE (Developer Platform & Experience) Service — quản lý API Developer Portal.
- SSC (Security & Compliance) Service — IAM cho vận hành.
- Fleet Optimization Service — thuộc nhóm AI/ML backend.
- Native mobile app (iOS/Android) — frontend riêng.
- Hardware integration (xe AV phần cứng) — phạm vi OEM.
- Chức năng UAV (drone delivery) — roadmap v2.0.
- Multi-region failover architecture — roadmap v2.0.

---

## 11. Technology Stack Summary

| Service | Language | Framework | Primary DB | Cache | Events |
|---------|----------|-----------|------------|-------|--------|
| RHS | Java 17+ | Spring Boot 3 | MongoDB | Redis | Kafka + NATS |
| FPE | Java 17+ | Spring Boot 3 | MongoDB | Redis | Kafka |
| BMS | Java 17+ | Spring Boot 3 | MongoDB + InfluxDB | Redis | Kafka |
| PAY | Java 17+ | Spring Boot 3 | MongoDB | Redis | Kafka |
| TMS | Java 17+ | Spring Boot 3 | MongoDB + S3/MinIO | Redis | Kafka |
| NCS | Java 17+ | Spring Boot 3 | MongoDB | Redis | Kafka |
| ABI | Java 17+ | Spring Boot 3 | Elasticsearch + InfluxDB + MongoDB | — | Kafka (consumer) |
| MKP | Java 17+ | Spring Boot 3 | MongoDB + S3/MinIO | Redis | — |

---

## 12. Integration Map (Service Dependencies)

```
RHS ──calls──► FPE (fare estimation + final fare)
RHS ──calls──► PAY (escrow + capture)
RHS ──calls──► NCS (ETA updates, trip status push)
RHS ──publishes──► Kafka [ride-events]

FPE ──queries──► HML (zone pricing, distance)
FPE ──listens──► Fleet Optimization (demand heatmaps)
FPE ──publishes──► Kafka [fare-events]

BMS ──calls──► PAY (invoice payment deduction)
BMS ──calls──► TMS (tenant config)
BMS ──calls──► NCS (invoice alerts, quota alerts)
BMS ──publishes──► Kafka [billing-events, metering-events]

PAY ──integrates──► Stripe, VNPay, MoMo, VNPT Money, Viettel Money
PAY ──publishes──► Kafka [payment-events]

TMS ──calls──► SSC (RBAC setup)
TMS ──calls──► BMS (subscription setup)
TMS ──calls──► DPE (API key generation)
TMS ──calls──► VMS (fleet allocation)
TMS ──publishes──► Kafka [tenant-events]

NCS ──listens──► Kafka [all events]
NCS ──integrates──► Firebase FCM/APNs, SendGrid, Twilio

ABI ──listens──► Kafka [ride, payment, billing events]
ABI ──queries──► RHS (trip data), BMS (revenue data)

MKP ──calls──► TMS (plugin activation per tenant)
MKP ──calls──► DPE (API flow configuration)
MKP ──calls──► PAY (partner payouts)
```

---

*Document Version: 1.0.0 | VNPT AV Platform — Services Provider Group PRD*
