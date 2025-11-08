/**
 * ADAPTIVE TYPEWRITER FOR SUPERHUMAN STREAMING
 * ============================================
 * File: app/static/js/adaptiveTypewriter.js
 * Version: 1.0.0 - "BEYOND-CHATGPT"
 * 
 * Features:
 * - Variable speed based on punctuation
 * - Smooth word-by-word display
 * - Auto-pause at sentence boundaries
 * - Markdown-aware chunking
 * - Performance optimized
 * 
 * خصائص خارقة:
 * - سرعة متغيرة حسب علامات الترقيم
 * - عرض سلس كلمة بكلمة
 * - توقف تلقائي عند حدود الجمل
 * - دعم Markdown
 * - أداء محسّن
 */

class AdaptiveTypewriter {
  /**
   * Create a new adaptive typewriter
   * @param {HTMLElement} targetElement - Target DOM element to type into
   * @param {Object} options - Configuration options
   */
  constructor(targetElement, options = {}) {
    this.targetElement = targetElement;
    this.options = {
      baseDelayMs: 3,                    // Base delay between characters (ms)
      punctuationDelayMultiplier: 6,     // Multiplier for punctuation delays
      commaDelayMultiplier: 2,           // Multiplier for comma delays  
      charsPerStep: 5,                   // Characters to display per animation frame
      enableMarkdown: true,              // Enable markdown formatting
      autoScroll: true,                  // Auto-scroll as content appears
      ...options
    };
    
    // State
    this.queue = [];                     // Queue of text chunks to display
    this.isTyping = false;               // Currently typing flag
    this.currentText = '';               // Accumulated text
    this.typingPromise = null;           // Promise for typing completion
    
    // Performance tracking
    this.startTime = null;
    this.charsTyped = 0;
  }
  
  /**
   * Append text to the typewriter queue
   * @param {string} text - Text to append
   */
  append(text) {
    if (!text) return;
    
    this.queue.push(text);
    
    // Start typing if not already typing
    if (!this.isTyping) {
      this.startTyping();
    }
  }
  
  /**
   * Start the typing animation
   */
  async startTyping() {
    if (this.isTyping) return;
    
    this.isTyping = true;
    this.startTime = performance.now();
    
    while (this.queue.length > 0) {
      const chunk = this.queue.shift();
      await this.typeChunk(chunk);
    }
    
    this.isTyping = false;
    
    // Log performance metrics
    const duration = performance.now() - this.startTime;
    const charsPerSecond = (this.charsTyped / duration) * 1000;
    console.log(`⚡ Typewriter stats: ${this.charsTyped} chars in ${duration.toFixed(0)}ms (${charsPerSecond.toFixed(0)} chars/s)`);
  }
  
  /**
   * Type a single chunk of text
   * @param {string} chunk - Text chunk to type
   */
  async typeChunk(chunk) {
    const chars = chunk.split('');
    
    for (let i = 0; i < chars.length; i += this.options.charsPerStep) {
      // Get next batch of characters
      const batch = chars.slice(i, i + this.options.charsPerStep).join('');
      
      // Append to current text
      this.currentText += batch;
      this.charsTyped += batch.length;
      
      // Update DOM
      this.updateDisplay();
      
      // Calculate delay based on last character
      const lastChar = batch[batch.length - 1];
      const delay = this.calculateDelay(lastChar);
      
      // Wait for the delay
      await this.sleep(delay);
    }
  }
  
  /**
   * Calculate delay based on character type
   * @param {string} char - Character to check
   * @returns {number} Delay in milliseconds
   */
  calculateDelay(char) {
    const base = this.options.baseDelayMs;
    
    // Longer pause after sentences
    if (char === '.' || char === '!' || char === '?') {
      return base * this.options.punctuationDelayMultiplier;
    }
    
    // Medium pause after commas
    if (char === ',' || char === ';' || char === ':') {
      return base * this.options.commaDelayMultiplier;
    }
    
    // Longer pause after line breaks
    if (char === '\n') {
      return base * this.options.punctuationDelayMultiplier;
    }
    
    // Default delay
    return base;
  }
  
