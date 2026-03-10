# PROJECT OVERVIEW — VNPT AV Platform: Services Provider Group

**Project**: VNPT AV Platform — Services Provider Group
**Version**: 1.0.0
**Status**: Phase 2 Complete — Architecture Approved
**Last Updated**: 2026-03-06

---

## 🎯 North Star Goal

Build the **Services Provider** group — the commercial engine of the VNPT AV Platform — enabling autonomous vehicle ride-hailing, dynamic pricing, multi-tenant billing, secure payment processing, enterprise onboarding, real-time notifications, business intelligence, and a marketplace ecosystem.

---

## 📊 Success KPIs

| KPI | Target |
|-----|--------|
| API P95 Latency (Read) | < 200ms |
| API P95 Latency (Write) | < 500ms |
| Concurrent Trips | ≥ 10,000 |
| Ride Completion Rate | > 95% |
| Payment Success Rate | > 99.5% |
| System Uptime | ≥ 99.9% |
| Average Wait Time | < 5 minutes |
| Critical Notification Delivery | < 5 seconds |
| ETA Accuracy | < 2 minutes deviation |

---

## 🏗️ SDLC Progress

| Phase | Status | Deliverable |
|-------|--------|-------------|
| Phase 1: PRD Analysis | ✅ Complete | `project-documentation/PRD.md` |
| Phase 2: Architecture Design | ✅ Complete | `project-documentation/ARCHITECTURE_SPEC.md` |
| Phase 3: Master Plan | 🔲 Pending | `project-documentation/MASTER_PLAN.md` |
| Phase 4: SRS Deep Dive | 🔲 Pending | `project-documentation/srs/SRS_*.md` |
| Phase 5: Detail Plans | 🔲 Pending | `project-documentation/plans/DETAIL_PLAN_*.md` |
| Phase 6: Development | 🔲 Pending | Implementation code |
| Phase 7: Review & Hardening | 🔲 Pending | Code review reports |

---

## 📁 Documentation Index

| Document | Path | Purpose |
|----------|------|---------|
| Product Requirements Document | [`PRD.md`](./PRD.md) | Business requirements — What to build |
| Architecture Specification | [`ARCHITECTURE_SPEC.md`](./ARCHITECTURE_SPEC.md) | Technical blueprint — How to build it |
| Master Plan | `MASTER_PLAN.md` *(pending)* | Implementation roadmap |
| Source Requirements | [`requirement-project.txt`](./requirement-project.txt) | Original raw requirements |

---

## 🔧 Service Portfolio

| # | Service | Code | Status |
|---|---------|------|--------|
| 1 | Ride-Hailing Service | RHS | Design complete |
| 2 | Fare & Pricing Engine | FPE | Design complete |
| 3 | Billing & Subscription Management | BMS | Design complete |
| 4 | Payment Processing | PAY | Design complete |
| 5 | Tenant & Organization Management | TMS | Design complete |
| 6 | Notification & Communication | NCS | Design complete |
| 7 | Analytics & Business Intelligence | ABI | Design complete |
| 8 | Marketplace & Integration Hub | MKP | Design complete |

---

## ⚠️ Key Architecture Decisions

| ADR | Decision | Rationale |
|-----|----------|-----------|
| ADR-001 | Separate MongoDB namespaces per service | Service autonomy, independent scaling |
| ADR-002 | Kafka (durable) + NATS (real-time) | Best-of-breed for each use case |
| ADR-003 | Escrow payment model | Financial safety — no charge on failed trips |
| ADR-005 | Saga pattern for tenant onboarding | Atomic distributed transaction without 2PC |
| ADR-007 | Kong API Gateway as single entry point | Centralized JWT validation + rate limiting |
| ADR-008 | Java 17+ / Spring Boot 3.x | Team proficiency, ecosystem maturity |

---

## 🚨 Risk Register

| Risk | Impact | Mitigation |
|------|--------|------------|
| Kafka consumer lag under peak load | High | HPA on consumer group pods + lag-based autoscaling |
| Payment gateway downtime | Critical | Multi-gateway fallback routing in PAY GatewayRouter |
| Cross-tenant data leak | Critical | `BaseMongoRepository.withTenant()` mandatory filter + integration tests |
| Onboarding Saga partial failure | High | Compensating transactions + rollback tested in integration suite |
| ETA ML model latency | Medium | Fallback to rule-based ETA (EC-004) |

---

## 🔗 Decision Log

| Date | Decision | Owner | Notes |
|------|----------|-------|-------|
| 2026-03-06 | PRD v1.0.0 approved | PM/BA Orchestrator | Based on `requirement-project.txt` |
| 2026-03-06 | ARCHITECTURE_SPEC v1.0.0 approved | Solutions Architect | Phase 2 `/link-arch` complete |

---

*Next Action*: Run `/plan-master` to generate `MASTER_PLAN.md` (Phase 3).
