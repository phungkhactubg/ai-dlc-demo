# Senior Java Backend Skeleton

This folder contains a reference implementation (skeleton) of a feature module following the **Expert Java Backend Developer** skill guidelines.

## Directory Structure

```
com.example.examplefeature/
├── model/         # Domain entities, DTOs, enums, value objects
├── repository/    # Spring Data repositories
├── service/       # Business logic (interfaces & implementations)
├── controller/    # REST controllers
├── adapter/       # External service integrations
├── config/        # Spring configuration classes
└── exception/     # Custom exceptions
```

## How to use

1.  **Copy**: Copy the `com/example/examplefeature` folder to your project's `src/main/java/com/example/<your_feature>`.
2.  **Rename**: Rename files and packages to match your feature name.
3.  **Implement**:
    *   Define your domain models in `model/`.
    *   Define `Service` and `Repository` interfaces first.
    *   Implement Repository (Spring Data JPA/MongoDB).
    *   Implement Service logic with `@Transactional`.
    *   Implement Controller handlers with proper validation.
    *   Register routes in the controller.
4.  **Wire**: Add the feature to your Spring Boot application context.

## Key Principles Demonstrated

*   **Interface-First**: Services depend on `Repository` interface, Controllers depend on `Service` interface.
*   **Constructor Injection**: All dependencies are `final` and injected via constructor (NO field injection).
*   **Transaction Boundaries**: `@Transactional` is properly configured on service methods.
*   **Exception Handling**: Custom exceptions with `@ControllerAdvice` for global error handling.
*   **Bean Validation**: Jakarta Bean Validation annotations on DTOs.
*   **Null Safety**: Use of `Optional<T>` and `@NonNull`/`@Nullable` annotations.
*   **Lombok Usage**: Proper use of `@RequiredArgsConstructor`, `@Data`, `@Value`, `@Builder`.
*   **Logging**: Structured logging with SLF4J (no sensitive data).

## Technology Stack

*   **Java**: 17+ (Records, Pattern Matching, Sealed Classes)
*   **Spring Boot**: 3.2+ (Spring Web, Spring Data, Spring Security)
*   **Build**: Maven 3.9+ or Gradle 8.x
*   **Database**: PostgreSQL (Spring Data JPA) or MongoDB (Spring Data MongoDB)
*   **Validation**: Jakarta Bean Validation 3.0+
*   **Testing**: JUnit 5, Mockito, TestContainers
*   **Lombok**: For boilerplate reduction
