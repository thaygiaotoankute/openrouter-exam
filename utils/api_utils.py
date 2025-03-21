import os
import base64
import requests
import json
import xml.etree.ElementTree as ET
from Crypto.PublicKey import RSA
from Crypto.Cipher import PKCS1_v1_5
import logging
import traceback

# Cấu hình logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)

def load_rsa_private_key_from_xml(xml_str):
    """Load RSA private key từ định dạng XML"""
    try:
        root = ET.fromstring(xml_str)
        def get_int(tag):
            text = root.find(tag).text
            return int.from_bytes(base64.b64decode(text), 'big')
        n = get_int('Modulus')
        e = get_int('Exponent')
        d = get_int('D')
        p = get_int('P')
        q = get_int('Q')
        key = RSA.construct((n, e, d, p, q))
        return key
    except Exception as e:
        logger.error(f"Error loading RSA key from XML: {str(e)}")
        logger.error(traceback.format_exc())
        raise

def decrypt_api_key(encrypted_key_base64, rsa_private_key):
    """Decrypt API key"""
    try:
        cipher = PKCS1_v1_5.new(rsa_private_key)
        encrypted_data = base64.b64decode(encrypted_key_base64)
        decrypted = cipher.decrypt(encrypted_data, None)
        
        if not decrypted:
            raise ValueError("Decryption failed")
        return decrypted.decode('utf-8')
    except Exception as e:
        logger.error(f"Error decrypting API key: {str(e)}")
        logger.error(traceback.format_exc())
        raise ValueError(f"Error decrypting API key: {str(e)}")

def get_openrouter_token():
    """Get API key bằng phương thức giải mã RSA từ GitHub"""
    logger.info("Fetching encrypted API key from GitHub")
    PRIVATE_KEY_XML = """<RSAKeyValue>
<Modulus>pWVItQwZ7NCPcBhSL4rqJrwh4OQquiPVtqTe4cqxO7o+UjYNzDPfLkfKAvR8k9ED4lq2TU11zEj8p2QZAM7obUlK4/HVexzfZd0qsXlCy5iaWoTQLXbVdzjvkC4mkO5TaX3Mpg/+p4oZjk1iS68tQFmju5cT19dcsPh554ICk8U=</Modulus>
<Exponent>AQAB</Exponent>
<P>0ZWwsKa9Vw9BJAsRaW4eV60i6Z+R6z9LNSgjNn4pYH2meZtGUbmJVowRv7EM5sytouB5EMru7sQbRHEQ7nrwSw==</P>
<Q>ygZQWNkUgfHhHBataXvYLxWgPB5UZTWogN8Mb33LT4rq7I5P1GX3oWtYF2AdmChX8Lq3Ms/A/jBhqYomhYOiLw==</Q>
<DP>qS9VOsTfA3Bk/VuR6rHh/JTfIgiWGnk1lOuZwVuGu0WzJWebFE3Z9+uKSFv8NjPz1w+tq0imKEhWWqGLMXg8kQ==</DP>
<DQ>UCtXQRrMB5EL6tCY+k4aCP1E+/ZxOUSk3Jcm4SuDPcp71WnYBgp8zULCz2vl8pa35yDBSFmnVXevmc7n4H3PIw==</DQ>
<InverseQ>Qm9RjBhxANWyIb8I28vjGz+Yb9CnunWxpHWbfRo1vF+Z38WB7dDgLsulAXMGrUPQTeG6K+ot5moeZ9ZcAc1Hzw==</InverseQ>
<D>F9lU9JY8HsOsCzPWlfhn7xHtqKn95z1HkcCQSuqZR82BMwWMU8efBONhI6/xTrcy4i7GXrsuozhbBiAO4ujy5qPytdFemLuqjwFTyvllkcOy3Kbe0deczxnPPCwmSMVKsYInByJoBP3JYoyVAj4bvY3UqZJtw+2u/OIOhoBe33k=</D>
</RSAKeyValue>"""
    
    try:
        # Tải khóa RSA private key
        logger.info("Loading RSA private key from XML")
        rsa_private_key = load_rsa_private_key_from_xml(PRIVATE_KEY_XML)
        
        # Lấy encrypted key từ GitHub
        github_url = "https://raw.githubusercontent.com/thayphuctoan/pconvert/refs/heads/main/openrouter-key"
        logger.info(f"Sending request to GitHub URL: {github_url}")
        
        response = requests.get(github_url, timeout=30)  # Tăng timeout lên 30 giây
        logger.info(f"GitHub response status code: {response.status_code}")
        
        # Nếu response thành công
        if response.status_code == 200:
            logger.info(f"GitHub response content length: {len(response.text)} characters")
            
            # Lọc các dòng không trống
            encrypted_keys = [line.strip() for line in response.text.splitlines() if line.strip()]
            logger.info(f"Found {len(encrypted_keys)} encrypted keys")
            
            if not encrypted_keys:
                logger.error("No encrypted API key found in the GitHub content")
                raise ValueError("No encrypted API key found")
            
            # Lấy key đầu tiên và giải mã
            logger.info("Decrypting the first encrypted key")
            token = decrypt_api_key(encrypted_keys[0], rsa_private_key)
            
            if not token:
                logger.error("Decrypted API key is empty")
                raise ValueError("Decrypted API key is empty")
            
            # Kiểm tra key có hợp lệ không (có thể cải thiện thêm)
            if len(token) < 10:  # Một API key thường dài hơn 10 ký tự
                logger.warning(f"Decrypted API key seems too short: {len(token)} characters")
            
            logger.info(f"Successfully obtained API key from GitHub (length: {len(token)} characters)")
            return token
        else:
            logger.error(f"Failed to get content from GitHub. Status code: {response.status_code}")
            raise Exception(f"GitHub request failed with status code {response.status_code}")
            
    except requests.exceptions.RequestException as e:
        logger.error(f"Request to GitHub failed: {str(e)}")
        logger.error(traceback.format_exc())
        raise Exception(f"Request to GitHub failed: {str(e)}")
    except Exception as e:
        logger.error(f"Error getting API key: {str(e)}")
        logger.error(traceback.format_exc())
        raise Exception(f"Error getting API key: {str(e)}")

