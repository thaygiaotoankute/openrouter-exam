// Biến lưu trữ thông tin về chủ đề đã chọn
let selectedGrade = '';
let selectedSubject = '';
let selectedTopic = '';

// Hàm được gọi khi trang được tải
document.addEventListener('DOMContentLoaded', function() {
    // Tải danh sách chủ đề
    fetchTopics();
    
    // Cập nhật nút tạo câu hỏi khi loại câu hỏi thay đổi
    document.querySelectorAll('input[name="questionType"]').forEach(input => {
        input.addEventListener('change', updateGenerateButton);
    });
    
    // Kiểm tra Gemini API Key khi người dùng nhập
    document.getElementById('geminiKey').addEventListener('input', updateGenerateButton);
});

// Hàm tải danh sách chủ đề từ API
function fetchTopics() {
    fetch('/api/topics')
        .then(response => {
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            return response.json();
        })
        .then(data => {
            displayTopics(data);
        })
        .catch(error => {
            document.getElementById('topicTree').innerHTML = `
                <div class="alert alert-danger">
                    Không thể tải dữ liệu chủ đề: ${error.message}
                </div>
            `;
        });
}

// Hàm hiển thị danh sách chủ đề
function displayTopics(topics) {
    const topicTree = document.getElementById('topicTree');
    topicTree.innerHTML = '';
    
    // Tạo HTML cho cây chủ đề
    Object.keys(topics).forEach(grade => {
        const gradeDiv = document.createElement('div');
        gradeDiv.className = 'mb-3';
        
        // Tiêu đề lớp
        const gradeHeader = document.createElement('div');
        gradeHeader.className = 'fw-bold fs-5 mb-2 btn btn-outline-primary w-100 text-start';
        gradeHeader.textContent = grade;
        gradeHeader.setAttribute('data-bs-toggle', 'collapse');
        gradeHeader.setAttribute('data-bs-target', `#${grade.replace(/\s+/g, '')}`);
        gradeHeader.setAttribute('aria-expanded', 'false');
        gradeDiv.appendChild(gradeHeader);
        
        // Nội dung lớp (có thể thu gọn)
        const gradeContent = document.createElement('div');
        gradeContent.className = 'collapse';
        gradeContent.id = grade.replace(/\s+/g, '');
        
        // Duyệt qua các môn học
        Object.keys(topics[grade]).forEach(subject => {
            const subjectDiv = document.createElement('div');
            subjectDiv.className = 'ms-3 mb-2';
            
            // Tiêu đề môn học
            const subjectHeader = document.createElement('div');
            subjectHeader.className = 'fw-bold mb-2 btn btn-outline-secondary w-100 text-start';
            subjectHeader.textContent = subject;
            subjectHeader.setAttribute('data-bs-toggle', 'collapse');
            subjectHeader.setAttribute('data-bs-target', `#${grade.replace(/\s+/g, '')}${subject.replace(/\s+/g, '')}`);
            subjectHeader.setAttribute('aria-expanded', 'false');
            subjectDiv.appendChild(subjectHeader);
            
            // Nội dung môn học (có thể thu gọn)
            const subjectContent = document.createElement('div');
            subjectContent.className = 'collapse';
            subjectContent.id = `${grade.replace(/\s+/g, '')}${subject.replace(/\s+/g, '')}`;
            
            // Duyệt qua các chủ đề
            topics[grade][subject].forEach(topic => {
                const topicBtn = document.createElement('button');
                topicBtn.className = 'btn btn-sm btn-outline-info w-100 text-start mb-1';
                topicBtn.textContent = topic;
                topicBtn.onclick = function() {
                    selectTopic(grade, subject, topic, this);
                };
                subjectContent.appendChild(topicBtn);
            });
            
            subjectDiv.appendChild(subjectContent);
            gradeContent.appendChild(subjectDiv);
        });
        
        gradeDiv.appendChild(gradeContent);
        topicTree.appendChild(gradeDiv);
    });
}

