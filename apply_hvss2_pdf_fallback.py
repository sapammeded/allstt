from pathlib import Path

p = Path('hvss2.html')
s = p.read_text(encoding='utf-8')

if 'HVSS-PDF-FALLBACK-V2' not in s:
    marker = '</body>'
    fallback = r'''<script id="HVSS-PDF-FALLBACK-V2">
(function(){
  function esc(v){
    return String(v==null?'':v)
      .normalize('NFD').replace(/[\u0300-\u036f]/g,'')
      .replace(/[\r\n\t]+/g,' ')
      .replace(/[^\x20-\x7E]/g,'?')
      .replace(/\\/g,'\\\\').replace(/\(/g,'\\(').replace(/\)/g,'\\)');
  }
  window.HVSS_PDF_FALLBACK=function(title,headers,rows,filename){
    try{
      const lines=[String(title||'HVSS REPORT'),'HVSS Security Control Center',''];
      (Array.isArray(rows)?rows:[]).forEach(function(r,i){
        lines.push('RECORD '+(i+1));
        (headers||[]).forEach(function(h,j){lines.push(String(h)+': '+String(r&&r[j]!=null?r[j]:'').replace(/[\r\n]+/g,' '));});
        lines.push('');
      });
      if(lines.length===3) lines.push('No data.');
      const wrapped=[];
      lines.forEach(function(line){
        line=String(line);
        if(!line){wrapped.push('');return;}
        for(let i=0;i<line.length;i+=105) wrapped.push(line.slice(i,i+105));
      });
      const pageLines=50,pages=[];
      for(let i=0;i<wrapped.length;i+=pageLines) pages.push(wrapped.slice(i,i+pageLines));
      if(!pages.length) pages.push(['No data.']);
      const pageCount=pages.length;
      const pageObjs=[],contentObjs=[];
      for(let i=0;i<pageCount;i++){pageObjs.push(3+i*2);contentObjs.push(4+i*2);}
      const fontObj=3+pageCount*2,objs=[];
      objs[1]='<< /Type /Catalog /Pages 2 0 R >>';
      objs[2]='<< /Type /Pages /Kids ['+pageObjs.map(function(n){return n+' 0 R';}).join(' ')+'] /Count '+pageCount+' >>';
      for(let pi=0;pi<pageCount;pi++){
        const pageObj=pageObjs[pi],contentObj=contentObjs[pi],body=['BT','/F1 12 Tf','1 0 0 1 28 568 Tm','('+esc(pi===0?title:String(title||'HVSS REPORT')+' (continued)')+') Tj','/F1 7 Tf'];
        let y=548;
        pages[pi].forEach(function(line){body.push('1 0 0 1 28 '+y+' Tm');body.push('('+esc(line)+') Tj');y-=10;});
        body.push('ET');
        const stream=body.join('\n');
        objs[pageObj]='<< /Type /Page /Parent 2 0 R /MediaBox [0 0 842 595] /Resources << /Font << /F1 '+fontObj+' 0 R >> >> /Contents '+contentObj+' 0 R >>';
        objs[contentObj]='<< /Length '+stream.length+' >>\nstream\n'+stream+'\nendstream';
      }
      objs[fontObj]='<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>';
      let pdf='%PDF-1.4\n%HVSS\n',offsets=[0];
      for(let n=1;n<objs.length;n++){offsets[n]=pdf.length;pdf+=n+' 0 obj\n'+objs[n]+'\nendobj\n';}
      const xref=pdf.length;
      pdf+='xref\n0 '+objs.length+'\n0000000000 65535 f \n';
      for(let n=1;n<objs.length;n++) pdf+=String(offsets[n]).padStart(10,'0')+' 00000 n \n';
      pdf+='trailer\n<< /Size '+objs.length+' /Root 1 0 R >>\nstartxref\n'+xref+'\n%%EOF';
      const base64=btoa(pdf);
      filename=filename||'HVSS_Report.pdf';
      if(window.Android&&Android.saveBase64File){Android.saveBase64File(filename,'application/pdf',base64);return true;}
      const a=document.createElement('a');a.href='data:application/pdf;base64,'+base64;a.download=filename;document.body.appendChild(a);a.click();a.remove();return true;
    }catch(e){console.error(e);alert('Gagal membuat PDF: '+(e.message||e));return false;}
  };
})();
</script>
'''
    if marker not in s:
        raise SystemExit('</body> marker not found')
    s=s.replace(marker,fallback+marker,1)

old='''if(!window.jspdf || !window.jspdf.jsPDF){
    alert("PDF engine belum siap. Pastikan internet aktif lalu refresh halaman.");
    return;
  }'''
new='''if(!window.jspdf || !window.jspdf.jsPDF || typeof window.jspdf.jsPDF.prototype.autoTable!=="function"){
    const r=reportData();
    let headers=[],rows=[];
    if(mode==="key"){
      headers=window.HVSS_KEY_HEADERS;
      rows=r.k.map((x,i)=>[i+1,dateLabel(x.outDate),x.outTime||"",x.borrower||"",x.division||"",x.security||"",x.keyName||"",String(x.keyNumber||""),dateLabel(x.inDate),x.inTime||"",x.returner||"",x.inDivision||"",x.inSecurity||"",x.remark||"",x.note||"",x.inDate?"RETURNED":"KEY OUT"]);
    }else if(mode==="visitor"){
      headers=window.HVSS_VISITOR_HEADERS;
      rows=r.v.map((x,i)=>[i+1,dateLabel(x.date),x.timeIn||"",x.timeOut||"",x.name||"",x.company||"",String(x.idcard||""),x.purpose||"",x.area||"",x.remark||"",x.timeOut?"OUT":"INSIDE"]);
    }else{
      headers=["Type","Date","Time","Name","Detail"];
      rows=r.v.map(x=>["VISITOR",dateLabel(x.date),x.timeIn||"",x.name||"",((x.company||"")+" • "+(x.area||"")).trim()]).concat(r.k.map(x=>["KEY",dateLabel(x.outDate||x.inDate),x.outTime||x.inTime||"",x.borrower||"",((x.keyName||"")+" • "+(x.keyNumber||"")).trim()]));
    }
    return window.HVSS_PDF_FALLBACK("HVSS "+String(mode||"REPORT").toUpperCase(),headers,rows,"HVSS_"+String(mode||"Report")+".pdf");
  }'''
if old not in s:
    raise SystemExit('main PDF engine guard not found')
s=s.replace(old,new,1)

old_key='''if(!window.jspdf||!window.jspdf.jsPDF||!window.jspdf.jsPDF.prototype.autoTable){return alert('PDF engine belum siap.');}'''
new_key='''if(!window.jspdf||!window.jspdf.jsPDF||typeof window.jspdf.jsPDF.prototype.autoTable!=="function"){
      return window.HVSS_PDF_FALLBACK('HVSS KEY LOAN LOG',window.HVSS_KEY_HEADERS||[],rows,'HVSS_Key_Loan_Log.pdf');
    }'''
if old_key in s:
    s=s.replace(old_key,new_key,1)
else:
    # Accept the current spacing variant used by some generated baselines.
    old_key2="if(!window.jspdf||!window.jspdf.jsPDF||!window.jspdf.jsPDF.prototype.autoTable){return alert('PDF engine belum siap.');}"
    if old_key2 not in s:
        raise SystemExit('Key Loan Log PDF engine guard not found')
    s=s.replace(old_key2,new_key,1)

p.write_text(s,encoding='utf-8')
print('HVSS2 PDF fallback applied')
