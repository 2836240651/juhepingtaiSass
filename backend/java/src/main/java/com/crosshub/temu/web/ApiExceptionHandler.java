package com.crosshub.temu.web;

import org.springframework.http.HttpStatus;
import org.springframework.web.bind.annotation.ExceptionHandler;
import org.springframework.web.bind.annotation.RestControllerAdvice;
import org.springframework.web.server.ResponseStatusException;

import java.util.Map;

@RestControllerAdvice
public class ApiExceptionHandler {
    @ExceptionHandler(ResponseStatusException.class)
    public Map<String, Object> handle(ResponseStatusException ex) {
        return Map.of(
                "code", ex.getStatusCode().value(),
                "msg", ex.getReason() == null ? "请求失败" : ex.getReason()
        );
    }

    @ExceptionHandler(Exception.class)
    public Map<String, Object> handleGeneric(Exception ex) {
        return Map.of(
                "code", HttpStatus.INTERNAL_SERVER_ERROR.value(),
                "msg", ex.getMessage() == null ? "服务器错误" : ex.getMessage()
        );
    }
}
