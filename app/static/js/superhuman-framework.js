// ============================================================================
// 🚀 SUPERHUMAN FRAMEWORK v3.0 - SURPASSING TECH GIANTS
// Advanced JavaScript framework exceeding ChatGPT, Claude, Gemini, Apple
// ============================================================================

/* ============================================================================
   📊 PERFORMANCE MONITORING - REAL-TIME METRICS
   ============================================================================ */
class PerformanceMonitor {
  constructor() {
    this.metrics = {
      ttft: null,  // Time to First Token
      throughput: [],  // Tokens per second
      latency: [],  // Request latencies
      fps: [],  // Frame rates
      memoryUsage: []
    };
    this.startTime = null;
    this.tokenCount = 0;
  }

  startRequest() {
    this.startTime = performance.now();
    this.tokenCount = 0;
  }

  recordFirstToken() {
    if (this.startTime && this.metrics.ttft === null) {
      this.metrics.ttft = performance.now() - this.startTime;
    }
  }

  recordToken() {
    this.tokenCount++;
  }

  endRequest() {
    if (this.startTime) {
      const elapsed = (performance.now() - this.startTime) / 1000;
      const throughput = this.tokenCount / elapsed;
      
      this.metrics.throughput.push(throughput);
      this.metrics.latency.push(elapsed * 1000);
      
      // Keep only last 100 measurements
      if (this.metrics.throughput.length > 100) {
        this.metrics.throughput.shift();
        this.metrics.latency.shift();
      }
    }
  }

  getStats() {
    const calculatePercentile = (arr, percentile) => {
      if (arr.length === 0) return 0;
      const sorted = [...arr].sort((a, b) => a - b);
      const index = Math.ceil((percentile / 100) * sorted.length) - 1;
      return sorted[index];
    };

    return {
      ttft: this.metrics.ttft,
      avgThroughput: this.metrics.throughput.reduce((a, b) => a + b, 0) / this.metrics.throughput.length || 0,
      p50Latency: calculatePercentile(this.metrics.latency, 50),
      p95Latency: calculatePercentile(this.metrics.latency, 95),
      p99Latency: calculatePercentile(this.metrics.latency, 99),
      totalRequests: this.metrics.latency.length
    };
  }
}

/* ============================================================================
   🌊 ADVANCED SSE CONSUMER - ULTRA-RELIABLE STREAMING
   ============================================================================ */
class SuperhumanSSE {
  constructor(url, options = {}) {
    this.url = url;
    this.options = {
      reconnect: true,
      maxReconnectAttempts: 5,
      reconnectDelay: 1000,
      heartbeatInterval: 30000,
      ...options
    };
    
    this.eventSource = null;
    this.reconnectAttempts = 0;
    this.isConnected = false;
    this.heartbeatTimer = null;
    this.handlers = {};
    this.performanceMonitor = new PerformanceMonitor();
  }

  on(event, handler) {
    if (!this.handlers[event]) {
      this.handlers[event] = [];
    }
    this.handlers[event].push(handler);
    return this;
  }

  emit(event, data) {
    if (this.handlers[event]) {
      this.handlers[event].forEach(handler => handler(data));
    }
  }

  connect() {
    this.performanceMonitor.startRequest();
    
    try {
      this.eventSource = new EventSource(this.url);
      
      this.eventSource.onopen = () => {
        this.isConnected = true;
        this.reconnectAttempts = 0;
        this.emit('open', { connected: true });
        this.startHeartbeat();
      };

      this.eventSource.onerror = (error) => {
        this.isConnected = false;
        this.emit('error', error);
        
        if (this.options.reconnect && this.reconnectAttempts < this.options.maxReconnectAttempts) {
          this.reconnect();
        } else {
          this.disconnect();
        }
      };

      // Custom event listeners
      this.setupEventListeners();
      
    } catch (error) {
      this.emit('error', error);
    }
  }

  setupEventListeners() {
    const events = ['start', 'delta', 'metadata', 'complete', 'error', 'ping', 'conversation'];
    
    events.forEach(event => {
      this.eventSource.addEventListener(event, (e) => {
        try {
          const data = JSON.parse(e.data);
          
          if (event === 'delta') {
            this.performanceMonitor.recordToken();
            if (this.performanceMonitor.metrics.ttft === null) {
              this.performanceMonitor.recordFirstToken();
            }
          }
          
          this.emit(event, data);
        } catch (error) {
          console.error(`Error parsing ${event} event:`, error);
        }
      });
    });
  }

