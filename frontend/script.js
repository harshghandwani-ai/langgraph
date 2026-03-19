document.addEventListener('DOMContentLoaded', () => {
    const chatForm = document.getElementById('chat-form');
    const messageInput = document.getElementById('message-input');
    const sendBtn = document.getElementById('send-btn');
    const chatMessages = document.getElementById('chat-messages');
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
    const toggleTheme = () => {
        const body = document.querySelector('.app-container');
        if (body.classList.contains('theme-dark')) {
            body.classList.remove('theme-dark');
            body.classList.add('theme-light');
            document.getElementById('theme-toggle-desktop').innerHTML = '<i class="fa-solid fa-moon"></i>';
            document.getElementById('theme-toggle-mobile').innerHTML = '<i class="fa-solid fa-moon"></i>';
        } else {
            body.classList.remove('theme-light');
            body.classList.add('theme-dark');
            document.getElementById('theme-toggle-desktop').innerHTML = '<i class="fa-solid fa-sun"></i>';
            document.getElementById('theme-toggle-mobile').innerHTML = '<i class="fa-solid fa-sun"></i>';
        }
    };
    
    const desktopThemeBtn = document.getElementById('theme-toggle-desktop');
    const mobileThemeBtn = document.getElementById('theme-toggle-mobile');
    if(desktopThemeBtn) desktopThemeBtn.addEventListener('click', toggleTheme);
    if(mobileThemeBtn) mobileThemeBtn.addEventListener('click', toggleTheme);

    // Navigation Logic
    const navItems = document.querySelectorAll('.nav-item, .bottom-nav-item');
    const pageViews = document.querySelectorAll('.page-view');
    const fabBtn = document.querySelector('.fab-btn');
    
    navItems.forEach(item => {
        item.addEventListener('click', () => {
            const targetPage = item.getAttribute('data-page');
            
            navItems.forEach(nav => {
                if(nav.getAttribute('data-page') === targetPage) {
                    nav.classList.add('active');
                } else {
                    nav.classList.remove('active');
                }
            });
            
            pageViews.forEach(page => {
                if(page.id === targetPage) {
                    page.classList.add('active');
                } else {
                    page.classList.remove('active');
                }
            });
            
            if(fabBtn) {
                if(targetPage === 'page-chat') {
                    fabBtn.style.display = 'none';
                } else {
                    fabBtn.style.display = 'flex';
                }
            }
        });
    });

    // New Chat
    if (newChatBtn) {
        newChatBtn.addEventListener('click', () => {
            chatMessages.innerHTML = '';
            chatMessages.appendChild(welcomeContainer);
            welcomeContainer.style.display = 'block';
        });
    }

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
