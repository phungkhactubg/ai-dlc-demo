package com.vnpt.avplatform.bms.config;

/**
 * Subscription plan definitions (FR-BMS-001).
 *
 * <p>The BMS supports three subscription tiers:</p>
 * <ul>
 *   <li>{@code STARTER} — entry-level plan with limited quotas</li>
 *   <li>{@code PROFESSIONAL} — mid-tier plan for growing fleets</li>
 *   <li>{@code ENTERPRISE} — full-feature plan with custom quotas</li>
 * </ul>
 *
 * <p>Each plan can be billed on a {@code MONTHLY} or {@code ANNUAL} cycle.
 * Annual billing provides a discount (configured separately in plan catalogue).</p>
 */
public final class SubscriptionPlanConfig {

    /**
     * Available subscription plan tiers.
     */
    public enum Plan {
        /** Entry-level plan — limited vehicles, trips, and API calls. */
        STARTER,
        /** Professional plan — expanded quotas for mid-size operations. */
        PROFESSIONAL,
        /** Enterprise plan — unlimited or custom quotas with SLA guarantees. */
        ENTERPRISE
    }

    /**
     * Billing cycle options for a subscription.
     */
    public enum BillingCycle {
        /** Billed every calendar month. */
        MONTHLY,
        /** Billed annually; typically discounted vs. 12 × MONTHLY. */
        ANNUAL
    }

    /**
     * Lifecycle states of a subscription.
     */
    public enum SubscriptionStatus {
        /** Free trial period; full features, no charge. */
        TRIAL,
        /** Active paid subscription within the billing period. */
        ACTIVE,
        /** Billing period has ended and was not renewed. */
        EXPIRED,
        /** Temporarily suspended due to policy violation or non-payment. */
        SUSPENDED,
        /** Explicitly cancelled by the tenant; access revoked at period end. */
        CANCELLED,
        /** Payment failed; grace period active before suspension. */
        PAST_DUE
    }

    private SubscriptionPlanConfig() {
        throw new UnsupportedOperationException("SubscriptionPlanConfig is a constants class");
    }
}
