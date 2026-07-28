package com.retakmesh.rnodebridge

import android.app.Notification
import android.app.NotificationChannel
import android.app.NotificationManager
import android.app.PendingIntent
import android.app.Service
import android.content.BroadcastReceiver
import android.content.Context
import android.content.Intent
import android.content.IntentFilter
import android.hardware.usb.UsbDevice
import android.hardware.usb.UsbManager
import android.os.Build
import android.os.IBinder
import com.hoho.android.usbserial.driver.UsbSerialDriver
import com.hoho.android.usbserial.driver.UsbSerialPort
import com.hoho.android.usbserial.driver.UsbSerialProber
import com.hoho.android.usbserial.driver.ProbeTable
import com.hoho.android.usbserial.driver.CdcAcmSerialDriver
import java.io.IOException

class RNodeBridgeService : Service() {

    private lateinit var usbManager: UsbManager
    private var serialPort: UsbSerialPort? = null
    private var tcpServer: TcpBridgeServer? = null
    private var bridgeThread: Thread? = null
    private var running = false

    private val usbDetachReceiver = object : BroadcastReceiver() {
        override fun onReceive(context: Context, intent: Intent) {
            if (UsbManager.ACTION_USB_DEVICE_DETACHED == intent.action) {
                val device = if (Build.VERSION.SDK_INT >= 33) {
                    intent.getParcelableExtra(UsbManager.EXTRA_DEVICE, UsbDevice::class.java)
                } else {
                    @Suppress("DEPRECATION")
                    intent.getParcelableExtra(UsbManager.EXTRA_DEVICE)
                }
                if (device?.vendorId == intent.getIntExtra("expected_vendor", 0)) {
                    stopBridge("USB device detached")
                }
            }
        }
    }

    override fun onCreate() {
        super.onCreate()
        usbManager = getSystemService(USB_SERVICE) as UsbManager

        val channelId = "rnode-bridge"
        val channel = NotificationChannel(
            channelId, "RNode Bridge",
            NotificationManager.IMPORTANCE_LOW
        )
        val nm = getSystemService(NotificationManager::class.java)
        nm.createNotificationChannel(channel)

        val openAppIntent = Intent(this, MainActivity::class.java).apply {
            flags = Intent.FLAG_ACTIVITY_SINGLE_TOP
        }
        val pi = PendingIntent.getActivity(this, 0, openAppIntent,
            PendingIntent.FLAG_IMMUTABLE or PendingIntent.FLAG_UPDATE_CURRENT)

        val notification = Notification.Builder(this, channelId)
            .setContentTitle("RNode Bridge")
            .setContentText("TCP bridge running on 127.0.0.1:9090")
            .setSmallIcon(android.R.drawable.ic_menu_share)
            .setContentIntent(pi)
            .setOngoing(true)
            .build()

        startForeground(1, notification)
    }

    override fun onStartCommand(intent: Intent?, flags: Int, startId: Int): Int {
        if (intent == null) return START_STICKY

        val vendorId = intent.getIntExtra("device_vendor_id", -1)
        val productId = intent.getIntExtra("device_product_id", -1)

        registerReceiver(usbDetachReceiver, IntentFilter(UsbManager.ACTION_USB_DEVICE_DETACHED))

        if (vendorId >= 0) {
            connectToDevice(vendorId, productId)
        }

        return START_STICKY
    }

    private fun connectToDevice(vendorId: Int, productId: Int) {
        val device = usbManager.deviceList.values.find {
            it.vendorId == vendorId && it.productId == productId
        } ?: run {
            stopBridge("Device not found")
            return
        }

        if (!usbManager.hasPermission(device)) {
            stopBridge("No USB permission")
            return
        }

        val connection = usbManager.openDevice(device)
        if (connection == null) {
            stopBridge("Failed to open USB device")
            return
        }

        try {
            val prober = UsbSerialProber(ProbeTable().apply {
                addProduct(device.vendorId, device.productId, CdcAcmSerialDriver::class.java)
            })
            val driver = prober.probeDevice(device) ?: run {
                connection.close()
                stopBridge("No serial driver for this device")
                return
            }

            val port = driver.ports[0]
            port.open(connection)
            port.setParameters(115200, 8, UsbSerialPort.STOPBITS_1, UsbSerialPort.PARITY_NONE)

            serialPort = port
            updateNotification("RNode connected on ${device.productName ?: "USB"}")

            val usbIo = object : TcpBridgeServer.UsbIo {
                @Synchronized
                override fun read(buffer: ByteArray): Int {
                    return port.read(buffer, 1000)
                }

                @Synchronized
                override fun write(data: ByteArray) {
                    port.write(data, 1000)
                }

                override fun close() {
                    try { port.close() } catch (_: Exception) {}
                    try { connection.close() } catch (_: Exception) {}
                }
            }

            tcpServer = TcpBridgeServer()
            tcpServer!!.start(usbIo)
            running = true

        } catch (e: Exception) {
            connection.close()
            stopBridge("Error: ${e.message}")
        }
    }

    private fun updateNotification(text: String) {
        val nm = getSystemService(NotificationManager::class.java)
        val notification = Notification.Builder(this, "rnode-bridge")
            .setContentTitle("RNode Bridge")
            .setContentText(text)
            .setSmallIcon(android.R.drawable.ic_menu_share)
            .setOngoing(true)
            .build()
        nm.notify(1, notification)
    }

    private fun stopBridge(reason: String) {
        running = false
        try {
            tcpServer?.stop()
        } catch (_: Exception) {}
        try {
            serialPort?.close()
        } catch (_: Exception) {}
        serialPort = null
        tcpServer = null
        updateNotification(reason)
        stopSelf()
    }

    override fun onBind(intent: Intent?): IBinder? = null

    override fun onDestroy() {
        running = false
        try { unregisterReceiver(usbDetachReceiver) } catch (_: Exception) {}
        try { tcpServer?.stop() } catch (_: Exception) {}
        try { serialPort?.close() } catch (_: Exception) {}
        super.onDestroy()
    }
}
