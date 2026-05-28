#include <unistd.h>
#include <stdlib.h>

int main(void) {
    const char *dir = "/home/tope/Projects/OS Toolkit/GitHubGrid";
    const char *python = "/home/tope/github-grid/.venv/bin/python";

    if (chdir(dir) != 0) {
        return 1;
    }

    execl(python, "python", "-m", "github_grid", (char *)NULL);
    return 1;
}
