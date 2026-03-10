package com.vnpt.avplatform.ncs.config;

import com.google.auth.oauth2.GoogleCredentials;
import com.google.firebase.FirebaseApp;
import com.google.firebase.FirebaseOptions;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.boot.autoconfigure.condition.ConditionalOnProperty;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

import java.io.FileInputStream;
import java.io.IOException;

/**
 * Firebase Admin SDK configuration for FCM push notification delivery (FR-NCS-002).
 *
 * <p>The Firebase app is only initialized when {@code firebase.enabled=true}. In local
 * development ({@code firebase.enabled=false}) no credentials are required and Firebase
 * is completely bypassed — the push notification adapter will log a warning instead of
 * attempting delivery.</p>
 *
 * <p>To enable Firebase:</p>
 * <ol>
 *   <li>Download the service account JSON from Firebase Console.</li>
 *   <li>Set {@code FIREBASE_CREDENTIALS_PATH} environment variable to the file path.</li>
 *   <li>Set {@code FIREBASE_ENABLED=true}.</li>
 * </ol>
 */
@Slf4j
@Configuration
public class FirebaseConfig {

    /**
     * Initialises the {@link FirebaseApp} bean using the service account credentials file.
     *
     * <p>This bean is only created when {@code firebase.enabled=true} is configured.
     * Returns {@code null} (and logs a warning) when the credentials path is empty,
     * preventing startup failure in environments where Firebase is not configured.</p>
     *
     * @param credentialsPath path to the Firebase service account JSON file
     * @return initialised {@link FirebaseApp}, or {@code null} if credentials are not set
     * @throws IOException if the credentials file cannot be read
     */
    @Bean
    @ConditionalOnProperty(name = "firebase.enabled", havingValue = "true", matchIfMissing = false)
    public FirebaseApp firebaseApp(
            @Value("${firebase.credentials-path:}") String credentialsPath) throws IOException {

        if (credentialsPath == null || credentialsPath.isBlank()) {
            log.warn("firebase.enabled=true but firebase.credentials-path is not set — "
                    + "Firebase push notifications will be unavailable");
            return null;
        }

        if (!FirebaseApp.getApps().isEmpty()) {
            log.info("FirebaseApp already initialised; reusing existing instance");
            return FirebaseApp.getInstance();
        }

        log.info("Initialising Firebase Admin SDK from credentials: {}", credentialsPath);

        try (FileInputStream serviceAccount = new FileInputStream(credentialsPath)) {
            FirebaseOptions options = FirebaseOptions.builder()
                    .setCredentials(GoogleCredentials.fromStream(serviceAccount))
                    .build();
            FirebaseApp app = FirebaseApp.initializeApp(options);
            log.info("Firebase Admin SDK initialised successfully: appName={}", app.getName());
            return app;
        }
    }
}
