from pathlib import Path

p = Path('hvss2.html')
s = p.read_text(encoding='utf-8')

# The native transport patch is already present in the current HVSS2 baseline.
# Keep it intact and repair only the cross-IIFE UI refresh bridge.
if 'function nativeCentralCall(' not in s or 'window.__HVSS_NATIVE_CENTRAL_RESOLVE' not in s:
    raise SystemExit('Expected native CENTRAL transport patch is missing; refusing to modify an unexpected HVSS2 baseline')

# Main HVSS functions live inside the application's own IIFE. The CENTRAL
# runtime lives in a separate IIFE, so direct references such as renderAll()
# and renderKeyLog() are out of scope. Export the required functions once.
render_anchor = 'function renderAll(){renderDashboard();renderVisitors();renderKeys();renderReport();renderHistory()}'
render_export = render_anchor + '\nwindow.HVSS_RENDER_ALL=renderAll;\nwindow.HVSS_RENDER_KEY_LOG=renderKeyLog;\nwindow.HVSS_ADD_BULK_KEY_ROW=addBulkKeyRow;'
if 'window.HVSS_RENDER_ALL=renderAll;' not in s:
    if render_anchor not in s:
        raise SystemExit('renderAll anchor not found; refusing to guess')
    s = s.replace(render_anchor, render_export, 1)

# Replace the broken cross-IIFE references inside applyCentral().
old_ui = '''    if(typeof renderAll==='function') if(document.getElementById("bkRows")&&!document.querySelector("#bkRows .key-bulk-row"))addBulkKeyRow();
renderAll();
    if(typeof renderKeyLog==='function')renderKeyLog();'''
new_ui = '''    if(typeof window.HVSS_ADD_BULK_KEY_ROW==='function'){
      if(document.getElementById("bkRows")&&!document.querySelector("#bkRows .key-bulk-row"))window.HVSS_ADD_BULK_KEY_ROW();
    }
    if(typeof window.HVSS_RENDER_ALL==='function')window.HVSS_RENDER_ALL();
    if(typeof window.HVSS_RENDER_KEY_LOG==='function')window.HVSS_RENDER_KEY_LOG();'''
if old_ui in s:
    s = s.replace(old_ui, new_ui, 1)
elif new_ui not in s:
    raise SystemExit('CENTRAL UI refresh anchor not found; refusing to guess')

p.write_text(s, encoding='utf-8')
print('HVSS2 native CENTRAL transport + UI scope repair applied')
