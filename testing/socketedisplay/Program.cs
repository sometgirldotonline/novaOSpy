using System;
using System.Drawing;
using System.Drawing.Imaging;
using System.IO;
using System.Net;
using System.Net.Sockets;
using System.Text;
using System.Threading;
using System.Threading.Tasks;
using System.Windows.Forms;
using System.Net.NetworkInformation;
using System.Collections.Generic;
namespace SDLReceiver
{
    public partial class MainForm : Form
    {
        private const int FRAME_PORT = 6000;
        private const int BACKCHANNEL_PORT = 6001;
        private const string HOST = "127.0.0.1";

        private PictureBox pictureBox;
        private Label statusLabel;
        private Button resizeButton;
        private NumericUpDown widthUpDown;
        private NumericUpDown heightUpDown;

        private TcpListener frameListener;
        private TcpListener backchannelListener;
        private CancellationTokenSource cancellationTokenSource;

        private int currentWidth = 64;
        private int currentHeight = 64;

        private TcpClient backchannelClient; // Store backchannel client reference
        static string GetCommaSeparatedIPs()
        {
            List<string> ipAddresses = new List<string>();

            // Get all network interfaces
            foreach (NetworkInterface networkInterface in NetworkInterface.GetAllNetworkInterfaces())
            {
                // Check if the network interface is up and operational
                if (networkInterface.OperationalStatus == OperationalStatus.Up)
                {
                    // Get the IP properties of the network interface
                    IPInterfaceProperties ipProperties = networkInterface.GetIPProperties();

                    // Loop through each unicast IP address assigned to the interface
                    foreach (UnicastIPAddressInformation ipInfo in ipProperties.UnicastAddresses)
                    {
                        // Add only IPv4 or IPv6 addresses to the list
                        if (ipInfo.Address.AddressFamily == AddressFamily.InterNetwork)
                        // ipInfo.Address.AddressFamily == AddressFamily.InterNetworkV6)
                        {
                            ipAddresses.Add(ipInfo.Address.ToString());
                        }
                    }
                }
            }

            // Join the list of IPs into a comma-separated string
            return string.Join(", ", ipAddresses);
        }
        public MainForm()
        {
            InitializeComponent();
            cancellationTokenSource = new CancellationTokenSource();
            StartServers();
        }

        private void InitializeComponent()
        {
            this.Size = new Size(800, 600);
            this.Text = "SDL Frame Receiver (IP: " + GetCommaSeparatedIPs() + ")";
            this.FormClosing += OnFormClosing;

            // Picture box for displaying frames
            pictureBox = new PictureBox
            {
                Location = new Point(10, 10),
                Size = new Size(640, 480),
                SizeMode = PictureBoxSizeMode.Zoom,
                BorderStyle = BorderStyle.FixedSingle,
                BackColor = Color.Black,
                Dock = DockStyle.Fill
            };
            this.Controls.Add(pictureBox);

            // Status label
            statusLabel = new Label
            {
                Location = new Point(10, 500),
                Size = new Size(400, 20),
                Text = "Starting servers..."
            };
            this.Controls.Add(statusLabel);

            // Resolution controls
            Label widthLabel = new Label
            {
                Location = new Point(660, 50),
                Size = new Size(50, 20),
                Text = "Width:"
            };
            this.Controls.Add(widthLabel);

            widthUpDown = new NumericUpDown
            {
                Location = new Point(710, 48),
                Size = new Size(60, 20),
                Minimum = 16,
                Maximum = 1920,
                Value = currentWidth
            };
            this.Controls.Add(widthUpDown);

            Label heightLabel = new Label
            {
                Location = new Point(660, 80),
                Size = new Size(50, 20),
                Text = "Height:"
            };
            this.Controls.Add(heightLabel);

            heightUpDown = new NumericUpDown
            {
                Location = new Point(710, 78),
                Size = new Size(60, 20),
                Minimum = 16,
                Maximum = 1080,
                Value = currentHeight
            };
            this.Controls.Add(heightUpDown);

            resizeButton = new Button
            {
                Location = new Point(660, 110),
                Size = new Size(100, 30),
                Text = "Send Resize",
                UseVisualStyleBackColor = true
            };
            resizeButton.Click += OnResizeButtonClick;
            this.Controls.Add(resizeButton);
        }

        private async void StartServers()
        {
            try
            {
                // Start frame receiver
                frameListener = new TcpListener(IPAddress.Parse(HOST), FRAME_PORT);
                frameListener.Start();
                UpdateStatus("Frame server started on port " + FRAME_PORT);

                // Start backchannel server
                backchannelListener = new TcpListener(IPAddress.Parse(HOST), BACKCHANNEL_PORT);
                backchannelListener.Start();
                UpdateStatus("Backchannel server started on port " + BACKCHANNEL_PORT);

                // Start accepting connections
                _ = Task.Run(() => AcceptFrameConnections(cancellationTokenSource.Token));
                _ = Task.Run(() => AcceptBackchannelConnections(cancellationTokenSource.Token));

                UpdateStatus("Waiting for Python connection...");
            }
            catch (Exception ex)
            {
                UpdateStatus($"Error starting servers: {ex.Message}");
            }
        }