// Hàm được gọi khi chọn một chủ đề
function selectTopic(grade, subject, topic, element) {
    // Bỏ chọn tất cả các nút chủ đề khác
    document.querySelectorAll('#topicTree button').forEach(btn => {
        btn.classList.remove('active');
    });
    
    // Đánh dấu nút được chọn
    element.classList.add('active');
    
    // Lưu thông tin chủ đề đã chọn
    selectedGrade = grade;
    selectedSubject = subject;
    selectedTopic = topic;
    
    // Cập nhật nút tạo câu hỏi
    updateGenerateButton();
}

// Hàm cập nhật trạng thái nút tạo câu hỏi
function updateGenerateButton() {
    const generateBtn = document.getElementById('generateBtn');
    const geminiKey = document.getElementById('geminiKey').value.trim();
    const questionType = document.querySelector('input[name="questionType"]:checked').value;
    
    if (selectedTopic && geminiKey) {
        generateBtn.disabled = false;
        
        // Cập nhật text của nút dựa trên loại câu hỏi
        if (questionType === 'trac_nghiem') {
            generateBtn.textContent = 'Tạo câu hỏi trắc nghiệm';
        } else if (questionType === 'dung_sai') {
            generateBtn.textContent = 'Tạo câu hỏi đúng sai';
        } else if (questionType === 'tra_loi_ngan') {
            generateBtn.textContent = 'Tạo câu hỏi trả lời ngắn';
        } else {
            generateBtn.textContent = 'Tạo câu hỏi tự luận';
        }
    } else {
        generateBtn.disabled = true;
    }
}

// Hàm gửi request tạo câu hỏi
function generateQuestions() {
    // Lấy dữ liệu từ form
    const numQuestions = document.getElementById('numQuestions').value;
    const questionType = document.querySelector('input[name="questionType"]:checked').value;
    const geminiKey = document.getElementById('geminiKey').value.trim();
    
    // Kiểm tra Gemini API key
    if (!geminiKey) {
        document.getElementById('generatedQuestions').innerHTML = 
            '<div class="alert alert-danger">Vui lòng nhập Gemini API Key</div>';
        return;
    }
    
    // Hiển thị thông báo đang tạo
    document.getElementById('generatedQuestions').innerHTML = 
        '<div class="alert alert-info">Đang tạo câu hỏi, vui lòng đợi...<br/>' +
        '<div class="spinner-border spinner-border-sm mt-2" role="status">' +
        '<span class="visually-hidden">Loading...</span></div></div>';
    
    // Gọi API
    fetch('/api/generate', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            subject: selectedGrade,
            topic: selectedTopic,
            num_questions: numQuestions,
            question_type: questionType,
            gemini_key: geminiKey
        })
    })
    .then(response => {
        if (!response.ok) {
            return response.json().then(data => {
                throw new Error(data.error || `Lỗi khi tạo câu hỏi: ${response.status}`);
            });
        }
        return response.json();
    })
    .then(data => {
        // Hiển thị câu hỏi
        document.getElementById('generatedQuestions').innerHTML = data.text;
        
        // Render công thức toán học
        if (window.MathJax) {
            MathJax.typesetPromise();
        }
        
        // Kích hoạt nút sao chép và xóa
        document.getElementById('copyBtn').disabled = false;
        document.getElementById('clearBtn').disabled = false;
    })
    .catch(error => {
        console.error('Error:', error);
        document.getElementById('generatedQuestions').innerHTML = 
            `<div class="alert alert-danger">${error.message}</div>`;
    });
}

// Hàm sao chép câu hỏi đã tạo
function copyQuestions() {
    const questionsContent = document.getElementById('generatedQuestions').innerText;
    
    if (questionsContent) {
        navigator.clipboard.writeText(questionsContent)
            .then(() => {
                // Thông báo sao chép thành công
                alert('Đã sao chép nội dung vào clipboard!');
            })
            .catch(err => {
                console.error('Lỗi khi sao chép: ', err);
                alert('Không thể sao chép nội dung. Vui lòng thử lại sau.');
            });
    }
}

// Hàm xóa câu hỏi đã tạo
function clearQuestions() {
    document.getElementById('generatedQuestions').innerHTML = '';
    document.getElementById('copyBtn').disabled = true;
    document.getElementById('clearBtn').disabled = true;
}
