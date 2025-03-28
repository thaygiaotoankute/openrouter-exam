from flask import Flask, request, jsonify, render_template, send_from_directory
import os
import json
import sys
import logging
import traceback

# Cấu hình logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')

# Thêm thư mục gốc vào path để import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.api_utils import call_gemini_api

app = Flask(__name__, 
          template_folder=os.path.join(os.path.dirname(os.path.dirname(__file__)), "templates"),
          static_folder=os.path.join(os.path.dirname(os.path.dirname(__file__)), "static"))

# Route chính - hiển thị trang web
@app.route('/', methods=['GET'])
def index():
    return render_template('index.html')

# API lấy dữ liệu chủ đề
@app.route('/api/topics', methods=['GET'])
def get_topics():
    try:
        app.logger.info("Getting topics data")
        
        # Thử nhiều đường dẫn khác nhau để tìm file
        possible_paths = [
            os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "topics_data.json"),
            os.path.join("data", "topics_data.json"),
            os.path.join("/var/task", "data", "topics_data.json"),
            os.path.join(os.getcwd(), "data", "topics_data.json")
        ]
        
        for path in possible_paths:
            app.logger.info(f"Trying path: {path}")
            if os.path.exists(path):
                app.logger.info(f"File found at: {path}")
                with open(path, 'r', encoding='utf-8') as f:
                    topics = json.load(f)
                return jsonify(topics)
            else:
                app.logger.info(f"File not found at: {path}")
        
        # Nếu không tìm thấy file, thử hard-code một phiên bản đơn giản
        app.logger.warning("Using hardcoded topics as fallback")
        fallback_topics = {
            "Lớp 10": {
                "ĐẠI SỐ": {
                    "1. Hàm số và đồ thị": {
                        "Hàm số": {
                            "Nhận biết": [
                                "Nhận biết được khái niệm hàm số",
                                "Hiểu được cách biểu diễn hàm số"
                            ],
                            "Thông hiểu": [
                                "Phân biệt được các loại hàm số",
                                "Xác định được miền xác định và tập giá trị"
                            ]
                        }
                    }
                },
                "HÌNH HỌC": {
                    "1. Véc tơ": {
                        "Véc tơ và phép toán": {
                            "Nhận biết": [
                                "Nhận biết được khái niệm véc tơ",
                                "Biết cách biểu diễn véc tơ"
                            ],
                            "Thông hiểu": [
                                "Hiểu được các phép toán trên véc tơ",
                                "Biết cách tính tổng, hiệu véc tơ"
                            ]
                        }
                    }
                }
            }
        }
        return jsonify(fallback_topics)
        
    except Exception as e:
        app.logger.error(f"Error getting topics: {str(e)}")
        app.logger.error(traceback.format_exc())
        return jsonify({'error': str(e)}), 500

