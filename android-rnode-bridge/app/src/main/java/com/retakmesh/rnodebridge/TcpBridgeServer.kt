package com.retakmesh.rnodebridge

import java.net.ServerSocket
import java.net.Socket
import java.util.concurrent.atomic.AtomicBoolean

class TcpBridgeServer(
    private val port: Int = 9090
) {
    private var serverSocket: ServerSocket? = null
    private var clientSocket: Socket? = null

    interface UsbIo {
        fun read(buffer: ByteArray): Int
        fun write(data: ByteArray)
        fun close()
    }

    fun start(usbIo: UsbIo) {
        serverSocket = ServerSocket(port, 1, java.net.InetAddress.getByName("127.0.0.1"))
        Thread {
            try {
                while (serverSocket?.isClosed == false) {
                    val socket = serverSocket?.accept() ?: break
                    clientSocket?.close()
                    clientSocket = socket
                    bridgeLoop(socket, usbIo)
                }
            } catch (_: Exception) {
            }
        }.apply { isDaemon = true }.start()
    }

    private fun bridgeLoop(socket: Socket, usbIo: UsbIo) {
        val connected = java.util.concurrent.atomic.AtomicBoolean(true)
        val tcpIn = socket.getInputStream()
        val tcpOut = socket.getOutputStream()

        val readerThread = Thread {
            val buf = ByteArray(4096)
            try {
                while (connected.get()) {
                    val n = usbIo.read(buf)
                    if (n > 0) {
                        tcpOut.write(buf, 0, n)
                        tcpOut.flush()
                    }
                }
            } catch (_: Exception) {
            }
        }

        val writerThread = Thread {
            val buf = ByteArray(4096)
            try {
                while (connected.get()) {
                    val n = tcpIn.read(buf)
                    if (n > 0) {
                        usbIo.write(buf.copyOfRange(0, n))
                    } else {
                        break
                    }
                }
            } catch (_: Exception) {
            }
            connected.set(false)
            try { socket.close() } catch (_: Exception) {}
        }

        readerThread.start()
        writerThread.start()

        try {
            writerThread.join()
        } catch (_: InterruptedException) {
        }
        try {
            socket.close()
        } catch (_: Exception) {
        }

        readerThread.interrupt()
    }

    fun stop() {
        try {
            serverSocket?.close()
        } catch (_: Exception) {
        }
        try {
            clientSocket?.close()
        } catch (_: Exception) {
        }
        serverSocket = null
        clientSocket = null
    }
}
