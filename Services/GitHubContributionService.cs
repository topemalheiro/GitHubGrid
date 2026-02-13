using System.Diagnostics;
using System.Text.Json;
using System.Text.RegularExpressions;
using GitHubGrid.Models;

namespace GitHubGrid.Services;

public sealed partial class GitHubContributionService
{
    private const string GraphQLQuery = @"query($username:String!){user(login:$username){contributionsCollection{contributionCalendar{totalContributions weeks{contributionDays{contributionCount date contributionLevel}}}}}}";

    [GeneratedRegex(@"^[a-zA-Z0-9](?:[a-zA-Z0-9\-]*[a-zA-Z0-9])?$")]
    private static partial Regex ValidGitHubUsername();

    public async Task<string> GetUsernameAsync()
    {
        var (success, output) = await RunGhAsync("api user --jq .login");
        if (!success)
            throw new InvalidOperationException("Failed to get GitHub username. Ensure 'gh auth login' has been run.");

        var username = output.Trim();
        if (!ValidGitHubUsername().IsMatch(username))
            throw new InvalidOperationException("Invalid GitHub username format received.");

        return username;
    }

    public async Task<ContributionData> FetchContributionsAsync(string username)
    {
        if (!ValidGitHubUsername().IsMatch(username))
            throw new ArgumentException("Invalid GitHub username format.", nameof(username));

        var args = $"api graphql -f query=\"{GraphQLQuery}\" -F username=\"{username}\"";

        var (success, output) = await RunGhAsync(args);
        if (!success)
            throw new InvalidOperationException("Failed to fetch contribution data from GitHub.");

        return ParseContributionResponse(output);
    }

    private static ContributionData ParseContributionResponse(string json)
    {
        using var doc = JsonDocument.Parse(json);
        var calendar = doc.RootElement
            .GetProperty("data")
            .GetProperty("user")
            .GetProperty("contributionsCollection")
            .GetProperty("contributionCalendar");

        var totalContributions = calendar.GetProperty("totalContributions").GetInt32();

        var weeks = new List<ContributionWeek>();
        foreach (var weekElement in calendar.GetProperty("weeks").EnumerateArray())
        {
            var days = new List<ContributionDay>();
            foreach (var dayElement in weekElement.GetProperty("contributionDays").EnumerateArray())
            {
                var date = DateOnly.Parse(dayElement.GetProperty("date").GetString()!);
                var count = dayElement.GetProperty("contributionCount").GetInt32();
                var levelStr = dayElement.GetProperty("contributionLevel").GetString()!;
                var level = ParseContributionLevel(levelStr);

                days.Add(new ContributionDay(date, count, level));
            }
            weeks.Add(new ContributionWeek(days));
        }

        return new ContributionData(totalContributions, weeks, DateTime.Now);
    }

    private static ContributionLevel ParseContributionLevel(string level) => level switch
    {
        "NONE" => ContributionLevel.None,
        "FIRST_QUARTILE" => ContributionLevel.FirstQuartile,
        "SECOND_QUARTILE" => ContributionLevel.SecondQuartile,
        "THIRD_QUARTILE" => ContributionLevel.ThirdQuartile,
        "FOURTH_QUARTILE" => ContributionLevel.FourthQuartile,
        _ => ContributionLevel.None
    };

    private static async Task<(bool Success, string Output)> RunGhAsync(string arguments)
    {
        try
        {
            var startInfo = new ProcessStartInfo
            {
                FileName = "gh",
                Arguments = arguments,
                UseShellExecute = false,
                CreateNoWindow = true,
                RedirectStandardOutput = true,
                RedirectStandardError = true
            };

            using var process = Process.Start(startInfo)
                ?? throw new InvalidOperationException("Failed to start gh process");

            using var cts = new CancellationTokenSource(TimeSpan.FromSeconds(30));
            var output = await process.StandardOutput.ReadToEndAsync(cts.Token);
            var error = await process.StandardError.ReadToEndAsync(cts.Token);
            await process.WaitForExitAsync(cts.Token);

            return process.ExitCode == 0
                ? (true, output)
                : (false, string.IsNullOrEmpty(error) ? output : error);
        }
        catch (OperationCanceledException)
        {
            throw new InvalidOperationException("GitHub CLI request timed out.");
        }
        catch (System.ComponentModel.Win32Exception)
        {
            throw new InvalidOperationException(
                "GitHub CLI (gh) not found. Install from https://cli.github.com and run 'gh auth login'.");
        }
    }
}
