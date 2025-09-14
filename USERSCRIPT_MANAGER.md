# Voyx Browser Userscript Manager

A comprehensive Tampermonkey-style userscript manager built into Voyx Browser, providing full compatibility with Greasemonkey/Tampermonkey userscripts.

## Features

### 🚀 Core Features
- **Full Tampermonkey Compatibility** - Supports all major GM_* API functions
- **Visual Script Manager** - Modern GUI for managing userscripts
- **Script Editor** - Built-in JavaScript editor with syntax highlighting
- **Template System** - Pre-built templates for common userscript tasks
- **Auto-Updates** - Automatic script updates from remote URLs
- **Import/Export** - Backup and restore your userscripts
- **Statistics** - Track script usage and performance

### 📝 Script Management
- Create, edit, and delete userscripts
- Enable/disable scripts individually
- URL pattern matching (include/exclude)
- Metadata editing
- Script validation and testing
- Backup and restore functionality

### 🔧 Supported GM API Functions

#### Storage Functions
- `GM_getValue(key, defaultValue)` - Get stored value
- `GM_setValue(key, value)` - Set stored value
- `GM_deleteValue(key)` - Delete stored value
- `GM_listValues()` - List all stored keys

#### HTTP Functions
- `GM_xmlhttpRequest(details)` - Make HTTP requests
- Cross-origin request support
- Custom headers and methods
- Progress tracking and timeout handling

#### UI Functions
- `GM_addStyle(css)` - Inject CSS styles
- `GM_notification(details)` - Show notifications
- `GM_registerMenuCommand(name, fn, accessKey)` - Add menu commands
- `GM_unregisterMenuCommand(menuCmdId)` - Remove menu commands

#### Utility Functions
- `GM_openInTab(url, options)` - Open URLs in new tabs
- `GM_setClipboard(data, info)` - Copy to clipboard
- `GM_log(...args)` - Enhanced logging
- `GM_info` - Script and environment information

#### Modern GM.* API
All functions are also available through the modern `GM.*` namespace:
```javascript
GM.getValue('key', 'default')
GM.setValue('key', 'value')
GM.xmlhttpRequest({...})
// etc.
```

## Getting Started

### Opening the Userscript Manager
1. Click the 📜 button in the browser toolbar
2. Or use the keyboard shortcut `Ctrl+Shift+U`

### Creating Your First Script
1. Click "New Script" in the userscript manager
2. Choose a template or start from scratch
3. Edit the script in the built-in editor
4. Save and enable the script

### Installing Scripts from URLs
1. Click "Install from URL"
2. Enter the script URL (e.g., from GitHub, Greasyfork)
3. The script will be downloaded and installed automatically

## Script Templates

### Available Templates
- **Basic Script** - Simple template with common structure
- **Ad Blocker** - Remove ads and unwanted elements
- **Dark Mode** - Apply dark theme to websites
- **Auto Scroll** - Automatically scroll through pages
- **Form Filler** - Auto-fill forms with predefined data
- **Page Monitor** - Monitor page changes and notify
- **Link Checker** - Check and highlight broken links

### Creating Custom Templates
Templates are stored in `userscript_templates.py` and can be easily extended.

## Example Userscript

```javascript
// ==UserScript==
// @name        My First Script
// @namespace   VoyxBrowser
// @version     1.0
// @description My first Voyx Browser userscript
// @author      Me
// @include     https://example.com/*
// @grant       GM_getValue
// @grant       GM_setValue
// @grant       GM_addStyle
// ==/UserScript==

(function() {
    'use strict';
    
    // Add custom styles
    GM_addStyle(`
        .my-highlight {
            background-color: yellow !important;
        }
    `);
    
    // Store visit count
    let visits = GM_getValue('visit_count', 0);
    visits++;
    GM_setValue('visit_count', visits);
    
    // Highlight all links
    document.querySelectorAll('a').forEach(link => {
        link.classList.add('my-highlight');
    });
    
    console.log(`This is visit #${visits}`);
    
})();
```

## Advanced Features

### Auto-Updates
Scripts can be automatically updated by including update URLs in metadata:
```javascript
// @updateURL   https://example.com/script.user.js
// @downloadURL https://example.com/script.user.js
```

### Resource Loading
Include external resources in your scripts:
```javascript
// @resource    JQUERY https://code.jquery.com/jquery-3.6.0.min.js
// @resource    CSS https://example.com/styles.css
```

### Cross-Origin Requests
Make requests to any domain:
```javascript
GM_xmlhttpRequest({
    method: 'GET',
    url: 'https://api.example.com/data',
    headers: {
        'Authorization': 'Bearer token'
    },
    onload: function(response) {
        console.log(response.responseText);
    }
});
```

### Persistent Storage
Store data that persists across browser sessions:
```javascript
// Store complex data
GM_setValue('user_preferences', {
    theme: 'dark',
    language: 'en',
    notifications: true
});

// Retrieve data
const prefs = GM_getValue('user_preferences', {});
```

## Keyboard Shortcuts

- `Ctrl+Shift+U` - Open userscript manager
- `Ctrl+Shift+D` - Toggle demo panel (in demo script)
- `Ctrl+Shift+N` - Show notification (in demo script)
- `Ctrl+S` - Save script in editor
- `Ctrl+F` - Format code in editor

## File Structure

```
userscripts/
├── storage/              # Script storage data
├── *.user.js            # Userscript files
└── example.user.js      # Example script

userscript_manager.py     # Core manager logic
userscript_gui.py         # GUI interface
userscript_api.py         # GM API implementation
userscript_templates.py   # Script templates
```

## Troubleshooting

### Script Not Running
1. Check if the script is enabled
2. Verify URL patterns match the current page
3. Check browser console for JavaScript errors
4. Enable debug mode in settings

### API Functions Not Working
1. Ensure proper `@grant` declarations in metadata
2. Check if the function is supported
3. Verify syntax and parameters

### Performance Issues
1. Disable unused scripts
2. Optimize script code
3. Check for infinite loops or heavy operations
4. Use script statistics to identify problematic scripts

## Security Considerations

- Scripts run with full page access
- Only install scripts from trusted sources
- Review script code before installation
- Use the built-in script validator
- Keep scripts updated

## Contributing

To add new features or templates:
1. Fork the repository
2. Add your changes to the appropriate files
3. Test thoroughly
4. Submit a pull request

## Support

For issues or questions:
- Check the browser console for errors
- Enable debug mode for detailed logging
- Review the demo script for examples
- Submit issues on GitHub

---

**Note**: This userscript manager provides Tampermonkey-level functionality within Voyx Browser, making it easy to run existing userscripts and create new ones with full API compatibility.