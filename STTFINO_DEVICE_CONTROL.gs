/**
 * STTFINO CENTRAL BACKEND v17 — UNIFIED ALLSTT
 * Includes FINDINGS + PHOTO UPLOAD + DEVICES / LICENSE CONTROL.
 * Deployment marker: ALLSTT_UNIFIED_V17
 *
 * DATA CONTRACT
 * finding_id | area_code | photo_url | description | finder_name |
 * created_at | status | updated_at | is_deleted
 *
 * IMPORTANT:
 * - New photo uploads accept the browser-safe Base64/form path and legacy
 *   raw-binary POST bodies.
 * - Google Sheet stores only HTTP(S) Drive URLs (JSON array in photo_url).
 * - Existing legacy Base64 rows are handled only by the one-time migration
 *   functions at the bottom.
 */
const SPREADSHEET_ID = '1dxjIOEhQhoJpkcWBaeHm5n1ERGky7ztSWjBiLoo6JTs';
const FINDINGS_SHEET = 'FINDINGS';
const FINDING_MEDIA_FOLDER_ID = '1G28FlBrRC81QRAUQpQB1L1HUssxiYL8N';
const FINDING_HEADERS = ['finding_id','area_code','photo_url','description','finder_name','created_at','status','updated_at','is_deleted'];
const CACHE_KEY = 'STTFINO_FINDINGS_V16';
const CACHE_SECONDS = 60;
const REVISION_KEY = 'STTFINO_FINDINGS_REVISION_V3';
const UPLOAD_STATUS_PREFIX = 'STTFINO_UPLOAD_V16_';
const UPLOAD_STATUS_SECONDS = 600;
const MIGRATION_CURSOR_KEY = 'STTFINO_LEGACY_PHOTO_CURSOR_V3';
const MAX_UPLOAD_BYTES = 6 * 1024 * 1024;

function doGet(e) {
  const action = String(e && e.parameter && e.parameter.action || '').trim().toUpperCase();
  try {
    if (action === 'GET_META') return json_({status:'success', revision:getRevision_()});
    if (action === 'GET_FINDINGS') return getFindings_();
    if (action === 'GET_UPLOAD_STATUS') return getUploadStatus_(e.parameter.upload_id);
    if (action === 'DEVICE_CHECK' || action === 'DEVICE_HEARTBEAT') return deviceCheck_(e.parameter);
    return json_({status:'error', message:'ALLSTT_UNIFIED_V17: Invalid GET action', service:'STTFINO3', api_version:'v17', action_received:action || null});
  } catch (err) {
    return json_({status:'error', message:String(err)});
  }
}

function doPost(e) {
  try {
    const action = String(e && e.parameter && e.parameter.action || '').toUpperCase();
    if (action === 'DEVICE_CHECK' || action === 'DEVICE_HEARTBEAT') return deviceCheck_(e.parameter);
    if (action === 'UPLOAD_PHOTO') return uploadPhotoBinary_(e);

    let body = {};
    const postText = e && e.postData && e.postData.contents || '';
    if (postText) {
      try { body = JSON.parse(postText); } catch (_) { body = {}; }
    }
    if ((!body || !body.action) && e && e.parameter && e.parameter.payload) {
      try { body = JSON.parse(String(e.parameter.payload)); } catch (_) { body = {}; }
    }
    if ((!body || !body.action) && action === 'SAVE_FINDING') {
      body = {action:'SAVE_FINDING', data:{
        finding_id:e.parameter.finding_id, area_code:e.parameter.area_code,
        photo_url:e.parameter.photo_url, description:e.parameter.description,
        finder_name:e.parameter.finder_name, created_at:e.parameter.created_at,
        status:e.parameter.status
      }};
    } else if ((!body || !body.action) && action === 'UPDATE_STATUS') {
      body = {action:'UPDATE_STATUS', finding_id:e.parameter.finding_id, status:e.parameter.status};
    } else if ((!body || !body.action) && action === 'DELETE_FINDING') {
      body = {action:'DELETE_FINDING', finding_id:e.parameter.finding_id};
    }
    const bodyAction = String(body.action || action || '').toUpperCase();
    if (bodyAction === 'SAVE_FINDING') return saveFinding_(body.data || {});
    if (bodyAction === 'UPDATE_STATUS') return updateStatus_(body.finding_id, body.status);
    if (bodyAction === 'DELETE_FINDING') return deleteFinding_(body.finding_id);
    return json_({status:'error', message:'Invalid POST action'});
  } catch (err) {
    return json_({status:'error', message:String(err)});
  }
}

