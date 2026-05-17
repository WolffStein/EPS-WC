package br.com.epswc.apreensao

import android.annotation.SuppressLint
import android.app.Activity
import android.content.ActivityNotFoundException
import android.content.Context
import android.content.Intent
import android.graphics.Bitmap
import android.net.Uri
import android.os.Bundle
import android.provider.MediaStore
import android.view.View
import android.webkit.CookieManager
import android.webkit.PermissionRequest
import android.webkit.ValueCallback
import android.webkit.WebChromeClient
import android.webkit.WebResourceRequest
import android.webkit.WebResourceError
import android.webkit.WebView
import android.webkit.WebViewClient
import android.widget.Toast
import androidx.activity.OnBackPressedCallback
import androidx.activity.result.contract.ActivityResultContracts
import androidx.appcompat.app.AppCompatActivity
import android.Manifest
import android.content.pm.PackageManager
import androidx.core.content.ContextCompat
import androidx.core.content.FileProvider
import br.com.epswc.apreensao.databinding.ActivityMainBinding
import java.io.File
import java.text.SimpleDateFormat
import java.util.Date
import java.util.Locale

class MainActivity : AppCompatActivity() {

    private lateinit var binding: ActivityMainBinding
    private lateinit var prefs: android.content.SharedPreferences

    private var filePathCallback: ValueCallback<Array<Uri>>? = null
    private var pendingCameraUri: Uri? = null
    private var lastFileChooserParams: WebChromeClient.FileChooserParams? = null

    private val requestCameraPermissionLauncher =
        registerForActivityResult(ActivityResultContracts.RequestPermission()) { isGranted ->
            launchFileChooser(lastFileChooserParams, isGranted)
        }

    private val fileChooserLauncher =
        registerForActivityResult(ActivityResultContracts.StartActivityForResult()) { result ->
            val callback = filePathCallback
            val resultUris = mutableListOf<Uri>()

            if (result.resultCode == Activity.RESULT_OK) {
                val data = result.data
                when {
                    data?.clipData != null -> {
                        val clipData = data.clipData ?: return@registerForActivityResult
                        for (index in 0 until clipData.itemCount) {
                            clipData.getItemAt(index)?.uri?.let(resultUris::add)
                        }
                    }

                    data?.data != null -> {
                        data.data?.let(resultUris::add)
                    }

                    pendingCameraUri != null -> {
                        pendingCameraUri?.let(resultUris::add)
                    }
                }
            }

            callback?.onReceiveValue(resultUris.takeIf { it.isNotEmpty() }?.toTypedArray())
            filePathCallback = null
            pendingCameraUri = null
        }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        binding = ActivityMainBinding.inflate(layoutInflater)
        setContentView(binding.root)

        prefs = getSharedPreferences(PREFS_NAME, Context.MODE_PRIVATE)

        setupButtons()
        setupWebView()
        setupBackNavigation()

