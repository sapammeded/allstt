from pathlib import Path

p=Path('stt.html')
s=p.read_text(encoding='utf-8')
old="await idbPut({left:await toBlob(leftData),right:await toBlob(rightData),savedAt:Date.now()})"
new="await idbPut({left:await toBlob(leftData),right:await toBlob(rightData),name:fields.name.value.trim(),title:fields.title.value.trim(),address:fields.address.value.trim(),subtitle:fields.subtitle.value.trim(),footer:fields.footer.value.trim(),savedAt:Date.now()})"
if old in s:
    s=s.replace(old,new,1)
old2="fields.name.value=localStorage.getItem('patrol_company_name_v1')||'';fields.title.value=localStorage.getItem('patrol_letter_title_v1')||'';fields.address.value=localStorage.getItem('patrol_company_address_v1')||'';fields.subtitle.value=localStorage.getItem('patrol_letter_subtitle_v1')||'';fields.footer.value=localStorage.getItem('patrol_letter_footer_v1')||'';"
new2="fields.name.value=d?.name||localStorage.getItem('patrol_company_name_v1')||'';fields.title.value=d?.title||localStorage.getItem('patrol_letter_title_v1')||'';fields.address.value=d?.address||localStorage.getItem('patrol_company_address_v1')||'';fields.subtitle.value=d?.subtitle||localStorage.getItem('patrol_letter_subtitle_v1')||'';fields.footer.value=d?.footer||localStorage.getItem('patrol_letter_footer_v1')||'';"
if old2 in s:
    s=s.replace(old2,new2,1)
p.write_text(s,encoding='utf-8')
print('identity persistence finalized')
