document.addEventListener('DOMContentLoaded', function() {
    // Các elements
    const topicTree = document.getElementById('topic-tree');
    const numQuestionsInput = document.getElementById('num-questions');
    const generateTracNghiemBtn = document.getElementById('generate-trac-nghiem');
    const generateDungSaiBtn = document.getElementById('generate-dung-sai');
    const generateTraLoiNganBtn = document.getElementById('generate-tra-loi-ngan');
    const generateTuLuanBtn = document.getElementById('generate-tu-luan');
    const resultArea = document.getElementById('result-area');
    const copyButton = document.getElementById('copy-button');
    const clearButton = document.getElementById('clear-button');
    const loadingOverlay = document.getElementById('loading-overlay');
    
    // Biến lưu trữ chủ đề đang được chọn
    let selectedSubject = null;
    let selectedTopic = null;
    
    // Tải dữ liệu chủ đề khi trang được load
    loadTopics();
    
    // Xử lý sự kiện click các nút tạo câu hỏi
    generateTracNghiemBtn.addEventListener('click', () => generateQuestions('trac_nghiem'));
    generateDungSaiBtn.addEventListener('click', () => generateQuestions('dung_sai'));
    generateTraLoiNganBtn.addEventListener('click', () => generateQuestions('tra_loi_ngan'));
    generateTuLuanBtn.addEventListener('click', () => generateQuestions('tu_luan'));
    
    // Xử lý sự kiện nút Copy
    copyButton.addEventListener('click', function() {
        navigator.clipboard.writeText(resultArea.textContent)
            .then(() => {
                alert('Đã sao chép nội dung vào clipboard');
            })
            .catch(err => {
                console.error('Không thể sao chép: ', err);
            });
    });
    
    // Xử lý sự kiện nút Clear
    clearButton.addEventListener('click', function() {
        resultArea.textContent = '';
        copyButton.disabled = true;
        clearButton.disabled = true;
    });
    
    // Hàm tải dữ liệu chủ đề
    function loadTopics() {
        fetch('/api/topics')
            .then(response => {
                if (!response.ok) {
                    throw new Error('Network response was not ok');
                }
                return response.json();
            })
            .then(topics => {
                renderTopicTree(topics);
            })
            .catch(error => {
                console.error('Error fetching topics:', error);
                topicTree.innerHTML = `<div class="alert alert-danger">Không thể tải dữ liệu chủ đề: ${error.message}</div>`;
            });
    }
    
    // Hàm render cây chủ đề
    function renderTopicTree(topics) {
        topicTree.innerHTML = '';
        const ul = document.createElement('ul');
        
        for (const [subject, subjectTopics] of Object.entries(topics)) {
            const li = document.createElement('li');
            
            // Tạo phần tử chủ đề chính (môn học)
            const subjectSpan = document.createElement('span');
            subjectSpan.textContent = subject;
            subjectSpan.classList.add('topic-item', 'fw-bold');
            subjectSpan.dataset.subject = subject;
            subjectSpan.dataset.topic = "Tổng quát";
            subjectSpan.addEventListener('click', onTopicSelected);
            
            li.appendChild(subjectSpan);
            
            // Thêm các chủ đề con
            if (typeof subjectTopics === 'object' && subjectTopics !== null) {
                const subUl = document.createElement('ul');
                renderSubTopics(subjectTopics, subUl, subject);
                li.appendChild(subUl);
            }
            
            ul.appendChild(li);
        }
        
        topicTree.appendChild(ul);
    }
    
    // Hàm render các chủ đề con
    function renderSubTopics(topics, parentElement, parentSubject) {
        for (const [topic, subtopics] of Object.entries(topics)) {
            const li = document.createElement('li');
            
            // Tạo phần tử chủ đề
            const topicSpan = document.createElement('span');
            topicSpan.textContent = topic;
            topicSpan.classList.add('topic-item');
            topicSpan.dataset.subject = parentSubject;
            topicSpan.dataset.topic = topic;
            topicSpan.addEventListener('click', onTopicSelected);
            
            li.appendChild(topicSpan);
            
            // Thêm các chủ đề con nếu có
            if (typeof subtopics === 'object' && subtopics !== null && !Array.isArray(subtopics)) {
                const subUl = document.createElement('ul');
                renderSubTopics(subtopics, subUl, parentSubject);
                li.appendChild(subUl);
            }
            
            parentElement.appendChild(li);
        }
    }
    
    // Xử lý khi chọn chủ đề
    function onTopicSelected(event) {
        // Xóa trạng thái selected của tất cả các chủ đề
        document.querySelectorAll('#topic-tree .topic-item').forEach(item => {
            item.classList.remove('selected');
        });
        
        // Cập nhật trạng thái selected của chủ đề được chọn
        event.target.classList.add('selected');
        
        // Lưu thông tin chủ đề được chọn
        selectedSubject = event.target.dataset.subject;
        selectedTopic = event.target.dataset.topic;
        
        // Enable các nút tạo câu hỏi
        enableGenerateButtons();
    }
    
    // Bật các nút tạo câu hỏi
    function enableGenerateButtons() {
        generateTracNghiemBtn.disabled = false;
        generateDungSaiBtn.disabled = false;
        generateTraLoiNganBtn.disabled = false;
        generateTuLuanBtn.disabled = false;
    }
    
    // Hàm tạo câu hỏi
    function generateQuestions(questionType) {
        // Kiểm tra chủ đề đã được chọn chưa
        if (!selectedSubject || !selectedTopic) {
            alert('Vui lòng chọn một chủ đề!');
            return;
        }
        
        // Lấy số lượng câu hỏi
        const numQuestions = parseInt(numQuestionsInput.value);
        if (isNaN(numQuestions) || numQuestions < 1 || numQuestions > 10) {
            alert('Số câu hỏi phải từ 1 đến 10!');
            return;
        }
        
        // Hiển thị loading
        loadingOverlay.classList.remove('d-none');
        resultArea.textContent = 'Đang tạo câu hỏi...';
        
        // Gọi API để tạo câu hỏi
        fetch('/api/generate', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                subject: selectedSubject,
                topic: selectedTopic,
                num_questions: numQuestions,
                question_type: questionType
            }),
        })
        .then(response => {
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            return response.json();
        })
        .then(data => {
            if (data.text) {
                resultArea.textContent = data.text;
                copyButton.disabled = false;
                clearButton.disabled = false;
            } else {
                resultArea.textContent = 'Lỗi: Không nhận được phản hồi từ API.';
            }
        })
        .catch(error => {
            console.error('Error generating questions:', error);
            resultArea.textContent = `Lỗi khi tạo câu hỏi: ${error.message}`;
        })
        .finally(() => {
            // Ẩn loading
            loadingOverlay.classList.add('d-none');
        });
    }
});
