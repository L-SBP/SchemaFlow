# Manual Verification Guide - Workspace Responsive Layout

## Quick Verification Checklist

### 🔍 Zoom Level Testing (Chrome DevTools)
1. Open Chrome DevTools (F12)
2. Press `Ctrl+Shift+M` to enable device simulation
3. Set device to "Responsive"
4. Test zoom levels: 100%, 200%, 300%, 400%, 500%
   - Use `Ctrl+Plus` / `Ctrl+Minus` to adjust zoom
   - Or set zoom in DevTools settings

### 📱 Breakpoint Testing
Test these viewport widths in DevTools responsive mode:

| Breakpoint | Width | Expected Behavior |
|------------|-------|-------------------|
| Mobile | 375px | Single column, panels stacked |
| Small Tablet | 768px | Dual column, right panel collapsible |
| Tablet | 1024px | Three columns, all panels visible |
| Desktop | 1440px | Three columns, comfortable spacing |
| Ultra-wide | 2560px | Three columns, max width constraints |

### ✅ Key Features to Verify

#### Input Bar Controls
- [ ] Model selector stays within input bar at all zoom levels
- [ ] Send button maintains minimum 44px clickable area
- [ ] Text input field doesn't overflow container
- [ ] Progressive degradation: full text → icon only → compact

#### Header Bar Layout
- [ ] Project name truncates with ellipsis when needed
- [ ] Project details button stays within header boundaries
- [ ] Buttons show icons only when space is limited
- [ ] Minimum 48px header height maintained

#### Panel Management
- [ ] DataViewer width clamps between 150px and 40% of viewport
- [ ] Drag resize handle works smoothly
- [ ] Panels auto-minimize at correct breakpoints:
  - Width < 1024px: DataViewer minimizes
  - Width < 768px: Session panel hides
  - Zoom > 200%: Mutual exclusion behavior

#### Global Scaling (High Zoom)
- [ ] At 300% zoom: Interface elements scale to 0.9x
- [ ] At 400% zoom: Interface elements scale to 0.8x  
- [ ] At 500% zoom: Interface elements scale to 0.7x
- [ ] Minimum clickable areas preserved (44px)
- [ ] Text remains readable (min 12px equivalent)

### 🧪 Interactive Testing Steps

#### Test 1: Input Bar Overflow Prevention
1. Set viewport to 375px width
2. Zoom to 500%
3. Verify model selector and send button stay within input bar
4. Try typing long text - should not cause horizontal scroll

#### Test 2: Panel Mutual Exclusion
1. Set zoom to 300%
2. Expand DataViewer panel
3. Verify Session panel auto-minimizes
4. Expand Session panel
5. Verify DataViewer auto-minimizes

#### Test 3: Drag Resize Constraints
1. Set viewport to 1440px width
2. Drag DataViewer resize handle to maximum width
3. Verify it stops at 40% of viewport (576px)
4. Drag to minimum width
5. Verify it stops at 150px

#### Test 4: Cross-Browser Compatibility
Test in each browser:
- [ ] Chrome: All features work
- [ ] Firefox: Layout consistent
- [ ] Safari: Responsive behavior intact
- [ ] Edge: No layout issues

### 🚨 Common Issues to Watch For

#### ❌ Overflow Problems
- Horizontal scrollbars appearing at page level
- Controls extending beyond container boundaries
- Text wrapping incorrectly at high zoom

#### ❌ Accessibility Issues
- Clickable areas smaller than 44px
- Text becoming unreadable (< 12px equivalent)
- Focus indicators not visible
- Keyboard navigation broken

#### ❌ Performance Issues
- Laggy transitions during resize
- Layout thrashing during zoom changes
- Memory leaks during repeated testing

### 📊 Performance Benchmarks

#### Target Metrics
- Resize operations: < 16ms (60fps)
- Zoom transitions: < 300ms
- Panel state changes: < 200ms
- Memory usage: Stable during testing

#### How to Measure
1. Open Chrome DevTools Performance tab
2. Start recording
3. Perform resize/zoom operations
4. Stop recording and analyze timeline

### 🔧 Debugging Tools

#### CSS Inspection
```css
/* Add to DevTools console to highlight containers */
document.querySelectorAll('.input-bar, .header-bar').forEach(el => {
  el.style.outline = '2px solid red';
});
```

#### Zoom Level Detection
```javascript
/* Check current zoom level in console */
console.log('Zoom Level:', window.devicePixelRatio * 100 + '%');
console.log('Viewport:', window.innerWidth + 'x' + window.innerHeight);
```

#### Global Scale Factor
```javascript
/* Check current global scale factor */
const root = document.documentElement;
const scaleFactor = getComputedStyle(root).getPropertyValue('--global-ui-scale-factor');
console.log('Global Scale Factor:', scaleFactor);
```

### ✅ Success Criteria

All tests pass when:
- ✅ No horizontal overflow at any zoom/viewport combination
- ✅ All controls stay within container boundaries
- ✅ Minimum accessibility standards maintained
- ✅ Smooth transitions between responsive states
- ✅ Consistent behavior across browsers
- ✅ Performance targets met

### 📝 Test Results Template

```
Date: ___________
Tester: ___________
Browser: ___________

Zoom Level Tests:
[ ] 100% - Normal operation
[ ] 200% - High zoom behavior
[ ] 300% - Global scaling 0.9x
[ ] 400% - Global scaling 0.8x
[ ] 500% - Global scaling 0.7x

Breakpoint Tests:
[ ] 375px - Mobile layout
[ ] 768px - Tablet layout
[ ] 1024px - Desktop layout
[ ] 1440px - Large desktop
[ ] 2560px - Ultra-wide

Feature Tests:
[ ] Input bar overflow prevention
[ ] Header bar layout integrity
[ ] Panel mutual exclusion
[ ] Drag resize constraints
[ ] Global scaling application

Issues Found:
_________________________________
_________________________________
_________________________________

Overall Status: PASS / FAIL
```

---

*This guide ensures comprehensive manual verification of the responsive layout system across all supported configurations.*