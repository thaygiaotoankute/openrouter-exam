// Biến lưu trữ thông tin về chủ đề đã chọn
let selectedGrade = '';
let selectedSubject = '';
let selectedTopic = '';
let selectedLevel = ''; // Thêm biến cho mức độ (Nhận biết, Thông hiểu...)
let selectedPath = []; // Đường dẫn đầy đủ đến chủ đề

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

// Hàm hiển thị danh sách chủ đề với khả năng thu gọn/mở rộng
function displayTopics(topics) {
    const topicTree = document.getElementById('topicTree');
    topicTree.innerHTML = '';
    
    // Tạo nút thu gọn/mở rộng tất cả
    const toggleAllButton = document.createElement('button');
    toggleAllButton.className = 'btn btn-sm btn-outline-dark mb-3 w-100';
    toggleAllButton.innerHTML = '<i class="fas fa-expand-alt me-1"></i> Mở rộng tất cả';
    toggleAllButton.onclick = function() {
        const collapseElements = document.querySelectorAll('.collapse');
        const isExpanded = this.getAttribute('data-expanded') === 'true';
        
        if (isExpanded) {
            collapseElements.forEach(el => {
                const bsCollapse = bootstrap.Collapse.getInstance(el);
                if (bsCollapse) bsCollapse.hide();
            });
            this.innerHTML = '<i class="fas fa-expand-alt me-1"></i> Mở rộng tất cả';
            this.setAttribute('data-expanded', 'false');
        } else {
            collapseElements.forEach(el => {
                new bootstrap.Collapse(el, { toggle: true });
            });
            this.innerHTML = '<i class="fas fa-compress-alt me-1"></i> Thu gọn tất cả';
            this.setAttribute('data-expanded', 'true');
        }
    };
    toggleAllButton.setAttribute('data-expanded', 'false');
    topicTree.appendChild(toggleAllButton);
    
    // Xử lý cấu trúc chủ đề đệ quy
    Object.keys(topics).forEach(grade => {
        topicTree.appendChild(createTopicElement(grade, topics[grade], [], grade));
    });
}

// Hàm đệ quy tạo các phần tử cho cấu trúc chủ đề
function createTopicElement(label, data, path, uniqueId) {
    const container = document.createElement('div');
    container.className = 'mb-2';
    
    // Xác định xem đây có phải là node lá (level) hay không
    const isLeafNode = Array.isArray(data);
    const isLevel = ['Nhận biết', 'Thông hiểu', 'Vận dụng', 'Vận dụng cao'].includes(label);
    
    // Tạo header cho mỗi cấp
    const header = document.createElement('div');
    
    // Tùy chỉnh class dựa vào mức độ
    let btnClass;
    if (path.length === 0) {
        btnClass = 'btn-outline-primary'; // Lớp
    } else if (path.length === 1) {
        btnClass = 'btn-outline-secondary'; // Môn học
    } else if (path.length === 2) {
        btnClass = 'btn-outline-info'; // Chương
    } else if (path.length === 3) {
        btnClass = 'btn-outline-success'; // Chủ đề
    } else if (isLevel) {
        btnClass = 'btn-outline-warning'; // Mức độ
    } else {
        btnClass = 'btn-outline-dark'; // Khác
    }
    
    // Tạo nút và nội dung
    if (isLeafNode) {
        // Nếu là mức độ, hiển thị dưới dạng danh sách các mục tiêu
        header.className = `fw-bold ms-${path.length * 2} btn ${btnClass} w-100 text-start`;
        header.textContent = label;
        
        // Tạo danh sách các mục tiêu
        const listContainer = document.createElement('div');
        listContainer.className = 'ms-4 mt-1 mb-2';
        
        // Thêm từng mục tiêu
        data.forEach(item => {
            const listItem = document.createElement('div');
            listItem.className = 'small mb-1';
            listItem.textContent = `• ${item}`;
            listContainer.appendChild(listItem);
        });
        
        container.appendChild(header);
        container.appendChild(listContainer);
        
        // Cho phép chọn level và mục tiêu
        header.onclick = function() {
            let fullPath = [...path, label];
            selectTopic(fullPath, this);
        };
    } else {
        // Nếu không phải node lá, tạo collapse với nút thu gọn/mở rộng
        const safeId = uniqueId.replace(/[^a-zA-Z0-9]/g, '_');
        
        header.className = `fw-bold ms-${path.length * 2} btn ${btnClass} w-100 text-start`;
        header.textContent = label;
        header.setAttribute('data-bs-toggle', 'collapse');
        header.setAttribute('data-bs-target', `#${safeId}`);
        header.setAttribute('aria-expanded', 'false');
        
        const content = document.createElement('div');
        content.className = 'collapse';
        content.id = safeId;
        
        // Đệ quy tạo nội dung cho node con
        if (typeof data === 'object' && !Array.isArray(data)) {
            Object.keys(data).forEach(key => {
                const newPath = [...path, label];
                const newUniqueId = `${uniqueId}_${key}`.replace(/[^a-zA-Z0-9]/g, '_');
                content.appendChild(createTopicElement(key, data[key], newPath, newUniqueId));
            });
        }
        
        container.appendChild(header);
        container.appendChild(content);
        
        // Thêm listener cho các node chứa mức độ có thể chọn
        if (path.length >= 3 || isLevel) {
            header.onclick = function(e) {
                // Xử lý sự kiện chọn chủ đề
                let fullPath = [...path, label];
                selectTopic(fullPath, this);
                
                // Toggle collapse
                e.stopPropagation();
                const bsCollapse = bootstrap.Collapse.getOrCreateInstance(document.getElementById(safeId));
                setTimeout(() => {
                    bsCollapse.toggle();
                }, 0);
            };
        }
    }
    
    return container;
}