def call_openrouter_api(prompt, max_tokens=4000, temperature=0.7):
    """Call OpenRouter API using the decrypted token"""
    logger.info(f"Calling OpenRouter API with prompt length: {len(prompt)}")
    
    try:
        # Lấy API key thông qua giải mã RSA
        try:
            api_key = get_openrouter_token()
            logger.info("Successfully retrieved API key for OpenRouter")
        except Exception as e:
            logger.error(f"Failed to get OpenRouter API key: {str(e)}")
            return f"Lỗi lấy API key: {str(e)}"
        
        api_url = "https://openrouter.ai/api/v1/chat/completions"
        model = "deepseek/deepseek-r1-zero:free"  # Hoặc model khác theo nhu cầu
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
            "HTTP-Referer": "https://exam-generator-app.com",  # Thay bằng domain thực tế
            "X-Title": "Exam Generator"  # Tên ứng dụng
        }
        
        data = {
            "model": model,
            "messages": [
                {"role": "user", "content": prompt}
            ],
            "max_tokens": max_tokens,
            "temperature": temperature
        }
        
        logger.info(f"Sending request to OpenRouter API for model: {model}")
        
        try:
            response = requests.post(api_url, headers=headers, json=data, timeout=180)
            logger.info(f"OpenRouter API response status code: {response.status_code}")
            
            # Thêm logging chi tiết hơn
            if response.status_code != 200:
                logger.error(f"OpenRouter API error: {response.status_code}")
                logger.error(f"Response content: {response.text[:500]}")
                return f"Lỗi từ OpenRouter API: Status code {response.status_code}, {response.text[:200]}"
            
            result = response.json()
            
            if 'choices' in result and len(result['choices']) > 0:
                content = result['choices'][0]['message']['content']
                logger.info(f"Received response with {len(content)} characters")
                return content
            else:
                logger.warning("Empty or invalid response from OpenRouter API")
                logger.warning(f"Response: {result}")
                return f"Phản hồi không hợp lệ từ OpenRouter API: {json.dumps(result)[:200]}"
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Network error requesting OpenRouter API: {str(e)}")
            return f"Lỗi kết nối đến OpenRouter API: {str(e)}"
            
    except Exception as e:
        logger.error(f"Error calling OpenRouter API: {str(e)}")
        logger.error(traceback.format_exc())
        return f"Lỗi gọi OpenRouter API: {str(e)}"
