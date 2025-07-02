using System;
using System.Collections.Generic;
using System.Net;
using System.Net.Sockets;
using System.Text;
using System.Threading;
using System.Threading.Tasks;

namespace SDLReceiver
{
    /// <summary>
    /// Handles network communication to receive frame data from the Python script.
    /// </summary>
    public class NetworkHandler
    {
        private const int FRAME_PORT = 6000;
        private const string HOST = "127.0.0.1";
        private Socket listenerSocket;
        private CancellationTokenSource cancellationTokenSource;

        private TcpClient commandClient;
        private NetworkStream commandStream;

        public event Action<byte[], int, int, int> FrameReceived;
        public event Action<string> FrameClientConnected; // Add this event

        public NetworkHandler()
        {
            cancellationTokenSource = new CancellationTokenSource();
        }

        public void Start()
        {
            listenerSocket = new Socket(AddressFamily.InterNetwork, SocketType.Stream, ProtocolType.Tcp);
            listenerSocket.Bind(new IPEndPoint(IPAddress.Parse(HOST), FRAME_PORT));
            listenerSocket.Listen(10);

            Task.Run(() => AcceptConnectionsAsync(cancellationTokenSource.Token));
        }

        private async Task AcceptConnectionsAsync(CancellationToken cancellationToken)
        {
            while (!cancellationToken.IsCancellationRequested)
            {
                try
                {
                    var clientSocket = await listenerSocket.AcceptAsync();
                    // Handle each client in its own task
                    _ = Task.Run(() => HandleClientAsync(clientSocket, cancellationToken));
                }
                catch (Exception ex)
                {
                    Console.WriteLine($"Accept error: {ex.Message}");
                }
            }
        }

        private async Task HandleClientAsync(Socket clientSocket, CancellationToken cancellationToken)
        {
            var remoteIp = ((IPEndPoint)clientSocket.RemoteEndPoint).Address.ToString();
            FrameClientConnected?.Invoke(remoteIp); // Notify MainForm or whoever is listening

            // Set a large buffer for receiving frame data
            byte[] buffer = new byte[4 * 1024 * 1024]; // 4MB
            int frameCount = 0;

            using (var stream = new NetworkStream(clientSocket, true))
            {
                while (!cancellationToken.IsCancellationRequested && clientSocket.Connected)
                {
                    try
                    {
                        // Read the size header line
                        string sizeLine = await ReadLineAsync(stream, cancellationToken);
                        if (string.IsNullOrEmpty(sizeLine)) break;

                        if (sizeLine.StartsWith("frameSize"))
                        {
                            var parts = sizeLine.Substring(9).Trim().Split(' ');
                            if (parts.Length == 2 &&
                                int.TryParse(parts[0], out int width) &&
                                int.TryParse(parts[1], out int height))
                            {
                                int expectedSize = width * height * 3;
                                if (buffer.Length < expectedSize)
                                    buffer = new byte[expectedSize + 1024]; // Resize if needed

                                // Read the full frame data
                                int totalRead = 0;
                                while (totalRead < expectedSize && clientSocket.Connected)
                                {
                                    int bytesRead = await stream.ReadAsync(buffer, totalRead, expectedSize - totalRead, cancellationToken);
                                    if (bytesRead == 0) break; // Connection closed
                                    totalRead += bytesRead;
                                }

                                if (totalRead == expectedSize)
                                {
                                    frameCount++;
                                    // Pass a copy of the relevant data to the event
                                    byte[] frameData = new byte[expectedSize];
                                    Array.Copy(buffer, 0, frameData, 0, expectedSize);
                                    FrameReceived?.Invoke(frameData, width, height, frameCount);
                                }
                            }
                        }
                    }
                    catch (Exception ex)
                    {
                        Console.WriteLine($"Frame handling error: {ex.Message}");
                        break;
                    }
                }
            }
        }

        private async Task<string> ReadLineAsync(NetworkStream stream, CancellationToken cancellationToken)
        {
            var lineBuffer = new List<byte>();
            var singleByte = new byte[1];
            while (true)
            {
                int bytesRead = await stream.ReadAsync(singleByte, 0, 1, cancellationToken);
                if (bytesRead == 0) return null; // Connection closed
                if (singleByte[0] == '\n') break;
                if (singleByte[0] != '\r') lineBuffer.Add(singleByte[0]);
            }
            return Encoding.UTF8.GetString(lineBuffer.ToArray());
        }

        public void Stop()
        {
            cancellationTokenSource.Cancel();
            listenerSocket?.Close();
        }

        /// <summary>
        /// Connects to the command channel for sending commands.
        /// </summary>
        /// <param name="host">The host to connect to.</param>
        /// <param name="port">The port to connect to.</param>
        public void ConnectCommandChannel(string host, int port)
        {
            commandClient = new TcpClient();
            commandClient.Connect(host, port);
            commandStream = commandClient.GetStream();
        }

        /// <summary>
        /// Sends a command string through the command channel.
        /// </summary>
        /// <param name="command">The command string to send.</param>
        public void SendCommand(string command)
        {
            if (commandStream == null) return;
            byte[] data = Encoding.UTF8.GetBytes(command + "\n");
            commandStream.Write(data, 0, data.Length);
        }
    }
}