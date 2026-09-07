/**
 * VACS V7.1 — Vehicle Access Control System
 * CREATED BY: Mbah Pri
 * FINAL P1 UI + BUGFIX
 */
const CONFIG={
  SPREADSHEET_ID:'1wFnASAShpQgFA4bMZE2PIH5ccKma66otpHNMjLZgyv4',
  TIMEZONE:'Asia/Jakarta',
  VERSION:'8.1',
  CREATED_BY:'Mbah Pri',
  LONG_STAY_HOURS:12,
  REPEATED_DENIAL_COUNT:3,
  REPEATED_DENIAL_WINDOW_MIN:60,
  ALERT_COOLDOWN_MIN:30
};
const VEHICLE_HEADERS=['Nama','Nomor Kendaraan','Bagian/Divisi','Jenis Kendaraan','Model','Warna Kendaraan','Access Type'];
// LOG_HEADERS kept exactly as-is for backward compatibility (columns A-J untouched).
// Column K (index 11) is appended separately as an optional idempotency key for offline sync;
// existing readers use getRange(2,1,n-1,10) so this addition never breaks legacy code.
const LOG_HEADERS=['Nama','Nomor Kendaraan','Bagian/Divisi','Jenis Kendaraan','Model','Warna Kendaraan','Jam Masuk','Jam Keluar','Hari/Tanggal','Keterangan'];
const LOG_EVENTID_COL=11;
const LOG_EVENTID_HEADER='Event ID (Sync)';

// ---- Enterprise extension: entity types, sheets, headers ----
const ENTITY_TYPES=['VEHICLE','VISITOR','CONTRACTOR','VENDOR','EMPLOYEE','EMERGENCY VEHICLE','DELIVERY','TEMPORARY VEHICLE','VIP'];
const AUTH_HEADERS=['AuthID','PersonName','Type','Company','Plate','Purpose','Host','GateAllowed','ValidFromDate','ValidUntilDate','TimeFrom','TimeUntil','Status','CreatedAt'];
const GATE_HEADERS=['GateID','GateName','Active'];
const EVENT_HEADERS=['EventID','ServerTimestamp','LocalTimestamp','PersonName','Type','Company','Plate','Purpose','Host','GateID','GateName','Direction','Device','Result','Reason','AuthID','SyncStatus'];
const ALERT_HEADERS=['AlertID','Type','Severity','Timestamp','Person','Plate','RelatedEvent','Status'];
const DEFAULT_GATES=[['GATE01','GATE 01'],['GATE02','GATE 02'],['LOADINGBAY','LOADING BAY'],['EMERGENCYGATE','EMERGENCY GATE'],['STAFFGATE','STAFF GATE']];
const DENY_REASONS={
  EXPIRED:'EXPIRED AUTHORIZATION',
  NOT_REGISTERED:'VEHICLE NOT REGISTERED',
  NOT_AUTHORIZED:'PERSON NOT AUTHORIZED',
  OUTSIDE_SCHEDULE:'OUTSIDE AUTHORIZED SCHEDULE',
  DUPLICATE_IN:'DUPLICATE IN',
  NO_ACTIVE_IN:'NO ACTIVE IN',
  BLOCKED:'AUTHORIZATION BLOCKED',
  GATE_NOT_AUTHORIZED:'GATE NOT AUTHORIZED FOR THIS PASS'
};

function db_(){return SpreadsheetApp.openById(CONFIG.SPREADSHEET_ID)}
function norm_(v){return String(v??'').toUpperCase().replace(/[^A-Z0-9]/g,'')}
function now_(){const d=new Date();return{timestamp:Utilities.formatDate(d,CONFIG.TIMEZONE,'yyyy-MM-dd HH:mm:ss'),date:Utilities.formatDate(d,CONFIG.TIMEZONE,'dd/MM/yyyy'),time:Utilities.formatDate(d,CONFIG.TIMEZONE,'HH:mm:ss'),year:Number(Utilities.formatDate(d,CONFIG.TIMEZONE,'yyyy'))}}
function hariTanggal_(v){
  const s=String(v??'').trim();
  const m=s.match(/(\d{1,2})\/(\d{1,2})\/(\d{4})$/);
  if(!m)return s;
  const d=Number(m[1]),mo=Number(m[2]),y=Number(m[3]);
  const dt=new Date(Date.UTC(y,mo-1,d));
  const hari=['Minggu','Senin','Selasa','Rabu','Kamis','Jumat','Sabtu'][dt.getUTCDay()];
  return hari+','+String(d).padStart(2,'0')+'/'+String(mo).padStart(2,'0')+'/'+y;
}
function dateKey_(v){
  const s=String(v??'').trim();
  const m=s.match(/(\d{1,2})\/(\d{1,2})\/(\d{4})$/);
  return m?String(m[1]).padStart(2,'0')+'/'+String(m[2]).padStart(2,'0')+'/'+m[3]:s;
}
function normalizeHariTanggal_(){
  // PERF FIX: previously re-scanned the ENTIRE date column on every single API call
  // (doGet->ensureDatabase_ runs this every request), which becomes very slow as
  // ACCESS_LOG grows. Now only the rows appended since the last normalization run.
  const sh=db_().getSheetByName('ACCESS_LOG'),n=sh.getLastRow();
  if(n<2)return;
  const props=PropertiesService.getScriptProperties();
  const lastNorm=Number(props.getProperty('VACS_NORM_ROW')||1);
  if(n<=lastNorm)return;
  const from=Math.max(2,lastNorm+1),count=n-from+1;
  const rg=sh.getRange(from,9,count,1),vals=rg.getValues();let changed=false;
  vals.forEach(r=>{const f=hariTanggal_(r[0]);if(f&&String(r[0]??'')!==f){r[0]=f;changed=true}});
  if(changed)rg.setValues(vals);
  props.setProperty('VACS_NORM_ROW',String(n));
}


const KNOWN_SHEETS=['VEHICLES','ACCESS_LOG','AUTHORIZATIONS','GATES','ACCESS_EVENTS','ALERTS'];
function ensureSheet_(ss,name,headers){
 let sh=ss.getSheetByName(name);
 const created=!sh;
 if(created)sh=ss.insertSheet(name);
 const current=sh.getRange(1,1,1,headers.length).getValues()[0];
 let missing=false; for(let i=0;i<headers.length;i++) if(String(current[i]||'')!==String(headers[i])){missing=true;break}
 if(created || missing) sh.getRange(1,1,1,headers.length).setValues([headers]);
 if(created) sh.setFrozenRows(1);
 return sh;
}
function ensureDatabase_(){
 const ss=db_();
 const v=ensureSheet_(ss,'VEHICLES',VEHICLE_HEADERS);
 const l=ensureSheet_(ss,'ACCESS_LOG',LOG_HEADERS);
 // Column K appended for idempotent offline sync only; existing 10-column readers are unaffected.
 l.getRange(1,LOG_EVENTID_COL,1,1).setValue(LOG_EVENTID_HEADER);
 // Enterprise extension sheets — created only if missing, never overwrite existing rows.
 ensureSheet_(ss,'AUTHORIZATIONS',AUTH_HEADERS);
 const gates=ensureSheet_(ss,'GATES',GATE_HEADERS);
 ensureSheet_(ss,'ACCESS_EVENTS',EVENT_HEADERS);
 ensureSheet_(ss,'ALERTS',ALERT_HEADERS);
 if(gates.getLastRow()<2){
  DEFAULT_GATES.forEach(g=>gates.getRange(gates.getLastRow()+1,1,1,3).setValues([[g[0],g[1],true]]));
 }
 // Only remove sheets that are neither part of the known enterprise schema nor user-created extras.
 // We never auto-delete unknown sheets anymore (legacy behavior deleted ANY extra sheet, which is
 // unsafe once we introduce new sheets / users add their own tabs). Cleanup is manual via Sheets UI.
 normalizeHariTanggal_();
 return ss
}
function doGet(e){try{ensureDatabase_();const p=(e&&e.parameter)||{};return response_(p.callback,{ok:true,data:route_(String(p.action||'health'),p)})}catch(err){const p=(e&&e.parameter)||{};return response_(p.callback,{ok:false,message:String(err&&err.message||err)})}}
function response_(cb,obj){const j=JSON.stringify(obj);if(cb){const s=String(cb).replace(/[^\w.$]/g,'');return ContentService.createTextOutput(s+'('+j+');').setMimeType(ContentService.MimeType.JAVASCRIPT)}return ContentService.createTextOutput(j).setMimeType(ContentService.MimeType.JSON)}

