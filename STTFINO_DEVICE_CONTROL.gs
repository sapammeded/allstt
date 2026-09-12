/**
 * STTFINO3 — CENTRAL BACKEND
 * Uses only DEVICES and FINDINGS in STTFINO3.
 */
const SPREADSHEET_ID='1dxjIOEhQhoJpkcWBaeHm5n1ERGky7ztSWjBiLoo6JTs';
const PHOTO_PARENT_FOLDER_ID='1G28FlBrRC81QRAUQpQB1L1HUssxiYL8N';
const PHOTO_FOLDER_NAME='STT - FINDING NOTES PHOTOS';
const ADMIN_KEY='amdshadow7373';
const DEVICES_SHEET='DEVICES';
const FINDINGS_SHEET='FINDINGS';
const DEVICE_HEADERS=['installation_id','user_name','app','device','android','app_version','activation_code','first_seen','last_seen','status','notes'];
const FINDING_HEADERS=['finding_id','area_code','photo_url','description','finder_name','created_at','status','updated_at','is_deleted'];
const ACTIVE='ACTIVE',BLOCKED='BLOCKED',PENDING='PENDING',REVOKED='REVOKED';

function json_(o){return ContentService.createTextOutput(JSON.stringify(o)).setMimeType(ContentService.MimeType.JSON);}
function nowIso_(){return new Date().toISOString();}
function clean_(v){return String(v==null?'':v).trim();}
function mergePostPayload_(p){var o=Object.assign({},p||{});try{if(p&&p.payload){var x=JSON.parse(String(p.payload));if(x&&typeof x==='object')Object.keys(x).forEach(function(k){o[k]=x[k];});}}catch(_){}return o;}

function ensureSheets_(){
  var ss=SpreadsheetApp.openById(SPREADSHEET_ID),d=ss.getSheetByName(DEVICES_SHEET),f=ss.getSheetByName(FINDINGS_SHEET);
  if(!d)d=ss.insertSheet(DEVICES_SHEET); if(!f)f=ss.insertSheet(FINDINGS_SHEET);
  ensureHeader_(d,DEVICE_HEADERS); ensureHeader_(f,FINDING_HEADERS); return {ss:ss,devices:d,findings:f};
}
function ensureHeader_(sh,h){
  if(sh.getLastRow()===0){sh.getRange(1,1,1,h.length).setValues([h]);sh.setFrozenRows(1);return;}
  var a=sh.getRange(1,1,1,h.length).getValues()[0],bad=false;
  for(var i=0;i<h.length;i++)if(String(a[i])!==h[i]){bad=true;break;}
  if(bad)sh.getRange(1,1,1,h.length).setValues([h]);
}

// Fast lookup: TextFinder searches only the key column instead of loading the whole sheet.
function findRow_(sh,col,value){
  var last=sh.getLastRow(); if(last<2)return 0;
  var v=clean_(value); if(!v)return 0;
  var hit=sh.getRange(2,col,last-1,1).createTextFinder(v).matchEntireCell(true).matchCase(true).findNext();
  return hit?hit.getRow():0;
}

