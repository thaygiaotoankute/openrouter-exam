import os
import base64
import requests
import xml.etree.ElementTree as ET
from Crypto.PublicKey import RSA
from Crypto.Cipher import PKCS1_v1_5

def load_rsa_private_key_from_xml(xml_str):
    """Load RSA private key từ định dạng XML"""
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
        raise ValueError(f"Error decrypting API key: {str(e)}")

def get_openrouter_token():
    """Get API key from GitHub (tận dụng từ get_mineru_token)"""
    # Ưu tiên dùng biến môi trường để Vercel có thể cấu hình
    if os.environ.get('OPENROUTER_API_KEY'):
        return os.environ.get('OPENROUTER_API_KEY')
    
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
        rsa_private_key = load_rsa_private_key_from_xml(PRIVATE_KEY_XML)
        # Thay đổi URL để lấy API key của OpenRouter từ GitHub repo
        github_url = "https://raw.githubusercontent.com/thayphuctoan/pconvert/refs/heads/main/openrouter-key"
        response = requests.get(github_url, timeout=10)
        response.raise_for_status()
        
        encrypted_keys = [line.strip() for line in response.text.splitlines() if line.strip()]
        if not encrypted_keys:
            raise ValueError("No encrypted API key found")
        
        token = decrypt_api_key(encrypted_keys[0], rsa_private_key)
        if not token:
            raise ValueError("Decrypted API key is empty")
        return token
    except Exception as e:
        raise Exception(f"Error getting API key: {str(e)}")

def call_openrouter_api(prompt, max_tokens=4000, temperature=0.7):
    """Call OpenRouter API using the decrypted token"""
    api_key = get_openrouter_token()
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
    
    try:
        response = requests.post(api_url, headers=headers, json=data, timeout=180)
        response.raise_for_status()
        result = response.json()
        
        if 'choices' in result and len(result['choices']) > 0:
            return result['choices'][0]['message']['content']
        else:
            return ""
    except Exception as e:
        print(f"Error calling OpenRouter API: {str(e)}")
        raise