function vehiclesFresh_(){const sh=db_().getSheetByName('VEHICLES'),n=sh.getLastRow();if(n<2)return[];return sh.getRange(2,1,n-1,Math.max(6,Math.min(VEHICLE_HEADERS.length,sh.getLastColumn()))).getValues().map((r,i)=>({row:i+2,name:String(r[0]??'').trim(),plate:String(r[1]??'').trim(),division:String(r[2]??'').trim(),type:String(r[3]??'').trim(),model:String(r[4]??'').trim(),color:String(r[5]??'').trim(),accessType:typeNorm_(r[6]||((ENTITY_TYPES.includes(String(r[3]||'').trim().toUpperCase()))?r[3]:'VISITOR'))}))}
function vehicles_(){const c=CacheService.getScriptCache(),k='vacs_vehicles_v1';try{const hit=c.get(k);if(hit)return JSON.parse(hit)}catch(e){}const data=vehiclesFresh_();try{c.put(k,JSON.stringify(data),25)}catch(e){}return data}
function clearVehiclesCache_(){try{CacheService.getScriptCache().remove('vacs_vehicles_v1')}catch(e){}}
function logs_(){const sh=db_().getSheetByName('ACCESS_LOG'),n=sh.getLastRow();if(n<2)return[];const tz=CONFIG.TIMEZONE;return sh.getRange(2,1,n-1,10).getValues().map((r,i)=>{const fmt=(v,pattern)=>v instanceof Date?Utilities.formatDate(v,tz,pattern):String(v??'');return{row:i+2,name:String(r[0]??''),plate:String(r[1]??''),division:String(r[2]??''),type:String(r[3]??''),model:String(r[4]??''),color:String(r[5]??''),inTime:fmt(r[6],'HH:mm:ss'),outTime:fmt(r[7],'HH:mm:ss'),date:dateKey_(r[8]),notes:String(r[9]??'')}})}

function audit_(action,plate,name,result,detail,device){
 console.log(JSON.stringify({timestamp:now_().timestamp,createdBy:CONFIG.CREATED_BY,action,plate,name,result,device,detail}));
}

function registerVehicle_(p){
 const row=[String(p.name||'').trim(),String(p.plate||'').trim(),String(p.division||'').trim(),String(p.vehicleType||p.type||'').trim(),String(p.model||'').trim(),String(p.color||'').trim(),typeNorm_(p.accessType||'VISITOR')];
 if(!row[0]||!row[1])throw Error('Nama dan Nomor Kendaraan wajib diisi.');
 const sh=db_().getSheetByName('VEHICLES'),key=norm_(row[1]),data=vehicles_(),old=data.find(v=>norm_(v.plate)===key);
 if(old){sh.getRange(old.row,1,1,7).setValues([row]);clearVehiclesCache_();audit_('UPDATE VEHICLE',row[1],row[0],'SUCCESS','Master diperbarui');return{mode:'updated',vehicle:row,message:'Kendaraan sudah terdaftar. Data diperbarui.'}}
 sh.getRange(sh.getLastRow()+1,1,1,7).setValues([row]);clearVehiclesCache_();audit_('REGISTER VEHICLE',row[1],row[0],'SUCCESS','Kendaraan baru');return{mode:'created',vehicle:row,message:'Kendaraan berhasil didaftarkan.'}
}
function searchVehicle_(q){const n=norm_(q);return{found:n?vehicles_().filter(v=>norm_(v.plate).includes(n)||norm_(v.name).includes(n)).slice(0,50):[]}}

function genId_(prefix){return (prefix||'EVT')+'-'+Utilities.getUuid().replace(/-/g,'').slice(0,12).toUpperCase()}
function eventIdExistsInLog_(eventId){
 if(!eventId)return false;
 const sh=db_().getSheetByName('ACCESS_LOG'),n=sh.getLastRow();if(n<2)return false;
 const vals=sh.getRange(2,LOG_EVENTID_COL,n-1,1).getValues();
 return vals.some(r=>String(r[0]||'')===String(eventId));
}
function eventIdExistsInEvents_(eventId){
 if(!eventId)return false;
 const sh=db_().getSheetByName('ACCESS_EVENTS'),n=sh.getLastRow();if(n<2)return false;
 const vals=sh.getRange(2,1,n-1,1).getValues();
 return vals.some(r=>String(r[0]||'')===String(eventId));
}
function gateInfo_(p){
 const list=gates_(),id=String(p.gateId||p.gate||'').trim();
 if(!id)return{gateId:'GATE01',gateName:'GATE 01'};
 const found=list.find(g=>norm_(g.id)===norm_(id)||norm_(g.name)===norm_(id));
 return found?{gateId:found.id,gateName:found.name}:{gateId:norm_(id)||'GATE01',gateName:id||'GATE 01'};
}
function logAccessEvent_(evt){
 const sh=db_().getSheetByName('ACCESS_EVENTS'),n=now_();
 const eventId=evt.eventId||genId_('EVT');
 sh.getRange(sh.getLastRow()+1,1,1,EVENT_HEADERS.length).setValues([[
  eventId,n.timestamp,evt.localTimestamp||n.timestamp,evt.personName||'',evt.type||'',evt.company||'',
  evt.plate||'',evt.purpose||'',evt.host||'',evt.gateId||'',evt.gateName||'',evt.direction||'',
  evt.device||'',evt.result||'',evt.reason||'',evt.authId||'',evt.syncStatus||'SYNCED'
 ]]);
 scanAlerts_(evt);
 return eventId;
}

function access_(p){
 const plate=String(p.plate||'').trim(),act=String(p.activity||'').toUpperCase(),device=String(p.device||'Unknown Device');
 const gi=gateInfo_(p),eventId=p.eventId?String(p.eventId):undefined;
 if(eventId&&eventIdExistsInLog_(eventId)){
  audit_('SYNC DUPLICATE',plate,'','SKIPPED','Event ID sudah pernah diproses',device);
  return{duplicate:true,eventId,message:'Event sudah tersinkron sebelumnya (idempotent).',createdBy:CONFIG.CREATED_BY};
 }
 if(!plate)throw Error('Nomor kendaraan kosong.');if(!['IN','OUT'].includes(act))throw Error('Aktivitas tidak valid.');
 const v=vehicles_().find(x=>norm_(x.plate)===norm_(plate));
 if(!v){
  audit_(act,plate,'','DENIED','Kendaraan tidak terdaftar',device);
  logAccessEvent_({eventId,personName:'',type:'VEHICLE',plate,direction:act,device,gateId:gi.gateId,gateName:gi.gateName,result:'DENIED',reason:DENY_REASONS.NOT_REGISTERED,localTimestamp:p.localTimestamp});
  throw Error('KENDARAAN TIDAK TERDAFTAR — AKSES DITOLAK.')
 }
 const lock=LockService.getScriptLock();lock.waitLock(15000);
 try{
  const n=now_(),sh=db_().getSheetByName('ACCESS_LOG'),logs=logs_();let open=null;
  for(let i=logs.length-1;i>=0;i--){const r=logs[i];if(norm_(r.plate)===norm_(v.plate)&&r.date===n.date&&r.inTime&&!r.outTime){open=r;break}}
  if(act==='IN'&&open){
   audit_('IN',plate,v.name,'DENIED','Masih INSIDE',device);
   logAccessEvent_({eventId,personName:v.name,type:'VEHICLE',plate:v.plate,direction:'IN',device,gateId:gi.gateId,gateName:gi.gateName,result:'DENIED',reason:DENY_REASONS.DUPLICATE_IN,localTimestamp:p.localTimestamp});
   throw Error('KENDARAAN MASIH DI DALAM. OUT terlebih dahulu.')
  }
  if(act==='OUT'&&!open){
   audit_('OUT',plate,v.name,'DENIED','Tidak ada IN aktif',device);
   logAccessEvent_({eventId,personName:v.name,type:'VEHICLE',plate:v.plate,direction:'OUT',device,gateId:gi.gateId,gateName:gi.gateName,result:'DENIED',reason:DENY_REASONS.NO_ACTIVE_IN,localTimestamp:p.localTimestamp});
   throw Error('TIDAK ADA IN AKTIF. OUT tidak dapat diproses.')
  }
  let logRow;
  if(act==='IN'){
   logRow=sh.getLastRow()+1;
   sh.getRange(logRow,1,1,10).setValues([[v.name,v.plate,v.division,v.type,v.model,v.color,n.time,'',hariTanggal_(n.date),String(p.notes||'')]]);
  }else{
   logRow=open.row;
   sh.getRange(open.row,8).setValue(n.time);if(String(p.notes||'').trim())sh.getRange(open.row,10).setValue(String(p.notes))
  }
  if(eventId)sh.getRange(logRow,LOG_EVENTID_COL,1,1).setValue(eventId);
  audit_('VEHICLE '+act,plate,v.name,'SUCCESS',`${act} ${n.time}`,device);mergeNames_();
  logAccessEvent_({eventId,personName:v.name,type:'VEHICLE',plate:v.plate,direction:act,device,gateId:gi.gateId,gateName:gi.gateName,result:'AUTHORIZED',reason:'',localTimestamp:p.localTimestamp});
  return{vehicle:v,activity:act,timestamp:n.timestamp,serverTime:n.time,gate:gi,createdBy:CONFIG.CREATED_BY}
 }finally{lock.releaseLock()}
}

