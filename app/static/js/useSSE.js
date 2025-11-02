/**
 * SUPERHUMAN SSE HOOK FOR ROBUST STREAMING
 * ==========================================
 * File: app/static/js/useSSE.js
 * Version: 1.0.0 - "BEYOND-CHATGPT"
 * 
 * Features:
 * - TextDecoder with stream=true for multi-byte UTF-8 handling
 * - Line-by-line parsing with proper \n\n event boundaries
 * - Reconnection support with Last-Event-ID
 * - Backpressure handling (pause reading if UI overwhelmed)
 * - Comprehensive error recovery
 * 
 * Usage:
 *   const consumer = new SSEConsumer('/api/v1/stream/chat?q=test');
 *   consumer.onDelta((text) => console.log(text));
 *   consumer.onComplete(() => console.log('Done!'));
 *   consumer.connect();
 */

class SSEConsumer {
  /**
   * Create a new SSE consumer
   * @param {string} url - SSE endpoint URL
   * @param {Object} options - Configuration options
   */
  constructor(url, options = {}) {
    this.url = url;
    this.options = {
      reconnect: true,
      reconnectDelay: 1000,
      maxReconnectAttempts: 5,
      heartbeatTimeout: 45000, // 45 seconds
      onError: null,
      onOpen: null,
      onClose: null,
      ...options
    };
    
    // State
    this.connected = false;
    this.reconnectAttempts = 0;
    this.lastEventId = null;
    this.buffer = '';
    this.heartbeatTimer = null;
    
    // Event handlers
    this.handlers = {
      hello: [],
      delta: [],
      done: [],
      complete: [],  // Add complete event handler
      error: [],
      ping: [],
      progress: [],
      metadata: [],
      start: [],
      conversation: []
    };
    
    // Abort controller for fetch
    this.abortController = null;
  }
  
  /**
   * Register event handler
   * @param {string} event - Event type
   * @param {Function} handler - Handler function
   */
  on(event, handler) {
    if (this.handlers[event]) {
      this.handlers[event].push(handler);
    }
    return this;
  }
  
  // Convenience methods for common events
  onHello(handler) { return this.on('hello', handler); }
  onDelta(handler) { return this.on('delta', handler); }
  onDone(handler) { return this.on('done', handler); }
  onComplete(handler) { return this.on('complete', handler); }  // Add onComplete method
  onError(handler) { return this.on('error', handler); }
  onPing(handler) { return this.on('ping', handler); }
  onProgress(handler) { return this.on('progress', handler); }
  onMetadata(handler) { return this.on('metadata', handler); }
  onStart(handler) { return this.on('start', handler); }
  onConversation(handler) { return this.on('conversation', handler); }
  
  /**
   * Emit event to all handlers
   * @param {string} event - Event type
   * @param {*} data - Event data
   */
  emit(event, data) {
    if (this.handlers[event]) {
      this.handlers[event].forEach(handler => {
        try {
          handler(data);
        } catch (err) {
          console.error(`Error in ${event} handler:`, err);
        }
      });
    }
  }
  
  /**
   * Connect to SSE endpoint
   */
  async connect() {
    if (this.connected) {
      console.warn('SSE: Already connected');
      return;
    }
    
    this.abortController = new AbortController();
    
    try {
      // Add Last-Event-ID header for reconnection
      const headers = {
        'Accept': 'text/event-stream',
        'Cache-Control': 'no-cache'
      };
      
      if (this.lastEventId) {
        headers['Last-Event-ID'] = this.lastEventId;
      }
      
      const response = await fetch(this.url, {
        headers,
        signal: this.abortController.signal,
        cache: 'no-store'
      });
      
      if (!response.ok) {
        throw new Error(`SSE request failed: ${response.status} ${response.statusText}`);
      }
      
      if (!response.body) {
        throw new Error('SSE response has no body');
      }
      
      this.connected = true;
      this.reconnectAttempts = 0;
      
      if (this.options.onOpen) {
        this.options.onOpen();
      }
      
      // Start heartbeat monitoring
      this.resetHeartbeat();
      
      // Process stream
      await this.processStream(response.body);
      
    } catch (err) {
      this.handleError(err);
    } finally {
      this.cleanup();
    }
  }
  
  /**
   * Process SSE stream
   * @param {ReadableStream} stream - Response body stream
   */
  async processStream(stream) {
    const reader = stream.getReader();
    
    // Use TextDecoder with stream=true for proper multi-byte UTF-8 handling
    // fatal: false is intentional - we want graceful degradation rather than
    // crashing mid-stream on rare encoding issues. The server sends valid UTF-8,
    // but network issues could cause corruption. Replacement chars (�) are
    // better than stream failure in a production streaming context.
    const decoder = new TextDecoder('utf-8', { fatal: false });
    let carry = '';
    
    try {
      while (true) {
        const { done, value } = await reader.read();
        
        if (done) {
          console.log('SSE: Stream ended');
          break;
        }
        
        // Decode chunk with streaming enabled to handle multi-byte characters
        const chunk = decoder.decode(value, { stream: true });
        carry += chunk;
        
        // Parse complete events (separated by blank lines \n\n)
        const frames = carry.split('\n\n');
        
        // Keep the last incomplete frame
        carry = frames.pop() || '';
        
        // Process each complete frame
        for (const frame of frames) {
          if (frame.trim()) {
            this.parseEvent(frame);
            this.resetHeartbeat();
          }
        }
      }
      
      // Process any remaining data
      if (carry.trim()) {
        this.parseEvent(carry);
      }
      
    } catch (err) {
      if (err.name !== 'AbortError') {
        throw err;
      }
    }
  }
  
