class OutlookMCPApp {
    constructor() {
        this.apiBaseUrl = window.location.origin;
        this.currentFile = null;
        this.init();
    }

    init() {
        // Initialize form toggle functionality
        this.initFormToggle();
        
        // Event listeners
        const intelligentSearchBtn = document.getElementById('intelligent-search-btn');
        const downloadBtn = document.getElementById('download-btn');
        const sendToExternalBtn = document.getElementById('send-to-external-api');
        
        if (intelligentSearchBtn) {
            intelligentSearchBtn.addEventListener('click', (e) => {
                console.log('🤖 Smart Search button clicked');
                e.preventDefault();
                this.intelligentSearch();
            });
            console.log('✅ Smart Search event listener attached');
        } else {
            console.error('❌ Smart Search button not found');
        }
        
        if (downloadBtn) {
            downloadBtn.addEventListener('click', (e) => {
                console.log('📥 Download button clicked');
                e.preventDefault();
                this.downloadAttachment();
            });
            console.log('✅ Download event listener attached');
        } else {
            console.error('❌ Download button not found');
        }
        
        if (sendToExternalBtn) {
            sendToExternalBtn.addEventListener('click', (e) => {
                console.log('🚀 Send to External API button clicked');
                e.preventDefault();
                this.sendToExternalAPI();
            });
            console.log('✅ External API event listener attached');
        } else {
            console.error('❌ External API button not found');
        }
        
        // Test button for debugging
        const testBtn = document.getElementById('test-btn');
        if (testBtn) {
            testBtn.addEventListener('click', (e) => {
                console.log('🐛 Test button clicked');
                e.preventDefault();
                this.testJavaScript();
            });
            console.log('✅ Test button event listener attached');
        }
    }

    initFormToggle() {
        const methodRadios = document.querySelectorAll('input[name="method"]');
        const directSection = document.getElementById('direct-section');
        const searchSection = document.getElementById('search-section');

        methodRadios.forEach(radio => {
            radio.addEventListener('change', () => {
                if (radio.value === 'direct') {
                    directSection.classList.remove('hidden');
                    searchSection.classList.add('hidden');
                } else {
                    directSection.classList.add('hidden');
                    searchSection.classList.remove('hidden');
                }
            });
        });
    }

    testJavaScript() {
        console.log('🐛 Testing JavaScript functionality...');
        this.showMessage('🐛 JavaScript is working! Event listeners are properly attached.', 'success');
        
        // Test form field access
        const apiKey = document.getElementById('composio_api_key').value;
        const hasApiKey = !!apiKey.trim();
        
        console.log('📋 Form field test:', { hasApiKey });
        
        if (hasApiKey) {
            this.showMessage('✅ API Key field is accessible and has content', 'success');
        } else {
            this.showMessage('⚠️ API Key field is empty - please enter your Composio API key to test fully', 'warning');
        }
        
        // Test loading indicator
        const loadingElement = document.getElementById('loading');
        if (loadingElement) {
            loadingElement.classList.add('active');
            this.showMessage('🔄 Testing loading indicator...', 'info');
            
            setTimeout(() => {
                loadingElement.classList.remove('active');
                this.showMessage('✅ Loading indicator test complete!', 'success');
            }, 2000);
        }
    }

