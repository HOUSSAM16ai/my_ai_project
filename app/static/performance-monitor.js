/**
 * Performance Monitor - Client-Side Performance Tracking
 * 
 * مراقب الأداء - تتبع أداء جانب العميل
 * 
 * Features:
 * - Page load time tracking
 * - Resource timing
 * - Memory usage monitoring
 * - Custom performance marks
 * 
 * Usage:
 *   PerformanceMonitor.init();
 *   PerformanceMonitor.mark('custom-event');
 *   PerformanceMonitor.measure('operation', 'start-mark', 'end-mark');
 *   PerformanceMonitor.getReport();
 * 
 * @version 1.0.0
 * @date 2025-12-31
 */

(function(window) {
    'use strict';
    
    const PerformanceMonitor = {
        // Configuration
        config: {
            enabled: true,
            logToConsole: false,
            reportInterval: 30000, // 30 seconds
            memoryCheckInterval: 10000 // 10 seconds
        },
        
        // State
        state: {
            initialized: false,
            marks: {},
            measures: {},
            memorySnapshots: [],
            errors: [],
            intervals: [] // Track intervals for cleanup
        },
        
        /**
         * Initialize performance monitoring
         */
        init: function() {
            if (this.state.initialized) {
                console.warn('PerformanceMonitor already initialized');
                return;
            }
            
            if (!this.config.enabled) {
                return;
            }
            
            // Check browser support
            if (!window.performance || !window.performance.mark) {
                console.warn('Performance API not supported');
                return;
            }
            
            this.state.initialized = true;
            
            // Track page load
            this.trackPageLoad();
            
            // Start memory monitoring
            if (window.performance.memory) {
                this.startMemoryMonitoring();
            }
            
            // Log initialization
            if (this.config.logToConsole) {
                console.log('[PerformanceMonitor] Initialized');
            }
        },
        
        /**
         * Track page load performance
         */
        trackPageLoad: function() {
            window.addEventListener('load', () => {
                setTimeout(() => {
                    const perfData = window.performance.timing;
                    const pageLoadTime = perfData.loadEventEnd - perfData.navigationStart;
                    const domReadyTime = perfData.domContentLoadedEventEnd - perfData.navigationStart;
                    
                    this.state.marks.pageLoad = {
                        total: pageLoadTime,
                        domReady: domReadyTime,
                        timestamp: Date.now()
                    };
                    
                    if (this.config.logToConsole) {
                        console.log(`[PerformanceMonitor] Page Load: ${pageLoadTime}ms (DOM Ready: ${domReadyTime}ms)`);
                    }
                }, 0);
            });
        },
        
        /**
         * Start memory monitoring
         */
        startMemoryMonitoring: function() {
            const intervalId = setInterval(() => {
                if (window.performance.memory) {
                    const memory = {
                        used: window.performance.memory.usedJSHeapSize,
                        total: window.performance.memory.totalJSHeapSize,
                        limit: window.performance.memory.jsHeapSizeLimit,
                        timestamp: Date.now()
                    };
                    
                    this.state.memorySnapshots.push(memory);
                    
                    // Keep only last 10 snapshots
                    if (this.state.memorySnapshots.length > 10) {
                        this.state.memorySnapshots.shift();
                    }
                    
                    // Warn if memory usage is high
                    const usagePercent = (memory.used / memory.limit) * 100;
                    if (usagePercent > 80) {
                        console.warn(`[PerformanceMonitor] High memory usage: ${usagePercent.toFixed(1)}%`);
                    }
                }
            }, this.config.memoryCheckInterval);
            
            // Store interval ID for cleanup
            this.state.intervals.push(intervalId);
        },
        
        /**
         * Create a performance mark
         * @param {string} name - Mark name
         */
        mark: function(name) {
            if (!this.state.initialized) return;
            
            try {
                window.performance.mark(name);
                this.state.marks[name] = {
                    timestamp: Date.now(),
                    performanceTimestamp: window.performance.now()
                };
            } catch (error) {
                this.state.errors.push({ type: 'mark', name, error: error.message });
            }
        },
        
        /**
         * Measure performance between two marks
         * @param {string} name - Measure name
         * @param {string} startMark - Start mark name
         * @param {string} endMark - End mark name
         */
        measure: function(name, startMark, endMark) {
            if (!this.state.initialized) return;
            
            try {
                window.performance.measure(name, startMark, endMark);
                const measure = window.performance.getEntriesByName(name, 'measure')[0];
                
                this.state.measures[name] = {
                    duration: measure.duration,
                    startTime: measure.startTime,
                    timestamp: Date.now()
                };
                
                if (this.config.logToConsole) {
                    console.log(`[PerformanceMonitor] ${name}: ${measure.duration.toFixed(2)}ms`);
                }
            } catch (error) {
                this.state.errors.push({ type: 'measure', name, error: error.message });
            }
        },
        
        /**
         * Get current memory usage
         * @returns {Object|null} Memory usage object or null
         */
        getMemoryUsage: function() {
            if (!window.performance.memory) return null;
            
            return {
                used: window.performance.memory.usedJSHeapSize,
                total: window.performance.memory.totalJSHeapSize,
                limit: window.performance.memory.jsHeapSizeLimit,
                usedMB: (window.performance.memory.usedJSHeapSize / 1024 / 1024).toFixed(2),
                totalMB: (window.performance.memory.totalJSHeapSize / 1024 / 1024).toFixed(2),
                limitMB: (window.performance.memory.jsHeapSizeLimit / 1024 / 1024).toFixed(2)
            };
        },
        
        /**
         * Get performance report
         * @returns {Object} Performance report
         */
        getReport: function() {
            return {
                marks: this.state.marks,
                measures: this.state.measures,
                memory: {
                    current: this.getMemoryUsage(),
                    snapshots: this.state.memorySnapshots
                },
                errors: this.state.errors,
                timestamp: Date.now()
            };
        },
        
        /**
         * Clear all performance data
         */
        clear: function() {
            if (window.performance.clearMarks) {
                window.performance.clearMarks();
            }
            if (window.performance.clearMeasures) {
                window.performance.clearMeasures();
            }
            
            this.state.marks = {};
            this.state.measures = {};
            this.state.errors = [];
        },
        
        /**
         * Cleanup and destroy performance monitor
         * CRITICAL: Call this to prevent memory leaks
         */
        destroy: function() {
            // Clear all intervals
            this.state.intervals.forEach(intervalId => {
                clearInterval(intervalId);
            });
            this.state.intervals = [];
            
            // Clear performance data
            this.clear();
            
            // Reset state
            this.state.initialized = false;
            this.state.memorySnapshots = [];
            
            if (this.config.logToConsole) {
                console.log('[PerformanceMonitor] Destroyed and cleaned up');
            }
        },
        
        /**
         * Log current report to console
         */
        logReport: function() {
            const report = this.getReport();
            console.group('[PerformanceMonitor] Report');
            console.log('Marks:', report.marks);
            console.log('Measures:', report.measures);
            console.log('Memory:', report.memory);
            if (report.errors.length > 0) {
                console.warn('Errors:', report.errors);
            }
            console.groupEnd();
        }
    };
    
    // Export to window
    window.PerformanceMonitor = PerformanceMonitor;
    
    // Detect Codespaces environment
    const isCodespaces = window.location.hostname.includes('github.dev') || 
                        window.location.hostname.includes('app.github.dev') ||
                        window.location.hostname.includes('preview.app.github.dev');
    
    // Auto-initialize with environment-specific settings
    if (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1') {
        PerformanceMonitor.config.logToConsole = true;
        PerformanceMonitor.init();
    } else if (isCodespaces) {
        // Codespaces: Less aggressive monitoring to conserve resources
        PerformanceMonitor.config.logToConsole = false;
        PerformanceMonitor.config.memoryCheckInterval = 30000; // 30 seconds (increased from 10)
        PerformanceMonitor.init();
    }
    
    // CRITICAL: Cleanup on page unload to prevent memory leaks
    window.addEventListener('beforeunload', () => {
        if (PerformanceMonitor.state.initialized) {
            PerformanceMonitor.destroy();
        }
    });
    
})(window);
