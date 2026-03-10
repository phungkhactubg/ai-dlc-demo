package com.vnpt.avplatform.tms.models.entity;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;
import org.springframework.data.mongodb.core.mapping.Field;

import java.math.BigDecimal;

@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class CancellationPolicy {

    @Field("free_cancel_window_min")
    private int freeCancelWindowMin;

    @Field("fee_per_min_after_dispatch")
    private BigDecimal feePerMinAfterDispatch;
}
