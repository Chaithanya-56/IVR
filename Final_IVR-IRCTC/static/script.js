document.addEventListener('DOMContentLoaded', () => {
    const chatMessages = document.getElementById('chat-messages');
    const chatInput = document.getElementById('chat-input');
    const sendBtn = document.getElementById('send-btn');
    const voiceBtn = document.getElementById('voice-btn');
    const chatModeBtn = document.getElementById('chat-mode-btn');
    const dtmfModeBtn = document.getElementById('dtmf-mode-btn');
    const chatInputContainer = document.getElementById('chat-input-container');
    const dtmfInputContainer = document.getElementById('dtmf-input-container');
    const dtmfInputField = document.getElementById('dtmf-input');
    const dtmfSubmitBtn = document.getElementById('dtmf-submit-btn');
    const dtmfClearBtn = document.getElementById('dtmf-clear-btn');
    const soundToggleBtn = document.getElementById('sound-toggle-btn');

    const ttsAudio = document.getElementById('tts-audio');

    let recognition;
    let isRecognizing = false;
    let speechEnabled = false; // Initially false to handle browser restriction
    let isSoundEnabled = true; // Enabled by default for automatic speech

    // --- Event Listeners ---
    // Enable speech after FIRST user interaction (MANDATORY for browser autoplay policy)
    document.addEventListener('click', () => {
        speechEnabled = true;
        console.log("TTS: Speech engine enabled by first interaction");
        
        // Optional priming to ensure audio engine is fully ready
        if (!window.speechSynthesis_primed) {
            primeSpeech();
            ttsAudio.play().catch(() => {}); 
            window.speechSynthesis_primed = true;
        }
    }, { once: true });

    sendBtn.addEventListener('click', handleSendMessage);
    chatInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') handleSendMessage();
    });

    voiceBtn.addEventListener('click', toggleVoiceRecognition);
    chatModeBtn.addEventListener('click', () => switchMode('chat'));
    dtmfModeBtn.addEventListener('click', () => switchMode('dtmf'));

    soundToggleBtn.addEventListener('click', (e) => {
        e.stopPropagation(); // Prevent document click trigger
        isSoundEnabled = !isSoundEnabled;
        if (isSoundEnabled) {
            soundToggleBtn.classList.add('active');
            soundToggleBtn.innerHTML = '<i class="fas fa-volume-up"></i>';
            speak("Sound enabled");
        } else {
            soundToggleBtn.classList.remove('active');
            soundToggleBtn.innerHTML = '<i class="fas fa-volume-mute"></i>';
            window.speechSynthesis.cancel();
        }
    });

    document.querySelectorAll('.dtmf-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            const digit = btn.dataset.digit;
            const currentState = document.getElementById('debug-state').textContent;

            if (digit === '#') {
                handleDtmfSubmit();
            } else if (digit === '*') {
                dtmfInputField.value = '';
            } else {
                dtmfInputField.value += digit;
                
                // --- AUTO-SUBMIT LOGIC FOR MENU OPTIONS ---
                // If in MAIN_MENU or TRAIN_SELECTION or CLASS_SELECTION, 
                // single digits should be processed immediately.
                const menuStates = ['MAIN_MENU', 'TRAIN_SELECTION', 'CLASS_SELECTION'];
                if (menuStates.includes(currentState) && dtmfInputField.value.length === 1) {
                    handleDtmfSubmit();
                }
                
                // If in DATE_SELECTION, options 1, 2, 3 are processed immediately.
                // Option 4 (Custom) waits for more digits.
                if (currentState === 'DATE_SELECTION') {
                    if (['1', '2', '3'].includes(dtmfInputField.value)) {
                        handleDtmfSubmit();
                    }
                }
            }
            // Visual feedback for DTMF press
            btn.style.transform = 'scale(0.9)';
            setTimeout(() => btn.style.transform = '', 100);
        });
    });

    dtmfSubmitBtn.addEventListener('click', handleDtmfSubmit);
    dtmfClearBtn.addEventListener('click', () => dtmfInputField.value = '');
    dtmfInputField.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') handleDtmfSubmit();
    });

    document.querySelectorAll('.action-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            const text = btn.dataset.text;
            chatInput.value = text;
            handleSendMessage();
        });
    });

    // --- Core Functions ---
    function handleSendMessage() {
        const message = chatInput.value.trim();
        if (message) {
            sendMessage(message);
        }
    }

    function handleDtmfSubmit() {
        const digits = dtmfInputField.value.trim();
        if (digits) {
            sendDtmf(digits);
            dtmfInputField.value = ''; // Clear after submission
        }
    }

    // Workaround for browser "user gesture" requirement for TTS
    function primeSpeech() {
        if (!window.speechSynthesis) return;
        const utterance = new SpeechSynthesisUtterance("");
        utterance.volume = 0;
        window.speechSynthesis.speak(utterance);
    }

    function handleDtmfPress(digit) {
        sendDtmf(digit);
    }

    function switchMode(mode) {
        if (mode === 'chat') {
            chatModeBtn.classList.add('active');
            dtmfModeBtn.classList.remove('active');
            chatInputContainer.classList.remove('hidden');
            dtmfInputContainer.classList.add('hidden');
        } else {
            dtmfModeBtn.classList.add('active');
            chatModeBtn.classList.remove('active');
            dtmfInputContainer.classList.remove('hidden');
            chatInputContainer.classList.add('hidden');
        }
    }

    // --- UI Functions ---
    function appendMessage(role, content) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${role}`;
        
        // Handle multi-line and potential grid options in content
        let formattedContent = content.replace(/\n/g, '<br>');
        
        let messageHTML = `
            <div class="bubble">
                <div class="bubble-content">${formattedContent}</div>
        `;

        // Add replay button for system messages
        if (role === 'system') {
            messageHTML += `
                <button class="replay-btn" title="Hear message">
                    <i class="fas fa-volume-up"></i>
                </button>
            `;
        }

        messageHTML += `</div>`;
        messageDiv.innerHTML = messageHTML;
        
        if (role === 'system') {
            const btn = messageDiv.querySelector('.replay-btn');
            btn.onclick = (e) => {
                e.stopPropagation();
                speak(content);
            };
        }
        
        chatMessages.appendChild(messageDiv);
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }

    function updateDebugPanel(state, intent, confidence, entities, history, dtmf_buffer) {
        document.getElementById('debug-state').textContent = state;
        document.getElementById('debug-intent').textContent = intent;
        document.getElementById('debug-confidence').textContent = `${(confidence * 100).toFixed(1)}%`;
        document.getElementById('debug-confidence-bar').style.width = `${confidence * 100}%`;
        
        // Update entity values
        document.getElementById('entity-source').textContent = entities.source || 'None';
        document.getElementById('entity-destination').textContent = entities.destination || 'None';
        document.getElementById('entity-date').textContent = entities.date || 'None';
        document.getElementById('entity-train').textContent = entities.selected_train || 'None';
        document.getElementById('entity-class').textContent = entities.train_class || 'None';

        // Update Buffer Display (Requested)
        const bufferDisplay = document.getElementById('debug-buffer');
        if (bufferDisplay) {
            bufferDisplay.textContent = dtmf_buffer || 'Empty';
        }

        // Update classes for styling
        ['source', 'destination', 'date', 'train', 'class'].forEach(key => {
            const el = document.getElementById(`entity-${key}`);
            let val;
            if (key === 'class') val = entities.train_class;
            else if (key === 'train') val = entities.selected_train;
            else val = entities[key];
            
            if (val) el.classList.remove('empty');
            else el.classList.add('empty');
        });

        // Update history log
        const historyDiv = document.getElementById('debug-history');
        if (historyDiv) {
            historyDiv.innerHTML = history.map(log => `
                <div class="history-item">
                    <span class="role ${log.role}">${log.role.toUpperCase()}</span>
                    <span class="content">${log.content}</span>
                </div>
            `).join('');
            historyDiv.scrollTop = historyDiv.scrollHeight;
        }
    }

    function renderSuggestionButtons(state) {
        console.log("Rendering suggestions for state:", state);
        const suggestionsContainer = document.getElementById('suggestion-buttons');
        suggestionsContainer.innerHTML = '';
        
        let suggestions = [];
        if (state === 'MAIN_MENU') {
            suggestions = ['Book Ticket', 'PNR Status', 'Train Schedule', 'Cancel Ticket'];
        } else if (state === 'ASK_SOURCE') {
            suggestions = ['Delhi', 'Mumbai', 'Bangalore', 'Hyderabad'];
        } else if (state === 'ASK_DESTINATION') {
            suggestions = ['Chennai', 'Kolkata', 'Pune', 'Lucknow'];
        } else if (state === 'DATE_SELECTION') {
            suggestions = ['Today', 'Tomorrow', 'Next Monday'];
        } else if (state === 'TRAIN_SELECTION') {
            suggestions = ['Confirm first train', 'Select Shatabdi'];
        } else if (state === 'CLASS_SELECTION') {
            suggestions = ['First Class', 'AC 2 Tier', 'Sleeper'];
        }

        if (suggestions.length > 0) {
            suggestions.forEach(text => {
                const btn = document.createElement('button');
                btn.className = 'action-btn'; // Use existing action-btn style
                btn.textContent = text;
                btn.onclick = () => {
                    chatInput.value = text;
                    handleSendMessage();
                };
                suggestionsContainer.appendChild(btn);
            });
            suggestionsContainer.style.display = 'flex';
        } else {
            suggestionsContainer.style.display = 'none';
        }
    }

    // --- API Communication ---
    async function sendMessage(message) {
        if (!message.trim()) return;
        console.log("[CLIENT] Sending Chat:", message);

        appendMessage('user', message);
        chatInput.value = '';
        renderSuggestionButtons('LOADING'); // Clear suggestions while loading

        try {
            const response = await fetch('/chat', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ 
                    message, 
                    session_id: SESSION_ID
                })
            });
            const data = await response.json();
            handleApiResponse(data);
        } catch (error) {
            console.error("Error sending message:", error);
            appendMessage('system', 'Error communicating with the server.');
        }
    }

    async function sendDtmf(digits) {
        console.log("[CLIENT] Sending DTMF:", digits);
        appendMessage('user', `DTMF: ${digits}`);
        try {
            const response = await fetch('/dtmf', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ 
                    digit: digits, 
                    session_id: SESSION_ID
                })
            });
            const data = await response.json();
            handleApiResponse(data);
        } catch (error) {
            console.error("Error sending DTMF:", error);
            appendMessage('system', 'Error communicating with the server.');
        }
    }

    function handleApiResponse(data) {
        // Reduced delay to ensure user gesture context is preserved for TTS
        setTimeout(() => {
            appendMessage('system', data.response);
            updateDebugPanel(data.state, data.intent, data.confidence, data.entities, data.history, data.dtmf_buffer);
            renderSuggestionButtons(data.state);
            speak(data.response);
        }, 100);
    }

    // --- Text-to-Speech (TTS) ---
    function speak(text) {
        if (!text || !speechEnabled || !isSoundEnabled) {
            console.log("TTS: Skipped (text empty, sound muted, or waiting for first interaction)");
            return;
        }

        // Cancel previous speech to prevent overlapping
        if (window.speechSynthesis) {
            window.speechSynthesis.cancel();
        }

        const utterance = new SpeechSynthesisUtterance(text);

        utterance.lang = "en-IN";
        utterance.rate = 1;
        utterance.pitch = 1;
        utterance.volume = 1;

        // Ensure voices are loaded and set an appropriate one
        const voices = window.speechSynthesis.getVoices();
        if (voices.length > 0) {
            utterance.voice = voices.find(v => v.lang.includes('en-IN')) || voices[0];
        }

        console.log("TTS Speaking automatically:", text.substring(0, 50));
        window.speechSynthesis.speak(utterance);
    }

    // --- Method 2: Backend TTS (Fallback) ---
    function speakViaBackend(text) {
        if (!isSoundEnabled || !speechEnabled) return;
        
        console.log(`TTS: Fetching audio from backend for: ${text.substring(0, 30)}...`);
        ttsAudio.src = `/tts?text=${encodeURIComponent(text)}`;
        ttsAudio.play().catch(e => console.error("Backend TTS failed", e));
    }

    // --- Voice Recognition ---
    if ('webkitSpeechRecognition' in window) {
        recognition = new webkitSpeechRecognition();
        recognition.continuous = false;
        recognition.lang = 'en-US';

        recognition.onstart = () => {
            isRecognizing = true;
            voiceBtn.classList.add('active');
            voiceBtn.style.boxShadow = '0 0 25px var(--accent-pink)';
        };

        recognition.onend = () => {
            isRecognizing = false;
            voiceBtn.classList.remove('active');
            voiceBtn.style.boxShadow = '';
        };

        recognition.onresult = (event) => {
            const transcript = event.results[0][0].transcript;
            chatInput.value = transcript;
            handleSendMessage();
        };
    } else {
        voiceBtn.style.display = 'none';
    }

    function toggleVoiceRecognition() {
        if (isRecognizing) recognition.stop();
        else recognition.start();
    }
});
