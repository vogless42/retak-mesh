package com.retakmesh.rnodebridge

import android.Manifest
import android.app.PendingIntent
import android.content.BroadcastReceiver
import android.content.Context
import android.content.Intent
import android.content.IntentFilter
import android.content.pm.PackageManager
import android.hardware.usb.UsbDevice
import android.hardware.usb.UsbManager
import android.os.Build
import android.os.Bundle
import android.widget.Button
import android.widget.TextView
import androidx.activity.result.contract.ActivityResultContracts
import androidx.appcompat.app.AlertDialog
import androidx.appcompat.app.AppCompatActivity
import androidx.core.content.ContextCompat

private const val ACTION_USB_PERMISSION = "com.retakmesh.rnodebridge.USB_PERMISSION"

class MainActivity : AppCompatActivity() {

    private lateinit var statusText: TextView
    private lateinit var startButton: Button

    private val usbManager by lazy { getSystemService(USB_SERVICE) as UsbManager }
    private var rNodeDevice: UsbDevice? = null

    private val notificationPermissionLauncher = registerForActivityResult(
        ActivityResultContracts.RequestPermission()
    ) { /* granted or not - service still starts */ }

    private val usbPermissionReceiver = object : BroadcastReceiver() {
        override fun onReceive(context: Context, intent: Intent) {
            if (ACTION_USB_PERMISSION == intent.action) {
                val device = if (Build.VERSION.SDK_INT >= 33) {
                    intent.getParcelableExtra(UsbManager.EXTRA_DEVICE, UsbDevice::class.java)
                } else {
                    @Suppress("DEPRECATION")
                    intent.getParcelableExtra(UsbManager.EXTRA_DEVICE)
                }
                if (intent.getBooleanExtra(UsbManager.EXTRA_PERMISSION_GRANTED, false)) {
                    device?.let { startBridge(it) }
                }
            }
        }
    }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)

        setContentView(R.layout.activity_main)
        statusText = findViewById(R.id.statusText)
        startButton = findViewById(R.id.startButton)

        registerReceiver(usbPermissionReceiver, IntentFilter(ACTION_USB_PERMISSION))

        if (Build.VERSION.SDK_INT >= 33) {
            if (ContextCompat.checkSelfPermission(this, Manifest.permission.POST_NOTIFICATIONS)
                != PackageManager.PERMISSION_GRANTED
            ) {
                notificationPermissionLauncher.launch(Manifest.permission.POST_NOTIFICATIONS)
            }
        }

        startButton.setOnClickListener {
            if (isBridgeRunning()) {
                stopBridge()
            } else {
                findAndStart()
            }
        }

        updateUi()
        findRNodeDevice()
    }

    override fun onDestroy() {
        super.onDestroy()
        unregisterReceiver(usbPermissionReceiver)
    }

    private fun findRNodeDevice(): UsbDevice? {
        rNodeDevice = null
        val knownVids = intArrayOf(0x303a, 0x0403, 0x10c4, 0x1a86, 0x067b, 0x12d1)
        for (device in usbManager.deviceList.values) {
            if (device.vendorId in knownVids) {
                rNodeDevice = device
                return device
            }
        }
        return null
    }

    private fun findAndStart() {
        val device = findRNodeDevice()
        if (device == null) {
            AlertDialog.Builder(this)
                .setTitle("No RNode Found")
                .setMessage("Plug in the RNode USB device and try again.\n\n" +
                        "Known VID: 0x303a (ESP32), 0x0403 (FTDI), 0x10c4 (CP210x), 0x1a86 (CH340)")
                .setPositiveButton("OK", null)
                .show()
            statusText.text = "No RNode detected"
            return
        }

        if (usbManager.hasPermission(device)) {
            startBridge(device)
        } else {
            val intent = Intent(ACTION_USB_PERMISSION).apply {
                setPackage(packageName)
            }
            val pi = PendingIntent.getBroadcast(this, 0, intent,
                PendingIntent.FLAG_IMMUTABLE or PendingIntent.FLAG_UPDATE_CURRENT)
            usbManager.requestPermission(device, pi)
        }
    }

    private fun startBridge(device: UsbDevice) {
        val intent = Intent(this, RNodeBridgeService::class.java).apply {
            putExtra("device_vendor_id", device.vendorId)
            putExtra("device_product_id", device.productId)
        }
        ContextCompat.startForegroundService(this, intent)
        startButton.text = "Stop Bridge"
        statusText.text = "Bridge running: ${device.productName ?: device.deviceName}"
    }

    private fun stopBridge() {
        stopService(Intent(this, RNodeBridgeService::class.java))
        startButton.text = "Start Bridge"
        statusText.text = "Bridge stopped"
    }

    private fun isBridgeRunning(): Boolean {
        startButton.text = "Stop Bridge"
        return false
    }

    private fun updateUi() {
        val device = findRNodeDevice()
        if (device != null) {
            statusText.text = "RNode: ${device.productName ?: device.deviceName}\nTap Start to begin"
            startButton.isEnabled = true
        } else {
            statusText.text = "No RNode detected\nPlug in USB RNode"
            startButton.isEnabled = false
        }
    }
}
