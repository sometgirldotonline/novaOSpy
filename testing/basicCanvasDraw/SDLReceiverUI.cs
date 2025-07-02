using System;
using System.Drawing;
using System.Drawing.Imaging;
using System.Windows.Forms;

namespace SDLReceiver
{
    public partial class MainForm : Form
    {
        private PictureBox pictureBox;
        private Label statusLabel;
        private Button resizeButton;
        private NumericUpDown widthUpDown;
        private NumericUpDown heightUpDown;

        private NetworkHandler networkHandler;
        private byte[] previousFrameCache;
        private int currentWidth = 64;
        private int currentHeight = 64;
        private bool uiVisible = true;

        public MainForm()
        {
            InitializeComponent();
            networkHandler = new NetworkHandler();
            networkHandler.FrameReceived += OnFrameReceived;
            networkHandler.FrameClientConnected += OnFrameClientConnected;
            networkHandler.Start();
        }

        private void InitializeComponent()
        {
            this.Size = new Size(800, 600);
            this.Text = "SDL Frame Receiver";
            this.FormClosing += OnFormClosing;
            this.KeyPreview = true;
            this.KeyDown += MainForm_KeyDown;

            pictureBox = new PictureBox
            {
                Dock = DockStyle.Fill,
                SizeMode = PictureBoxSizeMode.Zoom,
                BorderStyle = BorderStyle.FixedSingle,
                BackColor = Color.Black
            };
            this.Controls.Add(pictureBox);

            statusLabel = new Label
            {
                Dock = DockStyle.Bottom,
                Height = 24,
                Text = "Waiting for frames..."
            };
            this.Controls.Add(statusLabel);

            Panel resizePanel = new Panel
            {
                Height = 40,
                Dock = DockStyle.Top,
                BackColor = SystemColors.Control
            };

            Label widthLabel = new Label { Location = new Point(10, 10), Size = new Size(45, 20), Text = "Width:" };
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

            Label heightLabel = new Label { Location = new Point(130, 10), Size = new Size(50, 20), Text = "Height:" };
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
                Text = "Apply Resize"
            };
            resizeButton.Click += OnResizeButtonClick;
            resizePanel.Controls.Add(resizeButton);

            this.Controls.Add(resizePanel);
            pictureBox.SendToBack();
        }

        private void MainForm_KeyDown(object sender, KeyEventArgs e)
        {
            if (e.KeyCode == Keys.F19)
            {
                uiVisible = !uiVisible;
                foreach (Control ctrl in this.Controls)
                {
                    if (ctrl != pictureBox)
                        ctrl.Visible = uiVisible;
                }

                if (uiVisible)
                    UpdateStatus("UI shown (F19)");
            }
        }

        private void OnResizeButtonClick(object sender, EventArgs e)
        {
            currentWidth = (int)widthUpDown.Value;
            currentHeight = (int)heightUpDown.Value;
            UpdateStatus($"Resize applied: {currentWidth}x{currentHeight}");

            // Send the new resolution to the sender script
            networkHandler.SendCommand($"resolution {currentWidth} {currentHeight}");
        }

        private void OnFrameReceived(byte[] frameData, int width, int height, int frameNumber)
        {
            if (InvokeRequired)
            {
                Invoke(new Action(() => DisplayFrame(frameData, width, height, frameNumber)));
            }
            else
            {
                DisplayFrame(frameData, width, height, frameNumber);
            }
        }

        private void DisplayFrame(byte[] frameData, int width, int height, int frameNumber)
        {
            int expectedSize = width * height * 3;

            if (previousFrameCache == null || previousFrameCache.Length != expectedSize)
                previousFrameCache = new byte[expectedSize];

            using (var bitmap = new Bitmap(width, height, PixelFormat.Format24bppRgb))
            {
                var bmpData = bitmap.LockBits(new Rectangle(0, 0, width, height),
                                              ImageLockMode.WriteOnly,
                                              PixelFormat.Format24bppRgb);

                unsafe
                {
                    byte* ptr = (byte*)bmpData.Scan0;
                    int stride = Math.Abs(bmpData.Stride);

                    // This logic handles the differential frames sent by sdl.py
                    // where (0,0,0) means the pixel is unchanged.
                    // Note: This means true black (0,0,0) cannot be displayed with the current python script.
                    for (int y = 0; y < height; y++)
                    {
                        for (int x = 0; x < width; x++)
                        {
                            int idx = (y * width + x) * 3;
                            int dstIdx = y * stride + x * 3;

                            if (idx + 2 >= frameData.Length) continue;

                            byte r = frameData[idx];
                            byte g = frameData[idx + 1];
                            byte b = frameData[idx + 2];

                            if (r == 266 && g == 266 && b == 266)
                            {
                                // Unchanged pixel, use value from cache
                                if (dstIdx + 2 < previousFrameCache.Length)
                                {
                                    ptr[dstIdx] = previousFrameCache[dstIdx];
                                    ptr[dstIdx + 1] = previousFrameCache[dstIdx + 1];
                                    ptr[dstIdx + 2] = previousFrameCache[dstIdx + 2];
                                }
                            }
                            else
                            {
                                // New pixel, update bitmap and cache (convert RGB to BGR for bitmap)
                                ptr[dstIdx] = b;
                                ptr[dstIdx + 1] = g;
                                ptr[dstIdx + 2] = r;

                                if (dstIdx + 2 < previousFrameCache.Length)
                                {
                                    previousFrameCache[dstIdx] = b;
                                    previousFrameCache[dstIdx + 1] = g;
                                    previousFrameCache[dstIdx + 2] = r;
                                }
                            }
                        }
                    }
                }

                bitmap.UnlockBits(bmpData);
                var oldImage = pictureBox.Image;
                pictureBox.Image = new Bitmap(bitmap);
                oldImage?.Dispose();
            }

            if (frameNumber % 50 == 0)
                UpdateStatus($"✅ Frame {frameNumber}: {width}x{height}");
        }

        private void UpdateStatus(string message)
        {
            statusLabel.Text = $"{DateTime.Now:HH:mm:ss} - {message}";
        }

        private void OnFormClosing(object sender, FormClosingEventArgs e)
        {
            networkHandler.Stop();
        }

        private void OnFrameClientConnected(string remoteIp)
        {
            // Now connect the command channel using the actual remote IP
            networkHandler.ConnectCommandChannel(remoteIp, 6001);
        }
    }
}