function deviceCheck_(p){
  var id=clean_(p.installation_id),app=clean_(p.app||'ALLSTT').toUpperCase();
  if(!id)return json_({status:'ERROR',message:'installation_id wajib diisi'});
  var s=ensureSheets_().devices,row=findRow_(s,1,id),t=nowIso_();
  if(!row){
    s.appendRow([id,'',app,clean_(p.device),clean_(p.android),clean_(p.app_version),'',t,t,PENDING,'AUTO-REGISTERED: menunggu aktivasi administrator']);
    return json_({status:PENDING,message:'Perangkat menunggu aktivasi administrator.',device:{installation_id:id,status:PENDING}});
  }
  var old=s.getRange(row,1,1,DEVICE_HEADERS.length).getValues()[0];
  var oldStatus=clean_(old[9]).toUpperCase()||PENDING,code=clean_(old[6]),supplied=clean_(p.activation_code);
  // Never let the device overwrite administrator-controlled user_name, activation_code, or status.
  s.getRange(row,3,1,4).setValues([[app,clean_(p.device)||clean_(old[3]),clean_(p.android)||clean_(old[4]),clean_(p.app_version)||clean_(old[5])]]);
  if(!old[7])s.getRange(row,8).setValue(t); s.getRange(row,9).setValue(t);
  if(oldStatus===ACTIVE){
    if(!code)return json_({status:PENDING,message:'Perangkat ACTIVE tetapi kode aktivasi belum diisi administrator.'});
    if(supplied!==code)return json_({status:PENDING,message:'Kode aktivasi tidak cocok.'});
    return json_({status:ACTIVE,message:'Akses diizinkan.',user_name:clean_(old[1]),device:{installation_id:id,status:ACTIVE}});
  }
  if(oldStatus===BLOCKED)return json_({status:BLOCKED,message:'Perangkat diblokir administrator.'});
  if(oldStatus===REVOKED)return json_({status:REVOKED,message:'Akses perangkat dicabut administrator.'});
  return json_({status:PENDING,message:'Perangkat menunggu aktivasi administrator.'});
}

function deviceSetStatus_(p){
  if(clean_(p.admin_key)!==ADMIN_KEY)return json_({status:'ERROR',message:'ADMIN key salah'});
  var id=clean_(p.installation_id),status=clean_(p.status).toUpperCase();
  if(!id||[PENDING,ACTIVE,BLOCKED,REVOKED].indexOf(status)<0)return json_({status:'ERROR',message:'installation_id/status tidak valid'});
  var s=ensureSheets_().devices,row=findRow_(s,1,id); if(!row)return json_({status:'ERROR',message:'Device belum terdaftar'});
  s.getRange(row,10).setValue(status);s.getRange(row,9).setValue(nowIso_());
  return json_({status:'OK',installation_id:id,device_status:status});
}

