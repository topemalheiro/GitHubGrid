namespace GitHubGrid.Models;

public sealed record ContributionWeek(
    IReadOnlyList<ContributionDay> Days
);
