package com.vnpt.avplatform.tms.exception;

public class FileSizeExceededException extends RuntimeException {
    public FileSizeExceededException(String message) {
        super(message);
    }
}
