package com.vnpt.avplatform.tms.config;

import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.scheduling.annotation.EnableAsync;
import org.springframework.scheduling.concurrent.ThreadPoolTaskExecutor;

import java.util.concurrent.Executor;

@Slf4j
@Configuration
@EnableAsync
public class SagaConfig {

    public static final int STEP_TIMEOUT_SECONDS = 30;
    public static final int SAGA_TIMEOUT_SECONDS = 120;

    @Value("${saga.async.core-pool-size:5}")
    private int corePoolSize;

    @Value("${saga.async.max-pool-size:10}")
    private int maxPoolSize;

    @Value("${saga.async.queue-capacity:50}")
    private int queueCapacity;

    @Bean(name = "sagaExecutor")
    public Executor sagaExecutor() {
        ThreadPoolTaskExecutor executor = new ThreadPoolTaskExecutor();
        executor.setCorePoolSize(corePoolSize);
        executor.setMaxPoolSize(maxPoolSize);
        executor.setQueueCapacity(queueCapacity);
        executor.setThreadNamePrefix("saga-executor-");
        executor.setWaitForTasksToCompleteOnShutdown(true);
        executor.setAwaitTerminationSeconds(60);
        executor.initialize();
        log.info("Saga executor initialized: corePoolSize={}, maxPoolSize={}, queueCapacity={}", corePoolSize, maxPoolSize, queueCapacity);
        return executor;
    }
}
