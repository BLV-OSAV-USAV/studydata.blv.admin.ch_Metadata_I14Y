# I14Y Harvester

## Project Structure

For each agent:

- .github/workflows/[agent-workflow].yml: GitHub Actions workflow file for the specific organization and purpose
- scripts/[agent]/harvester.py: Main Python script for data harvesting
- scripts/[agent]/mapping.py: Python script containing the data mapping function

## Workflow

- The frequency at which the workflow runs is defined in the corresponding yml file.
- It can also be triggered or disabled manually from the Actions tab.
- After each run, a log file is generated and uploaded as an artifact, which can be downloaded from the Actions tab.

