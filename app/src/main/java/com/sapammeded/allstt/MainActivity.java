package com.sapammeded.allstt;

import android.Manifest;
import android.app.Activity;
import android.content.ActivityNotFoundException;
import android.content.ContentValues;
import android.content.Intent;
import android.content.pm.PackageManager;
import android.net.Uri;
import android.os.Build;
import android.os.Bundle;
import android.provider.MediaStore;
import android.webkit.CookieManager;
import android.webkit.GeolocationPermissions;
import android.webkit.JavascriptInterface;
import android.webkit.PermissionRequest;
import android.webkit.ValueCallback;
import android.webkit.WebChromeClient;
import android.webkit.WebView;
import android.webkit.WebViewClient;
import android.webkit.WebSettings;
import android.widget.Toast;
import android.util.Base64;

import java.io.ByteArrayOutputStream;
import java.io.InputStream;
import java.io.OutputStream;
import java.net.HttpURLConnection;
import java.net.URL;
import java.net.URLDecoder;
import java.nio.charset.StandardCharsets;

public class MainActivity extends Activity {
    private static final int FILE_CHOOSER = 4101;
    private static final int CAMERA_PERMISSION = 4102;
    private static final int SAVE_FILE = 4103;
    private static final int LOCATION_PERMISSION = 4104;

    private WebView webView;
    private ValueCallback<Uri[]> fileCallback;
    private Uri pendingCameraUri;

    private byte[] pendingSaveBytes;
    private String pendingSaveName;
    private String pendingSaveMime;

    private String pendingGeoOrigin;
    private GeolocationPermissions.Callback pendingGeoCallback;

    @Override protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        webView = new WebView(this);
        setContentView(webView);
        configureWebView();