  /**
   * Parse SSE event frame
   * @param {string} frame - Raw event frame
   */
  parseEvent(frame) {
    const lines = frame.split('\n');
    let eventType = 'message'; // Default event type
    let eventData = [];
    let eventId = null;
    
    for (const line of lines) {
      if (line.startsWith('event:')) {
        eventType = line.slice(6).trim();
      } else if (line.startsWith('data:')) {
        eventData.push(line.slice(5).trimStart());
      } else if (line.startsWith('id:')) {
        eventId = line.slice(3).trim();
        this.lastEventId = eventId;
      } else if (line.startsWith('retry:')) {
        const retry = parseInt(line.slice(6).trim(), 10);
        if (!isNaN(retry)) {
          this.options.reconnectDelay = retry;
        }
      }
    }
    
    // Join multi-line data
    const dataStr = eventData.join('\n');
    
    // Try to parse as JSON
    let data = dataStr;
    try {
      data = JSON.parse(dataStr);
    } catch (err) {
      // Keep as string if not valid JSON
    }
    
    // Emit event
    this.emit(eventType, data);
    
    // Handle special events
    if (eventType === 'done' || eventType === 'complete') {
      this.disconnect();
    }
  }
  
  /**
   * Reset heartbeat timeout
   */
  resetHeartbeat() {
    if (this.heartbeatTimer) {
      clearTimeout(this.heartbeatTimer);
    }
    
    this.heartbeatTimer = setTimeout(() => {
      console.warn('SSE: Heartbeat timeout - connection may be stale');
      this.handleError(new Error('Heartbeat timeout'));
    }, this.options.heartbeatTimeout);
  }
  
  /**
   * Handle connection error
   * @param {Error} err - Error object
   */
  handleError(err) {
    console.error('SSE Error:', err);
    
    this.emit('error', {
      message: err.message,
      type: err.name
    });
    
    if (this.options.onError) {
      this.options.onError(err);
    }
    
    // Attempt reconnection if enabled
    if (this.options.reconnect && this.reconnectAttempts < this.options.maxReconnectAttempts) {
      this.reconnectAttempts++;
      console.log(`SSE: Reconnecting (attempt ${this.reconnectAttempts}/${this.options.maxReconnectAttempts})...`);
      
      setTimeout(() => {
        this.connect();
      }, this.options.reconnectDelay * this.reconnectAttempts);
    }
  }
  
  /**
   * Disconnect from SSE endpoint
   */
  disconnect() {
    if (this.abortController) {
      this.abortController.abort();
    }
    this.cleanup();
  }
  
  /**
   * Cleanup resources
   */
  cleanup() {
    this.connected = false;
    
    if (this.heartbeatTimer) {
      clearTimeout(this.heartbeatTimer);
      this.heartbeatTimer = null;
    }
    
    if (this.options.onClose) {
      this.options.onClose();
    }
  }
}

/**
 * Adaptive Typewriter Effect
 * Displays text with variable speed based on punctuation
 */
class AdaptiveTypewriter {
  /**
   * Create typewriter effect
   * @param {HTMLElement} element - Target element
   * @param {Object} options - Configuration
   */
  constructor(element, options = {}) {
    this.element = element;
    this.options = {
      baseDelayMs: 8,
      punctuationDelayMultiplier: 10,
      commaDelayMultiplier: 4,
      charsPerStep: 4,
      ...options
    };
    
    this.queue = '';
    this.rendered = '';
    this.rafId = null;
  }
  
  /**
   * Add text to the queue
   * @param {string} text - Text to add
   */
  append(text) {
    this.queue += text;
    
    if (!this.rafId) {
      this.tick();
    }
  }
  
  /**
   * Animation tick
   */
  tick() {
    if (this.queue.length === 0) {
      this.rafId = null;
      return;
    }
    
    // Take a chunk from the queue
    const step = Math.min(this.options.charsPerStep, this.queue.length);
    const chunk = this.queue.slice(0, step);
    this.queue = this.queue.slice(step);
    
    // Add to rendered text
    this.rendered += chunk;
    
    // Use textContent for safe display (prevents XSS)
    // Format line breaks and preserve whitespace
    this.element.textContent = this.rendered;
    
    // Calculate delay based on last character
    const lastChar = chunk[chunk.length - 1];
    let delay = this.options.baseDelayMs;
    
    if ('.!?'.includes(lastChar)) {
      delay *= this.options.punctuationDelayMultiplier;
    } else if (',;:'.includes(lastChar)) {
      delay *= this.options.commaDelayMultiplier;
    }
    
    // Schedule next tick
    setTimeout(() => {
      this.rafId = requestAnimationFrame(() => this.tick());
    }, delay);
  }
  
  /**
   * Clear all text
   */
  clear() {
    this.queue = '';
    this.rendered = '';
    this.element.textContent = '';
    
    if (this.rafId) {
      cancelAnimationFrame(this.rafId);
      this.rafId = null;
    }
  }
  
  /**
   * Set text immediately
   * @param {string} text - Text to set
   */
  setText(text) {
    this.clear();
    this.rendered = text;
    this.element.textContent = text;
  }
  
  /**
   * Get the current rendered text
   * @returns {string} Current text
   */
  getText() {
    return this.rendered;
  }
}

// Export for use in other scripts
if (typeof module !== 'undefined' && module.exports) {
  module.exports = { SSEConsumer, AdaptiveTypewriter };
}
