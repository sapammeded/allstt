const SPREADSHEET_ID = '1mNsi4dr1V4L513N9zxoq2hbHcWtd09yInSxD6sHQlkk';
const DEVICES_SHEET = 'DEVICES';
const HEADERS = [
  'installation_id','user_name','app','device','android','app_version',
  'activation_code','first_seen','last_seen','status','notes'
];
const ACTIVE = 'ACTIVE';
const BLOCKED = 'BLOCKED';
const PENDING = 'PENDING';
const REVOKED = 'REVOKED';

function json_(obj){
  return ContentService.createTextOutput(JSON.stringify(obj))
    .setMimeType(ContentService.MimeType.JSON);
}

function sheet_(){
  const ss = SpreadsheetApp.openById(SPREADSHEET_ID);
  let sh = ss.getSheetByName(DEVICES_SHEET);
  if(!sh) sh = ss.insertSheet(DEVICES_SHEET);
  if(sh.getLastRow() === 0){
    sh.getRange(1,1,1,HEADERS.length).setValues([HEADERS]);
    sh.setFrozenRows(1);
  } else {
    const current = sh.getRange(1,1,1,HEADERS.length).getValues()[0];
    if(current.join('|') !== HEADERS.join('|')){
      sh.getRange(1,1,1,HEADERS.length).setValues([HEADERS]);
      sh.setFrozenRows(1);
    }
  }
  return sh;
}

function clean_(v){ return String(v == null ? '' : v).trim(); }
function now_(){ return new Date(); }

function rowToObject_(row){
  const o = {};
  HEADERS.forEach((h,i)=>o[h] = row[i]);
  return o;
}

function findRow_(sh, installationId, app){
  const last = sh.getLastRow();
  if(last < 2) return null;
  const values = sh.getRange(2,1,last-1,HEADERS.length).getValues();
  const targetId = clean_(installationId);
  const targetApp = clean_(app).toUpperCase();
  for(let i=0;i<values.length;i++){
    const id = clean_(values[i][0]);
    const a = clean_(values[i][2]).toUpperCase();
    if(id === targetId && a === targetApp) return { rowNumber:i+2, values:values[i] };
  }
  return null;
}

function ensurePending_(sh, data){
  const existing = findRow_(sh, data.installation_id, data.app);
  if(existing) return existing;
  const t = now_();
  const row = [
    data.installation_id,
    '',
    data.app,
    data.device,
    data.android,
    data.app_version,
    '',
    t,
    t,
    PENDING,
    'AUTO-REGISTERED: menunggu aktivasi administrator'
  ];
  sh.appendRow(row);
  return { rowNumber:sh.getLastRow(), values:row };
}

function deviceCheck_(data){
  const sh = sheet_();
  const id = clean_(data.installation_id);
  const app = clean_(data.app).toUpperCase();
  if(!id) return {status:'ERROR',message:'installation_id wajib diisi'};
  if(!app) return {status:'ERROR',message:'app wajib diisi'};

  const found = ensurePending_(sh, {
    installation_id:id,
    app:app,
    device:clean_(data.device),
    android:clean_(data.android),
    app_version:clean_(data.app_version)
  });

  const row = sh.getRange(found.rowNumber,1,1,HEADERS.length).getValues()[0];
  const obj = rowToObject_(row);
  const currentStatus = clean_(obj.status).toUpperCase() || PENDING;
  const currentCode = clean_(obj.activation_code);
  const suppliedCode = clean_(data.activation_code);
  const t = now_();

  // Keep device metadata current without changing owner-controlled fields.
  sh.getRange(found.rowNumber,4,1,3).setValues([[
    clean_(data.device) || obj.device,
    clean_(data.android) || obj.android,
    clean_(data.app_version) || obj.app_version
  ]]);
  if(!obj.first_seen) sh.getRange(found.rowNumber,8).setValue(t);
  sh.getRange(found.rowNumber,9).setValue(t);

  if(currentStatus === ACTIVE){
    if(currentCode && suppliedCode !== currentCode){
      return {status:'PENDING',message:'Kode aktivasi tidak cocok.'};
    }
    return {status:ACTIVE,message:'Akses diizinkan.'};
  }
  if(currentStatus === BLOCKED){
    return {status:BLOCKED,message:'Perangkat diblokir administrator.'};
  }
  if(currentStatus === REVOKED){
    return {status:REVOKED,message:'Akses perangkat dicabut administrator.'};
  }
  return {status:PENDING,message:'Perangkat menunggu aktivasi administrator.'};
}

function doGet(e){
  try{
    const p = e && e.parameter ? e.parameter : {};
    const action = clean_(p.action).toUpperCase();
    if(action === 'DEVICE_CHECK' || action === 'DEVICE_HEARTBEAT'){
      return json_(deviceCheck_(p));
    }
    if(action === 'PING') return json_({status:'OK',service:'STTFINO_DEVICE_CONTROL'});
    return json_({status:'ERROR',message:'Invalid action'});
  }catch(err){
    return json_({status:'ERROR',message:err && err.message ? err.message : String(err)});
  }
}

function doPost(e){
  try{
    const p = Object.assign({}, (e && e.parameter) || {});
    let body = {};
    try{ body = e && e.postData && e.postData.contents ? JSON.parse(e.postData.contents) : {}; }catch(_){ }
    Object.keys(body || {}).forEach(k=>p[k]=body[k]);
    const action = clean_(p.action).toUpperCase();
    if(action === 'DEVICE_CHECK' || action === 'DEVICE_HEARTBEAT'){
      return json_(deviceCheck_(p));
    }
    return json_({status:'ERROR',message:'Invalid action'});
  }catch(err){
    return json_({status:'ERROR',message:err && err.message ? err.message : String(err)});
  }
}

function setupDevicesSheet(){
  sheet_();
}