        // MainActivityGenius must install AndroidCentral before the first
        // launcher document executes. Do not start a premature document load.
        if (!(this instanceof MainActivityGenius)) {
            webView.loadUrl("file:///android_asset/launcher.html");
        }
    }

    private void configureWebView() {
        WebSettings s = webView.getSettings();
        s.setJavaScriptEnabled(true);
        s.setDomStorageEnabled(true);
        s.setDatabaseEnabled(true);
        s.setAllowFileAccess(true);
        s.setAllowContentAccess(true);
        s.setMediaPlaybackRequiresUserGesture(false);
        s.setJavaScriptCanOpenWindowsAutomatically(true);
        CookieManager.getInstance().setAcceptCookie(true);

        webView.addJavascriptInterface(new AndroidBridge(), "Android");
        webView.setWebViewClient(new WebViewClient() {
            @Override public void onPageFinished(WebView view, String url) {
                super.onPageFinished(view, url);
                installDownloadBridgePatch(view);
            }
        });
        webView.setWebChromeClient(new WebChromeClient() {
            @Override public boolean onShowFileChooser(WebView view, ValueCallback<Uri[]> callback, FileChooserParams params) {
                if (fileCallback != null) fileCallback.onReceiveValue(null);
                fileCallback = callback;

                if (params.isCaptureEnabled()) {
                    Intent cameraOnly = new Intent(MediaStore.ACTION_IMAGE_CAPTURE);
                    if (cameraOnly.resolveActivity(getPackageManager()) == null) {
                        fileCallback.onReceiveValue(null); fileCallback = null;
                        Toast.makeText(MainActivity.this, "Tidak ada aplikasi kamera", Toast.LENGTH_SHORT).show();
                        return true;
                    }
                    pendingCameraUri = createCameraUri();
                    if (pendingCameraUri != null) cameraOnly.putExtra(MediaStore.EXTRA_OUTPUT, pendingCameraUri);
                    cameraOnly.addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION | Intent.FLAG_GRANT_WRITE_URI_PERMISSION);
                    if (Build.VERSION.SDK_INT >= 23 && checkSelfPermission(Manifest.permission.CAMERA) != PackageManager.PERMISSION_GRANTED)
                        requestPermissions(new String[]{Manifest.permission.CAMERA}, CAMERA_PERMISSION);
                    try {
                        Intent chooser = Intent.createChooser(cameraOnly, "Pilih aplikasi kamera");
                        startActivityForResult(chooser, FILE_CHOOSER);
                    } catch (ActivityNotFoundException e) {
                        if (pendingCameraUri != null) try { getContentResolver().delete(pendingCameraUri, null, null); } catch (Exception ignored) {}
                        pendingCameraUri = null; fileCallback.onReceiveValue(null); fileCallback = null;
                        Toast.makeText(MainActivity.this, "Tidak ada aplikasi kamera", Toast.LENGTH_SHORT).show();
                    }
                    return true;
                }

                Intent picker;
                try { picker = params.createIntent(); } catch (Exception e) { picker = new Intent(Intent.ACTION_GET_CONTENT); }
                picker.addCategory(Intent.CATEGORY_OPENABLE);
                if (picker.getType() == null || picker.getType().isEmpty()) picker.setType("image/*");

                Intent camera = new Intent(MediaStore.ACTION_IMAGE_CAPTURE);
                if (camera.resolveActivity(getPackageManager()) != null) {
                    pendingCameraUri = createCameraUri();
                    if (pendingCameraUri != null) camera.putExtra(MediaStore.EXTRA_OUTPUT, pendingCameraUri);
                    camera.addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION | Intent.FLAG_GRANT_WRITE_URI_PERMISSION);
                }
                Intent chooser = new Intent(Intent.ACTION_CHOOSER);
                chooser.putExtra(Intent.EXTRA_INTENT, picker);
                if (camera.resolveActivity(getPackageManager()) != null) chooser.putExtra(Intent.EXTRA_INITIAL_INTENTS, new Intent[]{camera});
                chooser.putExtra(Intent.EXTRA_TITLE, "Pilih sumber foto");
                if (Build.VERSION.SDK_INT >= 23 && checkSelfPermission(Manifest.permission.CAMERA) != PackageManager.PERMISSION_GRANTED)
                    requestPermissions(new String[]{Manifest.permission.CAMERA}, CAMERA_PERMISSION);
                try { startActivityForResult(chooser, FILE_CHOOSER); }
                catch (ActivityNotFoundException e) {
                    fileCallback.onReceiveValue(null); fileCallback = null;
                    Toast.makeText(MainActivity.this, "Tidak ada aplikasi untuk memilih foto", Toast.LENGTH_SHORT).show();
                }
                return true;
            }

            @Override public void onPermissionRequest(PermissionRequest request) { runOnUiThread(() -> request.grant(request.getResources())); }

            @Override public void onGeolocationPermissionsShowPrompt(String origin, GeolocationPermissions.Callback callback) {
                if (Build.VERSION.SDK_INT < 23 || hasLocationPermission()) {
                    callback.invoke(origin, true, false);
                    return;
                }
                pendingGeoOrigin = origin;
                pendingGeoCallback = callback;
                requestPermissions(new String[]{Manifest.permission.ACCESS_FINE_LOCATION, Manifest.permission.ACCESS_COARSE_LOCATION}, LOCATION_PERMISSION);
            }
        });

        webView.setDownloadListener((url, userAgent, contentDisposition, mimeType, contentLength) -> handleWebDownload(url, contentDisposition, mimeType));
    }

    private boolean hasLocationPermission() {
        if (Build.VERSION.SDK_INT < 23) return true;
        return checkSelfPermission(Manifest.permission.ACCESS_FINE_LOCATION) == PackageManager.PERMISSION_GRANTED
                || checkSelfPermission(Manifest.permission.ACCESS_COARSE_LOCATION) == PackageManager.PERMISSION_GRANTED;
    }

    @Override public void onRequestPermissionsResult(int requestCode, String[] permissions, int[] grantResults) {
        super.onRequestPermissionsResult(requestCode, permissions, grantResults);
        if (requestCode == LOCATION_PERMISSION) {
            boolean granted = hasLocationPermission();
            if (pendingGeoCallback != null && pendingGeoOrigin != null) {
                pendingGeoCallback.invoke(pendingGeoOrigin, granted, false);
            }
            pendingGeoCallback = null;
            pendingGeoOrigin = null;
        }
    }

    private void installDownloadBridgePatch(WebView view) {
        String js = "(function(){if(window.__ALLSTT_DOWNLOAD_PATCH)return;window.__ALLSTT_DOWNLOAD_PATCH=true;" +
            "function save(a){try{if(!a||!a.hasAttribute('download')||!a.href)return false;var u=a.href,n=a.download||'ALLSTT_Download';" +
            "if(u.indexOf('blob:')!==0&&u.indexOf('data:')!==0)return false;" +
            "if(window.Android&&Android.saveBlobUrl){Android.saveBlobUrl(u,n);return true;}return false;}catch(e){return false;}}" +
            "var c=HTMLAnchorElement.prototype.click;HTMLAnchorElement.prototype.click=function(){if(save(this))return c.call(document.createElement('a'));return c.call(this)};" +
            "window.__ALLSTT_saveBlob=function(u,n){if(window.Android&&Android.saveBlobUrl){Android.saveBlobUrl(u,n);return true}return false};" +
            "})();";
        view.evaluateJavascript(js, null);
    }

    private void handleWebDownload(String url, String contentDisposition, String mimeType) {
        if (url == null || url.isEmpty()) return;
        String filename = extractFilename(contentDisposition);
        boolean defaultName = filename == null || filename.isEmpty();
        if (defaultName) filename = "ALLSTT_Download";

        if (defaultName && mimeType != null && mimeType.toLowerCase().contains("pdf")) {
            final String downloadUrl = url, downloadMime = mimeType, cd = contentDisposition;
            webView.evaluateJavascript(
                "(function(){try{" +
                "const p=(document.getElementById('petugasName')?.value||'Petugas').trim();" +
                "const s=(document.getElementById('shift')?.value||'SHIFT').trim().toUpperCase();" +
                "const d=document.getElementById('tanggal')?.value||'';" +
                "const ds=/^\\\\d{4}-\\\\d{2}-\\\\d{2}$/.test(d)?d.split('-').reverse().join('-'):'';" +
                "const safe=v=>String(v||'').replace(/[\\\\\\\\/:*?\\\"<>|]/g,'-').replace(/\\\\s+/g,'_').slice(0,80);" +
                "return encodeURIComponent(safe(p)+'_'+(ds||''+new Date().getDate().toString().padStart(2,'0')+'-'+(new Date().getMonth()+1).toString().padStart(2,'0')+'-'+new Date().getFullYear())+'_'+(safe(s)||'SHIFT')+'.pdf');" +
                "}catch(e){return 'Petugas_SHIFT.pdf';}})()",
                value -> {
                    String resolved = "Petugas_SHIFT.pdf";
                    try {
                        if (value != null) {
                            String raw = value;
                            if (raw.startsWith("\"") && raw.endsWith("\"")) raw = raw.substring(1, raw.length()-1);
                            resolved = URLDecoder.decode(raw, StandardCharsets.UTF_8.name());
                        }
                    } catch (Exception ignored) {}
                    handleWebDownloadResolved(downloadUrl, cd, downloadMime, resolved);
                }
            );
            return;
        }
        handleWebDownloadResolved(url, contentDisposition, mimeType, filename);
    }

    private String extractFilename(String contentDisposition) {
        if (contentDisposition == null) return null;
        int p = contentDisposition.indexOf("filename=");
        if (p < 0) return null;
        String name = contentDisposition.substring(p + 9).replace("\"", "").trim();
        return name.isEmpty() ? null : name;
    }

    private void handleWebDownloadResolved(String url, String contentDisposition, String mimeType, String filename) {
        if (filename == null || filename.isEmpty()) filename = "ALLSTT_Download";
        filename = filename.replaceAll("[\\\\/:*?\"<>|]", "_");
        if (!filename.toLowerCase().endsWith(".pdf") && mimeType != null && mimeType.toLowerCase().contains("pdf")) filename += ".pdf";

        if (url.startsWith("blob:")) {
            String safeUrl = org.json.JSONObject.quote(url);
            String safeName = org.json.JSONObject.quote(filename);
            String safeMime = org.json.JSONObject.quote(mimeType == null ? "application/octet-stream" : mimeType);
            webView.evaluateJavascript("(async()=>{try{const r=await fetch("+safeUrl+");const b=await r.blob();const fr=new FileReader();fr.onload=()=>Android.saveBase64File("+safeName+","+safeMime+",fr.result.split(',')[1]);fr.readAsDataURL(b);}catch(e){Android.downloadError(String(e));}})();", null);
            return;
        }

        if (url.startsWith("data:")) {
            int comma = url.indexOf(',');
            if (comma > 0) {
                String meta = url.substring(5, comma), data = url.substring(comma + 1);
                if (meta.contains(";base64")) {
                    String type = meta.substring(0, meta.indexOf(';'));
                    saveBase64File(filename, type, data);
                    return;
                }
            }
        }

        downloadUrlToPicker(url, filename, mimeType);
    }

    private void downloadUrlToPicker(String url, String filename, String mimeType) {
        final String requestedMime = mimeType;
        new Thread(() -> {
            HttpURLConnection conn = null;
            try {
                conn = (HttpURLConnection) new URL(url).openConnection();
                conn.setInstanceFollowRedirects(true);
                conn.setConnectTimeout(20000);
                conn.setReadTimeout(60000);
                String cookie = CookieManager.getInstance().getCookie(url);
                if (cookie != null) conn.setRequestProperty("Cookie", cookie);
                String ua = webView.getSettings().getUserAgentString();
                if (ua != null) conn.setRequestProperty("User-Agent", ua);
                int code = conn.getResponseCode();
                if (code < 200 || code >= 400) throw new Exception("HTTP " + code);
                String ct = conn.getContentType();
                String resolvedMime = requestedMime;
                if (resolvedMime == null || resolvedMime.isEmpty() || "application/octet-stream".equalsIgnoreCase(resolvedMime)) {
                    if (ct != null && !ct.isEmpty()) resolvedMime = ct.split(";")[0].trim();
                }
                ByteArrayOutputStream out = new ByteArrayOutputStream();
                InputStream in = conn.getInputStream();
                try (InputStream input = in) {
                    byte[] buf = new byte[8192]; int n;
                    while ((n = input.read(buf)) != -1) out.write(buf, 0, n);
                }
                byte[] bytes = out.toByteArray();
                runOnUiThread(() -> openSavePicker(bytes, filename, resolvedMime));
            } catch (Exception e) {
                final String msg = e.getMessage() == null ? "Gagal mengunduh file" : e.getMessage();
                runOnUiThread(() -> Toast.makeText(MainActivity.this, "Download gagal: " + msg, Toast.LENGTH_LONG).show());
            } finally { if (conn != null) conn.disconnect(); }
        }).start();
    }

    private void openSavePicker(byte[] bytes, String filename, String mime) {
        pendingSaveBytes = bytes; pendingSaveName = filename; pendingSaveMime = mime == null ? "application/octet-stream" : mime;
        if (Build.VERSION.SDK_INT >= 19) {
            Intent i = new Intent(Intent.ACTION_CREATE_DOCUMENT);
            i.addCategory(Intent.CATEGORY_OPENABLE); i.setType(pendingSaveMime); i.putExtra(Intent.EXTRA_TITLE, pendingSaveName);
            try { startActivityForResult(i, SAVE_FILE); return; } catch (ActivityNotFoundException ignored) {}
        }
        saveToDownloadsLegacy(pendingSaveBytes, pendingSaveName, pendingSaveMime);
        pendingSaveBytes = null; pendingSaveName = null; pendingSaveMime = null;
    }

    private void saveToDownloadsLegacy(byte[] bytes, String name, String mime) {
        try {
            ContentValues v = new ContentValues(); v.put(MediaStore.MediaColumns.DISPLAY_NAME, name); v.put(MediaStore.MediaColumns.MIME_TYPE, mime);
            if (Build.VERSION.SDK_INT >= 29) v.put(MediaStore.MediaColumns.RELATIVE_PATH, "Download");
            Uri u = getContentResolver().insert(MediaStore.Files.getContentUri("external"), v);
            if (u != null) { try (OutputStream os = getContentResolver().openOutputStream(u)) { os.write(bytes); } Toast.makeText(this, "File tersimpan: " + name, Toast.LENGTH_LONG).show(); }
        } catch (Exception e) { Toast.makeText(this, "Gagal menyimpan: " + e.getMessage(), Toast.LENGTH_LONG).show(); }
    }

    @Override protected void onActivityResult(int requestCode, int resultCode, Intent data) {
        super.onActivityResult(requestCode, resultCode, data);
        if (requestCode == SAVE_FILE) {
            if (resultCode == RESULT_OK && data != null && data.getData() != null && pendingSaveBytes != null) {
                try (OutputStream os = getContentResolver().openOutputStream(data.getData())) { os.write(pendingSaveBytes); Toast.makeText(this, "File tersimpan: " + pendingSaveName, Toast.LENGTH_LONG).show(); }
                catch (Exception e) { Toast.makeText(this, "Gagal menyimpan: " + e.getMessage(), Toast.LENGTH_LONG).show(); }
            }
            pendingSaveBytes = null; pendingSaveName = null; pendingSaveMime = null;
            return;
        }
        if (requestCode != FILE_CHOOSER || fileCallback == null) return;
        Uri[] results = null;
        if (resultCode == RESULT_OK) {
            if (data != null && data.getClipData() != null) {
                int n = data.getClipData().getItemCount(); results = new Uri[n];
                for (int i = 0; i < n; i++) results[i] = data.getClipData().getItemAt(i).getUri();
            } else if (data != null && data.getData() != null) results = new Uri[]{data.getData()};
            else if (pendingCameraUri != null) results = new Uri[]{pendingCameraUri};
        }
        if (results == null && resultCode == RESULT_OK && pendingCameraUri != null) results = new Uri[]{pendingCameraUri};
        fileCallback.onReceiveValue(results); fileCallback = null; pendingCameraUri = null;
    }

    private Uri createCameraUri() {
        try {
            ContentValues v = new ContentValues(); v.put(MediaStore.Images.Media.DISPLAY_NAME, "ALLSTT_" + System.currentTimeMillis() + ".jpg"); v.put(MediaStore.Images.Media.MIME_TYPE, "image/jpeg");
            if (Build.VERSION.SDK_INT >= 29) v.put(MediaStore.Images.Media.RELATIVE_PATH, "Pictures/ALLSTT");
            return getContentResolver().insert(MediaStore.Images.Media.EXTERNAL_CONTENT_URI, v);
        } catch (Exception e) { return null; }
    }

    private void saveBase64File(String name, String mime, String base64) {
        try {
            byte[] bytes = Base64.decode(base64, Base64.DEFAULT);
            openSavePicker(bytes, name, mime);
        } catch (Exception e) { Toast.makeText(this, "Gagal memproses file: " + e.getMessage(), Toast.LENGTH_LONG).show(); }
    }

    public class AndroidBridge {
        @JavascriptInterface public void saveBase64File(String name, String mime, String base64) { runOnUiThread(() -> MainActivity.this.saveBase64File(name, mime, base64)); }
        @JavascriptInterface public void saveBlobUrl(String url, String name) { runOnUiThread(() -> webView.evaluateJavascript("(async()=>{try{const r=await fetch("+org.json.JSONObject.quote(url)+");const b=await r.blob();const fr=new FileReader();fr.onload=()=>Android.saveBase64File("+org.json.JSONObject.quote(name)+", "+org.json.JSONObject.quote(b.type||'application/octet-stream')+", fr.result.split(',')[1]);fr.readAsDataURL(b);}catch(e){Android.downloadError(String(e));}})();", null)); }
        @JavascriptInterface public void downloadError(String message) { runOnUiThread(() -> Toast.makeText(MainActivity.this, message == null ? "Download gagal" : message, Toast.LENGTH_LONG).show()); }
    }

    @Override public void onBackPressed() {
        if (webView != null && webView.canGoBack()) webView.goBack(); else super.onBackPressed();
    }
}