// Hàm được gọi khi chọn một chủ đề
function selectTopic(fullPath, element) {
    // Bỏ chọn tất cả các nút chủ đề khác
    document.querySelectorAll('#topicTree .btn').forEach(btn => {
        btn.classList.remove('active');
    });
    
    // Đánh dấu nút được chọn
    element.classList.add('active');
    
    // Lưu thông tin chủ đề đã chọn
    selectedPath = fullPath;
    selectedGrade = fullPath[0] || '';
    selectedSubject = fullPath[1] || '';
    selectedTopic = fullPath[fullPath.length - 2] || '';
    selectedLevel = fullPath[fullPath.length - 1] || '';
    
    // Log thông tin để debug
    console.log("Selected path:", fullPath);
    console.log(`Selected: Grade=${selectedGrade}, Subject=${selectedSubject}, Topic=${selectedTopic}, Level=${selectedLevel}`);
    
    // Hiển thị thông tin chủ đề đã chọn
    updateSelectedTopicInfo();
    
    // Cập nhật nút tạo câu hỏi
    updateGenerateButton();
}

// Hàm cập nhật hiển thị thông tin chủ đề đã chọn
function updateSelectedTopicInfo() {
    const infoElement = document.getElementById('selectedTopicInfo');
    
    if (selectedPath.length > 0) {
        // Tạo nội dung hiển thị
        let content = '';
        
        // Hiển thị đường dẫn đầy đủ đến chủ đề
        for (let i = 0; i < selectedPath.length; i++) {
            if (i > 0) content += ' > ';
            
            // Đánh dấu cấp thông tin cuối cùng (chủ đề hoặc mức độ)
            if (i === selectedPath.length - 1) {
                content += `<strong>${selectedPath[i]}</strong>`;
            } else {
                content += selectedPath[i];
            }
        }
        
        infoElement.innerHTML = content;
    } else {
        infoElement.innerHTML = 'Vui lòng chọn chủ đề từ danh sách bên trái';
    }
}

// Hàm cập nhật trạng thái nút tạo câu hỏi
function updateGenerateButton() {
    const generateBtn = document.getElementById('generateBtn');
    const geminiKey = document.getElementById('geminiKey').value.trim();
    const questionType = document.querySelector('input[name="questionType"]:checked').value;
    
    if (selectedPath.length > 0 && geminiKey) {
        generateBtn.disabled = false;
        generateBtn.textContent = `Tạo câu hỏi ${getQuestionTypeName(questionType)}`;
    } else {
        generateBtn.disabled = true;
        generateBtn.textContent = 'Chọn chủ đề và nhập API key';
    }
}

// Hàm lấy tên loại câu hỏi
function getQuestionTypeName(type) {
    switch(type) {
        case 'trac_nghiem': return 'trắc nghiệm';
        case 'dung_sai': return 'đúng sai';
        case 'tra_loi_ngan': return 'trả lời ngắn';
        case 'tu_luan': return 'tự luận';
        default: return '';
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
    
    // Kiểm tra đã chọn chủ đề
    if (selectedPath.length === 0) {
        document.getElementById('generatedQuestions').innerHTML = 
            '<div class="alert alert-danger">Vui lòng chọn một chủ đề</div>';
        return;
    }
    
    // Hiển thị thông báo đang tạo
    document.getElementById('generatedQuestions').innerHTML = 
        '<div class="alert alert-info">Đang tạo câu hỏi, vui lòng đợi...<br/>' +
        '<div class="spinner-border spinner-border-sm mt-2" role="status">' +
        '<span class="visually-hidden">Loading...</span></div></div>';
    
    // Tạo chủ đề đầy đủ từ đường dẫn
    const topicDescription = selectedPath.join(" - ");
    
    // Gọi API
    fetch('/api/generate', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            subject: selectedGrade,
            topic: topicDescription,
            level: selectedLevel,
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