    async intelligentSearch() {
        console.log('🤖 Starting intelligent search...');
        
        // Show immediate feedback
        this.showMessage('🤖 Starting intelligent search...', 'info');
        
        // Get Composio configuration
        const composioApiKey = document.getElementById('composio_api_key').value.trim();
        const composioBaseUrl = document.getElementById('composio_base_url').value.trim();
        const composioServerId = document.getElementById('composio_server_id').value.trim();
        const composioUserId = document.getElementById('composio_user_id').value.trim();

        console.log('📋 Configuration:', { 
            hasApiKey: !!composioApiKey, 
            baseUrl: composioBaseUrl, 
            serverId: composioServerId, 
            userId: composioUserId 
        });

        if (!composioApiKey) {
            this.showMessage('❌ Composio API Key is required', 'error');
            return;
        }

        // Get search parameters
        const senderEmail = document.getElementById('sender_email_direct').value.trim() || 
                           document.getElementById('sender_email').value.trim();
        const emailSubject = document.getElementById('email_subject').value.trim();
        const attachmentName = document.getElementById('attachment_name_direct').value.trim() || 
                              document.getElementById('attachment_name').value.trim();

        if (!senderEmail && !emailSubject && !attachmentName) {
            this.showMessage('Please provide at least one search parameter (sender email, subject, or attachment name)', 'error');
            return;
        }

        const requestData = {
            composio_api_key: composioApiKey,
            composio_base_url: composioBaseUrl || 'https://mcp.composio.dev',
            composio_server_id: composioServerId || '76b9c7a4-85bc-4711-a848-f0d56fde2a5a',
            composio_user_id: composioUserId || 'userJS1',
            sender_email: senderEmail || null,
            email_subject: emailSubject || null,
            attachment_name: attachmentName || null,
            days_back: 7
        };

        const loadingElement = document.getElementById('loading');
        const formElement = document.getElementById('downloadForm');

        // Show loading state
        loadingElement.classList.add('active');
        formElement.style.opacity = '0.5';

        try {
            this.showMessage('🤖 Running intelligent search...', 'info');

            const response = await fetch(`${this.apiBaseUrl}/api/intelligent-search`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(requestData)
            });

            const result = await response.json();

            if (!response.ok) {
                throw new Error(result.detail || 'Intelligent search failed');
            }

            this.showMessage('✅ Intelligent search completed!', 'success');
            this.displayIntelligentSearchResults(result);

        } catch (error) {
            console.error('Intelligent search error:', error);
            this.showMessage(`Intelligent search error: ${error.message}`, 'error');
        } finally {
            // Hide loading state
            loadingElement.classList.remove('active');
            formElement.style.opacity = '1';
        }
    }

    async downloadAttachment() {
        console.log('📥 Starting download attachment process...');
        
        // Get Composio configuration
        const composioApiKey = document.getElementById('composio_api_key').value.trim();
        const composioBaseUrl = document.getElementById('composio_base_url').value.trim();
        const composioServerId = document.getElementById('composio_server_id').value.trim();
        const composioUserId = document.getElementById('composio_user_id').value.trim();

        console.log('📋 Download Configuration:', { 
            hasApiKey: !!composioApiKey, 
            baseUrl: composioBaseUrl, 
            serverId: composioServerId, 
            userId: composioUserId 
        });

        if (!composioApiKey) {
            this.showMessage('❌ Composio API Key is required', 'error');
            return;
        }

        // Get method with better error handling
        const methodElement = document.querySelector('input[name="method"]:checked');
        const method = methodElement ? methodElement.value : 'search'; // Default to search if no radio button found
        
        console.log('🔧 Selected method:', method);
        
        let requestData = {
            days_back: 7,
            composio_api_key: composioApiKey,
            composio_base_url: composioBaseUrl || 'https://mcp.composio.dev',
            composio_server_id: composioServerId || '76b9c7a4-85bc-4711-a848-f0d56fde2a5a',
            composio_user_id: composioUserId || 'userJS1'
        };

        if (method === 'direct') {
            // Direct IDs method
            console.log('🎯 Using direct IDs method...');
            const senderEmail = document.getElementById('sender_email_direct')?.value.trim() || '';
            const attachmentId = document.getElementById('attachment_id')?.value.trim() || '';
            const messageId = document.getElementById('message_id')?.value.trim() || '';
            const attachmentName = document.getElementById('attachment_name_direct')?.value.trim() || '';

            console.log('📋 Direct method data:', { senderEmail, hasAttachmentId: !!attachmentId, hasMessageId: !!messageId, attachmentName });

            if (!attachmentId || !messageId) {
                this.showMessage('❌ Attachment ID and Message ID are required for direct method', 'error');
                return;
            }

            requestData.sender_email = senderEmail || null;
            requestData.attachment_id = attachmentId;
            requestData.message_id = messageId;
            requestData.attachment_name = attachmentName || null;
        } else {
            // Search method
            console.log('🔍 Using search method...');
            const emailSubject = document.getElementById('email_subject')?.value.trim() || '';
            const senderEmail = document.getElementById('sender_email')?.value.trim() || '';
            const attachmentName = document.getElementById('attachment_name')?.value.trim() || '';

            console.log('📋 Search method data:', { emailSubject, senderEmail, attachmentName });

            // More flexible validation - require at least one search parameter
            if (!emailSubject && !senderEmail && !attachmentName) {
                this.showMessage('❌ Please provide at least one search parameter (sender email, subject, or attachment name)', 'error');
                return;
            }

            requestData.email_subject = emailSubject || null;
            requestData.sender_email = senderEmail || null;
            requestData.attachment_name = attachmentName || null;
        }

        const loadingElement = document.getElementById('loading');
        const formElement = document.getElementById('downloadForm');

        // Show loading state
        loadingElement.classList.add('active');
        formElement.style.opacity = '0.5';

        try {
            console.log('Sending request:', requestData);

            const response = await fetch(`${this.apiBaseUrl}/api/download-attachment`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(requestData)
            });

            const result = await response.json();
            console.log('Response:', result);

            if (!response.ok) {
                throw new Error(result.detail || 'Download failed');
            }

            this.displayResults(result, requestData);
            this.showMessage('File processed successfully!', 'success');

        } catch (error) {
            console.error('Download error:', error);
            this.showMessage(`Error: ${error.message}`, 'error');
        } finally {
            // Hide loading state
            loadingElement.classList.remove('active');
            formElement.style.opacity = '1';
        }
    }

    displayResults(result, requestData) {
        const resultsContainer = document.getElementById('results-container');
        const noResults = document.getElementById('no-results');
        const fileDetails = document.getElementById('file-details');
        const filePreview = document.getElementById('file-preview');

        // Store current file data
        this.currentFile = {
            data: result,
            filename: result.filename || requestData.attachment_name || 'attachment.pdf',
            content: result.content || result.file_content
        };

        if (result.status === 'success' && result.content) {
            // Show results
            resultsContainer.classList.remove('hidden');
            noResults.classList.add('hidden');

            // Update file details
            document.getElementById('file-name').textContent = this.currentFile.filename;
            document.getElementById('file-size').textContent = result.size || 'Unknown size';
            document.getElementById('file-type').textContent = result.content_type || 'application/pdf';
            document.getElementById('extraction-status').textContent = result.extraction_status || 'Available';

            // Show file preview or content info
            if (result.content_type && result.content_type.includes('pdf')) {
                filePreview.innerHTML = `
                    <div class="bg-red-50 p-4 rounded-lg border border-red-200">
                        <div class="flex items-center space-x-2 text-red-700">
                            <i class="fas fa-file-pdf text-2xl"></i>
                            <div>
                                <p class="font-medium">PDF Document</p>
                                <p class="text-sm">Ready for download and external processing</p>
                            </div>
                        </div>
                    </div>
                `;
            } else {
                filePreview.innerHTML = `
                    <div class="bg-gray-50 p-4 rounded-lg border border-gray-200">
                        <div class="flex items-center space-x-2 text-gray-700">
                            <i class="fas fa-file text-2xl"></i>
                            <div>
                                <p class="font-medium">File Content</p>
                                <p class="text-sm">Ready for processing</p>
                            </div>
                        </div>
                    </div>
                `;
            }

            fileDetails.classList.remove('hidden');
        } else {
            // Show no results
            resultsContainer.classList.add('hidden');
            noResults.classList.remove('hidden');
        }
    }

    downloadFile() {
        if (!this.currentFile) {
            this.showMessage('No file to download', 'error');
            return;
        }

        try {
            let content = this.currentFile.content;
            let mimeType = 'application/octet-stream';
            
            // Handle different content types
            if (typeof content === 'string') {
                if (content.startsWith('data:')) {
                    // Data URL format
                    const link = document.createElement('a');
                    link.href = content;
                    link.download = this.currentFile.filename;
                    link.click();
                    return;
                } else {
                    // Base64 or plain text
                    try {
                        content = atob(content);
                        mimeType = 'application/pdf';
                    } catch (e) {
                        // Not base64, treat as text
                        mimeType = 'text/plain';
                    }
                }
            }

            const blob = new Blob([content], { type: mimeType });
            const url = URL.createObjectURL(blob);
            const link = document.createElement('a');
            link.href = url;
            link.download = this.currentFile.filename;
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
            URL.revokeObjectURL(url);

            this.showMessage('File downloaded successfully!', 'success');
        } catch (error) {
            console.error('Download error:', error);
            this.showMessage(`Download error: ${error.message}`, 'error');
        }
    }

    async sendToExternalAPI() {
        if (!this.currentFile) {
            this.showMessage('No file to send to external system', 'error');
            return;
        }

        const apiUrl = document.getElementById('api_url').value.trim();
        const apiMethod = document.getElementById('api_method').value.trim();
        const apiKey = document.getElementById('external_api_key').value.trim();
        const customHeaders = document.getElementById('custom_headers').value.trim();

        if (!apiUrl) {
            this.showMessage('Please provide an API endpoint URL', 'error');
            return;
        }

        try {
            this.showMessage('Sending extracted data to external system...', 'info');

            const requestBody = {
                api_url: apiUrl,
                method: apiMethod || 'POST',
                file_data: this.currentFile.data
            };

            // Add API key if provided
            if (apiKey) {
                requestBody.api_key = apiKey;
            }

            // Parse and add custom headers if provided
            if (customHeaders) {
                try {
                    requestBody.headers = JSON.parse(customHeaders);
                } catch (e) {
                    this.showMessage('Invalid JSON format in custom headers', 'error');
                    return;
                }
            }

            const response = await fetch('/api/send-to-external-system', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(requestBody)
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || `External API request failed: ${response.status} ${response.statusText}`);
            }

            const apiResult = await response.json();
            console.log('External API response:', apiResult);

            this.showMessage('Successfully sent to external system!', 'success');
            
            // Display API results
            this.displayAPIResults(apiResult);

        } catch (error) {
            console.error('External API error:', error);
            this.showMessage(`External API error: ${error.message}`, 'error');
        }
    }

    displayAPIResults(result) {
        // Create a modal or section to show External API results
        const modal = document.createElement('div');
        modal.className = 'fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50';
        modal.innerHTML = `
            <div class="bg-white rounded-lg p-6 max-w-2xl w-full mx-4 max-h-96 overflow-y-auto">
                <div class="flex justify-between items-center mb-4">
                    <h3 class="text-lg font-semibold">External API Response</h3>
                    <button class="text-gray-500 hover:text-gray-700" onclick="this.parentElement.parentElement.parentElement.remove()">
                        <i class="fas fa-times"></i>
                    </button>
                </div>
                <div class="space-y-3">
                    <div>
                        <strong>Status:</strong> ${result.status}
                    </div>
                    <div>
                        <strong>Message:</strong> ${result.message}
                    </div>
                    <div>
                        <strong>API URL:</strong> ${result.api_url}
                    </div>
                    <div>
                        <strong>Method:</strong> ${result.method}
                    </div>
                    <div>
                        <strong>Response:</strong>
                        <pre class="bg-gray-100 p-3 rounded mt-2 text-sm overflow-x-auto">${JSON.stringify(result.api_response, null, 2)}</pre>
                    </div>
                </div>
            </div>
        `;
        document.body.appendChild(modal);
    }

    displayIntelligentSearchResults(result) {
        // Create results modal
        const modal = document.createElement('div');
        modal.className = 'fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50';
        modal.innerHTML = `
            <div class="bg-white rounded-lg p-6 max-w-4xl max-h-[80vh] overflow-y-auto">
                <div class="flex justify-between items-center mb-4">
                    <h3 class="text-xl font-bold text-gray-800">🤖 Intelligent Search Results</h3>
                    <button class="text-gray-500 hover:text-gray-700" onclick="this.parentElement.parentElement.parentElement.remove()">
                        <i class="fas fa-times"></i>
                    </button>
                </div>
                
                <div class="space-y-4">
                    <!-- Query Summary -->
                    <div class="bg-blue-50 p-4 rounded-lg">
                        <h4 class="font-semibold text-blue-800 mb-2">📊 Query Summary</h4>
                        <div class="grid grid-cols-2 gap-4 text-sm">
                            <div>Total Messages: <span class="font-medium">${result.query_results.total_messages}</span></div>
                            <div>With Attachments: <span class="font-medium">${result.query_results.messages_with_attachments}</span></div>
                        </div>
                    </div>
                    
                    <!-- Analysis Results -->
                    <div class="bg-purple-50 p-4 rounded-lg">
                        <h4 class="font-semibold text-purple-800 mb-2">🧠 Analysis Results</h4>
                        <div class="grid grid-cols-3 gap-4 text-sm">
                            <div>Total Candidates: <span class="font-medium">${result.analysis_results.total_candidates || 0}</span></div>
                            <div>High Confidence: <span class="font-medium">${result.analysis_results.high_confidence_matches || 0}</span></div>
                            <div>Medium Confidence: <span class="font-medium">${result.analysis_results.medium_confidence_matches || 0}</span></div>
                        </div>
                    </div>
                    
                    <!-- Best Match -->
                    ${result.recommended_download.status === 'success' ? `
                        <div class="bg-green-50 p-4 rounded-lg">
                            <h4 class="font-semibold text-green-800 mb-2">✨ Recommended Download</h4>
                            <div class="space-y-2 text-sm">
                                <div><strong>Attachment:</strong> ${result.recommended_download.attachment_name}</div>
                                <div><strong>Confidence:</strong> 
                                    <span class="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${
                                        result.recommended_download.confidence_score >= 0.8 ? 'bg-green-100 text-green-800' :
                                        result.recommended_download.confidence_score >= 0.6 ? 'bg-yellow-100 text-yellow-800' :
                                        'bg-red-100 text-red-800'
                                    }">
                                        ${(result.recommended_download.confidence_score * 100).toFixed(1)}%
                                    </span>
                                </div>
                                <div><strong>Match Reasons:</strong> ${result.recommended_download.match_reasons.join(', ')}</div>
                            </div>
                            
                            <div class="mt-4 flex space-x-3">
                                <button onclick="window.outlookApp.autoFillFromRecommendation(${JSON.stringify(result.recommended_download).replace(/"/g, '&quot;')})" 
                                        class="bg-green-600 hover:bg-green-700 text-white px-4 py-2 rounded text-sm">
                                    <i class="fas fa-magic mr-1"></i> Auto-Fill & Download
                                </button>
                                <button onclick="window.outlookApp.copyRecommendationIds('${result.recommended_download.attachment_id}', '${result.recommended_download.message_id}')" 
                                        class="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded text-sm">
                                    <i class="fas fa-copy mr-1"></i> Copy IDs
                                </button>
                            </div>
                        </div>
                    ` : `
                        <div class="bg-red-50 p-4 rounded-lg">
                            <h4 class="font-semibold text-red-800 mb-2">❌ No Suitable Match Found</h4>
                            <p class="text-sm text-red-600">${result.recommended_download.error || 'No attachments matched the search criteria with sufficient confidence.'}</p>
                        </div>
                    `}
                    
                    <!-- All Candidates (if any) -->
                    ${result.analysis_results.candidates && result.analysis_results.candidates.length > 0 ? `
                        <div class="bg-gray-50 p-4 rounded-lg">
                            <h4 class="font-semibold text-gray-800 mb-2">📋 All Candidates</h4>
                            <div class="space-y-2 max-h-40 overflow-y-auto">
                                ${result.analysis_results.candidates.map(candidate => `
                                    <div class="bg-white p-2 rounded border text-sm">
                                        <div class="flex justify-between items-start">
                                            <div>
                                                <div><strong>${candidate.attachment_name}</strong></div>
                                                <div class="text-gray-600">From: ${candidate.sender || 'Unknown'}</div>
                                                <div class="text-gray-600">Subject: ${candidate.subject || 'No subject'}</div>
                                            </div>
                                            <span class="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${
                                                candidate.confidence_score >= 0.8 ? 'bg-green-100 text-green-800' :
                                                candidate.confidence_score >= 0.6 ? 'bg-yellow-100 text-yellow-800' :
                                                'bg-red-100 text-red-800'
                                            }">
                                                ${(candidate.confidence_score * 100).toFixed(1)}%
                                            </span>
                                        </div>
                                    </div>
                                `).join('')}
                            </div>
                        </div>
                    ` : ''}
                </div>
            </div>
        `;
        
        document.body.appendChild(modal);
    }

    autoFillFromRecommendation(recommendation) {
        // Auto-fill form fields with recommended values
        document.getElementById('attachment_id').value = recommendation.attachment_id || '';
        document.getElementById('message_id').value = recommendation.message_id || '';
        document.getElementById('attachment_name_direct').value = recommendation.attachment_name || '';
        
        // Close modal
        document.querySelector('.fixed.inset-0').remove();
        
        // Show success message
        this.showMessage(`✅ Form auto-filled with recommended attachment: ${recommendation.attachment_name}`, 'success');
        
        // Optionally trigger download immediately
        setTimeout(() => {
            if (confirm('Would you like to download this attachment now?')) {
                this.downloadAttachment();
            }
        }, 1000);
    }

    copyRecommendationIds(attachmentId, messageId) {
        const text = `Attachment ID: ${attachmentId}\nMessage ID: ${messageId}`;
        navigator.clipboard.writeText(text).then(() => {
            this.showMessage('✅ IDs copied to clipboard', 'success');
        }).catch(() => {
            this.showMessage('❌ Failed to copy to clipboard', 'error');
        });
    }

    showMessage(message, type = 'info') {
        const messageContainer = document.getElementById('message-container') || this.createMessageContainer();
        
        const messageElement = document.createElement('div');
        messageElement.className = `message message-${type} p-4 mb-4 rounded-lg border`;
        
        let bgColor, textColor, icon;
        switch (type) {
            case 'success':
                bgColor = 'bg-green-50';
                textColor = 'text-green-800';
                icon = 'fas fa-check-circle';
                break;
            case 'error':
                bgColor = 'bg-red-50';
                textColor = 'text-red-800';
                icon = 'fas fa-exclamation-circle';
                break;
            case 'warning':
                bgColor = 'bg-yellow-50';
                textColor = 'text-yellow-800';
                icon = 'fas fa-exclamation-triangle';
                break;
            default:
                bgColor = 'bg-blue-50';
                textColor = 'text-blue-800';
                icon = 'fas fa-info-circle';
        }
        
        messageElement.className += ` ${bgColor} ${textColor}`;
        messageElement.innerHTML = `
            <div class="flex items-center space-x-2">
                <i class="${icon}"></i>
                <span>${message}</span>
            </div>
        `;
        
        messageContainer.appendChild(messageElement);
        
        // Auto-remove after 5 seconds
        setTimeout(() => {
            if (messageElement.parentNode) {
                messageElement.parentNode.removeChild(messageElement);
            }
        }, 5000);
    }

    createMessageContainer() {
        const container = document.createElement('div');
        container.id = 'message-container';
        container.className = 'fixed top-4 right-4 z-50 max-w-md';
        document.body.appendChild(container);
        return container;
    }
}

// Initialize the app when the page loads
document.addEventListener('DOMContentLoaded', () => {
    console.log('🚀 Initializing OutlookMCPApp...');
    window.outlookApp = new OutlookMCPApp();
    console.log('✅ OutlookMCPApp initialized successfully');
});
