package com.sapammeded.allstt;

import android.os.Bundle;
import android.view.View;
import android.view.ViewGroup;
import android.webkit.JavascriptInterface;
import android.webkit.WebView;

import java.io.ByteArrayOutputStream;
import java.io.InputStream;
import java.io.OutputStream;
import java.net.HttpURLConnection;
import java.net.URL;
import java.nio.charset.StandardCharsets;

/** Native transport layer for HVSS CENTRAL. */
public class MainActivityGenius extends MainActivity {
    private WebView hvssWebView;

    @Override protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        hvssWebView = findWebView(getWindow().getDecorView());
        if (hvssWebView != null) {
            hvssWebView.addJavascriptInterface(new CentralBridge(), "AndroidCentral");
            // addJavascriptInterface becomes visible after the next document load.
            // MainActivity has already started launcher.html in super.onCreate();
            // load it once more after the bridge is registered so every module gets
            // AndroidCentral from the first script execution.
            hvssWebView.loadUrl("file:///android_asset/launcher.html");
        }
    }

    private WebView findWebView(View v) {
        if (v instanceof WebView) return (WebView) v;
        if (v instanceof ViewGroup) {
            ViewGroup g = (ViewGroup) v;
            for (int i = 0; i < g.getChildCount(); i++) {
                WebView w = findWebView(g.getChildAt(i));
                if (w != null) return w;
            }
        }
        return null;
    }

    public class CentralBridge {
        @JavascriptInterface
        public void getCentral(String gasUrl, String spreadsheetId, String requestId) {
            try {
                URL base = new URL(gasUrl);
                if (!allowedHost(base.getHost())) throw new Exception("Host CENTRAL tidak diizinkan");
                String sep = gasUrl.contains("?") ? "&" : "?";
                String url = gasUrl + sep + "action=getCentral&spreadsheetId=" +
                        java.net.URLEncoder.encode(spreadsheetId, "UTF-8") +
                        "&_=" + System.currentTimeMillis();
                String result = unwrapJsonp(request(url, "GET", null));
                finish(requestId, true, result);
            } catch (Exception e) {
                finish(requestId, false, e.getMessage());
            }
        }

        @JavascriptInterface
        public void postCentral(String gasUrl, String body, String requestId) {
            try {
                URL base = new URL(gasUrl);
                if (!allowedHost(base.getHost())) throw new Exception("Host CENTRAL tidak diizinkan");
                String result = request(gasUrl, "POST", body == null ? "" : body);
                finish(requestId, true, result);
            } catch (Exception e) {
                finish(requestId, false, e.getMessage());
            }
        }

        private boolean allowedHost(String host) {
            return "script.google.com".equalsIgnoreCase(host) ||
                    "script.googleusercontent.com".equalsIgnoreCase(host);
        }

        private String request(String target, String method, String body) throws Exception {
            String current = target;
            String currentMethod = method;
            String currentBody = body;
            for (int redirects = 0; redirects < 6; redirects++) {
                HttpURLConnection c = (HttpURLConnection) new URL(current).openConnection();
                c.setInstanceFollowRedirects(false);
                c.setConnectTimeout(20000);
                c.setReadTimeout(60000);
                c.setRequestProperty("User-Agent", "ALLSTT-HVSS-Native/1.0");
                c.setRequestProperty("Accept", "application/json, application/javascript, text/javascript, */*");
                c.setRequestProperty("Accept-Language", "id-ID,id;q=0.9,en;q=0.7");
                c.setRequestMethod(currentMethod);
                if ("POST".equals(currentMethod)) {
                    c.setDoOutput(true);
                    c.setRequestProperty("Content-Type", "text/plain;charset=utf-8");
                    byte[] bytes = currentBody == null ? new byte[0] : currentBody.getBytes(StandardCharsets.UTF_8);
                    c.setFixedLengthStreamingMode(bytes.length);
                    try (OutputStream out = c.getOutputStream()) { out.write(bytes); }
                }
                int code = c.getResponseCode();
                if (code >= 300 && code < 400) {
                    String location = c.getHeaderField("Location");
                    c.disconnect();
                    if (location == null || location.isEmpty()) throw new Exception("Redirect CENTRAL tanpa Location");
                    URL next = new URL(new URL(current), location);
                    if (!allowedHost(next.getHost())) throw new Exception("Redirect CENTRAL menuju host tidak diizinkan");
                    current = next.toString();
                    // Apps Script Content Service redirects after handling the request.
                    // Preserve POST only for redirects that explicitly preserve the method.
                    if (code != 307 && code != 308) { currentMethod = "GET"; currentBody = null; }
                    continue;
                }
                InputStream in = (code >= 200 && code < 400) ? c.getInputStream() : c.getErrorStream();
                if (in == null) throw new Exception("HTTP " + code);
                ByteArrayOutputStream out = new ByteArrayOutputStream();
                try (InputStream input = in) {
                    byte[] buf = new byte[8192]; int n;
                    while ((n = input.read(buf)) != -1) out.write(buf, 0, n);
                }
                String text = out.toString(StandardCharsets.UTF_8.name());
                c.disconnect();
                if (code < 200 || code >= 300) throw new Exception("HTTP " + code + (text.isEmpty() ? "" : ": " + text));
                return text;
            }
            throw new Exception("Terlalu banyak redirect CENTRAL");
        }

        private String unwrapJsonp(String text) {
            if (text == null) return "null";
            String t = text.trim();
            if (t.startsWith("{") || t.startsWith("[")) return t;
            int open = t.indexOf('(');
            int close = t.lastIndexOf(')');
            if (open >= 0 && close > open) return t.substring(open + 1, close).trim();
            return t;
        }

        private void finish(String requestId, boolean ok, String data) {
            final String id = org.json.JSONObject.quote(requestId == null ? "" : requestId);
            final String payload = org.json.JSONObject.quote(data == null ? "" : data);
            final String js = "window.__HVSS_NATIVE_CENTRAL_RESOLVE(" + id + "," + ok + "," + payload + ");";
            runOnUiThread(() -> {
                if (hvssWebView != null) hvssWebView.evaluateJavascript(js, null);
            });
        }
    }
}
