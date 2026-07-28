package com.retakmesh.rnodebridge

import kotlinx.coroutines.Job
import kotlinx.coroutines.cancel
import java.io.InputStream
import java.io.OutputStream
import java.net.ServerSocket
import java.net.Socket

class TcpBridgeServer(
    private val port: Int = 9090
) {
    private var serverSocket: ServerSocket? = null
    private var clientSocket: Socket? = null
    private var bridgeJob: Job? = null

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
        val tcpIn = socket.getInputStream()
        val tcpOut = socket.getOutputStream()

        val readerThread = Thread {
            val buf = ByteArray(4096)
            try {
                while (socket.isConnected) {
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
                while (socket.isConnected) {
                    val n = tcpIn.read(buf)
                    if (n > 0) {
                        usbIo.write(buf.copyOfRange(0, n))
                    } else {
                        break
                    }
                }
            } catch (_: Exception) {
            }
        }

        readerThread.start()
        writerThread.start()

        try {
            readerThread.join()
        } catch (_: InterruptedException) {
        }
        try {
            writerThread.interrupt()
        } catch (_: Exception) {
        }

        try {
            socket.close()
        } catch (_: Exception) {
        }
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
