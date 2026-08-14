package com.codigocarta.mentalismo;

import android.app.Activity;
import android.content.pm.PackageManager;
import android.os.Build;
import android.os.Bundle;
import android.view.View;
import android.view.WindowManager;
import android.webkit.JavascriptInterface;
import android.webkit.PermissionRequest;
import android.webkit.WebChromeClient;
import android.webkit.WebSettings;
import android.webkit.WebView;
import android.webkit.WebViewClient;
import android.widget.Toast;

public class MainActivity extends Activity {

    private static final int REQUEST_MIC_PERMISSION = 101;
    private WebView webView;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);

        // --- PANTALLA COMPLETA E INMERSIVA Y MANTENER PANTALLA ENCENDIDA ---
        getWindow().addFlags(WindowManager.LayoutParams.FLAG_KEEP_SCREEN_ON);
        getWindow().addFlags(WindowManager.LayoutParams.FLAG_FULLSCREEN);
        setImmersiveMode();

        setContentView(R.layout.activity_main);

        webView = findViewById(R.id.webView);
        configureWebView();

        checkPermissions();
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
        webSettings.setMediaPlaybackRequiresUserGesture(false);
        webSettings.setDatabaseEnabled(true);

        webView.addJavascriptInterface(new WebAppInterface(this), "Android");

        webView.setWebViewClient(new CustomWebViewClient());
        webView.setWebChromeClient(new CustomWebChromeClient(this));

        webView.loadUrl("https://codigo-carta.vercel.app/probar_voz");
    }

    private void checkPermissions() {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.M) {
            if (checkSelfPermission(android.Manifest.permission.RECORD_AUDIO) != PackageManager.PERMISSION_GRANTED) {
                requestPermissions(new String[]{android.Manifest.permission.RECORD_AUDIO}, REQUEST_MIC_PERMISSION);
            }
        }
    }

    @Override
    public void onRequestPermissionsResult(int requestCode, String[] permissions, int[] grantResults) {
        super.onRequestPermissionsResult(requestCode, permissions, grantResults);
        if (requestCode == REQUEST_MIC_PERMISSION) {
            if (grantResults.length > 0 && grantResults[0] == PackageManager.PERMISSION_GRANTED) {
                Toast.makeText(this, "Permiso de Micrófono Concedido", Toast.LENGTH_SHORT).show();
                webView.reload();
            } else {
                Toast.makeText(this, "Permiso de Micrófono requerido", Toast.LENGTH_LONG).show();
            }
        }
    }
}

class CustomWebViewClient extends WebViewClient {
    @Override
    public boolean shouldOverrideUrlLoading(WebView view, String url) {
        view.loadUrl(url);
        return true;
    }
}

class CustomWebChromeClient extends WebChromeClient {
    private final Activity activity;

    public CustomWebChromeClient(Activity act) {
        this.activity = act;
    }

    @Override
    public void onPermissionRequest(final PermissionRequest request) {
        activity.runOnUiThread(new GrantPermissionRunnable(request));
    }
}

class GrantPermissionRunnable implements Runnable {
    private final PermissionRequest request;

    public GrantPermissionRunnable(PermissionRequest req) {
        this.request = req;
    }

    @Override
    public void run() {
        request.grant(request.getResources());
    }
}

class WebAppInterface {
    private final Activity activity;

    public WebAppInterface(Activity act) {
        this.activity = act;
    }

    @JavascriptInterface
    public void setBrightness(final float val) {
        activity.runOnUiThread(new SetBrightnessRunnable(activity, val));
    }
}

class SetBrightnessRunnable implements Runnable {
    private final Activity activity;
    private final float val;

    public SetBrightnessRunnable(Activity act, float v) {
        this.activity = act;
        this.val = v;
    }

    @Override
    public void run() {
        WindowManager.LayoutParams lp = activity.getWindow().getAttributes();
        if (val <= 0.05f) {
            lp.screenBrightness = 0.01f;
        } else {
            lp.screenBrightness = WindowManager.LayoutParams.BRIGHTNESS_OVERRIDE_NONE;
        }
        activity.getWindow().setAttributes(lp);
    }
}