  /**
   * Update the target element with current text
   */
  updateDisplay() {
    if (this.options.enableMarkdown) {
      // Apply markdown-like formatting
      const formatted = this.formatMarkdown(this.currentText);
      this.targetElement.innerHTML = formatted;
    } else {
      // Plain text with escaped HTML
      this.targetElement.textContent = this.currentText;
    }
    
    // Auto-scroll if enabled
    if (this.options.autoScroll) {
      this.autoScroll();
    }
  }
  
  /**
   * Format text with markdown-like styling
   * @param {string} text - Text to format
   * @returns {string} Formatted HTML
   */
  formatMarkdown(text) {
    // Escape HTML first
    let formatted = text
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#039;');
    
    // Apply markdown-style formatting
    formatted = formatted
      // Code blocks (triple backticks)
      .replace(/```([\s\S]*?)```/g, '<pre style="background: rgba(0,0,0,0.05); padding: 0.75rem; border-radius: 4px; overflow-x: auto; margin: 0.5rem 0;"><code>$1</code></pre>')
      // Inline code (single backticks)
      .replace(/`([^`]+)`/g, '<code style="background: rgba(0,0,0,0.1); padding: 0.2rem 0.4rem; border-radius: 3px; font-family: monospace; font-size: 0.9em;">$1</code>')
      // Bold text
      .replace(/\*\*([^*]+)\*\*/g, '<strong style="font-weight: 600;">$1</strong>')
      // Italic text
      .replace(/\*([^*]+)\*/g, '<em>$1</em>')
      // Headers
      .replace(/^### (.*?)$/gm, '<h3 style="margin-top: 1rem; margin-bottom: 0.5rem; font-size: 1.1em; font-weight: 600;">$1</h3>')
      .replace(/^## (.*?)$/gm, '<h2 style="margin-top: 1rem; margin-bottom: 0.5rem; font-size: 1.25em; font-weight: 600;">$1</h2>')
      .replace(/^# (.*?)$/gm, '<h1 style="margin-top: 1rem; margin-bottom: 0.5rem; font-size: 1.5em; font-weight: 600;">$1</h1>')
      // Line breaks
      .replace(/\n\n/g, '<br><br>')
      .replace(/\n/g, '<br>');
    
    return formatted;
  }
  
  /**
   * Auto-scroll the target element into view
   */
  autoScroll() {
    // Find the scrollable parent (usually messages container)
    let scrollParent = this.targetElement.parentElement;
    while (scrollParent && scrollParent !== document.body) {
      const overflow = window.getComputedStyle(scrollParent).overflowY;
      if (overflow === 'auto' || overflow === 'scroll') {
        scrollParent.scrollTop = scrollParent.scrollHeight;
        break;
      }
      scrollParent = scrollParent.parentElement;
    }
  }
  
  /**
   * Sleep for specified milliseconds
   * @param {number} ms - Milliseconds to sleep
   * @returns {Promise} Promise that resolves after delay
   */
  sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
  }
  
  /**
   * Clear all queued text and reset
   */
  clear() {
    this.queue = [];
    this.currentText = '';
    this.charsTyped = 0;
    this.targetElement.innerHTML = '';
  }
  
  /**
   * Wait for all typing to complete
   * @returns {Promise} Promise that resolves when typing is done
   */
  async waitForCompletion() {
    while (this.isTyping || this.queue.length > 0) {
      await this.sleep(50);
    }
  }
  
  /**
   * Get performance metrics
   * @returns {Object} Performance metrics
   */
  getMetrics() {
    const duration = this.startTime ? performance.now() - this.startTime : 0;
    return {
      charsTyped: this.charsTyped,
      durationMs: duration,
      charsPerSecond: duration > 0 ? (this.charsTyped / duration) * 1000 : 0,
      queueLength: this.queue.length,
      isTyping: this.isTyping
    };
  }
}

// Export for use in other scripts
if (typeof module !== 'undefined' && module.exports) {
  module.exports = AdaptiveTypewriter;
}
