import os
import requests
import json
import logging
import traceback

# Cấu hình logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)

def call_gemini_api(prompt, gemini_key, max_tokens=8192):
    """Gọi Gemini API để tạo câu hỏi"""
    try:
        if not gemini_key:
            logger.error("Chưa có Gemini API Key")
            return "Lỗi: Chưa có Gemini API Key"
        
        logger.info(f"Calling Gemini API with prompt length: {len(prompt)}")
        
        # Cắt bớt prompt nếu quá dài (Gemini có giới hạn đầu vào)
        if len(prompt) > 30000:
            logger.warning(f"Prompt too long ({len(prompt)} chars), truncating")
            prompt = prompt[:30000]
        
        GEMINI_API_URL = (
            "https://generativelanguage.googleapis.com/v1beta/models/"
            "gemini-2.0-flash:generateContent?key=" + gemini_key
        )
        
        payload = {
            "contents": [{
                "parts": [{
                    "text": prompt
                }]
            }],
            "generationConfig": {
                "temperature": 0.7,
                "maxOutputTokens": max_tokens,
            }
        }
        
        headers = {"Content-Type": "application/json"}
        logger.info("Sending request to Gemini API")
        resp = requests.post(GEMINI_API_URL, json=payload, headers=headers, timeout=(10, 180))
        
        logger.info(f"Gemini API response status: {resp.status_code}")
        
        if resp.status_code == 200:
            data = resp.json()
            if "candidates" in data and len(data["candidates"]) > 0:
                candidate = data["candidates"][0]
                if "content" in candidate and "parts" in candidate["content"]:
                    result = candidate["content"]["parts"][0].get("text", "")
                    if result.strip():
                        logger.info(f"Received response with {len(result)} characters")
                        return result
            
            logger.error("Không thể trích xuất được kết quả từ Gemini API")
            return "Lỗi: Không thể trích xuất được kết quả từ Gemini API."
        else:
            logger.error(f"Gemini API error: {resp.status_code} - {resp.text[:200]}")
            return f"Lỗi: Gemini API - HTTP {resp.status_code} - {resp.text[:200]}"
    
    except Exception as e:
        logger.error(f"Error calling Gemini API: {str(e)}")
        logger.error(traceback.format_exc())
        return f"Lỗi: Gọi Gemini API thất bại: {e}"