  startHeartbeat() {
    if (this.heartbeatTimer) {
      clearInterval(this.heartbeatTimer);
    }
    
    this.heartbeatTimer = setInterval(() => {
      if (!this.isConnected) {
        this.reconnect();
      }
    }, this.options.heartbeatInterval);
  }

  reconnect() {
    this.reconnectAttempts++;
    const delay = this.options.reconnectDelay * Math.pow(2, this.reconnectAttempts - 1);
    
    this.emit('reconnecting', { attempt: this.reconnectAttempts, delay });
    
    setTimeout(() => {
      this.disconnect();
      this.connect();
    }, delay);
  }

  disconnect() {
    if (this.eventSource) {
      this.eventSource.close();
      this.eventSource = null;
    }
    
    if (this.heartbeatTimer) {
      clearInterval(this.heartbeatTimer);
      this.heartbeatTimer = null;
    }
    
    this.isConnected = false;
    this.performanceMonitor.endRequest();
    this.emit('close', { stats: this.performanceMonitor.getStats() });
  }

  getPerformanceStats() {
    return this.performanceMonitor.getStats();
  }
}

/* ============================================================================
   ⚡ ADAPTIVE TYPEWRITER - SMOOTH TOKEN RENDERING
   ============================================================================ */
class AdaptiveTypewriter {
  constructor(element, options = {}) {
    this.element = element;
    this.options = {
      baseDelayMs: 10,
      punctuationDelayMultiplier: 5,
      commaDelayMultiplier: 2,
      charsPerStep: 2,
      enableMarkdown: true,
      ...options
    };
    
    this.buffer = '';
    this.isTyping = false;
    this.queue = [];
  }

  append(text) {
    this.queue.push(...text.split(''));
    
    if (!this.isTyping) {
      this.processQueue();
    }
  }

  async processQueue() {
    this.isTyping = true;
    
    while (this.queue.length > 0) {
      const char = this.queue.shift();
      this.buffer += char;
      
      // Render with markdown support
      if (this.options.enableMarkdown) {
        this.element.innerHTML = this.formatMarkdown(this.buffer);
      } else {
        this.element.textContent = this.buffer;
      }
      
      // Auto-scroll parent container
      const parent = this.element.closest('.messages-area, .chat-container');
      if (parent) {
        parent.scrollTop = parent.scrollHeight;
      }
      
      // Adaptive delay based on character type
      const delay = this.getDelay(char);
      await this.sleep(delay);
    }
    
    this.isTyping = false;
  }

  getDelay(char) {
    if (char === '.' || char === '!' || char === '?') {
      return this.options.baseDelayMs * this.options.punctuationDelayMultiplier;
    } else if (char === ',') {
      return this.options.baseDelayMs * this.options.commaDelayMultiplier;
    } else {
      return this.options.baseDelayMs;
    }
  }