function mergeNames_(){
 const sh=db_().getSheetByName('ACCESS_LOG'),last=sh.getLastRow();if(last<2)return;
 sh.getRange(2,1,last-1,1).breakApart();const rows=sh.getRange(2,1,last-1,10).getValues();let start=2;
 while(start<=last){const f=rows[start-2],name=String(f[0]||''),date=String(f[8]||'');let end=start+1;
  while(end<=last){const r=rows[end-2];if(String(r[0]||'')!==name||String(r[8]||'')!==date)break;end++}
  const span=end-start;sh.getRange(start,1,span,1).setVerticalAlignment('middle').setHorizontalAlignment('center');if(span>1)sh.getRange(start,1,span,1).mergeVertically();start=end
 }
}

function currentlyInside_(){const latest={};logs_().forEach(r=>{const k=norm_(r.plate);if(k)latest[k]=r});return Object.values(latest).filter(r=>r.inTime&&!r.outTime)}
function isoDateToLog_(iso){const a=String(iso||'').split('-');return a.length===3?a[2]+'/'+a[1]+'/'+a[0]:''}
function typeNorm_(v){const t=String(v||'').trim().toUpperCase();return ENTITY_TYPES.includes(t)?t:(t||'VEHICLE')}
function eventRows_(){const sh=db_().getSheetByName('ACCESS_EVENTS'),n=sh.getLastRow();if(n<2)return[];return sh.getRange(2,1,n-1,EVENT_HEADERS.length).getValues().map(r=>({eventId:String(r[0]||''),serverTimestamp:String(r[1]||''),localTimestamp:String(r[2]||''),personName:String(r[3]||''),type:typeNorm_(r[4]),company:String(r[5]||''),plate:String(r[6]||''),purpose:String(r[7]||''),host:String(r[8]||''),gateId:String(r[9]||''),gateName:String(r[10]||''),direction:String(r[11]||''),device:String(r[12]||''),result:String(r[13]||''),reason:String(r[14]||''),authId:String(r[15]||''),syncStatus:String(r[16]||'')}))}
function eventDate_(ts){const m=String(ts||'').match(/^(\d{4})-(\d{2})-(\d{2})/);return m?m[3]+'/'+m[2]+'/'+m[1]:''}
function report_(p){
 const date=String(p.date||'').trim()||(p.year&&p.month&&p.day?String(p.year)+'-'+String(p.month).padStart(2,'0')+'-'+String(p.day).padStart(2,'0'):'');
 if(!date)throw Error('Tanggal report wajib diisi.');
 const target=isoDateToLog_(date),filter=String(p.type||'ALL').trim().toUpperCase()||'ALL';
 if(filter!=='ALL'&&!ENTITY_TYPES.includes(filter))throw Error('Type tidak dikenal: '+filter);
 const ev=eventRows_().filter(e=>e.result==='AUTHORIZED'),masters=vehicles_(),masterByPlate={};masters.forEach(v=>masterByPlate[norm_(v.plate)]=v);
 const opening={};ev.forEach(e=>{const d=eventDate_(e.serverTimestamp);if(d&&String(e.serverTimestamp).slice(0,10)<String(date)){const k=norm_(e.plate);if(e.direction==='IN')opening[k]=e;else if(e.direction==='OUT')delete opening[k]}});
 const dayEv=ev.filter(e=>eventDate_(e.serverTimestamp)===target),inEv=dayEv.filter(e=>e.direction==='IN'),outEv=dayEv.filter(e=>e.direction==='OUT');
 const insideAtEnd={...opening};inEv.forEach(e=>insideAtEnd[norm_(e.plate)]=e);outEv.forEach(e=>delete insideAtEnd[norm_(e.plate)]);
 const typeOf=e=>typeNorm_(e.type||masterByPlate[norm_(e.plate)]?.accessType),match=e=>filter==='ALL'||typeOf(e)===filter;
 const openingRows=Object.values(opening).filter(match),inRows=inEv.filter(match),outRows=outEv.filter(match),closingRows=Object.values(insideAtEnd).filter(match),rows=[],seenRows={};
 const addRow=(e,isCarry)=>{const k=norm_(e.plate);if(seenRows[k])return;seenRows[k]=true;const v=masterByPlate[k]||{},out=outEv.find(x=>norm_(x.plate)===k);rows.push({name:e.personName||v.name||'',plate:e.plate,division:v.division||'',type:typeOf(e),model:v.model||'',color:v.color||'',inTime:String(e.serverTimestamp).slice(11,19),outTime:out?String(out.serverTimestamp).slice(11,19):'',inDate:eventDate_(e.serverTimestamp),outDate:out?eventDate_(out.serverTimestamp):'',date:target,notes:e.purpose||'',company:e.company||'',host:e.host||'',gateName:e.gateName||'',eventId:e.eventId||'',status:out?'OUT':(isCarry?'CARRYOVER / INSIDE':'INSIDE'),direction:'IN',carryover:!!isCarry});};
 openingRows.forEach(e=>addRow(e,true));inRows.forEach(e=>addRow(e,false));
 const legacy=logs_().filter(r=>r.date===target).filter(r=>!ev.some(e=>eventDate_(e.serverTimestamp)===target&&norm_(e.plate)===norm_(r.plate))).filter(r=>filter==='ALL'||typeNorm_(r.type)===filter);legacy.forEach(r=>rows.push({...r,type:typeNorm_(r.type),status:r.outTime?'OUT':'INSIDE',direction:'IN',inDate:r.date,outDate:r.outTime?r.date:''}));
 const countByType={};ENTITY_TYPES.filter(x=>x!=='VEHICLE').forEach(t=>countByType[t]={opening:0,in:0,out:0,inside:0});const add=(obj,key)=>{const t=typeOf(obj);if(countByType[t])countByType[t][key]++};openingRows.forEach(e=>add(e,'opening'));inRows.forEach(e=>add(e,'in'));outRows.forEach(e=>add(e,'out'));closingRows.forEach(e=>add(e,'inside'));
 const mobileCount=a=>a.filter(e=>{const v=masterByPlate[norm_(e.plate)]||{};return /motor|sepeda|roda ?dua|scooter|beat|vario|nmax|aerox|scoopy|vespa/i.test(String(v.type||'')+' '+String(v.model||''))}).length;
 return{createdBy:CONFIG.CREATED_BY,reportDate:date,reportLogDate:target,filterType:filter,rows,summary:{openingInside:openingRows.length,newIn:inRows.length,out:outRows.length,inside:closingRows.length,totalIn:inRows.length,totalOut:outRows.length,totalInside:closingRows.length,cars:inRows.length-mobileCount(inRows),motorcycles:mobileCount(inRows),categories:countByType}};
}

