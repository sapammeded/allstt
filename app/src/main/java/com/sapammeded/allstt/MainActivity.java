package com.sapammeded.allstt;

import android.Manifest;
import android.app.Activity;
import android.app.DownloadManager;
import android.content.ActivityNotFoundException;
import android.content.ClipData;
import android.content.Intent;
import android.content.pm.PackageManager;
import android.net.Uri;
import android.os.Build;
import android.os.Bundle;
import android.os.Environment;
import android.provider.MediaStore;
import android.util.Base64;
import android.webkit.CookieManager;
import android.webkit.GeolocationPermissions;
import android.webkit.JavascriptInterface;
import android.webkit.MimeTypeMap;
import android.webkit.PermissionRequest;
import android.webkit.ValueCallback;
import android.webkit.WebChromeClient;
import android.webkit.WebView;
import android.webkit.WebViewClient;
import android.webkit.WebSettings;
import android.widget.Toast;
import java.io.OutputStream;

public class MainActivity extends Activity {
    private static final int FILE_CHOOSER = 4101;
    private static final int CAMERA_PERMISSION = 4102;
    private WebView webView;
    private ValueCallback<Uri[]> fileCallback;
    private Uri pendingCameraUri;

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
        webView.addJavascriptInterface(new DownloadBridge(), "Android");
        webView.setWebViewClient(new WebViewClient());
        webView.setWebChromeClient(new WebChromeClient() {
            @Override public boolean onShowFileChooser(WebView view, ValueCallback<Uri[]> callback, FileChooserParams params) {
                if (fileCallback != null) fileCallback.onReceiveValue(null);
                fileCallback = callback;
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
                if (Build.VERSION.SDK_INT >= 23 && checkSelfPermission(Manifest.permission.CAMERA) != PackageManager.PERMISSION_GRANTED) requestPermissions(new String[]{Manifest.permission.CAMERA}, CAMERA_PERMISSION);
                try { startActivityForResult(chooser, FILE_CHOOSER); }
                catch (ActivityNotFoundException e) { fileCallback.onReceiveValue(null); fileCallback = null; Toast.makeText(MainActivity.this, "Tidak ada aplikasi untuk memilih foto", Toast.LENGTH_SHORT).show(); }
                return true;
            }
            @Override public void onPermissionRequest(PermissionRequest request) { runOnUiThread(() -> request.grant(request.getResources())); }
            @Override public void onGeolocationPermissionsShowPrompt(String origin, GeolocationPermissions.Callback callback) { callback.invoke(origin, true, false); }
        });
    }

    private Uri createCameraUri() {
        String name = "ALLSTT_" + System.currentTimeMillis() + ".jpg";
        android.content.ContentValues v = new android.content.ContentValues();
        v.put(MediaStore.Images.Media.DISPLAY_NAME, name);
        v.put(MediaStore.Images.Media.MIME_TYPE, "image/jpeg");
        if (Build.VERSION.SDK_INT >= 29) v.put(MediaStore.Images.Media.RELATIVE_PATH, "Pictures/ALLSTT");
        return getContentResolver().insert(MediaStore.Images.Media.EXTERNAL_CONTENT_URI, v);
    }

    @Override protected void onActivityResult(int requestCode, int resultCode, Intent data) {
        super.onActivityResult(requestCode, resultCode, data);
        if (requestCode != FILE_CHOOSER || fileCallback == null) return;
        Uri[] results = null;
        if (resultCode == RESULT_OK) {
            if (data != null && data.getClipData() != null) {
                ClipData clip = data.getClipData();
                results = new Uri[clip.getItemCount()];
                for (int i = 0; i < clip.getItemCount(); i++) results[i] = clip.getItemAt(i).getUri();
            } else if (data != null && data.getData() != null) results = new Uri[]{data.getData()};
            else if (pendingCameraUri != null) results = new Uri[]{pendingCameraUri};
        } else if (pendingCameraUri != null) { try { getContentResolver().delete(pendingCameraUri, null, null); } catch (Exception ignored) {} }
        fileCallback.onReceiveValue(results);
        fileCallback = null;
        pendingCameraUri = null;
    }

    private class DownloadBridge {
        @JavascriptInterface public void saveBase64(String dataUrl, String filename) {
            try {
                int comma = dataUrl.indexOf(',');
                String meta = comma > 0 ? dataUrl.substring(0, comma) : "data:application/octet-stream;base64";
                String body = comma > 0 ? dataUrl.substring(comma + 1) : dataUrl;
                String mime = "application/octet-stream";
                int colon = meta.indexOf(':'); int semi = meta.indexOf(';');
                if (colon >= 0 && semi > colon) mime = meta.substring(colon + 1, semi);
                byte[] bytes = Base64.decode(body, Base64.DEFAULT);
                String safe = (filename == null || filename.isEmpty()) ? "ALLSTT_Download" : filename.replaceAll("[^A-Za-z0-9._-]", "_");
                if (Build.VERSION.SDK_INT >= 29) {
                    android.content.ContentValues v = new android.content.ContentValues();
                    v.put(MediaStore.Downloads.DISPLAY_NAME, safe);
                    v.put(MediaStore.Downloads.MIME_TYPE, mime);
                    v.put(MediaStore.Downloads.RELATIVE_PATH, Environment.DIRECTORY_DOWNLOADS);
                    Uri uri = getContentResolver().insert(MediaStore.Downloads.EXTERNAL_CONTENT_URI, v);
                    if (uri == null) throw new Exception("Tidak dapat membuat file");
                    try (OutputStream out = getContentResolver().openOutputStream(uri)) { out.write(bytes); }
                }
                runOnUiThread(() -> Toast.makeText(MainActivity.this, "File tersimpan di Download", Toast.LENGTH_SHORT).show());
            } catch (Exception e) { runOnUiThread(() -> Toast.makeText(MainActivity.this, "Gagal menyimpan file", Toast.LENGTH_LONG).show()); }
        }
    }

    @Override public void onBackPressed() { if (webView.canGoBack()) webView.goBack(); else super.onBackPressed(); }
}