function sheet_() {
  const ss = SpreadsheetApp.openById(SPREADSHEET_ID);
  let sh = ss.getSheetByName(FINDINGS_SHEET);
  if (!sh) sh = ss.insertSheet(FINDINGS_SHEET);
  ensureHeaders_(sh);
  return sh;
}

function ensureHeaders_(sh) {
  const h = sh.getRange(1,1,1,FINDING_HEADERS.length).getValues()[0];
  let ok = true;
  for (let i=0;i<FINDING_HEADERS.length;i++) {
    if (String(h[i] || '').trim() !== FINDING_HEADERS[i]) { ok=false; break; }
  }
  if (!ok) sh.getRange(1,1,1,FINDING_HEADERS.length).setValues([FINDING_HEADERS]);
}

function getRevision_() {
  const p = PropertiesService.getScriptProperties();
  let v = p.getProperty(REVISION_KEY);
  if (!v) { v = String(Date.now()) + '-0'; p.setProperty(REVISION_KEY,v); }
  return v;
}

function bumpRevision_() {
  const v = String(Date.now()) + '-' + Math.floor(Math.random()*1000000);
  PropertiesService.getScriptProperties().setProperty(REVISION_KEY,v);
  try { CacheService.getScriptCache().remove(CACHE_KEY); } catch (_) {}
  return v;
}

function getFindings_() {
  const cache = CacheService.getScriptCache();
  const hit = cache.get(CACHE_KEY);
  if (hit) return json_(JSON.parse(hit));
  const sh = sheet_();
  const last = sh.getLastRow();
  const result = {status:'success', revision:getRevision_(), data:[], legacyPhotos:false};
  if (last <= 1) { safeCachePut_(CACHE_KEY, JSON.stringify(result), CACHE_SECONDS); return json_(result); }
  const rows = sh.getRange(2,1,last-1,FINDING_HEADERS.length).getValues();
  let legacy = false;
  result.data = rows.map(function(r){
    const raw = String(r[2] || '');
    if (containsDataImage_(raw)) legacy = true;
    return {finding_id:String(r[0]||''),area_code:String(r[1]||''),photo_url:parsePhotoUrlsSafe_(raw),description:String(r[3]||''),finder_name:String(r[4]||''),created_at:iso_(r[5]),status:normalizeStatus_(r[6]),updated_at:iso_(r[7]),is_deleted:isDeleted_(r[8])};
  }).filter(function(x){return x.finding_id && !x.is_deleted;});
  result.legacyPhotos = legacy;
  safeCachePut_(CACHE_KEY, JSON.stringify(result), CACHE_SECONDS);
  return json_(result);
}

function uploadPhotoBinary_(e) {
  const p = (e && e.parameter) || {};
  const uploadId = String(p.upload_id || '').trim() || ('UP-'+Date.now());
  const findingId = sanitizeId_(p.finding_id || 'finding');
  const mime = normalizeImageMime_(p.mime);
  const filename = safeFileName_(p.filename || ('finding_'+findingId+'_'+Date.now()+'.jpg'));
  const post = e && e.postData;
  const raw = post && post.contents || '';
  if (!raw) return json_({status:'error',message:'Payload foto kosong',upload_id:uploadId});
  try {
    let blob;
    const text = String(raw);
    const m = text.match(/^data:(image\/[^;]+);base64,(.+)$/s);
    if (m) blob = Utilities.newBlob(Utilities.base64Decode(m[2]), normalizeImageMime_(m[1]), filename);
    else {
      let decoded = null;
      try { decoded = Utilities.base64Decode(text); } catch (_) {}
      blob = decoded ? Utilities.newBlob(decoded, mime, filename) : Utilities.newBlob(raw, mime, filename);
    }
    if (blob.getBytes().length > MAX_UPLOAD_BYTES) return json_({status:'error',message:'Foto terlalu besar (>6 MB)',upload_id:uploadId});
    const folder = DriveApp.getFolderById(FINDING_MEDIA_FOLDER_ID);
    const file = folder.createFile(blob);
    const url = 'https://drive.google.com/uc?export=view&id='+file.getId();
    uploadStatusWrite_(uploadId,{status:'success',url:url,finding_id:findingId},UPLOAD_STATUS_SECONDS);
    return json_({status:'success',upload_id:uploadId,url:url,finding_id:findingId});
  } catch (err) {
    uploadStatusWrite_(uploadId,{status:'error',message:String(err&&err.message||err),finding_id:findingId},UPLOAD_STATUS_SECONDS);
    return json_({status:'error',message:String(err&&err.message||err),upload_id:uploadId});
  }
}