/* P1 UI-visible audit history is generated from ACCESS_LOG state changes.
   No third spreadsheet sheet is created. */
function auditEvents_(p){
 const rows=logs_(),q=String(p.q||'').toUpperCase().trim();
 const events=[];
 rows.forEach(r=>{
  if(r.inTime)events.push({timestamp:r.date+' '+r.inTime,createdBy:CONFIG.CREATED_BY,action:'VEHICLE IN',plate:r.plate,name:r.name,result:'SUCCESS',detail:'IN recorded'});
  if(r.outTime)events.push({timestamp:r.date+' '+r.outTime,createdBy:CONFIG.CREATED_BY,action:'VEHICLE OUT',plate:r.plate,name:r.name,result:'SUCCESS',detail:'OUT recorded'});
 });
 return{createdBy:CONFIG.CREATED_BY,events:events.filter(x=>!q||[x.plate,x.name,x.action].join(' ').toUpperCase().includes(q)).reverse().slice(0,500)}
}

function backup_(){
 const ss=db_(),stamp=Utilities.formatDate(new Date(),CONFIG.TIMEZONE,'yyyyMMdd_HHmmss');
 const file=DriveApp.getFileById(ss.getId()).makeCopy(`VACS_BACKUP_${stamp}_CREATED_BY_Mbah_Pri`);
 return{success:true,name:file.getName(),fileId:file.getId(),timestamp:now_().timestamp,createdBy:CONFIG.CREATED_BY}
}

function adminPin_(){return PropertiesService.getScriptProperties().getProperty('VACS_ADMIN_PIN')||'2580'}
function requireAdmin_(pin){if(String(pin||'')!==String(adminPin_()))throw Error('PIN ADMIN SALAH.');}
function deleteVehicle_(p){
 requireAdmin_(p.pin);
 const plate=String(p.plate||'').trim();
 if(!plate)throw Error('Nomor Kendaraan kosong.');
 const sh=db_().getSheetByName('VEHICLES'), v=vehicles_().find(x=>norm_(x.plate)===norm_(plate));
 if(!v)throw Error('Kendaraan tidak ditemukan di MASTER.');
 sh.deleteRow(v.row);
 clearVehiclesCache_();
 audit_('DELETE VEHICLE',v.plate,v.name,'SUCCESS','Master vehicle dihapus; ACCESS_LOG dipertahankan.');
 return{success:true,plate:v.plate,name:v.name,message:'Kendaraan dihapus dari MASTER. Riwayat ACCESS_LOG tetap dipertahankan.',createdBy:CONFIG.CREATED_BY}
}
function deleteAccessLog_(p){
 requireAdmin_(p.pin);
 const row=Number(p.row||0);
 const sh=db_().getSheetByName('ACCESS_LOG');
 if(!row||row<2||row>sh.getLastRow())throw Error('Baris ACCESS_LOG tidak valid.');
 const r=sh.getRange(row,1,1,10).getValues()[0];
 audit_('DELETE ACCESS LOG',String(r[1]||''),String(r[0]||''),'SUCCESS','Transaksi dihapus oleh admin setelah validasi.');
 sh.deleteRow(row);
 mergeNames_();
 return{success:true,message:'Transaksi dihapus dan tercatat pada audit server.',createdBy:CONFIG.CREATED_BY}
}
function setAdminPin_(p){
 requireAdmin_(p.currentPin);
 const next=String(p.newPin||'').trim();
 if(!/^\d{4,8}$/.test(next))throw Error('PIN baru harus 4–8 digit.');
 PropertiesService.getScriptProperties().setProperty('VACS_ADMIN_PIN',next);
 return{success:true,message:'PIN ADMIN berhasil diubah.'}
}
function importVehicles_(p){
 const a=JSON.parse(String(p.rows||'')).map(x=>[String(x.name||'').trim(),String(x.plate||'').trim(),String(x.division||'').trim(),String(x.vehicleType||x.type||'').trim(),String(x.model||'').trim(),String(x.color||'').trim(),typeNorm_(x.accessType||'VISITOR')]).filter(r=>r[1]);
 if(!a.length)throw Error('Nomor Kendaraan tidak ditemukan.');
 const sh=db_().getSheetByName('VEHICLES'),map={};vehicles_().forEach(v=>map[norm_(v.plate)]=v.row);let created=0,updated=0;
 a.forEach(r=>{const k=norm_(r[1]);if(map[k]){sh.getRange(map[k],1,1,7).setValues([r]);updated++}else{sh.getRange(sh.getLastRow()+1,1,1,7).setValues([r]);map[k]=sh.getLastRow();created++}});
 clearVehiclesCache_();
 return{created,updated,total:a.length,createdBy:CONFIG.CREATED_BY}
}

// ---- GATES ----
function gatesFresh_(){const sh=db_().getSheetByName('GATES'),n=sh.getLastRow();if(n<2)return[];return sh.getRange(2,1,n-1,3).getValues().map((r,i)=>({row:i+2,id:String(r[0]||'').trim(),name:String(r[1]||'').trim(),active:r[2]!==false&&r[2]!=='FALSE'}))}
function gates_(){const c=CacheService.getScriptCache(),k='vacs_gates_v1';try{const hit=c.get(k);if(hit)return JSON.parse(hit)}catch(e){}const data=gatesFresh_();try{c.put(k,JSON.stringify(data),60)}catch(e){}return data}
function clearGatesCache_(){try{CacheService.getScriptCache().remove('vacs_gates_v1')}catch(e){}}
function addGate_(p){
 requireAdmin_(p.pin);
 const name=String(p.name||'').trim();if(!name)throw Error('Nama gate wajib diisi.');
 const id=String(p.id||name).toUpperCase().replace(/[^A-Z0-9]/g,'')||genId_('GATE');
 const sh=db_().getSheetByName('GATES');
 if(gates_().some(g=>norm_(g.id)===norm_(id)))throw Error('Gate ID sudah ada.');
 sh.getRange(sh.getLastRow()+1,1,1,3).setValues([[id,name,true]]);
 clearGatesCache_();
 audit_('ADD GATE',id,name,'SUCCESS','Gate baru ditambahkan');
 return{id,name,createdBy:CONFIG.CREATED_BY}
}