# Endpoint debug để kiểm tra nội dung file
@app.route('/api/check-topics-structure', methods=['GET'])
def check_topics_structure():
    try:
        # Lấy dữ liệu chủ đề giống như API /api/topics
        topics_data = None
        possible_paths = [
            os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "topics_data.json"),
            os.path.join("data", "topics_data.json"),
            os.path.join("/var/task", "data", "topics_data.json")
        ]
        
        for path in possible_paths:
            if os.path.exists(path):
                with open(path, 'r', encoding='utf-8') as f:
                    topics_data = json.load(f)
                break
        
        if not topics_data:
            return jsonify({
                "error": "File not found",
                "fallback": "Using hardcoded data",
                "structure": "object with nested arrays"
            })
            
        # Trả về phân tích cấu trúc
        structure_info = {
            "is_object": isinstance(topics_data, dict),
            "top_level_keys": list(topics_data.keys()) if isinstance(topics_data, dict) else None,
            "sample_structure": {},
            "detailed_structure": {}
        }
        
        # Phân tích cấu trúc chi tiết hơn
        if isinstance(topics_data, dict) and len(topics_data) > 0:
            first_grade = list(topics_data.keys())[0]
            structure_info["sample_structure"]["first_grade"] = first_grade
            structure_info["sample_structure"]["first_grade_type"] = type(topics_data[first_grade]).__name__
            
            if isinstance(topics_data[first_grade], dict) and len(topics_data[first_grade]) > 0:
                first_subject = list(topics_data[first_grade].keys())[0]
                structure_info["sample_structure"]["first_subject"] = first_subject
                structure_info["sample_structure"]["first_subject_type"] = type(topics_data[first_grade][first_subject]).__name__
                structure_info["sample_structure"]["is_array"] = isinstance(topics_data[first_grade][first_subject], list)
                
                # Thêm mẫu dữ liệu
                structure_info["sample_data"] = topics_data[first_grade][first_subject]
                
                # Phân tích chi tiết từng cấp
                for grade in topics_data:
                    structure_info["detailed_structure"][grade] = {}
                    if isinstance(topics_data[grade], dict):
                        for subject in topics_data[grade]:
                            structure_info["detailed_structure"][grade][subject] = {
                                "type": type(topics_data[grade][subject]).__name__,
                                "is_array": isinstance(topics_data[grade][subject], list)
                            }
        
        return jsonify(structure_info)
        
    except Exception as e:
        return jsonify({"error": str(e), "traceback": traceback.format_exc()})

# API tạo câu hỏi - Sử dụng Gemini API
@app.route('/api/generate', methods=['POST'])
def generate():
    try:
        data = request.json
        if not data:
            return jsonify({'error': 'No data provided'}), 400
            
        subject = data.get('subject')
        topic = data.get('topic')
        level = data.get('level', '')  # Mức độ (Nhận biết, Thông hiểu...)
        num_questions = data.get('num_questions', 5)
        question_type = data.get('question_type', 'trac_nghiem')
        gemini_key = data.get('gemini_key', '')
        
        if not subject or not topic:
            return jsonify({'error': 'Subject and topic are required'}), 400
            
        if not gemini_key:
            return jsonify({'error': 'Gemini API key is required'}), 400
        
        app.logger.info(f"Generating questions: {subject} - {topic} - {level}, {num_questions} questions, type: {question_type}")
        
        # Nếu có mức độ, thêm vào prompt
        prompt_level = f" (mức độ {level})" if level else ""
        
        # Tạo prompt
        prompt = create_prompt(subject, topic + prompt_level, num_questions, question_type)
        
        # Gọi Gemini API
        response_text = call_gemini_api(prompt, gemini_key, max_tokens=8192)
        
        if response_text and isinstance(response_text, str) and response_text.startswith("Lỗi"):
            app.logger.error(f"Error response: {response_text}")
            return jsonify({'error': response_text}), 500
            
        if response_text:
            return jsonify({'text': response_text})
        else:
            return jsonify({'error': 'Failed to generate response'}), 500
            
    except Exception as e:
        app.logger.error(f"Error generating questions: {str(e)}")
        app.logger.error(traceback.format_exc())
        return jsonify({'error': str(e)}), 500