function getUploadStatus_(uploadId) {
  const id = String(uploadId || '').trim();
  if (!id) return json_({status:'error',message:'upload_id wajib diisi'});
  return json_(getUploadStatusObject_(id));
}
function getUploadStatusObject_(uploadId) {
  const raw = PropertiesService.getScriptProperties().getProperty(UPLOAD_STATUS_PREFIX+uploadId);
  return raw ? JSON.parse(raw) : {status:'pending',upload_id:uploadId};
}
function uploadStatusWrite_(uploadId,obj,seconds) {
  PropertiesService.getScriptProperties().setProperty(UPLOAD_STATUS_PREFIX+uploadId,JSON.stringify(obj));
  try { CacheService.getScriptCache().put(UPLOAD_STATUS_PREFIX+uploadId,JSON.stringify(obj),seconds); } catch (_) {}
}

function saveFinding_(data) {
  const id = sanitizeId_(data.finding_id);
  if (!id) return json_({status:'error',message:'finding_id wajib'});
  const photos = parsePhotoUrlsStrict_(data.photo_url);
  if (photos === null) return json_({status:'error',message:'photo_url harus berisi URL Drive/HTTP. Base64/data:image ditolak.'});
  const area = String(data.area_code || '').trim();
  const description = String(data.description || '');
  const finder = String(data.finder_name || '').trim() || 'Petugas';
  const status = normalizeStatus_(data.status);
  const now = new Date();
  const created = data.created_at ? new Date(data.created_at) : now;
  const createdSafe = isNaN(created.getTime()) ? now : created;
  const lock = LockService.getScriptLock();
  if (!lock.tryLock(5000)) return json_({status:'busy',message:'Central sedang menerima perubahan lain. Coba lagi.'});
  try {
    const sh = sheet_();
    const cell = findId_(sh,id);
    let row;
    let createdValue = createdSafe;
    if (cell) {
      row = cell.getRow();
      const oldCreated = sh.getRange(row,6).getValue();
      if (oldCreated) createdValue = oldCreated;
    } else row = sh.getLastRow() + 1;
    sh.getRange(row,1,1,9).setValues([[id,area,JSON.stringify(photos),description,finder,createdValue,status,now,false]]);
    SpreadsheetApp.flush();
    return json_({status:'success',finding_id:id,revision:bumpRevision_()});
  } finally { lock.releaseLock(); }
}

function updateStatus_(findingId,status) {
  const id = sanitizeId_(findingId);
  const lock = LockService.getScriptLock();
  if (!lock.tryLock(5000)) return json_({status:'busy',message:'Central sedang sibuk. Coba lagi.'});
  try {
    const sh = sheet_();
    const cell = findId_(sh,id);
    if (!cell) return json_({status:'error',message:'Finding ID not found'});
    sh.getRange(cell.getRow(),7,1,2).setValues([[normalizeStatus_(status),new Date()]]);
    SpreadsheetApp.flush();
    return json_({status:'success',finding_id:id,revision:bumpRevision_()});
  } finally { lock.releaseLock(); }
}

function deleteFinding_(findingId) {
  const id = sanitizeId_(findingId);
  const lock = LockService.getScriptLock();
  if (!lock.tryLock(5000)) return json_({status:'busy',message:'Central sedang sibuk. Coba lagi.'});
  try {
    const sh = sheet_();
    const cell = findId_(sh,id);
    if (!cell) return json_({status:'error',message:'Finding ID not found'});
    sh.getRange(cell.getRow(),8,1,2).setValues([[new Date(),true]]);
    SpreadsheetApp.flush();
    return json_({status:'success',finding_id:id,revision:bumpRevision_()});
  } finally { lock.releaseLock(); }
}

