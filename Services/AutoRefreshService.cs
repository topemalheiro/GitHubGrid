namespace GitHubGrid.Services;

public sealed class AutoRefreshService : IDisposable
{
    private System.Timers.Timer? _timer;
    private bool _disposed;

    public event EventHandler? RefreshTriggered;

    public void Start(int intervalMinutes)
    {
        Stop();
        _timer = new System.Timers.Timer(intervalMinutes * 60_000);
        _timer.Elapsed += (_, _) => RefreshTriggered?.Invoke(this, EventArgs.Empty);
        _timer.AutoReset = true;
        _timer.Start();
    }

    public void Stop()
    {
        _timer?.Stop();
        _timer?.Dispose();
        _timer = null;
    }

    public void Dispose()
    {
        if (_disposed) return;
        Stop();
        _disposed = true;
    }
}
