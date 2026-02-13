namespace GitHubGrid.Models;

public sealed record ContributionData(
    int TotalContributions,
    IReadOnlyList<ContributionWeek> Weeks,
    DateTime FetchedAt
);