function findId_(sh,id) {
  if (!id || sh.getLastRow() <= 1) return null;
  return sh.getRange(2,1,sh.getLastRow()-1,1).createTextFinder(id).matchEntireCell(true).findNext();
}
function parsePhotoUrlsStrict_(value) {
  if (value == null || value === '') return [];
  const items = Array.isArray(value) ? value : parseArray_(value);
  if (!Array.isArray(items)) return null;
  const out = [];
  for (let i=0;i<items.length;i++) {
    const x = typeof items[i] === 'string' ? items[i] : String(items[i] && items[i].url || '');
    const s = String(x || '').trim();
    if (!s) continue;
    if (/^data:image\//i.test(s)) return null;
    if (!/^https?:\/\//i.test(s)) return null;
    out.push(s);
  }
  return out;
}
function parsePhotoUrlsSafe_(value) {
  if (!value) return [];
  const x = parseArray_(value);
  if (!Array.isArray(x)) return [];
  return x.map(function(v){return typeof v==='string'?v:String(v&&v.url||'');}).filter(function(v){return /^https?:\/\//i.test(String(v).trim());});
}
function parseArray_(value) {
  if (Array.isArray(value)) return value;
  try { const x=JSON.parse(String(value)); return Array.isArray(x)?x:null; } catch (_) { return null; }
}
function containsDataImage_(v) { return /data:image\//i.test(String(v || '')); }
function normalizeStatus_(s) { const v=String(s||'OPEN').toUpperCase().trim(); return ['OPEN','IN PROGRESS','FIXED'].indexOf(v)>=0?v:'OPEN'; }
function isDeleted_(v) { return v === true || String(v || '').toUpperCase() === 'TRUE'; }
function iso_(v) { if(!v)return ''; const d=v instanceof Date?v:new Date(v); return isNaN(d.getTime())?String(v):d.toISOString(); }
function sanitizeId_(v) { return String(v || '').trim().replace(/[^A-Za-z0-9._:-]/g,'_').slice(0,160); }
function safeFileName_(v) { return String(v || 'file.jpg').replace(/[\\/:*?"<>|\x00-\x1F]/g,'_').slice(0,120); }
function normalizeImageMime_(v) { const m=String(v||'image/jpeg').toLowerCase(); return /^image\/(jpeg|jpg|png|webp|gif)$/i.test(m)?(m==='image/jpg'?'image/jpeg':m):'image/jpeg'; }
function safeCachePut_(key,value,seconds) { try { CacheService.getScriptCache().put(key,value,seconds); } catch (_) {} }

// One-time legacy migration helpers are retained for existing rows created by older versions.
function migrateLegacyPhotosBatch() {
  const sh=sheet_(), last=sh.getLastRow();
  if(last<=1)return 'NO_ROWS';
  const props=PropertiesService.getScriptProperties(), cursor=Number(props.getProperty(MIGRATION_CURSOR_KEY)||2);
  const end=Math.min(last,cursor+25);
  const rows=sh.getRange(cursor,1,end-cursor+1,9).getValues();
  for(let i=0;i<rows.length;i++){
    const row=cursor+i,raw=rows[i][2],id=String(rows[i][0]||'');
    if(id&&containsDataImage_(raw)){
      const urls=migrateLegacyPhotoValue_(raw,id);
      if(urls.length)sh.getRange(row,3).setValue(JSON.stringify(urls));
    }
  }
  if(end>=last){props.deleteProperty(MIGRATION_CURSOR_KEY);bumpRevision_();return 'DONE';}
  props.setProperty(MIGRATION_CURSOR_KEY,String(end+1));return 'MORE';
}
function migrateLegacyPhotoValue_(raw,findingId) {
  const items=parseArray_(raw)||[];const out=[];const folder=DriveApp.getFolderById(FINDING_MEDIA_FOLDER_ID);
  for(let i=0;i<items.length;i++){
    const s=String(typeof items[i]==='string'?items[i]:(items[i]&&items[i].data)||'');
    const m=s.match(/^data:(image\/[^;]+);base64,(.+)$/s); if(!m)continue;
    try{const blob=Utilities.newBlob(Utilities.base64Decode(m[2]),normalizeImageMime_(m[1]),'legacy_'+findingId+'_'+(i+1)+'.jpg');const file=folder.createFile(blob);out.push('https://drive.google.com/uc?export=view&id='+file.getId());}catch(_){}
  }
  return out;
}
function startLegacyPhotoCleanup(){PropertiesService.getScriptProperties().setProperty(MIGRATION_CURSOR_KEY,'2');return 'STARTED';}
function legacyPhotoCleanupTick(){return migrateLegacyPhotosBatch();}
function stopLegacyPhotoCleanup(){PropertiesService.getScriptProperties().deleteProperty(MIGRATION_CURSOR_KEY);return 'STOPPED';}

const DEVICES_SHEET = 'DEVICES';
const DEVICE_HEADERS = ['installation_id','user_name','app','device','android','app_version','activation_code','first_seen','last_seen','status','notes'];
const DEVICE_PENDING = 'PENDING';
const DEVICE_ACTIVE = 'ACTIVE';
const DEVICE_BLOCKED = 'BLOCKED';
const DEVICE_REVOKED = 'REVOKED';

function deviceSheet_() {
  const ss = SpreadsheetApp.openById(SPREADSHEET_ID);
  let sh = ss.getSheetByName(DEVICES_SHEET);
  if (!sh) sh = ss.insertSheet(DEVICES_SHEET);
  try { sh.showSheet(); } catch (ignore) {}
  const headerRange = sh.getRange(1,1,1,DEVICE_HEADERS.length);
  const currentHeader = headerRange.getValues()[0].map(function(v){return deviceClean_(v);});
  if (currentHeader.join('|') !== DEVICE_HEADERS.join('|')) headerRange.setValues([DEVICE_HEADERS]);
  sh.setFrozenRows(1);
  SpreadsheetApp.flush();
  return sh;
}
function setupDevicesSheet() {
  const ss=SpreadsheetApp.openById(SPREADSHEET_ID),sh=deviceSheet_();
  SpreadsheetApp.flush();
  Logger.log('STTFINO3: '+ss.getName());
  Logger.log('Spreadsheet ID: '+ss.getId());
  Logger.log('DEVICES sheet: '+sh.getName());
  Logger.log('DEVICES sheet ID: '+sh.getSheetId());
  Logger.log('DEVICES visible: '+!sh.isSheetHidden());
  Logger.log('DEVICES last row: '+sh.getLastRow());
  return sh.getName();
}
function deviceClean_(v){return String(v==null?'':v).trim();}
function deviceFindRow_(sh,id,app){
  const last=sh.getLastRow(); if(last<2)return null;
  const tid=deviceClean_(id),ta=deviceClean_(app).toUpperCase();
  if(!tid)return null;
  // Fast lookup: search only installation_id instead of loading the entire DEVICES sheet.
  const hit=sh.getRange(2,1,last-1,1).createTextFinder(tid).matchEntireCell(true).matchCase(true).findNext();
  if(!hit)return null;
  const row=hit.getRow(),values=sh.getRange(row,1,1,DEVICE_HEADERS.length).getValues()[0];
  if(deviceClean_(values[2]).toUpperCase()!==ta)return null;
  return {row:row,values:values};
}
function deviceCheck_(p){
  const id=deviceClean_(p&&p.installation_id),app=deviceClean_(p&&p.app).toUpperCase();
  if(!id||!app)return json_({status:'ERROR',message:'installation_id dan app wajib diisi'});
  const sh=deviceSheet_();
  let f=deviceFindRow_(sh,id,app),t=new Date();
  if(!f){
    sh.appendRow([id,'',app,deviceClean_(p.device),deviceClean_(p.android),deviceClean_(p.app_version),'',t,t,DEVICE_PENDING,'Menunggu aktivasi administrator']);
    f={row:sh.getLastRow(),values:sh.getRange(sh.getLastRow(),1,1,DEVICE_HEADERS.length).getValues()[0]};
  }
  const row=sh.getRange(f.row,1,1,DEVICE_HEADERS.length).getValues()[0];
  const currentStatus=deviceClean_(row[9]).toUpperCase()||DEVICE_PENDING;
  const activation=deviceClean_(row[6]);
  const supplied=deviceClean_(p.activation_code);
  // Device may refresh technical metadata only. user_name, activation_code and status remain admin-controlled.
  sh.getRange(f.row,4,1,3).setValues([[deviceClean_(p.device)||row[3],deviceClean_(p.android)||row[4],deviceClean_(p.app_version)||row[5]]]);
  if(!row[7])sh.getRange(f.row,8).setValue(t);
  sh.getRange(f.row,9).setValue(t);
  if(currentStatus===DEVICE_ACTIVE){
    if(!activation)return json_({status:DEVICE_PENDING,message:'Perangkat ACTIVE tetapi kode aktivasi belum diisi administrator.'});
    if(supplied!==activation)return json_({status:DEVICE_PENDING,message:'Kode aktivasi tidak cocok.'});
    return json_({status:DEVICE_ACTIVE,user_name:deviceClean_(row[1]),message:'Akses diizinkan.',device:{installation_id:id,status:DEVICE_ACTIVE}});
  }
  if(currentStatus===DEVICE_BLOCKED)return json_({status:DEVICE_BLOCKED,message:'Perangkat diblokir administrator.'});
  if(currentStatus===DEVICE_REVOKED)return json_({status:DEVICE_REVOKED,message:'Akses perangkat dicabut administrator.'});
  return json_({status:DEVICE_PENDING,message:'Perangkat menunggu aktivasi administrator.'});
}
function testDeviceCheck_(){
  const sample={installation_id:'TEST-INSTALLATION-V17',app:'ALLSTT',device:'TEST DEVICE',android:'TEST',app_version:'V17',activation_code:''};
  const result=deviceCheck_(sample); Logger.log(result.getContent()); return result.getContent();
}
function json_(data){return ContentService.createTextOutput(JSON.stringify(data)).setMimeType(ContentService.MimeType.JSON);}