// ---- AUTHORIZATIONS (Visitor/Contractor/Vendor/etc.) ----
function authorizations_(){
 const sh=db_().getSheetByName('AUTHORIZATIONS'),n=sh.getLastRow();if(n<2)return[];
 return sh.getRange(2,1,n-1,AUTH_HEADERS.length).getValues().map((r,i)=>({
  row:i+2,authId:String(r[0]||''),personName:String(r[1]||''),type:String(r[2]||''),company:String(r[3]||''),
  plate:String(r[4]||''),purpose:String(r[5]||''),host:String(r[6]||''),gateAllowed:String(r[7]||'ALL'),
  validFromDate:String(r[8]||''),validUntilDate:String(r[9]||''),timeFrom:String(r[10]||''),timeUntil:String(r[11]||''),
  status:String(r[12]||'ACTIVE'),createdAt:String(r[13]||'')
 }))
}
function createAuthorization_(p){
 const personName=String(p.personName||'').trim(),type=String(p.type||'VISITOR').toUpperCase();
 if(!personName)throw Error('Nama person wajib diisi.');
 if(!ENTITY_TYPES.includes(type))throw Error('Type tidak dikenal: '+type);
 const authId=genId_('AUTH'),n=now_();
 const row=[authId,personName,type,String(p.company||'').trim(),String(p.plate||'').trim().toUpperCase(),
  String(p.purpose||'').trim(),String(p.host||'').trim(),String(p.gateAllowed||'ALL').trim()||'ALL',
  String(p.validFromDate||n.date).trim(),String(p.validUntilDate||p.validFromDate||n.date).trim(),
  String(p.timeFrom||'00:00').trim(),String(p.timeUntil||'23:59').trim(),'ACTIVE',n.timestamp];
 db_().getSheetByName('AUTHORIZATIONS').getRange(db_().getSheetByName('AUTHORIZATIONS').getLastRow()+1,1,1,row.length).setValues([row]);
 audit_('CREATE AUTHORIZATION',row[4],personName,'SUCCESS','Type='+type+' Host='+row[6]);
 return{authId,personName,type,message:'Authorization berhasil dibuat.',createdBy:CONFIG.CREATED_BY}
}
function updateAuthorizationStatus_(p){
 requireAdmin_(p.pin);
 const authId=String(p.authId||'').trim(),status=String(p.status||'').toUpperCase();
 if(!['ACTIVE','BLOCKED','EXPIRED'].includes(status))throw Error('Status tidak valid.');
 const a=authorizations_().find(x=>x.authId===authId);if(!a)throw Error('Authorization tidak ditemukan.');
 db_().getSheetByName('AUTHORIZATIONS').getRange(a.row,13,1,1).setValue(status);
 audit_('UPDATE AUTHORIZATION',a.plate,a.personName,'SUCCESS','Status -> '+status);
 return{success:true,authId,status}
}
function searchAuthorizations_(q){
 const n=norm_(q);
 return{found:n?authorizations_().filter(a=>norm_(a.plate).includes(n)||norm_(a.personName).includes(n)||norm_(a.company).includes(n)||norm_(a.authId).includes(n)).slice(0,50):authorizations_().slice(-50).reverse()}
}
// Compute effective status against current date/time window.
function evaluateAuthorization_(a,n){
 if(a.status==='BLOCKED')return{ok:false,reason:DENY_REASONS.BLOCKED};
 const parseDate=s=>{const m=String(s||'').match(/(\d{4})-(\d{2})-(\d{2})|(\d{1,2})\/(\d{1,2})\/(\d{4})/);if(!m)return null;
  if(m[1])return new Date(Number(m[1]),Number(m[2])-1,Number(m[3]));
  return new Date(Number(m[6]),Number(m[5])-1,Number(m[4]))};
 const today=new Date(Utilities.formatDate(new Date(),CONFIG.TIMEZONE,'yyyy-MM-dd'));
 const from=parseDate(a.validFromDate),until=parseDate(a.validUntilDate);
 if(from&&today<from)return{ok:false,reason:DENY_REASONS.EXPIRED};
 if(until&&today>until)return{ok:false,reason:DENY_REASONS.EXPIRED};
 const toMin=s=>{const m=String(s||'').match(/(\d{1,2}):(\d{2})/);return m?Number(m[1])*60+Number(m[2]):null};
 const nowMin=toMin(n.time),fromMin=toMin(a.timeFrom),untilMin=toMin(a.timeUntil);
 if(nowMin!=null&&fromMin!=null&&untilMin!=null){
  const inWindow=fromMin<=untilMin?(nowMin>=fromMin&&nowMin<=untilMin):(nowMin>=fromMin||nowMin<=untilMin);
  if(!inWindow)return{ok:false,reason:DENY_REASONS.OUTSIDE_SCHEDULE};
 }
 return{ok:true}
}
function findAuthorizationFor_(p){
 const list=authorizations_();
 if(p.authId)return list.find(a=>a.authId===String(p.authId));
 const plate=norm_(p.plate||''),person=norm_(p.personName||'');
 let candidates=list.filter(a=>(plate&&norm_(a.plate)===plate)||(person&&norm_(a.personName)===person));
 candidates=candidates.filter(a=>a.status!=='BLOCKED');
 candidates.sort((x,y)=>String(y.createdAt).localeCompare(String(x.createdAt)));
 return candidates[0];
}
// Anti-duplicate IN/OUT for non-legacy entity access, mirrors legacy vehicle logic.
function findOpenAuthEvent_(personName,plate){
 const sh=db_().getSheetByName('ACCESS_EVENTS'),n=sh.getLastRow();if(n<2)return null;
 const rows=sh.getRange(2,1,n-1,EVENT_HEADERS.length).getValues();
 const today=now_().date.slice(0,10);
 for(let i=rows.length-1;i>=0;i--){
  const r=rows[i];
  const evPerson=String(r[3]||''),evPlate=String(r[6]||''),evDir=String(r[11]||''),evResult=String(r[13]||''),evTs=String(r[1]||'');
  if(evResult!=='AUTHORIZED')continue;
  if(!evTs.startsWith(now_().timestamp.slice(0,10)))continue;
  if((personName&&norm_(evPerson)===norm_(personName))||(plate&&evPlate&&norm_(evPlate)===norm_(plate))){
   if(evDir==='IN')return{row:i+2,dir:'IN'};
   if(evDir==='OUT')return null;
  }
 }
 return null;
}
function accessAuth_(p){
 const personName=String(p.personName||'').trim(),plate=String(p.plate||'').trim(),act=String(p.activity||'').toUpperCase();
 const device=String(p.device||'Unknown Device'),gi=gateInfo_(p),eventId=p.eventId?String(p.eventId):undefined;
 if(eventId&&eventIdExistsInEvents_(eventId))return{duplicate:true,eventId,message:'Event sudah tersinkron sebelumnya (idempotent).',createdBy:CONFIG.CREATED_BY};
 if(!['IN','OUT'].includes(act))throw Error('Aktivitas tidak valid.');
 const lock=LockService.getScriptLock();lock.waitLock(15000);
 try{
  const n=now_();
  const auth=findAuthorizationFor_(p);
  const common={eventId,personName,type:p.type||(auth?auth.type:'VISITOR'),company:p.company||(auth?auth.company:''),
   plate,purpose:p.purpose||(auth?auth.purpose:''),host:p.host||(auth?auth.host:''),device,
   gateId:gi.gateId,gateName:gi.gateName,authId:auth?auth.authId:'',localTimestamp:p.localTimestamp};
  if(!auth){
   logAccessEvent_({...common,direction:act,result:'DENIED',reason:DENY_REASONS.NOT_AUTHORIZED});
   throw Error('PERSON/VEHICLE TIDAK MEMILIKI AUTHORIZATION — AKSES DITOLAK.');
  }
  const evalr=evaluateAuthorization_(auth,n);
  if(!evalr.ok){
   logAccessEvent_({...common,direction:act,result:'DENIED',reason:evalr.reason});
   throw Error('ACCESS DENIED — REASON: '+evalr.reason);
  }
  if(auth.gateAllowed&&auth.gateAllowed!=='ALL'&&norm_(auth.gateAllowed)!==norm_(gi.gateId)&&norm_(auth.gateAllowed)!==norm_(gi.gateName)){
   logAccessEvent_({...common,direction:act,result:'DENIED',reason:DENY_REASONS.GATE_NOT_AUTHORIZED});
   throw Error('ACCESS DENIED — REASON: '+DENY_REASONS.GATE_NOT_AUTHORIZED);
  }
  const open=findOpenAuthEvent_(personName,plate);
  if(act==='IN'&&open){
   logAccessEvent_({...common,direction:'IN',result:'DENIED',reason:DENY_REASONS.DUPLICATE_IN});
   throw Error('ACCESS DENIED — REASON: '+DENY_REASONS.DUPLICATE_IN);
  }
  if(act==='OUT'&&!open){
   logAccessEvent_({...common,direction:'OUT',result:'DENIED',reason:DENY_REASONS.NO_ACTIVE_IN});
   throw Error('ACCESS DENIED — REASON: '+DENY_REASONS.NO_ACTIVE_IN);
  }
  const usedEventId=logAccessEvent_({...common,direction:act,result:'AUTHORIZED',reason:''});
  audit_('ACCESS '+act,plate,personName,'AUTHORIZED',common.type+' via '+gi.gateName,device);
  return{authorization:auth,activity:act,timestamp:n.timestamp,serverTime:n.time,gate:gi,eventId:usedEventId,createdBy:CONFIG.CREATED_BY}
 }finally{lock.releaseLock()}
}

