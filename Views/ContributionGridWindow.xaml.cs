using System.Globalization;
using System.Windows;
using System.Windows.Controls;
using System.Windows.Media;
using System.Windows.Shapes;
using GitHubGrid.Models;
using GitHubGrid.ViewModels;

namespace GitHubGrid.Views;

public partial class ContributionGridWindow : Window
{
    private const int CellSize = 13;
    private const int CellGap = 3;
    private const int CellStride = CellSize + CellGap;

    private readonly ContributionGridViewModel _viewModel;

    public ContributionGridWindow(ContributionGridViewModel viewModel)
    {
        InitializeComponent();
        _viewModel = viewModel;
        DataContext = viewModel;
        viewModel.ContributionDataChanged += () => Dispatcher.Invoke(RenderGrid);
        RenderLegend();
        RenderDayLabels();
    }

    public void RenderGrid()
    {
        RenderContributionCells();
        RenderMonthLabels();
        UpdateTodayContribution();
    }

    private void RenderContributionCells()
    {
        ContributionCanvas.Children.Clear();
        var data = _viewModel.ContributionData;
        if (data is null) return;

        for (var weekIdx = 0; weekIdx < data.Weeks.Count; weekIdx++)
        {
            var week = data.Weeks[weekIdx];
            for (var dayIdx = 0; dayIdx < week.Days.Count; dayIdx++)
            {
                var day = week.Days[dayIdx];

                var rowIdx = (int)day.Date.DayOfWeek;

                var rect = new Rectangle
                {
                    Width = CellSize,
                    Height = CellSize,
                    RadiusX = 2,
                    RadiusY = 2,
                    Fill = new SolidColorBrush(GetColorForLevel(day.Level)),
                    ToolTip = FormatTooltip(day)
                };

                ToolTipService.SetInitialShowDelay(rect, 50);
                ToolTipService.SetBetweenShowDelay(rect, 0);
                ToolTipService.SetShowDuration(rect, 30000);

                Canvas.SetLeft(rect, weekIdx * CellStride);
                Canvas.SetTop(rect, rowIdx * CellStride);
                ContributionCanvas.Children.Add(rect);
            }
        }

        ContributionCanvas.Width = data.Weeks.Count * CellStride - CellGap;
        ContributionCanvas.Height = 7 * CellStride - CellGap;
    }

    private void RenderMonthLabels()
    {
        MonthLabelsCanvas.Children.Clear();
        var data = _viewModel.ContributionData;
        if (data is null) return;

        MonthLabelsCanvas.Width = data.Weeks.Count * CellStride - CellGap;

        var lastMonth = -1;
        for (var weekIdx = 0; weekIdx < data.Weeks.Count; weekIdx++)
        {
            var week = data.Weeks[weekIdx];
            if (week.Days.Count == 0) continue;

            var firstDay = week.Days[0];
            var month = firstDay.Date.Month;

            if (month != lastMonth)
            {
                lastMonth = month;
                var label = new TextBlock
                {
                    Text = CultureInfo.CurrentCulture.DateTimeFormat.GetAbbreviatedMonthName(month),
                    FontSize = 10,
                    FontFamily = new FontFamily("Segoe UI"),
                    Foreground = (SolidColorBrush)FindResource("SecondaryTextBrush")
                };
                Canvas.SetLeft(label, weekIdx * CellStride);
                Canvas.SetTop(label, 0);
                MonthLabelsCanvas.Children.Add(label);
            }
        }
    }

    private void RenderDayLabels()
    {
        DayLabelsCanvas.Children.Clear();
        DayLabelsCanvas.Height = 7 * CellStride - CellGap;

        var dayNames = new (int row, string name)[] { (1, "Mon"), (3, "Wed"), (5, "Fri") };

        foreach (var (row, name) in dayNames)
        {
            var label = new TextBlock
            {
                Text = name,
                FontSize = 10,
                FontFamily = new FontFamily("Segoe UI"),
                Foreground = (SolidColorBrush)FindResource("SecondaryTextBrush")
            };
            Canvas.SetLeft(label, 0);
            Canvas.SetTop(label, row * CellStride + 1);
            DayLabelsCanvas.Children.Add(label);
        }
    }

    private void RenderLegend()
    {
        var levels = new[] {
            ContributionLevel.None,
            ContributionLevel.FirstQuartile,
            ContributionLevel.SecondQuartile,
            ContributionLevel.ThirdQuartile,
            ContributionLevel.FourthQuartile
        };

        for (var i = 0; i < levels.Length; i++)
        {
            var rect = new Rectangle
            {
                Width = 11,
                Height = 11,
                RadiusX = 2,
                RadiusY = 2,
                Fill = new SolidColorBrush(GetColorForLevel(levels[i]))
            };
            Canvas.SetLeft(rect, i * 15);
            Canvas.SetTop(rect, 1);
            LegendCanvas.Children.Add(rect);
        }
    }

    private static Color GetColorForLevel(ContributionLevel level) => level switch
    {
        ContributionLevel.None => (Color)ColorConverter.ConvertFromString("#161B22"),
        ContributionLevel.FirstQuartile => (Color)ColorConverter.ConvertFromString("#0E4429"),
        ContributionLevel.SecondQuartile => (Color)ColorConverter.ConvertFromString("#006D32"),
        ContributionLevel.ThirdQuartile => (Color)ColorConverter.ConvertFromString("#26A641"),
        ContributionLevel.FourthQuartile => (Color)ColorConverter.ConvertFromString("#39D353"),
        _ => (Color)ColorConverter.ConvertFromString("#161B22")
    };

    private static string FormatTooltip(ContributionDay day)
    {
        var count = day.ContributionCount == 0
            ? "No contributions"
            : $"{day.ContributionCount} contribution{(day.ContributionCount == 1 ? "" : "s")}";

        return $"{count} on {day.Date.ToString("MMMM d", CultureInfo.InvariantCulture)}{GetDaySuffix(day.Date.Day)}.";
    }

    private static string GetDaySuffix(int day) => day switch
    {
        1 or 21 or 31 => "st",
        2 or 22 => "nd",
        3 or 23 => "rd",
        _ => "th"
    };

    public void PositionNearTray()
    {
        var workArea = SystemParameters.WorkArea;
        Left = workArea.Right - ActualWidth - 16;
        Top = workArea.Bottom - ActualHeight - 16;
    }

    private void UpdateTodayContribution()
    {
        var data = _viewModel.ContributionData;
        if (data is null) return;

        var today = DateOnly.FromDateTime(DateTime.Now);
        var todayContribution = data.Weeks
            .SelectMany(w => w.Days)
            .FirstOrDefault(d => d.Date == today);

        if (todayContribution is not null)
        {
            var count = todayContribution.ContributionCount;
            TodayContributionText.Text = count == 0
                ? "No contributions today"
                : $"{count} contribution{(count == 1 ? "" : "s")} today";
        }
        else
        {
            TodayContributionText.Text = "";
        }
    }

    private void Window_Deactivated(object? sender, EventArgs e)
    {
        Hide();
    }
}
