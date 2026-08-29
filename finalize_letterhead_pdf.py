from pathlib import Path
p=Path('stt.html')
s=p.read_text(encoding='utf-8')
old="window.__sttApplyLetterhead=async function(pdf){syncGlobals();const W=pdf.internal.pageSize.getWidth(),L=12,R=12;if(leftData){try{pdf.addImage(leftData,'AUTO',L,10,28,28)}catch(_){}}if(rightData){try{pdf.addImage(rightData,'AUTO',W-R-28,10,28,28)}catch(_){}}pdf.setTextColor(11,61,145);pdf.setFont('helvetica','bold');pdf.setFontSize(15);pdf.text(fields.name.value.trim()||'NAMA PERUSAHAAN',W/2,15,{align:'center'});if(fields.title.value.trim()){pdf.setFontSize(10);pdf.text(fields.title.value.trim(),W/2,22,{align:'center'})}pdf.setTextColor(30,41,59);pdf.setFont('helvetica','normal');pdf.setFontSize(8);let y=28;if(fields.address.value.trim()){const lines=pdf.splitTextToSize(fields.address.value.trim(),105);pdf.text(lines,W/2,y,{align:'center'});y+=lines.length*4}if(fields.subtitle.value.trim())pdf.text(fields.subtitle.value.trim(),W/2,y,{align:'center'});pdf.setDrawColor(11,61,145);pdf.setLineWidth(.6);pdf.line(L,40,W-R,40)};"
new="window.__sttApplyLetterhead=async function(pdf){syncGlobals();try{localStorage.setItem('patrol_letter_title_v1',fields.title.value.trim());localStorage.setItem('patrol_letter_subtitle_v1',fields.subtitle.value.trim());localStorage.setItem('patrol_letter_footer_v1',fields.footer.value.trim())}catch(_){}};"
if old in s:s=s.replace(old,new,1)
# Existing PDF already has a professional cover/header and already draws the two logo globals.
# Make its fixed report subtitle configurable without changing layout.
s=s.replace("pdf.text('SECURITY PATROL & INCIDENT DOCUMENTATION',W/2,contactY,{align:'center'});","pdf.text(localStorage.getItem('patrol_letter_subtitle_v1') || 'SECURITY PATROL & INCIDENT DOCUMENTATION',W/2,contactY,{align:'center'});")
s=s.replace("pdf.text(`Laporan Patroli Security • ${petugas}`,M,H-8);","pdf.text(localStorage.getItem('patrol_letter_footer_v1') || `Laporan Patroli Security • ${petugas}`,M,H-8);")
p.write_text(s,encoding='utf-8')
print('letterhead PDF integration finalized')
