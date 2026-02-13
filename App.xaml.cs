using System.Drawing;
using System.Drawing.Drawing2D;
using System.Windows;
using System.Windows.Controls;
using Hardcodet.Wpf.TaskbarNotification;
using GitHubGrid.ViewModels;
using GitHubGrid.Views;

namespace GitHubGrid;

public partial class App : Application
{
    private TaskbarIcon? _trayIcon;
    private ContributionGridWindow? _gridWindow;
    private ContributionGridViewModel? _viewModel;

    protected override async void OnStartup(StartupEventArgs e)
    {
        base.OnStartup(e);

        _viewModel = new ContributionGridViewModel();
        _gridWindow = new ContributionGridWindow(_viewModel);

        _trayIcon = new TaskbarIcon
        {
            Icon = CreateTrayIcon(),
            ToolTipText = "GitHubGrid",
            ContextMenu = CreateContextMenu()
        };

        _trayIcon.TrayLeftMouseUp += (_, _) => ToggleGridWindow();

        try
        {
            await _viewModel.InitializeAsync();
            _gridWindow.RenderGrid();
        }
        catch (Exception ex)
        {
            _trayIcon.ShowBalloonTip(
                "GitHubGrid",
                $"Failed to load: {ex.Message}",
                BalloonIcon.Error);
        }
    }

    private void ToggleGridWindow()
    {
        if (_gridWindow is null) return;

        if (_gridWindow.IsVisible)
        {
            _gridWindow.Hide();
        }
        else
        {
            _gridWindow.Show();
            _gridWindow.PositionNearTray();
            _gridWindow.Activate();
        }
    }

    private ContextMenu CreateContextMenu()
    {
        var menu = new ContextMenu();

        var refreshItem = new MenuItem { Header = "Refresh" };
        refreshItem.Click += async (_, _) =>
        {
            if (_viewModel is not null) await _viewModel.RefreshAsync();
        };

        var exitItem = new MenuItem { Header = "Exit" };
        exitItem.Click += (_, _) =>
        {
            _trayIcon?.Dispose();
            Shutdown();
        };

        menu.Items.Add(refreshItem);
        menu.Items.Add(new Separator());
        menu.Items.Add(exitItem);

        return menu;
    }

    private static Icon CreateTrayIcon()
    {
        var bitmap = new Bitmap(32, 32);
        using var g = Graphics.FromImage(bitmap);
        g.SmoothingMode = SmoothingMode.AntiAlias;
        g.Clear(Color.Transparent);

        // Draw a mini contribution grid (4x4)
        var colors = new[] {
            Color.FromArgb(0x0E, 0x44, 0x29),
            Color.FromArgb(0x00, 0x6D, 0x32),
            Color.FromArgb(0x26, 0xA6, 0x41),
            Color.FromArgb(0x39, 0xD3, 0x53)
        };

        var rng = new Random(42);
        for (var row = 0; row < 4; row++)
        {
            for (var col = 0; col < 4; col++)
            {
                var color = colors[rng.Next(colors.Length)];
                using var brush = new SolidBrush(color);
                g.FillRoundedRectangle(brush, col * 8, row * 8, 6, 6, 1);
            }
        }

        var handle = bitmap.GetHicon();
        return Icon.FromHandle(handle);
    }

    protected override void OnExit(ExitEventArgs e)
    {
        _trayIcon?.Dispose();
        base.OnExit(e);
    }
}

internal static class GraphicsExtensions
{
    public static void FillRoundedRectangle(this Graphics g, Brush brush, int x, int y, int w, int h, int r)
    {
        using var path = new GraphicsPath();
        path.AddArc(x, y, r * 2, r * 2, 180, 90);
        path.AddArc(x + w - r * 2, y, r * 2, r * 2, 270, 90);
        path.AddArc(x + w - r * 2, y + h - r * 2, r * 2, r * 2, 0, 90);
        path.AddArc(x, y + h - r * 2, r * 2, r * 2, 90, 90);
        path.CloseFigure();
        g.FillPath(brush, path);
    }
}