# Hàm tạo prompt
def create_prompt(subject, topic, num_questions, question_type):
    # Đọc TikZ examples
    try:
        # Thử nhiều đường dẫn khác nhau
        possible_paths = [
            os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "tikz_examples.txt"),
            os.path.join("data", "tikz_examples.txt"),
            os.path.join("/var/task", "data", "tikz_examples.txt")
        ]
        
        tikz_examples = "# Không thể tải mã TikZ mẫu"
        
        for path in possible_paths:
            if os.path.exists(path):
                with open(path, 'r', encoding='utf-8') as f:
                    tikz_examples = f.read()
                break
    except Exception as e:
        app.logger.error(f"Error loading TikZ examples: {str(e)}")
        tikz_examples = "# Không thể tải mã TikZ mẫu"
    
    # Phần chung của prompt
    base_prompt = f"""
    Hãy tạo {num_questions} câu hỏi về chủ đề "{topic}" thuộc mức độ {subject}. 
    
    Yêu cầu chung:
    1. Xác định mức độ từ chủ đề:
    a) Phân tích chủ đề "{topic}" để xác định mức độ (nhận biết, thông hiểu, vận dụng, hoặc vận dụng cao).
    b) Sử dụng mức độ này cho tất cả câu hỏi.

    2. Mức độ khó: Dựa trên Thang đo Bloom sửa đổi:
    a) Nhận biết (Dễ): Nhận ra, Xác định, Liệt kê, Mô tả, Nêu, Trình bày, Nhớ
    b) Thông hiểu (Trung bình): Giải thích, So sánh, Phân loại, Diễn giải, Tóm tắt, Chứng minh, Biểu diễn
    c) Vận dụng (Khó): Áp dụng, Giải quyết, Tính toán, Sử dụng, Thực hiện, Thực hành, Triển khai
    d) Vận dụng cao (Rất khó): Phân tích, Đánh giá, Sáng tạo, Tổng hợp, Thiết kế, Đề xuất, Mô hình hóa, Lập luận

    3. Đảm bảo câu hỏi phù hợp với trình độ học sinh và thuộc mức độ {subject}.
    4. Mỗi câu hỏi phải kèm theo đáp án chi tiết và hướng dẫn giải từng bước.
    5. Sử dụng công thức toán học dưới dạng LaTeX, bọc trong dấu $.
    5.1. Bọc trong dấu $ các loại công thức sau:
        - Phương trình đại số
        - Biểu thức số học
        - Hàm lượng giác (\\sin, \\cos, \\tan,\\cotan)
        - Hàm logarit và hàm mũ
        - Giới hạn, tổng, tích phân
        - Ký hiệu toán học đặc biệt (như \\pi, \\infty, \\sum, \\int)
        - Bất đẳng thức
        - Kí hiệu độ là ^\\circ, kí hiệu thuộc là \\in, kí hiệu không thuộc là \\notin, kí hiệu khác là \\neq, sử dụng kí hiệu \\pm cho dấu +-
        - Kí hiệu tam giác là \\triangle{{}}, ví dụ \\triangle{{ABC}} là tam giác ABC, kí hiệu tập hợp rỗng là \\varnothing
        - kí hiệu dấu tương đương là \\Leftrightarrow, kí hiệu dương vô cùng là +\\infty
        - Tập hợp số hữu tỉ là \\mathbb{{Q}}, tập hợp số tự nhiên là \\mathbb{{N}}, tập hợp số vô tỉ là \\mathbb{{I}}, tập hợp số thực là \\mathbb{{R}}
        - Kí hiệu tập xác định D là \\mathscr{{D}} 
        - Kí hiệu dấu lớn hơn hoặc bằng là \\geqslant, kí hiệu nhỏ hơn hoặc bằng là \\leqslant
        - Kí hiệu song song là \\parallel, kí hiệu vuông góc là \\perp, kí hiệu góc là \\widehat, ví dụ \\widehat{{A}} là góc A
        - Kí hiệu đồng dạng là \\backsim
    5.2. Đối với công thức LaTeX, giữ nguyên cú pháp và bọc toàn bộ trong dấu $.
    5.3. Ví dụ về định dạng mong muốn:
    - "Phương trình bậc hai $ax^2 + bx + c = 0$"
    - "Định lý Pytago: $a^2 + b^2 = c^2$"
    - "Giá trị của pi là $\\pi \approx 3.14159$"
    - "$\\frac{{d}}{{dx}}f(x) = \\lim_{{h \\to 0}} \\frac{{f(x+h) - f(x)}}{{h}}$"

    6. Sử dụng mã TikZ cho hình vẽ:
    Khi cần vẽ hình minh họa, hãy sử dụng mã TikZ. Dưới đây là một số ví dụ mã TikZ có thể được sử dụng và điều chỉnh:

    {tikz_examples}

    Khi sử dụng mã TikZ:
    - Đặt mã TikZ trong cặp thẻ \\begin{{tikzpicture}} và \\end{{tikzpicture}}.
    - Điều chỉnh các thông số như tọa độ, nhãn, và màu sắc để phù hợp với yêu cầu của câu hỏi.
    - Đặt mã TikZ ở vị trí phù hợp trong câu hỏi hoặc lời giải.
    - Nếu cần, thêm chú thích để giải thích các phần quan trọng của hình vẽ.

    Hãy tạo câu hỏi với nội dung phong phú, đa dạng và có tính ứng dụng cao. Sử dụng hình vẽ TikZ khi cần thiết để minh họa các khái niệm hoặc bài toán.
    """
    
    # Định dạng dựa trên loại câu hỏi
    if question_type == 'trac_nghiem':
        format_prompt = """
        Định dạng câu hỏi trắc nghiệm:
        \\begin{ex}
        Nội dung câu hỏi trắc nghiệm
        [Đặt mã TikZ ở đây nếu cần hình vẽ]
        \\choice
        {Nội dung phương án A}
        {Nội dung phương án B}
        {Nội dung phương án C}
        {Nội dung phương án D}
        \\loigiai{Lời giải chi tiết ở đây. [Đặt mã TikZ ở đây nếu cần hình vẽ minh họa cho lời giải]}
        \\end{ex}
        """
    elif question_type == 'dung_sai':
        format_prompt = """
        Định dạng câu hỏi đúng sai:
        \\begin{ex}
        Nội dung câu hỏi đúng sai
        [Đặt mã TikZ ở đây nếu cần hình vẽ]
        \\choiceTF[t]
        {Phương án A}
        {Phương án B}
        {Phương án C}
        {Phương án D}
        Mỗi phương án là một mệnh đề chứ không phải là đúng hoặc sai và bắt buộc có 4 phương án,Mỗi mệnh đề là một khẳng định liên quan đến câu hỏi chứ không phải là lời giải của câu hỏi. Và 4 phương án là các mệnh đề liên quan nhau và mệnh đề cuối luôn là mệnh đề khó. Mỗi phương án không được ghi đúng hoặc sai
        \\loigiai{Lời giải chi tiết ở đây. [Đặt mã TikZ ở đây nếu cần hình vẽ minh họa cho lời giải]}
        \\end{ex}
        """
    elif question_type == 'tra_loi_ngan':
        format_prompt = """
        Định dạng câu hỏi trả lời ngắn:
        \\begin{ex}
        Nội dung câu hỏi trả lời ngắn
        [Đặt mã TikZ ở đây nếu cần hình vẽ]
        \\shortans{}
        \\loigiai{Lời giải chi tiết ở đây. [Đặt mã TikZ ở đây nếu cần hình vẽ minh họa cho lời giải]}
        \\end{ex}
        """
    else:  # tu_luan
        format_prompt = """
        Định dạng câu hỏi tự luận:
        \\begin{bt}
        Nội dung câu hỏi tự luận
        [Đặt mã TikZ ở đây nếu cần hình vẽ]
        \\begin{enumerate}
        \\item Ý 1 nếu câu hỏi tự luận có nhiều ý
        \\item Ý 2 nếu câu hỏi tự luận có nhiều ý
        \\end{enumerate}
        \\loigiai{Lời giải chi tiết ở đây. [Đặt mã TikZ ở đây nếu cần hình vẽ minh họa cho lời giải]}
        \\end{bt}
        """
    
    return base_prompt + "\n\n" + format_prompt

# Serve static files
@app.route('/static/<path:path>')
def serve_static(path):
    return send_from_directory(app.static_folder, path)

# Vercel requires a flask app instance at the module level
app_instance = app
