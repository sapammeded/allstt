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
import android.provider.DocumentsContract;
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
import java.io.File;
import java.io.FileOutputStream;
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

    private WebView webView;
    private ValueCallback<Uri[]> fileCallback;
    private Uri pendingCameraUri;

    private byte[] pendingSaveBytes;
    private String pendingSaveName;
    private String pendingSaveMime;

    @Override protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        webView = new WebView(this);
        setContentView(webView);
        configureWebView();
        webView.loadUrl("file:///android_asset/launcher.html");
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
        webView.setWebViewClient(new WebViewClient());
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
            @Override public void onGeolocationPermissionsShowPrompt(String origin, GeolocationPermissions.Callback callback) { callback.invoke(origin, true, false); }
        });

        webView.setDownloadListener((url, userAgent, contentDisposition, mimeType, contentLength) -> handleWebDownload(url, contentDisposition, mimeType));
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
                "const ds=/^\\d{4}-\\d{2}-\\d{2}$/.test(d)?d.split('-').reverse().join('-'):'';" +
                "const safe=v=>String(v||'').replace(/[\\\\/:*?\"<>|]/g,'-').replace(/\\s+/g,'_').slice(0,80);" +
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
                if (mimeType == null || mimeType.isEmpty()) mimeType = ct;
                ByteArrayOutputStream out = new ByteArrayOutputStream();
                try (InputStream in = conn.getInputStream()) {
                    byte[] buf = new byte[8192]; int n;
                    while ((n = in.read(buf)) != -1) out.write(buf, 0, n);
                }
                final byte[] bytes = out.toByteArray();
                final String finalMime = mimeType == null ? "application/octet-stream" : mimeType;
                runOnUiThread(() -> openSavePicker(bytes, filename, finalMime));
            } catch (Exception e) {
                runOnUiThread(() -> Toast.makeText(MainActivity.this, "Download gagal: " + e.getMessage(), Toast.LENGTH_LONG).show());
            } finally { if (conn != null) conn.disconnect(); }
        }).start();
    }

    private void openSavePicker(byte[] bytes, String filename, String mimeType) {
        pendingSaveBytes = bytes;
        pendingSaveName = filename == null || filename.isEmpty() ? "ALLSTT_Download" : filename.replaceAll("[\\\\/:*?\"<>|]", "_");
        pendingSaveMime = mimeType == null || mimeType.isEmpty() ? "application/octet-stream" : mimeType;
        try {
            Intent intent = new Intent(Intent.ACTION_CREATE_DOCUMENT);
            intent.addCategory(Intent.CATEGORY_OPENABLE);
            intent.setType(pendingSaveMime);
            intent.putExtra(Intent.EXTRA_TITLE, pendingSaveName);
            startActivityForResult(intent, SAVE_FILE);
        } catch (ActivityNotFoundException e) {
            pendingSaveBytes = null;
            Toast.makeText(this, "File picker tidak tersedia", Toast.LENGTH_LONG).show();
        }
    }

    private void saveSelectedFile(Uri uri) {
        if (uri == null || pendingSaveBytes == null) return;
        try (OutputStream out = getContentResolver().openOutputStream(uri)) {
            if (out == null) throw new Exception("Tidak dapat membuka lokasi tujuan");
            out.write(pendingSaveBytes);
            Toast.makeText(this, "File berhasil disimpan", Toast.LENGTH_LONG).show();
        } catch (Exception e) {
            Toast.makeText(this, "Gagal menyimpan: " + e.getMessage(), Toast.LENGTH_LONG).show();
        } finally {
            pendingSaveBytes = null; pendingSaveName = null; pendingSaveMime = null;
        }
    }

    private void saveBase64File(String filename, String mimeType, String base64) {
        try {
            byte[] bytes = Base64.decode(base64, Base64.DEFAULT);
            runOnUiThread(() -> openSavePicker(bytes, filename, mimeType));
        } catch (Exception e) { downloadError(e.getMessage()); }
    }

    private Uri createCameraUri() {
        String name = "ALLSTT_" + System.currentTimeMillis() + ".jpg";
        ContentValues v = new ContentValues();
        v.put(MediaStore.Images.Media.DISPLAY_NAME, name);
        v.put(MediaStore.Images.Media.MIME_TYPE, "image/jpeg");
        if (Build.VERSION.SDK_INT >= 29) v.put(MediaStore.Images.Media.RELATIVE_PATH, "Pictures/ALLSTT");
        return getContentResolver().insert(MediaStore.Images.Media.EXTERNAL_CONTENT_URI, v);
    }

    @Override protected void onActivityResult(int requestCode, int resultCode, Intent data) {
        super.onActivityResult(requestCode, resultCode, data);
        if (requestCode == SAVE_FILE) {
            if (resultCode == RESULT_OK && data != null) saveSelectedFile(data.getData());
            else { pendingSaveBytes = null; pendingSaveName = null; pendingSaveMime = null; }
            return;
        }
        if (requestCode != FILE_CHOOSER || fileCallback == null) return;
        Uri[] results = null;
        if (resultCode == RESULT_OK) {
            if (data != null && data.getClipData() != null) {
                int count = data.getClipData().getItemCount(); results = new Uri[count];
                for (int i = 0; i < count; i++) results[i] = data.getClipData().getItemAt(i).getUri();
            } else if (data != null && data.getData() != null) results = new Uri[]{data.getData()};
            else if (pendingCameraUri != null) results = new Uri[]{pendingCameraUri};
        } else if (pendingCameraUri != null) {
            try { getContentResolver().delete(pendingCameraUri, null, null); } catch (Exception ignored) {}
        }
        fileCallback.onReceiveValue(results); fileCallback = null; pendingCameraUri = null;
    }

    public class AndroidBridge {
        @JavascriptInterface public void saveBase64File(String filename, String mimeType, String base64) { MainActivity.this.saveBase64File(filename, mimeType, base64); }
        @JavascriptInterface public void downloadError(String message) { MainActivity.this.downloadError(message); }
    }

    private void downloadError(String message) {
        runOnUiThread(() -> Toast.makeText(MainActivity.this, "Download gagal: " + message, Toast.LENGTH_LONG).show());
    }

    @Override public void onBackPressed() {
        if (webView.canGoBack()) webView.goBack(); else super.onBackPressed();
    }
}
