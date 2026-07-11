package com.crosshub.common;

import java.util.LinkedHashMap;
import java.util.Map;

public final class ApiResult {
    private ApiResult() {}

    public static Map<String, Object> ok(Object data) {
        Map<String, Object> res = new LinkedHashMap<>();
        res.put("code", 0);
        res.put("data", data);
        return res;
    }

    public static Map<String, Object> conflict(int code, String message, String errorCode, Object data) {
        Map<String, Object> res = new LinkedHashMap<>();
        res.put("code", code);
        res.put("msg", message);
        res.put("error_code", errorCode);
        res.put("data", data);
        return res;
    }

    public static Map<String, Object> error(int httpCode, String errorCode, String message) {
        Map<String, Object> res = new LinkedHashMap<>();
        res.put("code", httpCode);
        res.put("error_code", errorCode);
        res.put("msg", message);
        return res;
    }
}
