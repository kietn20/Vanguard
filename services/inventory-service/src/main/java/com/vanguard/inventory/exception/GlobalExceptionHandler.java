package com.vanguard.inventory.exception;

import java.util.stream.Collectors;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.validation.FieldError;
import org.springframework.web.bind.MethodArgumentNotValidException;
import org.springframework.web.bind.annotation.ExceptionHandler;
import org.springframework.web.bind.annotation.RestControllerAdvice;
import org.springframework.web.context.request.WebRequest;

import com.vanguard.inventory.dto.ErrorResponse;





/**
 * Global exception handler for all REST controllers.
 *
 * @RestControllerAdvice applies to all @RestController classes.
 *                       Catches exceptions and converts them to proper HTTP
 *                       responses.
 */
@RestControllerAdvice
public class GlobalExceptionHandler {

    private static final Logger logger = LoggerFactory.getLogger(GlobalExceptionHandler.class);

    // handle PartNotFoundException (404 Not Found)
    @ExceptionHandler(PartNotFoundException.class)
    public ResponseEntity<ErrorResponse> handlePartNotFound(PartNotFoundException ex, WebRequest request) {

        logger.warn("Part not found: {}", ex.getPartNumber());

        ErrorResponse error = ErrorResponse.of(
                HttpStatus.NOT_FOUND.value(),
                "Not Found",
                ex.getMessage(),
                request.getDescription(false).replace("uri=", ""));

        return ResponseEntity.status(HttpStatus.NOT_FOUND).body(error);
    }



    // handle InsufficientStockException (400 Bad Request)
    @ExceptionHandler(InsufficientStockException.class)
    public ResponseEntity<ErrorResponse> handleInsufficientStock(InsufficientStockException ex, WebRequest request) {

        logger.warn("Insufficient stock: {}", ex.getMessage());

        ErrorResponse error = ErrorResponse.of(
                HttpStatus.BAD_REQUEST.value(),
                "Bad Request",
                ex.getMessage(),
                request.getDescription(false).replace("uri=", ""));

        return ResponseEntity.status(HttpStatus.BAD_REQUEST).body(error);
    }


    // handle validation errors (400 Bad Request)
    @ExceptionHandler(MethodArgumentNotValidException.class)
    public ResponseEntity<ErrorResponse> handleValidationErrors(MethodArgumentNotValidException ex, WebRequest request) {

        String errors = ex.getBindingResult()
                .getFieldErrors()
                .stream()
                .map(FieldError::getDefaultMessage)
                .collect(Collectors.joining(", "));

        logger.warn("Validation error: {}", errors);

        ErrorResponse error = ErrorResponse.of(
                HttpStatus.BAD_REQUEST.value(),
                "Validation Failed",
                errors,
                request.getDescription(false).replace("uri=", ""));

        return ResponseEntity.status(HttpStatus.BAD_REQUEST).body(error);
    }


    // handle all other exceptions (500 Internal Server Error)
    @ExceptionHandler(Exception.class)
    public ResponseEntity<ErrorResponse> handleGeneralException(
            Exception ex,
            WebRequest request) {

        logger.error("Unexpected error: ", ex);

        ErrorResponse error = ErrorResponse.of(
                HttpStatus.INTERNAL_SERVER_ERROR.value(),
                "Internal Server Error",
                "An unexpected error occurred.",
                request.getDescription(false).replace("uri=", ""));

        return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR).body(error);
    }
}