        private async Task AcceptFrameConnections(CancellationToken cancellationToken)
        {
            while (!cancellationToken.IsCancellationRequested)
            {
                try
                {
                    var client = await frameListener.AcceptTcpClientAsync();
                    UpdateStatus("Python frame sender connected");
                    _ = Task.Run(() => HandleFrameClient(client, cancellationToken));
                }
                catch (ObjectDisposedException)
                {
                    break;
                }
                catch (Exception ex)
                {
                    UpdateStatus($"Frame connection error: {ex.Message}");
                }
            }
        }

        private async Task AcceptBackchannelConnections(CancellationToken cancellationToken)
        {
            while (!cancellationToken.IsCancellationRequested)
            {
                try
                {
                    var client = await backchannelListener.AcceptTcpClientAsync();
                    UpdateStatus("Python backchannel connected");
                    _ = Task.Run(() => HandleBackchannelClient(client, cancellationToken));
                }
                catch (ObjectDisposedException)
                {
                    break;
                }
                catch (Exception ex)
                {
                    UpdateStatus($"Backchannel connection error: {ex.Message}");
                }
            }
        }

        private async Task HandleFrameClient(TcpClient client, CancellationToken cancellationToken)
        {
            using (client)
            using (var stream = client.GetStream())
            {
                // Optimize client settings
                client.ReceiveBufferSize = 1024 * 1024; // 1MB receive buffer
                client.NoDelay = true;

                byte[] buffer = new byte[4 * 1024 * 1024]; // 4MB buffer for larger frames
                int frameCount = 0;

                while (!cancellationToken.IsCancellationRequested && client.Connected)
                {
                    try
                    {
                        // Read size header more efficiently
                        string sizeLine = await ReadLineAsync(stream, cancellationToken);
                        if (string.IsNullOrEmpty(sizeLine))
                        {
                            UpdateStatus("Connection closed - empty size line");
                            return;
                        }

                        if (sizeLine.StartsWith("frameSize"))
                        {
                            Console.WriteLine("Fs");
                            var parts = sizeLine.Substring(9).Trim().Split(' ');
                            if (parts.Length == 2 &&
                                int.TryParse(parts[0], out int width) &&
                                int.TryParse(parts[1], out int height))
                            {
                                currentWidth = width;
                                currentHeight = height;

                                int expectedSize = width * height * 3;

                                // Only show progress for larger frames
                                // if (frameCount % 100 == 0 && expectedSize > 50000)
                                // {
                                UpdateStatus($"Receiving frame {frameCount}: {width}x{height} ({expectedSize} bytes)");
                                // }

                                // Ensure buffer is large enough
                                if (buffer.Length < expectedSize)
                                {
                                    buffer = new byte[expectedSize + 1024]; // Add some padding
                                }

                                // Read frame data in larger chunks for better performance
                                int totalRead = 0;
                                while (totalRead < expectedSize && client.Connected)
                                {
                                    int remainingBytes = expectedSize - totalRead;
                                    int chunkSize = Math.Min(65536, remainingBytes); // 64KB chunks

                                    int bytesRead = await stream.ReadAsync(
                                        buffer, totalRead, chunkSize, cancellationToken);

                                    if (bytesRead == 0)
                                    {
                                        UpdateStatus($"Connection closed at {totalRead}/{expectedSize} bytes");
                                        return;
                                    }

                                    totalRead += bytesRead;
                                }

                                if (totalRead == expectedSize)
                                {
                                    frameCount++;

                                    // Process frame asynchronously to avoid blocking reception
                                    _ = Task.Run(() => DisplayFrame(buffer, height, width, frameCount));
                                }
                                else
                                {
                                    UpdateStatus($"⚠️ Incomplete frame: {totalRead}/{expectedSize}");
                                }
                            }
                            else
                            {
                                UpdateStatus($"⚠️ Invalid frame size: '{sizeLine}'");
                            }
                        }
                        else
                        {
                            UpdateStatus($"⚠️ Unknown message: '{sizeLine}'");
                        }
                    }
                    catch (Exception ex)
                    {
                        UpdateStatus($"Frame handling error: {ex.Message}");
                        break;
                    }
                }
            }

            UpdateStatus("Frame client disconnected");
        }

