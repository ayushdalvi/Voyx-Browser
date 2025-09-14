"""
Userscript Templates - Pre-built templates for common userscript tasks.
"""

TEMPLATES = {
    "Basic Script": {
        "description": "Basic userscript template with common structure",
        "code": """// ==UserScript==
// @name        New Userscript
// @namespace   VoyxBrowser
// @version     1.0
// @description Enter description here
// @author      You
// @include     *
// @grant       none
// ==/UserScript==

(function() {
    'use strict';
    
    // Your code here
    console.log('Userscript loaded!');
    
})();"""
    },
    
    "Ad Blocker": {
        "description": "Remove ads and unwanted elements from websites",
        "code": """// ==UserScript==
// @name        Ad Blocker
// @namespace   VoyxBrowser
// @version     1.0
// @description Block ads and unwanted elements
// @author      You
// @include     *
// @grant       GM_addStyle
// ==/UserScript==

(function() {
    'use strict';
    
    // CSS to hide common ad elements
    const adBlockCSS = `
        .ad, .ads, .advertisement, .banner-ad,
        [class*="ad-"], [class*="ads-"], [class*="advertisement"],
        [id*="ad-"], [id*="ads-"], [id*="advertisement"],
        .popup, .modal-ad, .sponsored,
        iframe[src*="doubleclick"], iframe[src*="googlesyndication"]
        {
            display: none !important;
            visibility: hidden !important;
            opacity: 0 !important;
            height: 0 !important;
            width: 0 !important;
        }
    `;
    
    GM_addStyle(adBlockCSS);
    
    // Remove ad elements dynamically
    function removeAds() {
        const adSelectors = [
            '.ad', '.ads', '.advertisement', '.banner-ad',
            '[class*="ad-"]', '[class*="ads-"]', '[class*="advertisement"]',
            '[id*="ad-"]', '[id*="ads-"]', '[id*="advertisement"]',
            '.popup', '.modal-ad', '.sponsored'
        ];
        
        adSelectors.forEach(selector => {
            document.querySelectorAll(selector).forEach(el => {
                el.remove();
            });
        });
    }
    
    // Run on page load and periodically
    removeAds();
    setInterval(removeAds, 2000);
    
})();"""
    },
    
    "Dark Mode": {
        "description": "Apply dark mode to any website",
        "code": """// ==UserScript==
// @name        Universal Dark Mode
// @namespace   VoyxBrowser
// @version     1.0
// @description Apply dark mode to any website
// @author      You
// @include     *
// @grant       GM_addStyle
// ==/UserScript==

(function() {
    'use strict';
    
    const darkModeCSS = `
        html {
            filter: invert(1) hue-rotate(180deg) !important;
            background: #111 !important;
        }
        
        img, video, iframe, svg, embed, object {
            filter: invert(1) hue-rotate(180deg) !important;
        }
        
        [style*="background-image"] {
            filter: invert(1) hue-rotate(180deg) !important;
        }
    `;
    
    // Add toggle button
    const toggleButton = document.createElement('button');
    toggleButton.innerHTML = '🌙';
    toggleButton.style.cssText = `
        position: fixed;
        top: 10px;
        right: 10px;
        z-index: 10000;
        background: #333;
        color: white;
        border: none;
        border-radius: 50%;
        width: 40px;
        height: 40px;
        cursor: pointer;
        font-size: 16px;
    `;
    
    let darkModeEnabled = false;
    let styleElement = null;
    
    function toggleDarkMode() {
        if (darkModeEnabled) {
            if (styleElement) {
                styleElement.remove();
                styleElement = null;
            }
            toggleButton.innerHTML = '🌙';
            darkModeEnabled = false;
        } else {
            styleElement = GM_addStyle(darkModeCSS);
            toggleButton.innerHTML = '☀️';
            darkModeEnabled = true;
        }
    }
    
    toggleButton.addEventListener('click', toggleDarkMode);
    document.body.appendChild(toggleButton);
    
})();"""
    },
    
    "Auto Scroll": {
        "description": "Automatically scroll through pages",
        "code": """// ==UserScript==
// @name        Auto Scroll
// @namespace   VoyxBrowser
// @version     1.0
// @description Automatically scroll through pages
// @author      You
// @include     *
// @grant       none
// ==/UserScript==

(function() {
    'use strict';
    
    let isScrolling = false;
    let scrollSpeed = 2;
    let scrollInterval;
    
    // Create control panel
    const controlPanel = document.createElement('div');
    controlPanel.style.cssText = `
        position: fixed;
        top: 50px;
        right: 10px;
        z-index: 10000;
        background: rgba(0, 0, 0, 0.8);
        color: white;
        padding: 10px;
        border-radius: 5px;
        font-family: Arial, sans-serif;
        font-size: 12px;
    `;
    
    controlPanel.innerHTML = `
        <div>Auto Scroll</div>
        <button id="toggleScroll">Start</button>
        <br><br>
        <label>Speed: <input type="range" id="speedSlider" min="1" max="10" value="2"></label>
        <span id="speedValue">2</span>
    `;
    
    document.body.appendChild(controlPanel);
    
    const toggleButton = document.getElementById('toggleScroll');
    const speedSlider = document.getElementById('speedSlider');
    const speedValue = document.getElementById('speedValue');
    
    function startScrolling() {
        scrollInterval = setInterval(() => {
            window.scrollBy(0, scrollSpeed);
            
            // Stop if reached bottom
            if (window.innerHeight + window.scrollY >= document.body.offsetHeight) {
                stopScrolling();
            }
        }, 50);
    }
    
    function stopScrolling() {
        clearInterval(scrollInterval);
        isScrolling = false;
        toggleButton.textContent = 'Start';
    }
    
    toggleButton.addEventListener('click', () => {
        if (isScrolling) {
            stopScrolling();
        } else {
            startScrolling();
            isScrolling = true;
            toggleButton.textContent = 'Stop';
        }
    });
    
    speedSlider.addEventListener('input', (e) => {
        scrollSpeed = parseInt(e.target.value);
        speedValue.textContent = scrollSpeed;
    });
    
    // Keyboard shortcuts
    document.addEventListener('keydown', (e) => {
        if (e.ctrlKey && e.key === 's') {
            e.preventDefault();
            toggleButton.click();
        }
    });
    
})();"""
    },
    
    "Form Filler": {
        "description": "Automatically fill forms with predefined data",
        "code": """// ==UserScript==
// @name        Form Filler
// @namespace   VoyxBrowser
// @version     1.0
// @description Automatically fill forms with predefined data
// @author      You
// @include     *
// @grant       GM_getValue
// @grant       GM_setValue
// ==/UserScript==

(function() {
    'use strict';
    
    // Default form data
    const defaultFormData = {
        name: 'John Doe',
        email: 'john.doe@example.com',
        phone: '555-0123',
        address: '123 Main St',
        city: 'Anytown',
        zip: '12345',
        country: 'USA'
    };
    
    // Load saved data or use defaults
    let formData = {};
    Object.keys(defaultFormData).forEach(key => {
        formData[key] = GM_getValue(key, defaultFormData[key]);
    });
    
    // Create fill button
    const fillButton = document.createElement('button');
    fillButton.innerHTML = '📝 Fill Form';
    fillButton.style.cssText = `
        position: fixed;
        top: 100px;
        right: 10px;
        z-index: 10000;
        background: #4CAF50;
        color: white;
        border: none;
        padding: 10px;
        border-radius: 5px;
        cursor: pointer;
        font-size: 12px;
    `;
    
    function fillForm() {
        // Common field mappings
        const fieldMappings = {
            name: ['name', 'fullname', 'full_name', 'username', 'user_name'],
            email: ['email', 'e-mail', 'mail', 'email_address'],
            phone: ['phone', 'telephone', 'tel', 'mobile', 'cell'],
            address: ['address', 'street', 'addr', 'address1'],
            city: ['city', 'town', 'locality'],
            zip: ['zip', 'postal', 'postcode', 'postal_code', 'zipcode'],
            country: ['country', 'nation']
        };
        
        Object.keys(fieldMappings).forEach(dataKey => {
            const value = formData[dataKey];
            fieldMappings[dataKey].forEach(fieldName => {
                // Try different selectors
                const selectors = [
                    `input[name="${fieldName}"]`,
                    `input[id="${fieldName}"]`,
                    `input[name*="${fieldName}"]`,
                    `input[id*="${fieldName}"]`,
                    `input[placeholder*="${fieldName}"]`,
                    `textarea[name="${fieldName}"]`,
                    `textarea[id="${fieldName}"]`,
                    `select[name="${fieldName}"]`,
                    `select[id="${fieldName}"]`
                ];
                
                selectors.forEach(selector => {
                    const elements = document.querySelectorAll(selector);
                    elements.forEach(element => {
                        if (element.type === 'select-one') {
                            // Handle select elements
                            for (let option of element.options) {
                                if (option.text.toLowerCase().includes(value.toLowerCase())) {
                                    element.value = option.value;
                                    break;
                                }
                            }
                        } else {
                            element.value = value;
                            element.dispatchEvent(new Event('input', { bubbles: true }));
                            element.dispatchEvent(new Event('change', { bubbles: true }));
                        }
                    });
                });
            });
        });
        
        console.log('Form filled with predefined data');
    }
    
    fillButton.addEventListener('click', fillForm);
    document.body.appendChild(fillButton);
    
    // Auto-fill on Ctrl+F
    document.addEventListener('keydown', (e) => {
        if (e.ctrlKey && e.key === 'f' && e.shiftKey) {
            e.preventDefault();
            fillForm();
        }
    });
    
})();"""
    },
    
    "Page Monitor": {
        "description": "Monitor page changes and notify when content updates",
        "code": """// ==UserScript==
// @name        Page Monitor
// @namespace   VoyxBrowser
// @version     1.0
// @description Monitor page changes and notify when content updates
// @author      You
// @include     *
// @grant       GM_getValue
// @grant       GM_setValue
// @grant       GM_notification
// ==/UserScript==

(function() {
    'use strict';
    
    let isMonitoring = false;
    let lastContent = '';
    let monitorInterval;
    
    // Create monitor panel
    const monitorPanel = document.createElement('div');
    monitorPanel.style.cssText = `
        position: fixed;
        top: 150px;
        right: 10px;
        z-index: 10000;
        background: rgba(0, 0, 0, 0.8);
        color: white;
        padding: 10px;
        border-radius: 5px;
        font-family: Arial, sans-serif;
        font-size: 12px;
        min-width: 150px;
    `;
    
    monitorPanel.innerHTML = `
        <div>Page Monitor</div>
        <button id="toggleMonitor">Start Monitoring</button>
        <br><br>
        <label>Check every: 
            <select id="intervalSelect">
                <option value="5000">5 seconds</option>
                <option value="30000" selected>30 seconds</option>
                <option value="60000">1 minute</option>
                <option value="300000">5 minutes</option>
            </select>
        </label>
        <br><br>
        <div id="status">Stopped</div>
    `;
    
    document.body.appendChild(monitorPanel);
    
    const toggleButton = document.getElementById('toggleMonitor');
    const intervalSelect = document.getElementById('intervalSelect');
    const statusDiv = document.getElementById('status');
    
    function getPageContent() {
        // Get main content, excluding scripts and styles
        const content = document.body.innerText || document.body.textContent || '';
        return content.trim();
    }
    
    function checkForChanges() {
        const currentContent = getPageContent();
        
        if (lastContent && lastContent !== currentContent) {
            // Content changed
            statusDiv.textContent = 'Change detected!';
            statusDiv.style.color = '#ff6b6b';
            
            // Show notification
            if (typeof GM_notification !== 'undefined') {
                GM_notification({
                    title: 'Page Changed',
                    text: `Content updated on ${window.location.hostname}`,
                    timeout: 5000
                });
            }
            
            // Flash the page
            document.body.style.backgroundColor = '#ffff00';
            setTimeout(() => {
                document.body.style.backgroundColor = '';
            }, 500);
            
            console.log('Page content changed!');
        }
        
        lastContent = currentContent;
    }
    
    function startMonitoring() {
        const interval = parseInt(intervalSelect.value);
        lastContent = getPageContent();
        
        monitorInterval = setInterval(checkForChanges, interval);
        isMonitoring = true;
        
        toggleButton.textContent = 'Stop Monitoring';
        statusDiv.textContent = 'Monitoring...';
        statusDiv.style.color = '#4CAF50';
    }
    
    function stopMonitoring() {
        clearInterval(monitorInterval);
        isMonitoring = false;
        
        toggleButton.textContent = 'Start Monitoring';
        statusDiv.textContent = 'Stopped';
        statusDiv.style.color = '#ffffff';
    }
    
    toggleButton.addEventListener('click', () => {
        if (isMonitoring) {
            stopMonitoring();
        } else {
            startMonitoring();
        }
    });
    
})();"""
    },
    
    "Link Checker": {
        "description": "Check and highlight broken links on the page",
        "code": """// ==UserScript==
// @name        Link Checker
// @namespace   VoyxBrowser
// @version     1.0
// @description Check and highlight broken links on the page
// @author      You
// @include     *
// @grant       GM_xmlhttpRequest
// ==/UserScript==

(function() {
    'use strict';
    
    let isChecking = false;
    let checkedLinks = new Set();
    
    // Create checker panel
    const checkerPanel = document.createElement('div');
    checkerPanel.style.cssText = `
        position: fixed;
        top: 200px;
        right: 10px;
        z-index: 10000;
        background: rgba(0, 0, 0, 0.8);
        color: white;
        padding: 10px;
        border-radius: 5px;
        font-family: Arial, sans-serif;
        font-size: 12px;
        min-width: 150px;
    `;
    
    checkerPanel.innerHTML = `
        <div>Link Checker</div>
        <button id="checkLinks">Check Links</button>
        <br><br>
        <div id="progress">Ready</div>
        <div id="results"></div>
    `;
    
    document.body.appendChild(checkerPanel);
    
    const checkButton = document.getElementById('checkLinks');
    const progressDiv = document.getElementById('progress');
    const resultsDiv = document.getElementById('results');
    
    function checkLink(url, linkElement) {
        return new Promise((resolve) => {
            if (checkedLinks.has(url)) {
                resolve('cached');
                return;
            }
            
            GM_xmlhttpRequest({
                method: 'HEAD',
                url: url,
                timeout: 10000,
                onload: function(response) {
                    checkedLinks.add(url);
                    if (response.status >= 200 && response.status < 400) {
                        linkElement.style.borderLeft = '3px solid #4CAF50';
                        linkElement.title = `✓ Link OK (${response.status})`;
                        resolve('ok');
                    } else {
                        linkElement.style.borderLeft = '3px solid #ff6b6b';
                        linkElement.title = `✗ Link Error (${response.status})`;
                        resolve('error');
                    }
                },
                onerror: function() {
                    checkedLinks.add(url);
                    linkElement.style.borderLeft = '3px solid #ff6b6b';
                    linkElement.title = '✗ Link Error (Network)';
                    resolve('error');
                },
                ontimeout: function() {
                    checkedLinks.add(url);
                    linkElement.style.borderLeft = '3px solid #ffa500';
                    linkElement.title = '⚠ Link Timeout';
                    resolve('timeout');
                }
            });
        });
    }
    
    async function checkAllLinks() {
        if (isChecking) return;
        
        isChecking = true;
        checkButton.disabled = true;
        checkButton.textContent = 'Checking...';
        
        const links = document.querySelectorAll('a[href]');
        let checked = 0;
        let errors = 0;
        let timeouts = 0;
        
        progressDiv.textContent = `Found ${links.length} links`;
        resultsDiv.innerHTML = '';
        
        for (const link of links) {
            const href = link.href;
            
            // Skip non-HTTP links
            if (!href.startsWith('http')) {
                continue;
            }
            
            const result = await checkLink(href, link);
            checked++;
            
            if (result === 'error') errors++;
            if (result === 'timeout') timeouts++;
            
            progressDiv.textContent = `Checked ${checked}/${links.length}`;
            
            // Small delay to avoid overwhelming the server
            await new Promise(resolve => setTimeout(resolve, 100));
        }
        
        resultsDiv.innerHTML = `
            <div>✓ Working: ${checked - errors - timeouts}</div>
            <div>✗ Broken: ${errors}</div>
            <div>⚠ Timeout: ${timeouts}</div>
        `;
        
        isChecking = false;
        checkButton.disabled = false;
        checkButton.textContent = 'Check Links';
        progressDiv.textContent = 'Complete';
    }
    
    checkButton.addEventListener('click', checkAllLinks);
    
})();"""
    }
}

def get_template(name):
    """Get a template by name."""
    return TEMPLATES.get(name)

def get_template_names():
    """Get list of all template names."""
    return list(TEMPLATES.keys())

def get_templates_by_category():
    """Get templates organized by category."""
    categories = {
        "Basic": ["Basic Script"],
        "Content Blocking": ["Ad Blocker"],
        "UI Enhancement": ["Dark Mode", "Auto Scroll"],
        "Form Automation": ["Form Filler"],
        "Monitoring": ["Page Monitor", "Link Checker"]
    }
    return categories