// ---- EXCEPTIONS / SECURITY EVENTS ----
function exceptions_(p){
 const sh=db_().getSheetByName('ACCESS_EVENTS'),n=sh.getLastRow();if(n<2)return{events:[]};
 const q=String(p.q||'').toUpperCase().trim();
 const rows=sh.getRange(2,1,n-1,EVENT_HEADERS.length).getValues().map(r=>({
  eventId:r[0],timestamp:r[1],personName:r[3],type:r[4],company:r[5],plate:r[6],purpose:r[7],host:r[8],
  gateId:r[9],gateName:r[10],direction:r[11],device:r[12],result:r[13],reason:r[14]
 })).filter(e=>e.result==='DENIED');
 return{events:rows.filter(x=>!q||[x.plate,x.personName,x.reason,x.type].join(' ').toUpperCase().includes(q)).reverse().slice(0,300)}
}

// ---- ALERTS ----
function alertsSheet_(){return db_().getSheetByName('ALERTS')}
function alerts_(p){
 const sh=alertsSheet_(),n=sh.getLastRow();if(n<2)return{alerts:[]};
 const status=String(p&&p.status||'').toUpperCase();
 const rows=sh.getRange(2,1,n-1,ALERT_HEADERS.length).getValues().map((r,i)=>({row:i+2,alertId:r[0],type:r[1],severity:r[2],timestamp:r[3],person:r[4],plate:r[5],relatedEvent:r[6],status:r[7]}));
 return{alerts:rows.filter(a=>!status||a.status===status).reverse().slice(0,200)}
}
function findOpenAlertCooldown_(type,subjectKey){
 const sh=alertsSheet_(),n=sh.getLastRow();if(n<2)return false;
 const rows=sh.getRange(2,1,n-1,ALERT_HEADERS.length).getValues();
 const cutoff=new Date(Date.now()-CONFIG.ALERT_COOLDOWN_MIN*60000);
 return rows.some(r=>String(r[1])===type&&(String(r[4])===subjectKey||String(r[5])===subjectKey)&&String(r[7])==='OPEN'&&new Date(r[3])>cutoff);
}
function createAlert_(type,severity,person,plate,relatedEvent){
 const subjectKey=person||plate;
 if(findOpenAlertCooldown_(type,subjectKey))return; // dedupe/cooldown
 const sh=alertsSheet_(),alertId=genId_('ALERT'),n=now_();
 sh.getRange(sh.getLastRow()+1,1,1,ALERT_HEADERS.length).setValues([[alertId,type,severity,n.timestamp,person||'',plate||'',relatedEvent||'','OPEN']]);
 audit_('ALERT',plate,person,severity,type);
}
function ackAlert_(p){const a=alerts_({}).alerts.find(x=>x.alertId===p.alertId);if(!a)throw Error('Alert tidak ditemukan.');alertsSheet_().getRange(a.row,8,1,1).setValue('ACKNOWLEDGED');return{success:true}}
function resolveAlert_(p){const a=alerts_({}).alerts.find(x=>x.alertId===p.alertId);if(!a)throw Error('Alert tidak ditemukan.');alertsSheet_().getRange(a.row,8,1,1).setValue('RESOLVED');return{success:true}}
// Lightweight, on-write alert scan — runs inline after each access event (cheap: bounded reads), no extra polling/triggers needed.
function scanAlerts_(evt){
 try{
  if(evt.result==='DENIED'){
   const sh=db_().getSheetByName('ACCESS_EVENTS'),n=sh.getLastRow();
   if(n>=2){
    const window=CONFIG.REPEATED_DENIAL_WINDOW_MIN*60000,cutoff=Date.now()-window;
    const rows=sh.getRange(Math.max(2,n-200),1,Math.min(200,n-1),EVENT_HEADERS.length).getValues();
    const subject=evt.personName||evt.plate;
    const count=rows.filter(r=>String(r[13])==='DENIED'&&(String(r[3])===evt.personName||String(r[6])===evt.plate)&&new Date(String(r[1]).replace(' ','T')).getTime()>=cutoff).length;
    if(count>=CONFIG.REPEATED_DENIAL_COUNT)createAlert_('REPEATED_DENIED_ACCESS','HIGH',evt.personName,evt.plate,evt.eventId);
   }
  }
  if(evt.result==='AUTHORIZED'&&evt.direction==='IN'){
   // Long-stay is evaluated lazily via commandCenter_/scanLongStay_ (time-based, not on a single write).
  }
 }catch(err){/* alerting must never block the access transaction */}
}
function scanLongStay_(){
 const thresholdMs=CONFIG.LONG_STAY_HOURS*3600000,nowMs=Date.now();
 currentlyInside_().forEach(r=>{
  const inMs=Date.parse((r.date.split('/').reverse().join('-'))+'T'+r.inTime);
  if(!isNaN(inMs)&&nowMs-inMs>thresholdMs)createAlert_('LONG_STAY','MEDIUM',r.name,r.plate,'');
 });
 const sh=db_().getSheetByName('ACCESS_EVENTS'),n=sh.getLastRow();
 if(n>=2){
  const rows=sh.getRange(2,1,n-1,EVENT_HEADERS.length).getValues();
  const openMap={};
  rows.forEach((r,i)=>{const key=String(r[3])+'|'+String(r[6]);if(String(r[13])==='AUTHORIZED'){if(String(r[11])==='IN')openMap[key]={ts:r[1],person:r[3],plate:r[6]};else if(String(r[11])==='OUT')delete openMap[key]}});
  Object.values(openMap).forEach(o=>{const inMs=Date.parse(String(o.ts).replace(' ','T'));if(!isNaN(inMs)&&nowMs-inMs>thresholdMs)createAlert_('LONG_STAY','MEDIUM',o.person,o.plate,'')});
 }
}

// ---- COMMAND CENTER ----
function commandCenter_(){
 scanLongStay_();
 const insideVehicles=currentlyInside_();
 const sh=db_().getSheetByName('ACCESS_EVENTS'),n=sh.getLastRow();
 const insideByType={VISITOR:0,CONTRACTOR:0,VENDOR:0,EMPLOYEE:0,'EMERGENCY VEHICLE':0,DELIVERY:0,'TEMPORARY VEHICLE':0,VIP:0};
 const gateCounts={};gates_().forEach(g=>gateCounts[g.id]={gateId:g.id,gateName:g.name,active:g.active,todayIn:0,todayOut:0});
 let lastAccess=[];
 if(n>=2){
  const rows=sh.getRange(2,1,n-1,EVENT_HEADERS.length).getValues();
  const openMap={};
  const today=now_().timestamp.slice(0,10);
  rows.forEach(r=>{
   const ts=String(r[1]),type=String(r[4]),plate=String(r[6]),person=String(r[3]),gateId=String(r[9]),dir=String(r[11]),result=String(r[13]);
   if(result==='AUTHORIZED'&&ts.startsWith(today)&&gateCounts[gateId]){if(dir==='IN')gateCounts[gateId].todayIn++;else if(dir==='OUT')gateCounts[gateId].todayOut++}
   if(result==='AUTHORIZED'){const key=person+'|'+plate;if(dir==='IN')openMap[key]={type};else if(dir==='OUT')delete openMap[key]}
  });
  Object.values(openMap).forEach(o=>{if(insideByType[o.type]!=null)insideByType[o.type]++});
  lastAccess=rows.slice(-15).reverse().map(r=>({timestamp:r[1],plate:r[6],person:r[3],type:r[4],direction:r[11],result:r[13],reason:r[14],gateName:r[10]}));
 }
 const legacyLast=logs_().slice(-10).reverse().map(r=>({timestamp:r.date+' '+(r.outTime||r.inTime),plate:r.plate,person:r.name,type:'VEHICLE',direction:r.outTime?'OUT':'IN',result:'AUTHORIZED',reason:'',gateName:'GATE 01'}));
 const merged=[...lastAccess,...legacyLast].sort((a,b)=>String(b.timestamp).localeCompare(String(a.timestamp))).slice(0,15);
 const openAlerts=alerts_({status:'OPEN'}).alerts.length;
 return{
  systemStatus:'ONLINE',
  inside:{total:insideVehicles.length+Object.values(insideByType).reduce((a,b)=>a+b,0),vehicles:insideVehicles.length,...insideByType},
  gates:Object.values(gateCounts),
  lastAccess:merged,
  openAlerts,
  unexpectedVehicles:[], // reserved: populated only if a plate is found INSIDE with no VEHICLES/AUTHORIZATIONS match
  createdBy:CONFIG.CREATED_BY
 }
}

