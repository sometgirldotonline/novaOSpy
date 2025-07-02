using SDLReceiver;
using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.Drawing;
using System.Drawing.Imaging;
using System.IO;
using System.Net;
using System.Net.NetworkInformation;
using System.Net.Sockets;
using System.Text;
using System.Threading;
using System.Threading.Tasks;
using System.Windows.Forms;
namespace SDLReceiver
{
    public partial class MainForm : Form
    {
        private const int FRAME_PORT = 6000;
        private Socket frameListener;
        private int currentWidth = 64;
        private int currentHeight = 64;

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
            this.KeyPreview = true; // Enable form to receive key events
            this.KeyDown += MainForm_KeyDown;
            cancellationTokenSource = new CancellationTokenSource();
            StartServers();
        }
        private void MainForm_KeyDown(object sender, KeyEventArgs e)
        {
            if (e.KeyCode == Keys.F19)
            {
                uiVisible = !uiVisible;

                // Toggle all controls except pictureBox
                foreach (Control ctrl in this.Controls)
                {
                    if (ctrl != pictureBox)
                    {
                        ctrl.Visible = uiVisible;
                    }
                }
                // Optionally, update status if UI is shown
                if (uiVisible)
                {
                    UpdateStatus("UI shown (F19)");
                }
            }
        }
        private void InitializeComponent()
        {
            this.Size = new Size(800, 600);
            this.Text = "SDL Frame Receiver (IP: " + GetCommaSeparatedIPs() + ")";
            this.FormClosing += OnFormClosing;

            // Picture box for displaying frames
            pictureBox = new PictureBox
            {
                Dock = DockStyle.Fill,
                SizeMode = PictureBoxSizeMode.Zoom,
                BorderStyle = BorderStyle.FixedSingle,
                BackColor = Color.Black
            };
            this.Controls.Add(pictureBox);

            // Status label
            statusLabel = new Label
            {
                Dock = DockStyle.Bottom,
                Height = 24,
                Text = "Starting servers..."
            };
            this.Controls.Add(statusLabel);

            // --- Panel for resize controls ---
            Panel resizePanel = new Panel
            {
                Height = 40,
                Dock = DockStyle.Top,
                BackColor = SystemColors.Control
            };

            Label widthLabel = new Label
            {
                Location = new Point(10, 10),
                Size = new Size(45, 20),
                Text = "Width:"
            };
            resizePanel.Controls.Add(widthLabel);

            widthUpDown = new NumericUpDown
            {
                Location = new Point(60, 8),
                Size = new Size(60, 20),
                Minimum = 16,
                Maximum = 1920,
                Value = currentWidth
            };
            resizePanel.Controls.Add(widthUpDown);

            Label heightLabel = new Label
            {
                Location = new Point(130, 10),
                Size = new Size(50, 20),
                Text = "Height:"
            };
            resizePanel.Controls.Add(heightLabel);

            heightUpDown = new NumericUpDown
            {
                Location = new Point(185, 8),
                Size = new Size(60, 20),
                Minimum = 16,
                Maximum = 1080,
                Value = currentHeight
            };
            resizePanel.Controls.Add(heightUpDown);

            resizeButton = new Button
            {
                Location = new Point(260, 6),
                Size = new Size(100, 26),
                Text = "Send Resize",
                UseVisualStyleBackColor = true
            };
            resizeButton.Click += OnResizeButtonClick;
            resizePanel.Controls.Add(resizeButton);

            this.Controls.Add(resizePanel);

            // Ensure pictureBox is at the back after all controls are added
            pictureBox.SendToBack();
        }
        private async void StartServers()
        {
            try
            {
                // Start frame receiver
                frameListener = new Socket(IPAddress.Parse(HOST), FRAME_PORT);
                frameListener.Start();
                UpdateStatus("Frame server started on port " + FRAME_PORT);

                // Start accepting connections
                _ = Task.Run(() => AcceptFrameConnections(cancellationTokenSource.Token));
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

                catch (ObjectDisposedException)
                {
                    break;
                }
                catch (Exception ex)
                {
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

private void DisplayFrame(byte[] frameData, int width, int height, int frameNumber)
{
    try
    {
        int expectedSize = width * height * 3;
        int sparseSize = width * height;

        // Initialize previous frame cache if needed
        if (previousFrameCache == null || previousFrameCache.Length != expectedSize)
            previousFrameCache = new byte[expectedSize];

        bool isSparse = frameData.Length == sparseSize;

        using (var bitmap = new Bitmap(width, height, PixelFormat.Format24bppRgb))
        {
            var bmpData = bitmap.LockBits(
                new Rectangle(0, 0, width, height),
                ImageLockMode.WriteOnly,
                PixelFormat.Format24bppRgb);

            try
            {
                unsafe
                {
                    byte* ptr = (byte*)bmpData.Scan0;
                    int stride = Math.Abs(bmpData.Stride);

                    if (isSparse)
                    {
                        // Each pixel is 1 byte: 0 = use previous, nonzero = new grayscale value
                        for (int y = 0; y < height; y++)
                        {
                            for (int x = 0; x < width; x++)
                            {
                                int idx = y * width + x;
                                int dstIdx = y * stride + x * 3;

                                byte val = frameData[idx];
                                if (val == 0)
                                {
                                    // Use previous
                                    ptr[dstIdx] = previousFrameCache[dstIdx];
                                    ptr[dstIdx + 1] = previousFrameCache[dstIdx + 1];
                                    ptr[dstIdx + 2] = previousFrameCache[dstIdx + 2];
                                }
                                else
                                {
                                    // New grayscale value
                                    ptr[dstIdx] = ptr[dstIdx + 1] = ptr[dstIdx + 2] = val;
                                    previousFrameCache[dstIdx] = previousFrameCache[dstIdx + 1] = previousFrameCache[dstIdx + 2] = val;
                                }
                            }
                        }
                    }
                    else if (frameData.Length >= expectedSize)
                    {
                        // Each pixel is 3 bytes: (R,G,B)
                        for (int y = 0; y < height; y++)
                        {
                            for (int x = 0; x < width; x++)
                            {
                                int idx = (y * width + x) * 3;
                                int dstIdx = y * stride + x * 3;

                                byte r = frameData[idx];
                                byte g = frameData[idx + 1];
                                byte b = frameData[idx + 2];

                                if (r == 0 && r == 1 && b == 0)
                                {
                                    // Use previous
                                    ptr[dstIdx] = previousFrameCache[dstIdx];
                                    ptr[dstIdx + 1] = previousFrameCache[dstIdx + 1];
                                    ptr[dstIdx + 2] = previousFrameCache[dstIdx + 2];
                                }
                                else
                                {
                                    // New pixel (convert RGB to BGR for bitmap)
                                    ptr[dstIdx] = b;
                                    ptr[dstIdx + 1] = g;
                                    ptr[dstIdx + 2] = r;
                                    previousFrameCache[dstIdx] = b;
                                    previousFrameCache[dstIdx + 1] = g;
                                    previousFrameCache[dstIdx + 2] = r;
                                }
                            }
                        }
                    }
                    else
                    {
                        UpdateStatus($"Frame {frameNumber} data size mismatch: {frameData.Length}");
                        return;
                    }
                }
            }
            finally
            {
                bitmap.UnlockBits(bmpData);
            }

            // Update UI
            if (InvokeRequired)
            {
                Invoke(new Action(() => {
                    var oldImage = pictureBox.Image;
                    pictureBox.Image = new Bitmap(bitmap);
                    oldImage?.Dispose();

                    if (frameNumber % 50 == 0)
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

if (message == "keep-alive")
{
    await writer.WriteLineAsync("ack");
}
else
{

}
                    catch (Exception ex)
                    {
                }
            }


                else
{
}
            catch (Exception ex)
            {
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


        private void OnFormClosing(object sender, FormClosingEventArgs e)
{
    cancellationTokenSource.Cancel();
    frameListener?.Stop();
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