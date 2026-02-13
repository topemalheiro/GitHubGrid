namespace GitHubGrid.Models;

public enum ContributionLevel
{
    None,
    FirstQuartile,
    SecondQuartile,
    ThirdQuartile,
    FourthQuartile
}

public sealed record ContributionDay(
    DateOnly Date,
    int ContributionCount,
    ContributionLevel Level
);
