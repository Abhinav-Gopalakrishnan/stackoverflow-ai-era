# CLI publication: 14 work commits, 10 issues, 6 PRs, 6 project tasks

These are user-run commands. Preparing this guide/helper does not stage, commit, push, create issues, create project items, or open/merge PRs.

Rishiikesh branch: `m2/review2-text-mining` (already created).

Adhikkesh branch: `m5/review2-forecasting` (created from updated main after all Rishiikesh PRs are merged).

Each member has a separate branch and can have one open PR from that branch against main at a time. Use three sequential batches per member: 2 commits, 2 commits, 3 commits. Finish and merge all three Rishiikesh PRs first, then create Adhikkesh's branch from main. Rishiikesh goes first because forecasting imports the shared corpus utilities.

`--merge` preserves all 14 work commits. GitHub also creates six PR merge commits; the resulting main history therefore contains 14 work commits plus 6 merge commits. Squash merging would not preserve the seven separate work commits per person.

## 1. Authenticate and prepare

```bash
cd /home/adhikkesh/adhikkesh/SEM7/BA/stackoverflow-ai-era

gh auth status
```

Both accounts must be stored in gh: `Adhikkesh` and `Rishiikesh-20`. If Rishiikesh is not stored, run this and authenticate his account. For an entirely terminal-based login, choose "Paste an authentication token" at the prompt using his token with repo/read:org/project permissions; browser device login is also available:

```bash
gh auth login --hostname github.com --git-protocol https --scopes project
```

The helper sets repository-local Git author name and a GitHub noreply email derived from the logged-in account's numeric ID. Authentication and Git author identity are both checked. The init command retains/creates the requested branch and switches origin to HTTPS so the gh credential helper controls which account pushes.

```bash
python scripts/review2_git_workflow.py init m2
python scripts/review2_git_workflow.py plan
```

The plan command is read-only. It prints all 14 commit groups and rejects unassigned files or overlaps. No full ignored corpus, per-question private parquet, dictionary cache or credentials are staged.

## 2. Create Rishiikesh's five issues and three project tasks

```bash
python scripts/review2_git_workflow.py identity m2
gh auth refresh --hostname github.com --scopes project
python scripts/review2_git_workflow.py issues m2

```

Each member receives five assigned repo issues. Three of those issues are added as tasks to project 3 owned by Abhinav-Gopalakrishnan. No extra draft tasks are needed.

Adhikkesh's issues are created later in step 4, after his own branch is created. Do not switch identities to publish M5 commits on the M2 branch. The helper rejects a mismatched branch or account.

- Rishiikesh project tasks: corpus; independent tone/topic review; notebook/slides/handoff.
- Adhikkesh project tasks: series; evaluation; forecasts/joint ITS interpretation.

Issue titles use G1–G5 publication groups; their bodies list the exact Review 2 plan task IDs. Project fields include status, reviewer, rubric, phase and original plan deadlines. The existing project's Phase options are 0–5, so stages 4/5 are reused; Review 2 is explicit in every new title. No existing project field/options are modified.

Local IDs are saved in ignored `.review2_git_state.json`. Keep it until publication is complete. Re-running the issues command resumes from recorded issues instead of creating duplicates.

## 3. Rishiikesh: seven commits and three PRs

```bash
python scripts/review2_git_workflow.py identity m2

# Two commits; push; create corpus PR; request Nishanth's review.
python scripts/review2_git_workflow.py batch m2 1
# After the PR has been checked:
python scripts/review2_git_workflow.py merge m2 1

# Two more commits; push; create tone/validation-workflow PR.
python scripts/review2_git_workflow.py batch m2 2
# After review:
python scripts/review2_git_workflow.py merge m2 2

# Three more commits; push; create complexity/notebook/slides PR.
python scripts/review2_git_workflow.py batch m2 3
# After review:
python scripts/review2_git_workflow.py merge m2 3
```

If you prefer each commit separately, replace any batch command with its individual commits and a pr command. For example:

```bash
python scripts/review2_git_workflow.py commit m2 1
python scripts/review2_git_workflow.py commit m2 2
python scripts/review2_git_workflow.py pr m2 1
```

Batch 2 uses commits 3/4; batch 3 uses commits 5/6/7. Each commit message references its actual issue number. The helper stages only that commit's explicit paths and stops if the index already contains unrelated staged work.

## 4. Adhikkesh: seven commits and three PRs

Only after all three Rishiikesh PRs are merged, create Adhikkesh's branch from updated main. Pending local M5 files carry over without being staged on Rishiikesh's branch.

```bash
python scripts/review2_git_workflow.py init m5
python scripts/review2_git_workflow.py identity m5
python scripts/review2_git_workflow.py issues m5

python scripts/review2_git_workflow.py batch m5 1
# After Akshay's review:
python scripts/review2_git_workflow.py merge m5 1

python scripts/review2_git_workflow.py batch m5 2
# After review:
python scripts/review2_git_workflow.py merge m5 2

python scripts/review2_git_workflow.py batch m5 3
# After review:
python scripts/review2_git_workflow.py merge m5 3
```

Each merge preserves the local branch, fetches main, and fast-forwards the branch to main for its next PR. It never force-pushes, resets, stashes, rewrites author dates, or fakes reviews. If Git reports a conflict from another person's concurrent main changes, stop and inspect it; do not force the branch forward.

GitHub notifications are sent when YOU run the issue/PR commands; the prepared helper itself has not contacted anyone.

## 5. Verify

```bash
python scripts/review2_git_workflow.py status
git status --short
gh pr list --repo Abhinav-Gopalakrishnan/stackoverflow-ai-era --state all --head m2/review2-text-mining
gh pr list --repo Abhinav-Gopalakrishnan/stackoverflow-ai-era --state all --head m5/review2-forecasting
gh project item-list 3 --owner Abhinav-Gopalakrishnan --format json
```

The expected publication count is five issues, seven work commits, three PRs and three project tasks for each member. Two issues remain open intentionally:

- Rishiikesh's independent human tone validation/topic review.
- Adhikkesh's integrated forecast/ITS interpretation awaiting Akshay.

Completed issues use `Closes #N` in PR bodies. Pending issues use `Refs #N`, and their project Evidence field links to the PR while their status remains In Progress. Completed task cards move to Completed only on actual merge. Full corpora and per-question metadata remain Drive handoffs.
