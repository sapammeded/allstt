from pathlib import Path

p = Path('hvss2.html')
s = p.read_text(encoding='utf-8')
if 'HVSS-KEY-LOAN-LOG-PATCH-V1' in s:
    print('HVSS-KEY-LOAN-LOG-PATCH-V1 already present')
    raise SystemExit(0)

nav_marker = '  <button type="button" class="tab" data-page="report">Daily Report</button>'
nav_add = '  <button type="button" class="tab" data-page="keylogPage">Key Loan Log</button>\n' + nav_marker
if nav_marker not in s:
    raise SystemExit('Key Loan Log insertion marker not found')
s = s.replace(nav_marker, nav_add, 1)

section_marker = '<section class="page" id="report">'
section = r'''<section class="page" id="keylogPage">
 <div class="card">
  <div class="head">
   <div><h2>Key Loan Log</h2><div class="muted">Central history dari Google Spreadsheet • bisa dicari berdasarkan tanggal</div></div>
   <div class="actions no-print" style="margin:0"><button type="button" class="btn dark" id="keyLogExcel">Excel</button><button type="button" class="btn primary" id="keyLogPdf">PDF</button></div>
  </div>
  <div class="toolbar no-print">
   <input id="keyLogFrom" type="date">
   <input id="keyLogTo" type="date">
   <input id="keyLogSearch" placeholder="Search borrower / key / division / security">
   <button type="button" class="btn secondary" id="keyLogToday">Today</button>
   <button type="button" class="btn secondary" id="keyLogAll">All History</button>
  </div>
  <div class="muted" id="keyLogCount" style="margin-bottom:8px">0 record(s)</div>
  <div class="tablewrap"><table class="table"><thead><tr><th>No</th><th>Date Out</th><th>Time Out</th><th>Borrower</th><th>Division</th><th>Security OUT</th><th>Key</th><th>Key Number</th><th>Date In</th><th>Time In</th><th>Returner</th><th>Division IN</th><th>Security IN</th><th>Remark</th><th>Keterangan</th><th>Status</th></tr></thead><tbody id="keyLogBody"></tbody></table></div>
 </div>
</section>
'''
if section_marker not in s:
    raise SystemExit('Report section marker not found')
s = s.replace(section_marker, section + section_marker, 1)

script = r'''<script id="HVSS-KEY-LOAN-LOG-PATCH-V1">
(function(){
  const $k=id=>document.getElementById(id);
  const norm=v=>String(v==null?'':v).trim().toLowerCase();
  const rowData=()=>{
    try{
      const rows=typeof makeKeyRows==='function'?makeKeyRows(''):[];
      return Array.isArray(rows)?rows.slice(1):[];
    }catch(e){return []}
  };
  function inRange(x,from,to){
    const d=typeof dateKey==='function'?dateKey(x[1]||''):String(x[1]||'');
    if(from && d<from)return false;
    if(to && d>to)return false;
    return true;
  }
  function render(){
    const body=$k('keyLogBody'), search=norm($k('keyLogSearch')?.value), from=$k('keyLogFrom')?.value||'', to=$k('keyLogTo')?.value||'';
    let rows=rowData().filter(r=>inRange(r,from,to));
    if(search) rows=rows.filter(r=>r.some(v=>norm(v).includes(search)));
    if(body) body.innerHTML=rows.length?rows.map((r,i)=>'<tr>'+r.map(v=>'<td>'+String(v==null?'':v).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;')+'</td>').join('')+'</tr>').join(''):'<tr><td colspan="16" class="empty">Tidak ada data pada filter ini.</td></tr>';
    if($k('keyLogCount')) $k('keyLogCount').textContent=rows.length+' record(s)';
    return rows;
  }
  async function pull(){
    try{if(window.HVSS_CENTRAL_PULL) await window.HVSS_CENTRAL_PULL();}
    catch(e){alert('Gagal mengambil Key Loan Log dari CENTRAL: '+(e.message||e));}
    render();
  }
  function todayValue(){return typeof today==='function'?today():new Date().toISOString().slice(0,10)}
  $k('keyLogSearch')?.addEventListener('input',render);
  $k('keyLogFrom')?.addEventListener('change',render);
  $k('keyLogTo')?.addEventListener('change',render);
  $k('keyLogToday')?.addEventListener('click',function(){const d=todayValue();$k('keyLogFrom').value=d;$k('keyLogTo').value=d;pull();});
  $k('keyLogAll')?.addEventListener('click',function(){$k('keyLogFrom').value='';$k('keyLogTo').value='';pull();});
  $k('keyLogExcel')?.addEventListener('click',function(){
    if(typeof exportFromCentral!=='function'||typeof exportWorkbook!=='function'||typeof makeKeyRows!=='function'){return alert('Export engine belum siap.');}
    exportFromCentral(function(){
      const rows=render();
      return [{name:'Key Loan Log',rows:[window.HVSS_KEY_HEADERS].concat(rows)}];
    },'HVSS_Key_Loan_Log.xlsx');
  });
  $k('keyLogPdf')?.addEventListener('click',async function(){
    await pull();
    const rows=render();
    if(!window.jspdf||!window.jspdf.jsPDF||!window.jspdf.jsPDF.prototype.autoTable){return alert('PDF engine belum siap.');}
    const doc=new window.jspdf.jsPDF({orientation:'landscape',unit:'mm',format:'a4'});
    const d=($k('keyLogFrom')?.value||'')+' s/d '+($k('keyLogTo')?.value||'');
    doc.setFontSize(15);doc.text('HVSS KEY LOAN LOG',10,12);doc.setFontSize(9);doc.text('Periode: '+d,10,18);
    doc.autoTable({startY:23,head:[window.HVSS_KEY_HEADERS],body:rows,styles:{fontSize:6,cellPadding:1.5},headStyles:{fontSize:6},margin:{left:7,right:7}});
    doc.save('HVSS_Key_Loan_Log.pdf');
  });
  document.querySelectorAll('.tab[data-page="keylogPage"]').forEach(function(btn){btn.addEventListener('click',pull);});
  window.addEventListener('load',function(){setTimeout(render,200);});
})();
</script>
'''
if '</body>' not in s:
    raise SystemExit('</body> marker not found')
s = s.replace('</body>', script + '</body>', 1)
p.write_text(s, encoding='utf-8')
print('patched hvss2.html with HVSS-KEY-LOAN-LOG-PATCH-V1')