        // More efficient line reading
        private async Task<string> ReadLineAsync(NetworkStream stream, CancellationToken cancellationToken)
        {
            var lineBuffer = new List<byte>(256);
            byte[] singleByte = new byte[1];

            while (true)
            {
                int bytesRead = await stream.ReadAsync(singleByte, 0, 1, cancellationToken);
                if (bytesRead == 0)
                    return null;

                if (singleByte[0] == '\n')
                    break;

                if (singleByte[0] != '\r')
                    lineBuffer.Add(singleByte[0]);
            }

            return Encoding.UTF8.GetString(lineBuffer.ToArray());
        }

        // Optimized display with frame skipping for better performance
        private void DisplayFrame(byte[] frameData, int width, int height, int frameNumber)
        {
            try
            {
                int expectedSize = width * height * 3;
                if (frameData.Length < expectedSize)
                {
                    UpdateStatus($"Frame {frameNumber} too small: {frameData.Length}/{expectedSize}");
                    return;
                }

                // Skip frame processing if we're behind (basic frame dropping)
                if (frameNumber % 2 == 0 && expectedSize > 100000) // Skip every other frame for large frames
                {
                    return;
                }

                // Create and process bitmap more efficiently
                using (var bitmap = new Bitmap(width, height, PixelFormat.Format24bppRgb))
                {
                    // Cache for the previous frame
                    byte[] previousFrameCache = new byte[width * height * 3];

                    var bmpData = bitmap.LockBits(
                        new Rectangle(0, 0, width, height),
                        ImageLockMode.WriteOnly,
                        PixelFormat.Format24bppRgb);

                    try
                    {
                        // Use unsafe code for faster pixel copying
                        unsafe
                        {
                            byte* ptr = (byte*)bmpData.Scan0;
                            int stride = Math.Abs(bmpData.Stride);

                            // Copy data more efficiently using blocks
                            fixed (byte* src = frameData)
                            fixed (byte* cache = previousFrameCache)
                            {
                                for (int y = 0; y < height; y++)
                                {
                                    byte* srcRow = src + (y * width * 3);
                                    byte* dstRow = ptr + (y * stride);
                                    byte* cacheRow = cache + (y * width * 3);

                                    for (int x = 0; x < width; x++)
                                    {
                                        // Check if the pixel is marked as transparent (e.g., all channels are 0)
                                        if (srcRow[x * 3] == 0 && srcRow[x * 3 + 1] == 0 && srcRow[x * 3 + 2] == 0)
                                        {
                                            // Use the cached pixel for transparency
                                            dstRow[x * 3] = cacheRow[x * 3];       // B
                                            dstRow[x * 3 + 1] = cacheRow[x * 3 + 1]; // G
                                            dstRow[x * 3 + 2] = cacheRow[x * 3 + 2]; // R
                                        }
                                        else
                                        {
                                            // Copy the current pixel and update the cache
                                            dstRow[x * 3] = srcRow[x * 3 + 2];     // B
                                            dstRow[x * 3 + 1] = srcRow[x * 3 + 1]; // G
                                            dstRow[x * 3 + 2] = srcRow[x * 3];     // R

                                            // Update the cache
                                            cacheRow[x * 3] = srcRow[x * 3 + 2];     // B
                                            cacheRow[x * 3 + 1] = srcRow[x * 3 + 1]; // G
                                            cacheRow[x * 3 + 2] = srcRow[x * 3];     // R
                                        }
                                    }
                                }
                            }
                        }
                    }
                    finally
                    {
                        bitmap.UnlockBits(bmpData);
                    }

                    // Update UI less frequently for better performance
                    if (InvokeRequired)
                    {
                        Invoke(new Action(() => {
                            var oldImage = pictureBox.Image;
                            pictureBox.Image = new Bitmap(bitmap); // Create copy
                            oldImage?.Dispose();

                            if (frameNumber % 50 == 0) // Update status less frequently
                            {
                                UpdateStatus($"✅ Frame {frameNumber}: {width}x{height}");
                            }
                        }));
                    }
                }
            }
            catch (Exception ex)
            {
                UpdateStatus($"Display error frame {frameNumber}: {ex.Message}");
            }
        }

        private async Task HandleBackchannelClient(TcpClient client, CancellationToken cancellationToken)
        {
            backchannelClient = client; // Store reference for sending messages
            using (client)
            using (var stream = client.GetStream())
            using (var reader = new StreamReader(stream))
            using (var writer = new StreamWriter(stream) { AutoFlush = true })
            {
                while (!cancellationToken.IsCancellationRequested && client.Connected)
                {
                    try
                    {
                        string message = await reader.ReadLineAsync();
                        if (string.IsNullOrEmpty(message))
                            break;

                        if (message == "keep-alive")
                        {
                            await writer.WriteLineAsync("ack");
                        }
                        else
                        {
                            UpdateStatus($"Backchannel received: {message}");
                        }

                    }
                    catch (Exception ex)
                    {
                        UpdateStatus($"Backchannel error: {ex.Message}");
                        break;
                    }
                }
            }

            backchannelClient = null;
            UpdateStatus("Backchannel client disconnected");
        }

