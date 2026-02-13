using System.ComponentModel;
using System.Diagnostics;
using System.Runtime.CompilerServices;
using System.Windows;
using System.Windows.Input;
using GitHubGrid.Models;
using GitHubGrid.Services;

namespace GitHubGrid.ViewModels;

public sealed class ContributionGridViewModel : INotifyPropertyChanged
{
    private readonly GitHubContributionService _contributionService = new();
    private readonly AutoRefreshService _autoRefreshService = new();

    private ContributionData? _contributionData;
    private string _username = "";
    private string _statusText = "Loading...";
    private bool _isLoading;

    public ContributionData? ContributionData
    {
        get => _contributionData;
        private set { _contributionData = value; OnPropertyChanged(); }
    }

    public string Username
    {
        get => _username;
        private set { _username = value; OnPropertyChanged(); }
    }

    public string StatusText
    {
        get => _statusText;
        private set { _statusText = value; OnPropertyChanged(); }
    }

    public bool IsLoading
    {
        get => _isLoading;
        private set { _isLoading = value; OnPropertyChanged(); }
    }

    public ICommand RefreshCommand { get; }
    public ICommand QuitCommand { get; }

    public event Action? ContributionDataChanged;

    public ContributionGridViewModel()
    {
        RefreshCommand = new RelayCommand(_ => _ = RefreshAsync());
        QuitCommand = new RelayCommand(_ => Application.Current.Shutdown());

        _autoRefreshService.RefreshTriggered += async (_, _) =>
        {
            try { await RefreshAsync(); }
            catch (Exception ex) { Debug.WriteLine($"Auto-refresh failed: {ex.Message}"); }
        };
    }

    public async Task InitializeAsync()
    {
        IsLoading = true;
        StatusText = "Loading...";

        try
        {
            Username = await _contributionService.GetUsernameAsync();
            await RefreshAsync();
            _autoRefreshService.Start(20);
        }
        catch (Exception ex)
        {
            Debug.WriteLine($"Initialize failed: {ex}");
            StatusText = "Failed to connect. Check gh CLI authentication.";
            IsLoading = false;
        }
    }

    public async Task RefreshAsync()
    {
        if (string.IsNullOrEmpty(Username)) return;

        IsLoading = true;
        StatusText = "Refreshing...";

        try
        {
            var data = await _contributionService.FetchContributionsAsync(Username);
            ContributionData = data;
            StatusText = $"{data.TotalContributions} contributions in the last year";
            ContributionDataChanged?.Invoke();
        }
        catch (Exception ex)
        {
            Debug.WriteLine($"Refresh failed: {ex}");
            StatusText = "Failed to refresh. Check internet connection.";
        }
        finally
        {
            IsLoading = false;
        }
    }

    public event PropertyChangedEventHandler? PropertyChanged;

    private void OnPropertyChanged([CallerMemberName] string? propertyName = null)
    {
        PropertyChanged?.Invoke(this, new PropertyChangedEventArgs(propertyName));
    }
}
