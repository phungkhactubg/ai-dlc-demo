package com.example.examplefeature.exception;

/**
 * Base exception for all example feature exceptions.
 * All custom exceptions should extend this class.
 */
public abstract class ExampleException extends RuntimeException {

    private final String errorCode;

    public ExampleException(String message) {
        super(message);
        this.errorCode = this.getClass().getSimpleName();
    }

    public ExampleException(String message, Throwable cause) {
        super(message, cause);
        this.errorCode = this.getClass().getSimpleName();
    }

    public String getErrorCode() {
        return errorCode;
    }
}

/**
 * Exception thrown when a resource is not found.
 * Typically results in HTTP 404 response.
 */
public class ResourceNotFoundException extends ExampleException {

    private final String resourceType;
    private final String resourceId;

    public ResourceNotFoundException(String resourceType, String resourceId) {
        super(String.format("%s not found: %s", resourceType, resourceId));
        this.resourceType = resourceType;
        this.resourceId = resourceId;
    }

    public String getResourceType() {
        return resourceType;
    }

    public String getResourceId() {
        return resourceId;
    }
}

/**
 * Exception thrown when a business rule is violated.
 * Typically results in HTTP 400 response.
 */
public class BusinessException extends ExampleException {

    public BusinessException(String message) {
        super(message);
    }

    public BusinessException(String message, Throwable cause) {
        super(message, cause);
    }
}

/**
 * Exception thrown when a duplicate resource is detected.
 * Typically results in HTTP 409 response.
 */
public class DuplicateResourceException extends ExampleException {

    private final String resourceType;
    private final String identifier;

    public DuplicateResourceException(String resourceType, String identifier) {
        super(String.format("%s already exists: %s", resourceType, identifier));
        this.resourceType = resourceType;
        this.identifier = identifier;
    }

    public String getResourceType() {
        return resourceType;
    }

    public String getIdentifier() {
        return identifier;
    }
}

/**
 * Exception thrown when invalid input is provided.
 * Typically results in HTTP 400 response.
 */
public class InvalidInputException extends ExampleException {

    private final String fieldName;
    private final String fieldValue;

    public InvalidInputException(String fieldName, String fieldValue, String reason) {
        super(String.format("Invalid value for field '%s': %s. Reason: %s", fieldName, fieldValue, reason));
        this.fieldName = fieldName;
        this.fieldValue = fieldValue;
    }

    public String getFieldName() {
        return fieldName;
    }

    public String getFieldValue() {
        return fieldValue;
    }
}

/**
 * Exception thrown when an operation is attempted in an invalid state.
 * Typically results in HTTP 400 response.
 */
public class InvalidStateException extends ExampleException {

    private final String currentState;
    private final String requiredState;

    public InvalidStateException(String currentState, String requiredState) {
        super(String.format("Invalid state. Current: %s, Required: %s", currentState, requiredState));
        this.currentState = currentState;
        this.requiredState = requiredState;
    }

    public String getCurrentState() {
        return currentState;
    }

    public String getRequiredState() {
        return requiredState;
    }
}
