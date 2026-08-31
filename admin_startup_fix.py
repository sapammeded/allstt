from pathlib import Path
p=Path('stt.html')
s=p.read_text(encoding='utf-8')
marker='ALLSTT-ADMIN-STARTUP-FIX'
if marker not in s:
    fix='''<script id="ALLSTT-ADMIN-STARTUP-FIX">document.addEventListener("DOMContentLoaded",function(){var a=document.getElementById("adminSection"),c=document.getElementById("companySection"),l=document.getElementById("logoUploadSection");if(a)a.style.display="none";if(c)c.style.display="none";if(l)l.style.display="none";});</script>'''
    s=s.replace('</body>',fix+'\n</body>',1)
p.write_text(s,encoding='utf-8')
