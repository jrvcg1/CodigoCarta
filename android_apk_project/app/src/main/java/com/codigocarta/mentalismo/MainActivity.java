package com.codigocarta.mentalismo;

import android.app.Activity;
import android.os.Bundle;
import android.os.Handler;
import android.os.Looper;
import android.view.View;
import android.view.WindowManager;
import android.webkit.JavascriptInterface;
import android.webkit.WebChromeClient;
import android.webkit.WebSettings;
import android.webkit.WebView;
import android.webkit.WebViewClient;
import java.io.BufferedReader;
import java.io.InputStreamReader;
import java.net.HttpURLConnection;
import java.net.URL;
import org.json.JSONObject;

public class MainActivity extends Activity {

    public WebView webView;
    public float currentBrightness = 0.30f;
    public Handler handler = new Handler(Looper.getMainLooper());
    public boolean isPollingActive = true;
    public String lastVersion = null;
    public String lastUpdatedAt = null;
    public String currentApiUrl = "https://codigo-carta.vercel.app/api/carta_actual";

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);

        getWindow().addFlags(WindowManager.LayoutParams.FLAG_KEEP_SCREEN_ON);
        getWindow().addFlags(WindowManager.LayoutParams.FLAG_FULLSCREEN);
        
        applyBrightness(currentBrightness);
        setImmersiveMode();

        setContentView(R.layout.activity_main);

        webView = (WebView) findViewById(R.id.webView);
        configureWebView();

        new PollingWorker(this).start();
    }

    public void applyBrightness(float val) {
        try {
            WindowManager.LayoutParams lp = getWindow().getAttributes();
            lp.screenBrightness = Math.max(0.05f, Math.min(1.0f, val));
            getWindow().setAttributes(lp);
        } catch (Exception e) {
            e.printStackTrace();
        }
    }

    private void setImmersiveMode() {
        View decorView = getWindow().getDecorView();
        decorView.setSystemUiVisibility(
                View.SYSTEM_UI_FLAG_LAYOUT_STABLE
                        | View.SYSTEM_UI_FLAG_LAYOUT_HIDE_NAVIGATION
                        | View.SYSTEM_UI_FLAG_LAYOUT_FULLSCREEN
                        | View.SYSTEM_UI_FLAG_HIDE_NAVIGATION
                        | View.SYSTEM_UI_FLAG_FULLSCREEN
                        | View.SYSTEM_UI_FLAG_IMMERSIVE_STICKY
        );
    }

    @Override
    public void onWindowFocusChanged(boolean hasFocus) {
        super.onWindowFocusChanged(hasFocus);
        if (hasFocus) {
            setImmersiveMode();
        }
    }

    private void configureWebView() {
        WebSettings webSettings = webView.getSettings();
        webSettings.setJavaScriptEnabled(true);
        webSettings.setDomStorageEnabled(true);
        webSettings.setAllowFileAccess(true);
        webSettings.setAllowContentAccess(true);
        webSettings.setAllowFileAccessFromFileURLs(true);
        webSettings.setAllowUniversalAccessFromFileURLs(true);
        webSettings.setMediaPlaybackRequiresUserGesture(false);
        webSettings.setDatabaseEnabled(true);
        webSettings.setCacheMode(WebSettings.LOAD_DEFAULT);

        webView.addJavascriptInterface(new WebAppInterface(this), "Android");
        webView.setWebViewClient(new CustomWebViewClient());
        webView.setWebChromeClient(new WebChromeClient());

        webView.loadUrl("file:///android_asset/marco_analogico.html");
    }

    public void triggerCardReveal(String val, String suit) {
        isPollingActive = false;
        handler.post(new RevealRunnable(this, val, suit));
    }
}

class CustomWebViewClient extends WebViewClient {
    @Override
    public boolean shouldOverrideUrlLoading(WebView view, String url) {
        view.loadUrl(url);
        return true;
    }
}

class WebAppInterface {
    private final MainActivity activity;

    public WebAppInterface(MainActivity act) {
        this.activity = act;
    }

    @JavascriptInterface
    public void setBrightness(final float val) {
        if (activity != null) {
            activity.handler.post(new BrightnessRunnable(activity, val));
        }
    }

    @JavascriptInterface
    public void setApiUrl(final String url) {
        if (activity != null && url != null && url.length() > 0) {
            activity.currentApiUrl = url;
        }
    }
}

class RevealRunnable implements Runnable {
    private final MainActivity activity;
    private final String valor;
    private final String suit;

    public RevealRunnable(MainActivity act, String v, String s) {
        this.activity = act;
        this.valor = v;
        this.suit = s;
    }

    @Override
    public void run() {
        if (activity != null && activity.webView != null) {
            activity.webView.evaluateJavascript("if(window.revealCard){window.revealCard('" + valor + "','" + suit + "');}", null);
        }
    }
}

class BrightnessRunnable implements Runnable {
    private final MainActivity activity;
    private final float val;

    public BrightnessRunnable(MainActivity act, float v) {
        this.activity = act;
        this.val = v;
    }

    @Override
    public void run() {
        if (activity != null) {
            activity.applyBrightness(val);
        }
    }
}

class PollingWorker extends Thread {
    private final MainActivity activity;

    public PollingWorker(MainActivity act) {
        this.activity = act;
    }

    @Override
    public void run() {
        while (true) {
            try {
                Thread.sleep(4000);
                if (activity == null || !activity.isPollingActive) continue;

                String urlStr = activity.currentApiUrl;
                if (!urlStr.contains("?")) {
                    urlStr += "?_t=" + System.currentTimeMillis();
                } else {
                    urlStr += "&_t=" + System.currentTimeMillis();
                }

                URL url = new URL(urlStr);
                HttpURLConnection conn = (HttpURLConnection) url.openConnection();
                conn.setRequestMethod("GET");
                conn.setConnectTimeout(5000);
                conn.setReadTimeout(5000);
                conn.setRequestProperty("Accept", "application/json");

                int code = conn.getResponseCode();
                if (code == 200) {
                    BufferedReader in = new BufferedReader(new InputStreamReader(conn.getInputStream()));
                    StringBuilder sb = new StringBuilder();
                    String line;
                    while ((line = in.readLine()) != null) {
                        sb.append(line);
                    }
                    in.close();

                    JSONObject json = new JSONObject(sb.toString());
                    String version = json.optString("version", "");
                    String updated = json.optString("updated_at", "");
                    String valor = json.optString("valor", "");
                    String suit = json.optString("palo_id", "");

                    if (activity.lastVersion == null && activity.lastUpdatedAt == null) {
                        activity.lastVersion = version;
                        activity.lastUpdatedAt = updated;
                    } else {
                        boolean verDiff = (version.length() > 0 && !version.equals(activity.lastVersion));
                        boolean timeDiff = (updated.length() > 0 && !updated.equals(activity.lastUpdatedAt));
                        if ((verDiff || timeDiff) && valor.length() > 0 && suit.length() > 0) {
                            activity.lastVersion = version;
                            activity.lastUpdatedAt = updated;
                            activity.triggerCardReveal(valor, suit);
                        }
                    }
                }
            } catch (Exception e) {
                // retry
            }
        }
    }
}
