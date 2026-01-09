package com.vanguard.inventory.dto;

import java.time.Instant;

// standardized error response for all API errors
public record ErrorResponse(
        int status,
        String error,
        String message,
        String path,
        Instant timestamp)
{
    public static ErrorResponse of(int status, String error, String message, String path) {
        return new ErrorResponse(
                status,
                error,
                message,
                path,
                Instant.now());
    }
}