        val configuredUrl = loadSavedBackendUrl()
        if (configuredUrl.isBlank()) {
            showServerConfig()
        } else {
            binding.serverUrlInput.setText(configuredUrl)
            openBackend(configuredUrl)
        }
    }

    private fun setupButtons() {
        binding.saveServerButton.setOnClickListener {
            val typedUrl = normalizeBackendUrl(binding.serverUrlInput.text?.toString())
            if (typedUrl == null) {
                showConfigMessage(getString(R.string.invalid_server_url), isError = true)
                return@setOnClickListener
            }

            saveBackendUrl(typedUrl)
            showConfigMessage(getString(R.string.server_saved_message), isError = false)
            openBackend(typedUrl)
        }

        binding.retryOpenButton.setOnClickListener {
            val typedUrl = normalizeBackendUrl(binding.serverUrlInput.text?.toString())
            if (typedUrl == null) {
                showConfigMessage(getString(R.string.invalid_server_url), isError = true)
                return@setOnClickListener
            }

            openBackend(typedUrl)
        }

        binding.changeServerButton.setOnClickListener {
            showServerConfig()
        }
    }

    @SuppressLint("SetJavaScriptEnabled")
    private fun setupWebView() {
        val settings = binding.appWebView.settings
        settings.javaScriptEnabled = true
        settings.domStorageEnabled = true
        settings.allowFileAccess = true
        settings.allowContentAccess = true
        settings.databaseEnabled = true
        settings.loadWithOverviewMode = true
        settings.useWideViewPort = true
        settings.mediaPlaybackRequiresUserGesture = false

        CookieManager.getInstance().setAcceptCookie(true)
        CookieManager.getInstance().setAcceptThirdPartyCookies(binding.appWebView, true)

        binding.appWebView.setDownloadListener { url, _, _, _, _ ->
            try {
                val i = Intent(Intent.ACTION_VIEW)
                i.data = Uri.parse(url)
                startActivity(i)
            } catch (e: Exception) {
                Toast.makeText(this@MainActivity, "Nenhum navegador encontrado para baixar o arquivo", Toast.LENGTH_SHORT).show()
            }
        }

        binding.appWebView.webViewClient = object : WebViewClient() {
            override fun shouldOverrideUrlLoading(
                view: WebView,
                request: WebResourceRequest,
            ): Boolean {
                val target = request.url.toString()
                
                // Envia qualquer link de PDF para o navegador externo (Chrome)
                if (target.contains("/pdf/")) {
                    try {
                        val intent = Intent(Intent.ACTION_VIEW, request.url)
                        intent.setPackage("com.android.chrome")
                        startActivity(intent)
                        return true
                    } catch (e: Exception) {
                        try {
                            startActivity(Intent(Intent.ACTION_VIEW, request.url))
                            return true
                        } catch (e2: Exception) {
                            // fallback
                        }
                    }
                }

                if (target.startsWith("http://") || target.startsWith("https://")) {
                    return false
                }

                return try {
                    startActivity(Intent(Intent.ACTION_VIEW, request.url))
                    true
                } catch (_: ActivityNotFoundException) {
                    false
                }
            }

            override fun onPageStarted(view: WebView, url: String?, favicon: Bitmap?) {
                binding.pageLoader.visibility = View.VISIBLE
            }

            override fun onPageFinished(view: WebView, url: String?) {
                binding.pageLoader.visibility = View.GONE
                binding.currentServerLabel.text = url ?: loadSavedBackendUrl()
            }

            override fun onReceivedError(
                view: WebView,
                request: WebResourceRequest,
                error: WebResourceError,
            ) {
                if (!request.isForMainFrame) {
                    return
                }
                binding.pageLoader.visibility = View.GONE
                val currentUrl = request.url.toString()
                binding.serverUrlInput.setText(currentUrl)
                showServerConfig(
                    getString(R.string.server_connection_failed, currentUrl),
                    true,
                )
            }
        }

        binding.appWebView.webChromeClient = object : WebChromeClient() {
            override fun onPermissionRequest(request: PermissionRequest) {
                runOnUiThread {
                    request.grant(request.resources)
                }
            }

            override fun onShowFileChooser(
                webView: WebView?,
                filePathCallback: ValueCallback<Array<Uri>>?,
                fileChooserParams: FileChooserParams?,
            ): Boolean {
                this@MainActivity.filePathCallback?.onReceiveValue(null)
                this@MainActivity.filePathCallback = filePathCallback
                this@MainActivity.lastFileChooserParams = fileChooserParams

                val permission = Manifest.permission.CAMERA
                if (ContextCompat.checkSelfPermission(this@MainActivity, permission) == PackageManager.PERMISSION_GRANTED) {
                    launchFileChooser(fileChooserParams, true)
                } else {
                    requestCameraPermissionLauncher.launch(permission)
                }

                return true
            }
        }
    }

    private fun launchFileChooser(fileChooserParams: WebChromeClient.FileChooserParams?, hasCameraPermission: Boolean) {
        val pickerIntent = fileChooserParams?.createIntent() ?: Intent(Intent.ACTION_GET_CONTENT)
        pickerIntent.addCategory(Intent.CATEGORY_OPENABLE)
        pickerIntent.type = buildAcceptedMimeType(fileChooserParams)

        val extraIntents = mutableListOf<Intent>()
        if (hasCameraPermission) {
            createCameraIntent()?.let(extraIntents::add)
        }

        val chooserIntent = Intent(Intent.ACTION_CHOOSER).apply {
            putExtra(Intent.EXTRA_INTENT, pickerIntent)
            putExtra(Intent.EXTRA_TITLE, getString(R.string.file_chooser_title))
            putExtra(Intent.EXTRA_INITIAL_INTENTS, extraIntents.toTypedArray())
        }

        try {
            fileChooserLauncher.launch(chooserIntent)
        } catch (_: ActivityNotFoundException) {
            this.filePathCallback?.onReceiveValue(null)
            this.filePathCallback = null
            pendingCameraUri = null
            Toast.makeText(
                this,
                getString(R.string.file_chooser_unavailable),
                Toast.LENGTH_LONG,
            ).show()
        }
    }

    private fun setupBackNavigation() {
        onBackPressedDispatcher.addCallback(
            this,
            object : OnBackPressedCallback(true) {
                override fun handleOnBackPressed() {
                    if (binding.webContainer.visibility == View.VISIBLE && binding.appWebView.canGoBack()) {
                        binding.appWebView.goBack()
                    } else if (binding.webContainer.visibility == View.VISIBLE) {
                        showServerConfig()
                    } else {
                        finish()
                    }
                }
            },
        )
    }

    private fun buildAcceptedMimeType(fileChooserParams: WebChromeClient.FileChooserParams?): String {
        val acceptedTypes = fileChooserParams
            ?.acceptTypes
            ?.map { it.trim() }
            ?.filter { it.isNotBlank() }
            .orEmpty()

        return acceptedTypes.firstOrNull() ?: "image/*"
    }

    private fun createCameraIntent(): Intent? {
        val imageFile = createTempImageFile() ?: return null
        val authority = "${BuildConfig.APPLICATION_ID}.fileprovider"
        val photoUri = FileProvider.getUriForFile(this, authority, imageFile)
        pendingCameraUri = photoUri

        return Intent(MediaStore.ACTION_IMAGE_CAPTURE).apply {
            putExtra(MediaStore.EXTRA_OUTPUT, photoUri)
            addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION)
            addFlags(Intent.FLAG_GRANT_WRITE_URI_PERMISSION)
        }.takeIf { it.resolveActivity(packageManager) != null }
    }

    private fun createTempImageFile(): File? {
        return try {
            val stamp = SimpleDateFormat("yyyyMMdd_HHmmss", Locale.US).format(Date())
            val targetDir = File(cacheDir, "captured").apply { mkdirs() }
            File.createTempFile("camera_$stamp", ".jpg", targetDir)
        } catch (_: Exception) {
            null
        }
    }

    private fun openBackend(url: String) {
        binding.currentServerLabel.text = url
        binding.webContainer.visibility = View.VISIBLE
        binding.serverConfigContainer.visibility = View.GONE
        binding.appWebView.loadUrl(url)
    }

    private fun showServerConfig(message: String? = null, isError: Boolean = false) {
        binding.webContainer.visibility = View.GONE
        binding.serverConfigContainer.visibility = View.VISIBLE
        showConfigMessage(message, isError)
    }

    private fun showConfigMessage(message: String?, isError: Boolean) {
        if (message.isNullOrBlank()) {
            binding.serverStatus.visibility = View.GONE
            return
        }

        binding.serverStatus.visibility = View.VISIBLE
        binding.serverStatus.text = message
        binding.serverStatus.setTextColor(
            if (isError) getColor(R.color.error_text) else getColor(R.color.success_text),
        )
    }

    private fun loadSavedBackendUrl(): String {
        val stored = prefs.getString(KEY_BACKEND_URL, BuildConfig.DEFAULT_BACKEND_URL).orEmpty()
        return stored.trim()
    }

    private fun saveBackendUrl(url: String) {
        prefs.edit().putString(KEY_BACKEND_URL, url).apply()
    }

    private fun normalizeBackendUrl(rawValue: String?): String? {
        val trimmed = rawValue.orEmpty().trim()
        if (trimmed.isBlank()) {
            return null
        }

        val withScheme = if (trimmed.startsWith("http://") || trimmed.startsWith("https://")) {
            trimmed
        } else {
            "http://$trimmed"
        }

        return withScheme
            .takeIf { Uri.parse(it).host != null }
            ?.let { if (it.endsWith("/")) it else "$it/" }
    }

    companion object {
        private const val PREFS_NAME = "assistente_apreensao_prefs"
        private const val KEY_BACKEND_URL = "backend_url"
    }
}
