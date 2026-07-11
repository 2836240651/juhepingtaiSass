package com.crosshub.amazon.service;

import java.util.Map;

public interface AmazonWriteService {
    Map<String, Object> replyMessage(String id, String templateId, String note);
    Map<String, Object> handleReview(String id, String note);
    Map<String, Object> acknowledgeCase(String id, String note);
    Map<String, Object> shipOutbound(String id, String trackingNo);
}
