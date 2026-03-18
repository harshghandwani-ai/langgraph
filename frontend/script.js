document.addEventListener('DOMContentLoaded', () => {
    const chatForm = document.getElementById('chat-form');
    const messageInput = document.getElementById('message-input');
    const sendBtn = document.getElementById('send-btn');
    const chatMessages = document.getElementById('chat-messages');
    const themeToggle = document.getElementById('theme-toggle');
    const mobileMenuBtn = document.getElementById('mobile-menu-btn');
    const sidebar = document.getElementById('sidebar');
    const newChatBtn = document.getElementById('new-chat-btn');
    const welcomeContainer = document.querySelector('.welcome-container');
    const messageTemplate = document.getElementById('message-template');

    // Auto-resize textarea
    messageInput.addEventListener('input', function() {
        this.style.height = 'auto';
        this.style.height = (this.scrollHeight) + 'px';
        if (this.scrollHeight > 200) {
            this.style.overflowY = 'auto';
        } else {
            this.style.overflowY = 'hidden';
        }
        
        // Enable/disable send button
        if (this.value.trim().length > 0) {
            sendBtn.removeAttribute('disabled');
        } else {
            sendBtn.setAttribute('disabled', 'true');
        }
    });

    // Handle Enter key (Shift+Enter for new line)
    messageInput.addEventListener('keydown', function(e) {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            if (this.value.trim().length > 0) {
                chatForm.dispatchEvent(new Event('submit'));
            }
        }
    });

    // Theme Toggle
    themeToggle.addEventListener('click', () => {
        const body = document.querySelector('.app-container');
        if (body.classList.contains('theme-dark')) {
            body.classList.remove('theme-dark');
            body.classList.add('theme-light');
            themeToggle.innerHTML = '<i class="fa-solid fa-moon"></i>';
        } else {
            body.classList.remove('theme-light');
            body.classList.add('theme-dark');
            themeToggle.innerHTML = '<i class="fa-solid fa-sun"></i>';
        }
    });

    // Mobile Menu Toggle
    mobileMenuBtn.addEventListener('click', () => {
        sidebar.classList.toggle('open');
    });

    // Close sidebar when clicking outside on mobile
    document.addEventListener('click', (e) => {
        if (window.innerWidth <= 768) {
            if (!sidebar.contains(e.target) && !mobileMenuBtn.contains(e.target) && sidebar.classList.contains('open')) {
                sidebar.classList.remove('open');
            }
        }
    });

    // New Chat
    newChatBtn.addEventListener('click', () => {
        chatMessages.innerHTML = '';
        chatMessages.appendChild(welcomeContainer);
        welcomeContainer.style.display = 'block';
    });

    // Form Submit
    chatForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const message = messageInput.value.trim();
        if (!message) return;

        // Hide welcome message if it exists
        if (welcomeContainer) {
            welcomeContainer.style.display = 'none';
        }

        // Add user message
        appendMessage('user', message);

        // Clear input
        messageInput.value = '';
        messageInput.style.height = 'auto';
        sendBtn.setAttribute('disabled', 'true');

        // Add typing indicator
        const typingId = addTypingIndicator();

        try {
            // Replace with actual API endpoint
            const response = await fetch('/api/chat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ message: message })
            });

            const data = await response.json();
            
            // Remove typing indicator
            removeElement(typingId);
            
            // Add AI response
            if (response.ok) {
                appendMessage('ai', data.answer);
            } else {
                appendMessage('system', 'Sorry, I encountered an error while processing your request.');
            }
            
        } catch (error) {
            removeElement(typingId);
            appendMessage('system', 'Connection error. Please ensure the server is running.');
            console.error('Error:', error);
        }
    });

    function appendMessage(sender, text) {
        const item = messageTemplate.content.cloneNode(true);
        const messageDiv = item.querySelector('.message');
        const avatarDiv = item.querySelector('.avatar');
        const contentDiv = item.querySelector('.message-text');

        if (sender === 'user') {
            messageDiv.classList.add('user-message');
            avatarDiv.innerHTML = '<i class="fa-solid fa-user"></i>';
            // Simple text encoding to prevent XSS
            contentDiv.textContent = text;
        } else if (sender === 'ai') {
            messageDiv.classList.add('ai-message');
            avatarDiv.innerHTML = '<i class="fa-solid fa-wallet"></i>';
            // Can use marked.js later for markdown support
            contentDiv.innerHTML = '<p>' + text.replace(/\n/g, '<br>') + '</p>';
        } else {
            messageDiv.classList.add('ai-message');
            avatarDiv.innerHTML = '<i class="fa-solid fa-circle-exclamation" style="color: #ff5555"></i>';
            contentDiv.innerHTML = '<p style="color: #ff5555">' + text + '</p>';
        }

        chatMessages.appendChild(messageDiv);
        scrollToBottom();
    }

    function addTypingIndicator() {
        const id = 'typing-' + Date.now();
        const item = messageTemplate.content.cloneNode(true);
        const messageDiv = item.querySelector('.message');
        const avatarDiv = item.querySelector('.avatar');
        const contentDiv = item.querySelector('.message-text');

        messageDiv.id = id;
        messageDiv.classList.add('ai-message');
        avatarDiv.innerHTML = '<i class="fa-solid fa-wallet"></i>';
        
        contentDiv.innerHTML = `
            <div class="typing-indicator">
                <div class="typing-dot"></div>
                <div class="typing-dot"></div>
                <div class="typing-dot"></div>
            </div>
        `;

        chatMessages.appendChild(messageDiv);
        scrollToBottom();
        return id;
    }

    function removeElement(id) {
        const el = document.getElementById(id);
        if (el) {
            el.remove();
        }
    }

    function scrollToBottom() {
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }
});