// ---- OFFLINE SYNC ----
function syncQueue_(p){
 const events=JSON.parse(String(p.events||'[]'));
 const results=[];
 events.forEach(e=>{
  try{
   const payload={...(e.payload||{}),eventId:e.eventId,localTimestamp:e.localTimestamp};
   let r;
   if(e.kind==='auth')r=accessAuth_(payload);else r=access_(payload);
   results.push({eventId:e.eventId,status:r&&r.duplicate?'SYNCED':'SYNCED',message:r&&r.duplicate?'ALREADY SYNCED':'OK'});
  }catch(err){
   results.push({eventId:e.eventId,status:'FAILED',message:String(err&&err.message||err)});
  }
 });
 return{results,createdBy:CONFIG.CREATED_BY}
}

function dashboard_(){const v=vehicles_(),l=logs_(),d=now_().date,t=l.filter(x=>x.date===d);return{vehicles:v.length,owners:new Set(v.map(x=>x.name).filter(Boolean)).size,inToday:t.filter(x=>x.inTime).length,outToday:t.filter(x=>x.outTime).length,inside:currentlyInside_().length,createdBy:CONFIG.CREATED_BY}}
function health_(){ensureDatabase_();return{system:'VACS',status:'ONLINE',version:CONFIG.VERSION,createdBy:CONFIG.CREATED_BY,timestamp:now_().timestamp,spreadsheetId:CONFIG.SPREADSHEET_ID,sheets:db_().getSheets().map(s=>s.getName())}}
function route_(a,p){switch(a){case'health':return health_();case'dashboard':return dashboard_();case'search':return searchVehicle_(p.q||'');case'registerVehicle':return registerVehicle_(p);case'access':return access_(p);case'current':return currentlyInside_();case'report':return report_(p);case'audit':return auditEvents_(p);case'backup':return backup_();case'importVehicles':return importVehicles_(p);case'deleteVehicle':return deleteVehicle_(p);case'deleteAccessLog':return deleteAccessLog_(p);case'setAdminPin':return setAdminPin_(p);default:throw Error('Action tidak dikenal: '+a)}}
function setupVACS(){return health_()}
function onEdit(e){try{if(e.range.getSheet().getName()==='ACCESS_LOG')mergeNames_()}catch(err){}}