  formatMarkdown(text) {
    return text
      .replace(/```([\s\S]*?)```/g, '<pre><code>$1</code></pre>')
      .replace(/`([^`]+)`/g, '<code>$1</code>')
      .replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>')
      .replace(/\*([^*]+)\*/g, '<em>$1</em>')
      .replace(/\n/g, '<br>');
  }

  sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
  }

  clear() {
    this.buffer = '';
    this.queue = [];
    this.element.innerHTML = '';
    this.isTyping = false;
  }
}

/* ============================================================================
   🔄 REQUEST DEDUPLICATION - PREVENT DUPLICATE REQUESTS
   ============================================================================ */
class RequestDeduplicator {
  constructor() {
    this.cache = new Map();
    this.ttl = 5000; // 5 seconds
  }

  async fetch(url, options = {}) {
    const key = this.generateKey(url, options);
    
    // Return cached promise if exists
    if (this.cache.has(key)) {
      return this.cache.get(key);
    }
    
    // Create new request
    const promise = fetch(url, options);
    this.cache.set(key, promise);
    
    // Clean up after TTL
    setTimeout(() => {
      this.cache.delete(key);
    }, this.ttl);
    
    return promise;
  }

  generateKey(url, options) {
    return `${url}_${JSON.stringify(options.body || '')}`;
  }

  clear() {
    this.cache.clear();
  }
}

/* ============================================================================
   📦 REQUEST BATCHER - BATCH MULTIPLE REQUESTS
   ============================================================================ */
class RequestBatcher {
  constructor(options = {}) {
    this.options = {
      batchDelay: 50,
      maxBatchSize: 10,
      ...options
    };
    
    this.queue = [];
    this.timer = null;
  }

  async add(request) {
    return new Promise((resolve, reject) => {
      this.queue.push({ request, resolve, reject });
      
      if (this.queue.length >= this.options.maxBatchSize) {
        this.flush();
      } else if (!this.timer) {
        this.timer = setTimeout(() => this.flush(), this.options.batchDelay);
      }
    });
  }

  async flush() {
    if (this.timer) {
      clearTimeout(this.timer);
      this.timer = null;
    }
    
    if (this.queue.length === 0) return;
    
    const batch = this.queue.splice(0);
    
    try {
      // Execute all requests in parallel
      const results = await Promise.all(
        batch.map(item => item.request())
      );
      
      // Resolve each promise
      batch.forEach((item, index) => {
        item.resolve(results[index]);
      });
    } catch (error) {
      // Reject all promises
      batch.forEach(item => item.reject(error));
    }
  }
}

/* ============================================================================
   🧠 OPTIMISTIC UI MANAGER - INSTANT UPDATES
   ============================================================================ */
class OptimisticUIManager {
  constructor() {
    this.pendingUpdates = new Map();
    this.rollbackHandlers = new Map();
  }

  async update(id, optimisticData, actualRequest, rollbackFn) {
    // Apply optimistic update immediately
    this.pendingUpdates.set(id, optimisticData);
    this.rollbackHandlers.set(id, rollbackFn);
    
    try {
      // Execute actual request
      const result = await actualRequest();
      
      // Remove pending update on success
      this.pendingUpdates.delete(id);
      this.rollbackHandlers.delete(id);
      
      return result;
    } catch (error) {
      // Rollback on error
      const rollback = this.rollbackHandlers.get(id);
      if (rollback) {
        rollback();
      }
      
      this.pendingUpdates.delete(id);
      this.rollbackHandlers.delete(id);
      
      throw error;
    }
  }

  isPending(id) {
    return this.pendingUpdates.has(id);
  }

  rollbackAll() {
    this.rollbackHandlers.forEach(rollback => rollback());
    this.pendingUpdates.clear();
    this.rollbackHandlers.clear();
  }
}

/* ============================================================================
   🎯 DEBOUNCE & THROTTLE UTILITIES
   ============================================================================ */
function debounce(func, delay) {
  let timer;
  return function(...args) {
    clearTimeout(timer);
    timer = setTimeout(() => func.apply(this, args), delay);
  };
}

function throttle(func, limit) {
  let inThrottle;
  return function(...args) {
    if (!inThrottle) {
      func.apply(this, args);
      inThrottle = true;
      setTimeout(() => inThrottle = false, limit);
    }
  };
}

/* ============================================================================
   🔄 VIRTUAL SCROLLER - EFFICIENT LIST RENDERING
   ============================================================================ */
class VirtualScroller {
  constructor(container, options = {}) {
    this.container = container;
    this.options = {
      itemHeight: 100,
      buffer: 5,
      ...options
    };
    
    this.items = [];
    this.visibleRange = { start: 0, end: 0 };
    this.scrollTop = 0;
    
    this.setupListeners();
  }

  setItems(items) {
    this.items = items;
    this.render();
  }

  setupListeners() {
    this.container.addEventListener('scroll', throttle(() => {
      this.scrollTop = this.container.scrollTop;
      this.render();
    }, 16)); // ~60fps
  }

  calculateVisibleRange() {
    const containerHeight = this.container.clientHeight;
    const start = Math.max(0, Math.floor(this.scrollTop / this.options.itemHeight) - this.options.buffer);
    const end = Math.min(
      this.items.length,
      Math.ceil((this.scrollTop + containerHeight) / this.options.itemHeight) + this.options.buffer
    );
    
    return { start, end };
  }

  render() {
    const { start, end } = this.calculateVisibleRange();
    
    if (start === this.visibleRange.start && end === this.visibleRange.end) {
      return; // No change
    }
    
    this.visibleRange = { start, end };
    
    // Create spacer elements
    const topSpacer = document.createElement('div');
    topSpacer.style.height = `${start * this.options.itemHeight}px`;
    
    const bottomSpacer = document.createElement('div');
    bottomSpacer.style.height = `${(this.items.length - end) * this.options.itemHeight}px`;
    
    // Render visible items
    const fragment = document.createDocumentFragment();
    fragment.appendChild(topSpacer);
    
    for (let i = start; i < end; i++) {
      const item = this.renderItem(this.items[i], i);
      fragment.appendChild(item);
    }
    
    fragment.appendChild(bottomSpacer);
    
    // Update container
    this.container.innerHTML = '';
    this.container.appendChild(fragment);
  }

  renderItem(data, index) {
    // Override this method to customize rendering
    const div = document.createElement('div');
    div.textContent = JSON.stringify(data);
    div.style.height = `${this.options.itemHeight}px`;
    return div;
  }
}

/* ============================================================================
   💾 SMART CACHE - INTELLIGENT CACHING SYSTEM
   ============================================================================ */
class SmartCache {
  constructor(options = {}) {
    this.options = {
      maxSize: 100,
      ttl: 300000, // 5 minutes
      ...options
    };
    
    this.cache = new Map();
    this.accessCount = new Map();
    this.timestamps = new Map();
  }

  set(key, value) {
    // Remove oldest/least used if at capacity
    if (this.cache.size >= this.options.maxSize) {
      this.evict();
    }
    
    this.cache.set(key, value);
    this.accessCount.set(key, 0);
    this.timestamps.set(key, Date.now());
  }

  get(key) {
    if (!this.cache.has(key)) {
      return null;
    }
    
    // Check if expired
    const age = Date.now() - this.timestamps.get(key);
    if (age > this.options.ttl) {
      this.delete(key);
      return null;
    }
    
    // Increment access count
    this.accessCount.set(key, this.accessCount.get(key) + 1);
    
    return this.cache.get(key);
  }

  delete(key) {
    this.cache.delete(key);
    this.accessCount.delete(key);
    this.timestamps.delete(key);
  }

  evict() {
    // LRU + LFU hybrid eviction
    let minScore = Infinity;
    let evictKey = null;
    
    for (const [key, count] of this.accessCount.entries()) {
      const age = Date.now() - this.timestamps.get(key);
      const score = count / (age / 1000); // Accesses per second
      
      if (score < minScore) {
        minScore = score;
        evictKey = key;
      }
    }
    
    if (evictKey) {
      this.delete(evictKey);
    }
  }

  clear() {
    this.cache.clear();
    this.accessCount.clear();
    this.timestamps.clear();
  }

  getStats() {
    return {
      size: this.cache.size,
      maxSize: this.options.maxSize,
      utilization: (this.cache.size / this.options.maxSize * 100).toFixed(1) + '%'
    };
  }
}

/* ============================================================================
   🎨 THEME MANAGER - ADVANCED THEME SWITCHING
   ============================================================================ */
class ThemeManager {
  constructor() {
    this.currentTheme = this.getStoredTheme() || 'dark';
    this.applyTheme(this.currentTheme);
    this.setupListeners();
  }

  getStoredTheme() {
    return localStorage.getItem('theme');
  }

  applyTheme(theme) {
    document.documentElement.setAttribute('data-theme', theme);
    localStorage.setItem('theme', theme);
    this.currentTheme = theme;
    
    // Emit custom event
    window.dispatchEvent(new CustomEvent('themechange', { detail: { theme } }));
  }

  toggle() {
    const newTheme = this.currentTheme === 'dark' ? 'light' : 'dark';
    this.applyTheme(newTheme);
    return newTheme;
  }

  setupListeners() {
    // Detect system preference changes
    if (window.matchMedia) {
      window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', (e) => {
        if (!this.getStoredTheme()) {
          this.applyTheme(e.matches ? 'dark' : 'light');
        }
      });
    }
  }
}

/* ============================================================================
   📡 WEB WORKER MANAGER - OFFLOAD HEAVY PROCESSING
   ============================================================================ */
class WorkerManager {
  constructor() {
    this.workers = new Map();
    this.taskQueue = [];
  }

  createWorker(name, workerCode) {
    const blob = new Blob([workerCode], { type: 'application/javascript' });
    const worker = new Worker(URL.createObjectURL(blob));
    
    this.workers.set(name, {
      worker,
      busy: false,
      taskCount: 0
    });
    
    return worker;
  }

  async executeTask(workerName, data) {
    const workerInfo = this.workers.get(workerName);
    
    if (!workerInfo) {
      throw new Error(`Worker ${workerName} not found`);
    }
    
    return new Promise((resolve, reject) => {
      workerInfo.busy = true;
      workerInfo.taskCount++;
      
      workerInfo.worker.postMessage(data);
      
      workerInfo.worker.onmessage = (e) => {
        workerInfo.busy = false;
        resolve(e.data);
      };
      
      workerInfo.worker.onerror = (error) => {
        workerInfo.busy = false;
        reject(error);
      };
    });
  }

  terminateWorker(name) {
    const workerInfo = this.workers.get(name);
    if (workerInfo) {
      workerInfo.worker.terminate();
      this.workers.delete(name);
    }
  }

  terminateAll() {
    this.workers.forEach((info, name) => {
      info.worker.terminate();
    });
    this.workers.clear();
  }

  getStats() {
    const stats = {};
    this.workers.forEach((info, name) => {
      stats[name] = {
        busy: info.busy,
        taskCount: info.taskCount
      };
    });
    return stats;
  }
}

/* ============================================================================
   🎯 NOTIFICATION MANAGER - BEAUTIFUL NOTIFICATIONS
   ============================================================================ */
class NotificationManager {
  constructor() {
    this.container = this.createContainer();
    this.notifications = [];
  }

  createContainer() {
    const container = document.createElement('div');
    container.className = 'notification-container';
    container.style.cssText = `
      position: fixed;
      top: 20px;
      right: 20px;
      z-index: 10000;
      display: flex;
      flex-direction: column;
      gap: 12px;
    `;
    document.body.appendChild(container);
    return container;
  }

  show(message, type = 'info', duration = 5000) {
    const notification = document.createElement('div');
    notification.className = `notification notification-${type}`;
    
    const icons = {
      success: '✅',
      error: '❌',
      warning: '⚠️',
      info: 'ℹ️'
    };
    
    notification.innerHTML = `
      <div style="
        display: flex;
        align-items: center;
        gap: 12px;
        padding: 16px 20px;
        background: var(--bg-secondary);
        border-radius: 12px;
        box-shadow: 0 8px 24px rgba(0, 0, 0, 0.2);
        backdrop-filter: blur(10px);
        border: 1px solid var(--border-color);
        min-width: 300px;
        animation: slideIn 0.3s ease-out;
      ">
        <span style="font-size: 1.5rem;">${icons[type]}</span>
        <span style="flex: 1; color: var(--text-primary);">${message}</span>
        <button onclick="this.parentElement.parentElement.remove()" style="
          background: none;
          border: none;
          color: var(--text-secondary);
          cursor: pointer;
          font-size: 1.2rem;
          padding: 0;
        ">×</button>
      </div>
    `;
    
    this.container.appendChild(notification);
    this.notifications.push(notification);
    
    if (duration > 0) {
      setTimeout(() => {
        notification.style.animation = 'slideOut 0.3s ease-out';
        setTimeout(() => {
          notification.remove();
          this.notifications = this.notifications.filter(n => n !== notification);
        }, 300);
      }, duration);
    }
    
    return notification;
  }

  success(message, duration) {
    return this.show(message, 'success', duration);
  }

  error(message, duration) {
    return this.show(message, 'error', duration);
  }

  warning(message, duration) {
    return this.show(message, 'warning', duration);
  }

  info(message, duration) {
    return this.show(message, 'info', duration);
  }

  clearAll() {
    this.notifications.forEach(n => n.remove());
    this.notifications = [];
  }
}

/* ============================================================================
   🚀 EXPORT SUPERHUMAN FRAMEWORK
   ============================================================================ */
window.SuperhumanFramework = {
  PerformanceMonitor,
  SuperhumanSSE,
  AdaptiveTypewriter,
  RequestDeduplicator,
  RequestBatcher,
  OptimisticUIManager,
  VirtualScroller,
  SmartCache,
  ThemeManager,
  WorkerManager,
  NotificationManager,
  debounce,
  throttle
};

// Add CSS animations
const style = document.createElement('style');
style.textContent = `
  @keyframes slideIn {
    from {
      opacity: 0;
      transform: translateX(100px);
    }
    to {
      opacity: 1;
      transform: translateX(0);
    }
  }
  
  @keyframes slideOut {
    from {
      opacity: 1;
      transform: translateX(0);
    }
    to {
      opacity: 0;
      transform: translateX(100px);
    }
  }
`;
document.head.appendChild(style);

console.log('🚀 Superhuman Framework v3.0 loaded successfully!');
