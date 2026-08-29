package com.sapammeded.allstt;

import android.Manifest;
import android.app.Activity;
import android.app.DownloadManager;
import android.content.ActivityNotFoundException;
import android.content.ContentValues;
import android.content.Intent;
import android.content.pm.PackageManager;
import android.net.Uri;
import android.os.Build;
import android.os.Bundle;
import android.os.Environment;
import android.provider.MediaStore;
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
import android.util.Base64;

import java.io.File;
import java.io.FileOutputStream;
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

        webView.addJavascriptInterface(new AndroidBridge(), "Android");
        webView.setWebViewClient(new WebViewClient());
        webView.setWebChromeClient(new WebChromeClient() {
            @Override public boolean onShowFileChooser(WebView view, ValueCallback<Uri[]> callback, FileChooserParams params) {
                if (fileCallback != null) fileCallback.onReceiveValue(null);
                fileCallback = callback;

                // IMPORTANT: capture-enabled inputs are camera inputs. Use a chooser
                // containing only ACTION_IMAGE_CAPTURE apps, so Gallery is never shown
                // when the user presses KAMERA HP. Normal file inputs keep the picker.
                if (params.isCaptureEnabled()) {
                    Intent cameraOnly = new Intent(MediaStore.ACTION_IMAGE_CAPTURE);
                    if (cameraOnly.resolveActivity(getPackageManager()) == null) {
                        fileCallback.onReceiveValue(null);
                        fileCallback = null;
                        Toast.makeText(MainActivity.this, "Tidak ada aplikasi kamera", Toast.LENGTH_SHORT).show();
                        return true;
                    }

                    pendingCameraUri = createCameraUri();
                    if (pendingCameraUri != null) {
                        cameraOnly.putExtra(MediaStore.EXTRA_OUTPUT, pendingCameraUri);
                    }
                    cameraOnly.addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION | Intent.FLAG_GRANT_WRITE_URI_PERMISSION);

                    if (Build.VERSION.SDK_INT >= 23 && checkSelfPermission(Manifest.permission.CAMERA) != PackageManager.PERMISSION_GRANTED) {
                        requestPermissions(new String[]{Manifest.permission.CAMERA}, CAMERA_PERMISSION);
                    }

                    try {
                        Intent chooser = Intent.createChooser(cameraOnly, "Pilih aplikasi kamera");
                        startActivityForResult(chooser, FILE_CHOOSER);
                    } catch (ActivityNotFoundException e) {
                        if (pendingCameraUri != null) {
                            try { getContentResolver().delete(pendingCameraUri, null, null); } catch (Exception ignored) {}
                        }
                        pendingCameraUri = null;
                        fileCallback.onReceiveValue(null);
                        fileCallback = null;
                        Toast.makeText(MainActivity.this, "Tidak ada aplikasi kamera", Toast.LENGTH_SHORT).show();
                    }
                    return true;
                }

                Intent picker;
                try { picker = params.createIntent(); }
                catch (Exception e) { picker = new Intent(Intent.ACTION_GET_CONTENT); }
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
                if (camera.resolveActivity(getPackageManager()) != null)
                    chooser.putExtra(Intent.EXTRA_INITIAL_INTENTS, new Intent[]{camera});
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

            @Override public void onPermissionRequest(PermissionRequest request) {
                runOnUiThread(() -> request.grant(request.getResources()));
            }

            @Override public void onGeolocationPermissionsShowPrompt(String origin, GeolocationPermissions.Callback callback) {
                callback.invoke(origin, true, false);
            }
        });

        webView.setDownloadListener((url, userAgent, contentDisposition, mimeType, contentLength) -> handleWebDownload(url, contentDisposition, mimeType));
    }

    private void handleWebDownload(String url, String contentDisposition, String mimeType) {
        if (url == null || url.isEmpty()) return;
        String filename = "ALLSTT_Download";
        if (contentDisposition != null) {
            int p = contentDisposition.indexOf("filename=");
            if (p >= 0) {
                filename = contentDisposition.substring(p + 9).replace("\"", "").trim();
            }
        }
        if (filename.equals("ALLSTT_Download") && mimeType != null) {
            String ext = MimeTypeMap.getSingleton().getExtensionFromMimeType(mimeType);
            if (ext != null && !ext.isEmpty()) filename += "." + ext;
        }

        if (url.startsWith("blob:")) {
            final String safeUrl = org.json.JSONObject.quote(url);
            final String safeName = org.json.JSONObject.quote(filename);
            final String safeMime = org.json.JSONObject.quote(mimeType == null ? "application/octet-stream" : mimeType);
            webView.evaluateJavascript("(async()=>{try{const r=await fetch("+safeUrl+");const b=await r.blob();const fr=new FileReader();fr.onload=()=>Android.saveBase64File("+safeName+","+safeMime+",fr.result.split(',')[1]);fr.readAsDataURL(b);}catch(e){Android.downloadError(String(e));}})();", null);
            return;
        }

        if (url.startsWith("data:")) {
            int comma = url.indexOf(',');
            if (comma > 0) {
                String meta = url.substring(5, comma);
                String data = url.substring(comma + 1);
                if (meta.contains(";base64")) {
                    String type = meta.substring(0, meta.indexOf(';'));
                    new AndroidBridge().saveBase64File(filename, type, data);
                    return;
                }
            }
        }

        try {
            DownloadManager.Request request = new DownloadManager.Request(Uri.parse(url));
            request.setTitle(filename);
            request.setDescription("ALLSTT");
            request.setNotificationVisibility(DownloadManager.Request.VISIBILITY_VISIBLE_NOTIFY_COMPLETED);
            request.setMimeType(mimeType);
            request.setDestinationInExternalPublicDir(Environment.DIRECTORY_DOWNLOADS, filename);
            ((DownloadManager)getSystemService(DOWNLOAD_SERVICE)).enqueue(request);
            Toast.makeText(this, "Download dimulai: " + filename, Toast.LENGTH_SHORT).show();
        } catch (Exception e) {
            Toast.makeText(this, "Gagal memulai download: " + e.getMessage(), Toast.LENGTH_LONG).show();
        }
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
        if (requestCode != FILE_CHOOSER || fileCallback == null) return;
        Uri[] results = null;
        if (resultCode == RESULT_OK) {
            if (data != null && data.getClipData() != null) {
                int count = data.getClipData().getItemCount();
                results = new Uri[count];
                for (int i = 0; i < count; i++) results[i] = data.getClipData().getItemAt(i).getUri();
            } else if (data != null && data.getData() != null) {
                results = new Uri[]{data.getData()};
            } else if (pendingCameraUri != null) {
                results = new Uri[]{pendingCameraUri};
            }
        } else if (pendingCameraUri != null) {
            try { getContentResolver().delete(pendingCameraUri, null, null); } catch (Exception ignored) {}
        }
        fileCallback.onReceiveValue(results);
        fileCallback = null;
        pendingCameraUri = null;
    }

    public class AndroidBridge {
        @JavascriptInterface public void saveBase64File(String filename, String mimeType, String base64) {
            try {
                byte[] bytes = Base64.decode(base64, Base64.DEFAULT);
                String safeName = filename == null || filename.isEmpty() ? "ALLSTT_Download" : filename.replaceAll("[\\\\/:*?\"<>|]", "_");
                if (Build.VERSION.SDK_INT >= 29) {
                    ContentValues values = new ContentValues();
                    values.put(MediaStore.Downloads.DISPLAY_NAME, safeName);
                    values.put(MediaStore.Downloads.MIME_TYPE, mimeType == null ? "application/octet-stream" : mimeType);
                    values.put(MediaStore.Downloads.RELATIVE_PATH, Environment.DIRECTORY_DOWNLOADS);
                    Uri uri = getContentResolver().insert(MediaStore.Downloads.EXTERNAL_CONTENT_URI, values);
                    if (uri == null) throw new Exception("Tidak dapat membuat file Downloads");
                    try (OutputStream out = getContentResolver().openOutputStream(uri)) { out.write(bytes); }
                } else {
                    File dir = Environment.getExternalStoragePublicDirectory(Environment.DIRECTORY_DOWNLOADS);
                    if (!dir.exists()) dir.mkdirs();
                    try (FileOutputStream out = new FileOutputStream(new File(dir, safeName))) { out.write(bytes); }
                }
                runOnUiThread(() -> Toast.makeText(MainActivity.this, "PDF berhasil disimpan ke Download: " + safeName, Toast.LENGTH_LONG).show());
            } catch (Exception e) {
                downloadError(e.getMessage());
            }
        }

        @JavascriptInterface public void downloadError(String message) {
            runOnUiThread(() -> Toast.makeText(MainActivity.this, "Download gagal: " + message, Toast.LENGTH_LONG).show());
        }
    }

    @Override public void onBackPressed() {
        if (webView.canGoBack()) webView.goBack(); else super.onBackPressed();
    }
}