// ===== VACS V8.1 COMPATIBILITY / ENTERPRISE ROUTES =====
// Appended overrides are intentional: legacy V7.x behavior remains intact while the
// enterprise UI gets the missing endpoints without changing ACCESS_LOG columns A-J.
function eventIdExistsAny_(eventId){
  return !!eventId && (eventIdExistsInLog_(eventId) || eventIdExistsInEvents_(eventId));
}
function findOpenAuthEvent_(personName,plate){
  const sh=db_().getSheetByName('ACCESS_EVENTS'),n=sh.getLastRow();
  if(n<2)return null;
  const rows=sh.getRange(2,1,n-1,EVENT_HEADERS.length).getValues();
  for(let i=rows.length-1;i>=0;i--){
    const r=rows[i],result=String(r[13]||''),dir=String(r[11]||'');
    if(result!=='AUTHORIZED')continue;
    const rp=String(r[3]||''),rv=String(r[6]||'');
    const match=(personName&&norm_(rp)===norm_(personName))||(plate&&norm_(rv)===norm_(plate));
    if(!match)continue;
    if(dir==='IN')return{row:i+2,dir:'IN'};
    if(dir==='OUT')return null;
  }
  return null;
}
function access_(p){
  const plate=String(p.plate||'').trim(),act=String(p.activity||'').toUpperCase();
  const device=String(p.device||p.deviceId||'Unknown Device'),gi=gateInfo_(p),eventId=p.eventId?String(p.eventId):undefined;
  if(eventId&&eventIdExistsAny_(eventId))return{duplicate:true,eventId,message:'Event sudah tersinkron sebelumnya (idempotent).',createdBy:CONFIG.CREATED_BY};
  if(!plate)throw Error('Nomor kendaraan kosong.');
  if(!['IN','OUT'].includes(act))throw Error('Aktivitas tidak valid.');
  const v=vehicles_().find(x=>norm_(x.plate)===norm_(plate));
  if(!v){
    const eid=logAccessEvent_({eventId,personName:'',type:'VEHICLE',plate,direction:act,device,gateId:gi.gateId,gateName:gi.gateName,result:'DENIED',reason:DENY_REASONS.NOT_REGISTERED,localTimestamp:p.localTimestamp,syncStatus:p.syncStatus||'SYNCED'});
    audit_(act,plate,'','DENIED',DENY_REASONS.NOT_REGISTERED,device);
    throw Error('KENDARAAN TIDAK TERDAFTAR — AKSES DITOLAK. EVENT: '+eid);
  }
  const lock=LockService.getScriptLock();
  try{lock.waitLock(8000)}catch(le){throw Error('SERVER SIBUK — coba lagi (gate lain sedang transaksi).')}
  try{
    const n=now_(),sh=db_().getSheetByName('ACCESS_LOG'),logs=logs_();
    let open=null;
    for(let i=logs.length-1;i>=0;i--){const r=logs[i];if(norm_(r.plate)===norm_(v.plate)&&r.inTime&&!r.outTime){open=r;break}}
    if(act==='IN'&&open){
      logAccessEvent_({eventId,personName:v.name,type:'VEHICLE',plate:v.plate,direction:'IN',device,gateId:gi.gateId,gateName:gi.gateName,result:'DENIED',reason:DENY_REASONS.DUPLICATE_IN,localTimestamp:p.localTimestamp});
      throw Error('KENDARAAN MASIH DI DALAM. OUT terlebih dahulu.');
    }
    if(act==='OUT'&&!open){
      logAccessEvent_({eventId,personName:v.name,type:'VEHICLE',plate:v.plate,direction:'OUT',device,gateId:gi.gateId,gateName:gi.gateName,result:'DENIED',reason:DENY_REASONS.NO_ACTIVE_IN,localTimestamp:p.localTimestamp});
      throw Error('TIDAK ADA IN AKTIF. OUT tidak dapat diproses.');
    }
    let logRow;
    if(act==='IN'){
      logRow=sh.getLastRow()+1;
      sh.getRange(logRow,1,1,10).setValues([[v.name,v.plate,v.division,v.type,v.model,v.color,n.time,'',hariTanggal_(n.date),String(p.notes||'')]]);
    }else{
      logRow=open.row;sh.getRange(open.row,8).setValue(n.time);if(String(p.notes||'').trim())sh.getRange(open.row,10).setValue(String(p.notes));
    }
    if(eventId)sh.getRange(logRow,LOG_EVENTID_COL,1,1).setValue(eventId);
    const used=logAccessEvent_({eventId,personName:v.name,type:'VEHICLE',plate:v.plate,direction:act,device,gateId:gi.gateId,gateName:gi.gateName,result:'AUTHORIZED',reason:'',localTimestamp:p.localTimestamp,syncStatus:p.syncStatus||'SYNCED'});
    audit_('VEHICLE '+act,plate,v.name,'SUCCESS',act+' '+n.time+' via '+gi.gateName,device);mergeNames_();
    return{vehicle:v,activity:act,timestamp:n.timestamp,serverTime:n.time,gate:gi,eventId:used,createdBy:CONFIG.CREATED_BY};
  }finally{lock.releaseLock()}
}
function accessAuth_(p){
  const personName=String(p.personName||'').trim(),plate=String(p.plate||'').trim(),act=String(p.activity||'').toUpperCase();
  const device=String(p.device||p.deviceId||'Unknown Device'),gi=gateInfo_(p),eventId=p.eventId?String(p.eventId):undefined;
  if(eventId&&eventIdExistsAny_(eventId))return{duplicate:true,eventId,message:'Event sudah tersinkron sebelumnya (idempotent).',createdBy:CONFIG.CREATED_BY};
  if(!['IN','OUT'].includes(act))throw Error('Aktivitas tidak valid.');
  const lock=LockService.getScriptLock();
  try{lock.waitLock(8000)}catch(le){throw Error('SERVER SIBUK — coba lagi (gate lain sedang transaksi).')}
  try{
    const n=now_(),auth=findAuthorizationFor_(p);
    const common={eventId,personName,type:p.type||(auth?auth.type:'VISITOR'),company:p.company||(auth?auth.company:''),plate,purpose:p.purpose||(auth?auth.purpose:''),host:p.host||(auth?auth.host:''),device,gateId:gi.gateId,gateName:gi.gateName,authId:auth?auth.authId:'',localTimestamp:p.localTimestamp,syncStatus:p.syncStatus||'SYNCED'};
    if(!auth){logAccessEvent_({...common,direction:act,result:'DENIED',reason:DENY_REASONS.NOT_AUTHORIZED});throw Error('PERSON/VEHICLE TIDAK MEMILIKI AUTHORIZATION — AKSES DITOLAK.');}
    const evalr=evaluateAuthorization_(auth,n);
    if(!evalr.ok){logAccessEvent_({...common,direction:act,result:'DENIED',reason:evalr.reason});throw Error('ACCESS DENIED — REASON: '+evalr.reason);}
    if(auth.gateAllowed&&String(auth.gateAllowed).toUpperCase()!=='ALL'){
      const allowed=String(auth.gateAllowed).split(/[,|;]/).map(x=>norm_(x));
      if(!allowed.includes(norm_(gi.gateId))&&!allowed.includes(norm_(gi.gateName))){logAccessEvent_({...common,direction:act,result:'DENIED',reason:DENY_REASONS.GATE_NOT_AUTHORIZED});throw Error('ACCESS DENIED — REASON: '+DENY_REASONS.GATE_NOT_AUTHORIZED);}
    }
    const open=findOpenAuthEvent_(personName,plate);
    if(act==='IN'&&open){logAccessEvent_({...common,direction:'IN',result:'DENIED',reason:DENY_REASONS.DUPLICATE_IN});throw Error('ACCESS DENIED — REASON: '+DENY_REASONS.DUPLICATE_IN);}
    if(act==='OUT'&&!open){logAccessEvent_({...common,direction:'OUT',result:'DENIED',reason:DENY_REASONS.NO_ACTIVE_IN});throw Error('ACCESS DENIED — REASON: '+DENY_REASONS.NO_ACTIVE_IN);}
    const used=logAccessEvent_({...common,direction:act,result:'AUTHORIZED',reason:''});
    audit_('ACCESS '+act,plate,personName,'AUTHORIZED',common.type+' via '+gi.gateName,device);
    return{authorization:auth,activity:act,timestamp:n.timestamp,serverTime:n.time,gate:gi,eventId:used,createdBy:CONFIG.CREATED_BY};
  }finally{lock.releaseLock()}
}
function commandCenter_(){
  scanLongStay_();
  const gates=gates_().map(g=>({gateId:g.id,gateName:g.name,active:g.active,todayIn:0,todayOut:0}));
  const gateMap={};gates.forEach(g=>gateMap[g.gateId]=g);
  const sh=db_().getSheetByName('ACCESS_EVENTS'),n=sh.getLastRow(),events=n>=2?sh.getRange(2,1,n-1,EVENT_HEADERS.length).getValues():[];
  const openMap={};let lastAccess=[];
  events.forEach(r=>{
    const ts=String(r[1]||''),person=String(r[3]||''),type=String(r[4]||''),plate=String(r[6]||''),gid=String(r[9]||''),dir=String(r[11]||''),result=String(r[13]||'');
    if(result==='AUTHORIZED'&&ts.slice(0,10)===now_().timestamp.slice(0,10)&&gateMap[gid]){if(dir==='IN')gateMap[gid].todayIn++;if(dir==='OUT')gateMap[gid].todayOut++;}
    if(result==='AUTHORIZED'){const key=(person||'')+'|'+(plate||'');if(dir==='IN')openMap[key]={person,type,plate,gateName:String(r[10]||'')};else if(dir==='OUT')delete openMap[key];}
  });
  const insideByType={VISITOR:0,CONTRACTOR:0,VENDOR:0,EMPLOYEE:0,'EMERGENCY VEHICLE':0,DELIVERY:0,'TEMPORARY VEHICLE':0,VIP:0};
  Object.values(openMap).forEach(o=>{if(insideByType[o.type]!=null)insideByType[o.type]++;});
  const legacy=currentlyInside_();
  const known=new Set(vehicles_().map(v=>norm_(v.plate)));
  const unexpected=legacy.filter(v=>v.plate&&!known.has(norm_(v.plate))).map(v=>({plate:v.plate,person:v.name,timestamp:v.date+' '+v.inTime}));
  lastAccess=events.slice(-20).reverse().map(r=>({eventId:r[0],timestamp:r[1],plate:r[6],person:r[3],type:r[4],direction:r[11],result:r[13],reason:r[14],gateName:r[10],device:r[12]}));
  const auth=authorizations_(),today=now_().date;
  const expected=auth.filter(a=>a.status==='ACTIVE'&&dateKey_(a.validFromDate)<=dateKey_(today)&&dateKey_(a.validUntilDate)>=dateKey_(today)).length;
  return{systemStatus:'ONLINE',inside:{total:legacy.length+Object.keys(openMap).length,vehicles:legacy.length,...insideByType},expected,visitors:insideByType.VISITOR,contractors:insideByType.CONTRACTOR,vendors:insideByType.VENDOR,employees:insideByType.EMPLOYEE,temporary:insideByType['TEMPORARY VEHICLE'],vip:insideByType.VIP,unexpectedVehicles:unexpected,gates,lastAccess,openAlerts:alerts_({status:'OPEN'}).alerts.length,createdBy:CONFIG.CREATED_BY};
}
function route_(a,p){switch(a){
 case'health':return health_();case'dashboard':return p.date?dashboardByDate_(p):dashboard_();case'commandCenter':return p.date?commandCenterByDate_(p):commandCenter_();
 case'search':return searchVehicle_(p.q||'');case'registerVehicle':return registerVehicle_(p);case'access':return access_(p);
 case'accessAuth':return accessAuth_(p);case'current':return currentlyInside_();case'report':return report_(p);case'audit':return auditEvents_(p);case'exceptions':return exceptions_(p);
 case'backup':return backup_();case'importVehicles':return importVehicles_(p);case'deleteVehicle':return deleteVehicle_(p);case'deleteAccessLog':return deleteAccessLog_(p);case'setAdminPin':return setAdminPin_(p);
 case'gates':return{gates:gates_()};case'addGate':return addGate_(p);case'authorizations':return searchAuthorizations_(p.q||'');case'createAuthorization':return createAuthorization_(p);case'updateAuthorizationStatus':return updateAuthorizationStatus_(p);
 case'alerts':return alerts_(p);case'ackAlert':return ackAlert_(p);case'resolveAlert':return resolveAlert_(p);case'syncQueue':return syncQueue_(p);
 default:throw Error('Action tidak dikenal: '+a)}}