function findingsRevision_(){var f=ensureSheets_().findings,last=f.getLastRow();return last<2?'0':String(f.getRange(last,8).getValue()||f.getRange(last,6).getValue()||last);}
function toIso_(v){if(!v)return '';var d=v instanceof Date?v:new Date(v);return isNaN(d.getTime())?String(v):d.toISOString();}
function truthy_(v){return String(v).toLowerCase()==='true'||v===true||String(v)==='1';}
function getFindings_(){
  var f=ensureSheets_().findings,last=f.getLastRow(); if(last<2)return json_({status:'success',data:[],revision:'0'});
  var a=f.getRange(2,1,last-1,FINDING_HEADERS.length).getValues().map(function(r){return {finding_id:String(r[0]||''),area_code:String(r[1]||''),photo_url:String(r[2]||''),description:String(r[3]||''),finder_name:String(r[4]||''),created_at:toIso_(r[5]),status:String(r[6]||'OPEN').toUpperCase(),updated_at:toIso_(r[7]),is_deleted:truthy_(r[8])};}).filter(function(x){return x.finding_id&&!x.is_deleted;});
  return json_({status:'success',data:a,revision:findingsRevision_()});
}
function saveFinding_(p){
  var id=clean_(p.finding_id);if(!id)return json_({status:'error',message:'finding_id wajib diisi'});
  var s=ensureSheets_().findings,row=findRow_(s,1,id),created=clean_(p.created_at)||nowIso_(),data=[id,clean_(p.area_code),clean_(p.photo_url)||'[]',clean_(p.description),clean_(p.finder_name),created,(clean_(p.status)||'OPEN').toUpperCase(),nowIso_(),'FALSE'];
  if(row)s.getRange(row,1,1,FINDING_HEADERS.length).setValues([data]);else s.appendRow(data); return json_({status:'success',finding:data});
}
function updateStatus_(p){
  var id=clean_(p.finding_id),st=clean_(p.status).toUpperCase();if(!id||['OPEN','IN PROGRESS','FIXED'].indexOf(st)<0)return json_({status:'error',message:'Data status tidak valid'});
  var s=ensureSheets_().findings,row=findRow_(s,1,id);if(!row)return json_({status:'error',message:'Finding tidak ditemukan'});s.getRange(row,7).setValue(st);s.getRange(row,8).setValue(nowIso_());return json_({status:'success',finding_id:id,status:st});
}
function deleteFinding_(p){var id=clean_(p.finding_id),s=ensureSheets_().findings,row=findRow_(s,1,id);if(!row)return json_({status:'success',finding_id:id});s.getRange(row,8).setValue(nowIso_());s.getRange(row,9).setValue('TRUE');return json_({status:'success',finding_id:id,is_deleted:true});}
function uploadPhoto_(e){
  var p=(e&&e.parameter)||{},uploadId=clean_(p.upload_id)||'UP-'+Date.now(),findingId=clean_(p.finding_id)||'finding',mime=clean_(p.mime)||'image/jpeg',filename=(clean_(p.filename)||('finding_'+findingId+'_'+Date.now()+'.jpg')).replace(/[\\/:*?"<>|]/g,'_').slice(0,100),raw=e&&e.postData&&e.postData.contents;
  if(!raw)return json_({status:'error',message:'Payload foto kosong',upload_id:uploadId});
  var blob=Utilities.newBlob(raw,mime,filename);if(blob.getBytes().length>6*1024*1024)return json_({status:'error',message:'Foto terlalu besar',upload_id:uploadId});
  var parent=DriveApp.getFolderById(PHOTO_PARENT_FOLDER_ID),folders=parent.getFoldersByName(PHOTO_FOLDER_NAME),folder=folders.hasNext()?folders.next():parent.createFolder(PHOTO_FOLDER_NAME),file=folder.createFile(blob),url='https://drive.google.com/uc?export=view&id='+file.getId();
  PropertiesService.getScriptProperties().setProperty('UPLOAD_'+uploadId,JSON.stringify({status:'success',url:url,finding_id:findingId}));return json_({status:'success',upload_id:uploadId,url:url});
}
function getUploadStatus_(id){if(!id)return json_({status:'error',message:'upload_id wajib diisi'});var raw=PropertiesService.getScriptProperties().getProperty('UPLOAD_'+id);return raw?json_(JSON.parse(raw)):json_({status:'pending',upload_id:id});}

function doGet(e){try{var p=(e&&e.parameter)||{},a=clean_(p.action).toUpperCase();if(a==='PING')return json_({status:'OK',service:'STTFINO3_DEVICE_CONTROL',spreadsheet:'STTFINO3'});if(a==='GET_META')return json_({status:'success',revision:findingsRevision_()});if(a==='GET_FINDINGS')return getFindings_();if(a==='GET_UPLOAD_STATUS')return getUploadStatus_(clean_(p.upload_id));if(a==='DEVICE_CHECK'||a==='DEVICE_HEARTBEAT')return deviceCheck_(p);return json_({status:'ERROR',message:'Invalid action',action_received:a});}catch(err){return json_({status:'ERROR',message:String(err&&err.message||err)});}}
function doPost(e){try{var p=mergePostPayload_((e&&e.parameter)||{}),a=clean_(p.action).toUpperCase();if(a==='UPLOAD_PHOTO')return uploadPhoto_(e);if(a==='DEVICE_CHECK'||a==='DEVICE_HEARTBEAT')return deviceCheck_(p);if(a==='DEVICE_SET_STATUS')return deviceSetStatus_(p);if(a==='SAVE_FINDING')return saveFinding_(p);if(a==='UPDATE_STATUS')return updateStatus_(p);if(a==='DELETE_FINDING')return deleteFinding_(p);return json_({status:'ERROR',message:'Invalid POST action',action_received:a});}catch(err){return json_({status:'ERROR',message:String(err&&err.message||err)});}}
function setupDevicesSheet(){ensureSheets_();}