        private async Task SendBackchannelMessage(string message)
        {
            try
            {
                if (backchannelClient != null && backchannelClient.Connected)
                {
                    var stream = backchannelClient.GetStream();
                    var writer = new StreamWriter(stream) { AutoFlush = true };
                    await writer.WriteLineAsync(message);
                    UpdateStatus($"Sent: {message}");
                }
                else
                {
                    UpdateStatus("No backchannel connection available");
                }
            }
            catch (Exception ex)
            {
                UpdateStatus($"Backchannel send error: {ex.Message}");
            }
        }

        private void DisplayFrame(byte[] frameData, int width, int height)
        {
            try
            {
                // Validate frame data size
                int expectedSize = width * height * 3;
                if (frameData.Length < expectedSize)
                {
                    UpdateStatus($"Frame data too small: got {frameData.Length}, expected {expectedSize}");
                    return;
                }

                // Debug: Check if we have any non-zero data
                bool hasData = false;
                int nonZeroCount = 0;
                for (int i = 0; i < Math.Min(expectedSize, frameData.Length); i++)
                {
                    if (frameData[i] != 0)
                    {
                        hasData = true;
                        nonZeroCount++;
                    }
                }

                UpdateStatus($"Frame data check: {nonZeroCount} non-zero bytes out of {expectedSize}");

                if (!hasData)
                {
                    UpdateStatus("⚠️ All frame data is zero - no visible content!");
                }

                // Create bitmap from RGB data
                Bitmap bitmap = new Bitmap(width, height, PixelFormat.Format24bppRgb);

                BitmapData bmpData = bitmap.LockBits(
                    new Rectangle(0, 0, width, height),
                    ImageLockMode.WriteOnly,
                    PixelFormat.Format24bppRgb);

                // Calculate the stride (bytes per row)
                int stride = Math.Abs(bmpData.Stride);
                int bytesPerPixel = 3;

                // Copy frame data row by row to handle stride differences
                unsafe
                {
                    byte* ptr = (byte*)bmpData.Scan0;
                    for (int y = 0; y < height; y++)
                    {
                        for (int x = 0; x < width; x++)
                        {
                            int srcIndex = (y * width + x) * bytesPerPixel;
                            int dstIndex = y * stride + x * bytesPerPixel;

                            if (srcIndex + 2 < frameData.Length)
                            {
                                // BGR format for bitmap
                                ptr[dstIndex] = frameData[srcIndex + 2];     // B
                                ptr[dstIndex + 1] = frameData[srcIndex + 1]; // G
                                ptr[dstIndex + 2] = frameData[srcIndex];     // R
                            }
                        }
                    }
                }

                bitmap.UnlockBits(bmpData);

                // Update UI on main thread
                if (InvokeRequired)
                {
                    Invoke(new Action(() => {
                        pictureBox.Image?.Dispose();
                        pictureBox.Image = bitmap;
                        UpdateStatus($"✅ Displayed frame {width}x{height} (non-zero: {nonZeroCount})");
                    }));
                }
                else
                {
                    pictureBox.Image?.Dispose();
                    pictureBox.Image = bitmap;
                    UpdateStatus($"✅ Displayed frame {width}x{height} (non-zero: {nonZeroCount})");
                }
            }
            catch (Exception ex)
            {
                UpdateStatus($"Display error: {ex.Message}");
            }
        }

        private void UpdateStatus(string message)
        {
            if (InvokeRequired)
            {
                Invoke(new Action(() => {
                    statusLabel.Text = $"{DateTime.Now:HH:mm:ss} - {message}";
                }));
            }
            else
            {
                statusLabel.Text = $"{DateTime.Now:HH:mm:ss} - {message}";
            }
        }

        private async void OnResizeButtonClick(object sender, EventArgs e)
        {
            int newWidth = (int)widthUpDown.Value;
            int newHeight = (int)heightUpDown.Value;

            await SendBackchannelMessage($"NewRes {newWidth} {newHeight}");
            UpdateStatus($"Sent resize command: {newWidth}x{newHeight}");
        }

        private void OnFormClosing(object sender, FormClosingEventArgs e)
        {
            cancellationTokenSource.Cancel();
            frameListener?.Stop();
            backchannelListener?.Stop();
        }
    }

    static class Program
    {
        [STAThread]
        static void Main()
        {
            Application.EnableVisualStyles();
            Application.SetCompatibleTextRenderingDefault(false);
            Application.Run(new MainForm());
        }
    }
}
