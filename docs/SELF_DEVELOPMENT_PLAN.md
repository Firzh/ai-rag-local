# Self Development Agent Plan

Repository: `Firzh/ai-rag-local`  
Target branch: `feature/self-develop-agents`  
Status: experimental  
Default mode: read-only planning  
Commit mode: guarded commit only  
Push mode: disabled  
Merge to main branch: human owner only  

---

## 1. Purpose

This document defines the initial design for a local self-development agent system for the `ai-rag-local` project.

The purpose is to allow the project to develop itself in a controlled local environment while the computer is on. The agent system must work only inside a dedicated branch, must produce verifiable changes, and must not mix experimental autonomous development with the main development branch.

This system does not replace the human developer. It assists with small, reviewable, testable development tasks.

Primary goals:

1. Read and understand selected project files.
2. Generate development plans.
3. Propose small code patches.
4. Review patches with a stronger model.
5. Apply only approved patches.
6. Run verification commands.
7. Update `CHANGELOG.md` for every commit.
8. Create a verification report for every commit.
9. Commit only through a guarded commit gate.
10. Prevent push and merge actions by agents.

---

## 2. Core Principle

The agent system must follow this rule:

```text
Junior Agent may draft patches.
Senior Agent must review and approve or rewrite patches.
Agent Runner applies only approved patches.
Commit Gate Script commits only after changelog and verification pass.
Human Owner is the only party allowed to push, merge, or release.
```

---

## 3. Branch Policy

Official working branch:

```bash
feature/self-develop-agents
```

Rules:

1. All self-development experiments must happen on `feature/self-develop-agents`.
2. Agents must not work on `master`, `main`, or any release branch.
3. Agents must not create pull requests automatically.
4. Agents must not merge into `master` or `main`.
5. Agents must not push to remote.
6. Human Owner decides whether a commit is worth keeping.
7. Human Owner decides whether a branch is safe to merge.

Branch validation command:

```bash
git branch --show-current
```

Expected output:

```text
feature/self-develop-agents
```

If the active branch is not `feature/self-develop-agents`, the workflow must stop.

---

## 4. System Roles

The system has five actors:

1. Junior Agent
2. Senior Agent
3. Agent Runner
4. Commit Gate Script
5. Human Owner

Each actor has a different authority level.

---

## 5. Junior Agent

Model:

```text
Qwen2.5 Coder 1.5B
```

Target RAM limit:

```text
4 GB
```

Primary function:

```text
Low-cost code reading, planning, and draft patch generation.
```

Allowed tasks:

1. Read selected files.
2. Summarize project structure.
3. Identify likely files related to a task.
4. Draft a development plan.
5. Draft a small patch.
6. Draft a simple test.
7. Draft changelog text.
8. Draft risk notes.

Forbidden actions:

1. Must not apply patches to the working tree.
2. Must not run `git commit`.
3. Must not run `git push`.
4. Must not merge branches.
5. Must not approve its own patch.
6. Must not modify secrets.
7. Must not modify local databases.
8. Must not modify generated data.
9. Must not change production-like config without Senior Agent approval.
10. Must not make broad architectural changes without Senior Agent review.

Junior Agent output directory:

```text
data/agent_workspace/plans/
data/agent_workspace/patches/
data/agent_workspace/notes/
```

Important rule:

```text
Junior Agent output is a proposal only. It is not a final repository change.
```

---

## 6. Senior Agent

Model:

```text
Qwen3 Coder 4B Q5_K_M
```

Target RAM limit:

```text
8 GB
```

Primary function:

```text
Technical review, risk control, final patch ownership, and commit approval.
```

Allowed tasks:

1. Review Junior Agent plans.
2. Review Junior Agent patches.
3. Reject unsafe patches.
4. Request a revision.
5. Rewrite a patch.
6. Create the final approved patch.
7. Decide verification commands.
8. Validate changelog content.
9. Validate verification report content.
10. Approve or reject commit eligibility.

Forbidden actions:

1. Must not push to remote.
2. Must not merge to `master` or `main`.
3. Must not directly bypass Agent Runner.
4. Must not directly bypass Commit Gate Script.
5. Must not approve commits without changelog.
6. Must not approve commits without verification report.
7. Must not approve commits if required tests fail.
8. Must not approve changes that touch denied paths.
9. Must not approve oversized patches unless the task explicitly allows it.
10. Must not approve destructive shell commands.

Senior Agent output directory:

```text
data/agent_workspace/reviews/
data/agent_workspace/final_patches/
data/agent_workspace/commit_notes/
```

Important rule:

```text
Senior Agent owns the final patch decision, but does not execute git commit directly.
```

---

## 7. Agent Runner

Agent Runner is a Python orchestrator.

Primary function:

```text
Execute the workflow, call agents, manage files, apply approved patches, and run verification.
```

Allowed tasks:

1. Read task manifest.
2. Check active branch.
3. Read allowed repository files.
4. Send selected context to Junior Agent.
5. Send plan and patch to Senior Agent.
6. Save all intermediate outputs.
7. Validate allowed paths.
8. Validate denied paths.
9. Apply only Senior-approved final patches.
10. Run verification commands.
11. Create verification report.
12. Call Commit Gate Script.

Forbidden actions:

1. Must not apply Junior patch directly.
2. Must not apply patch without Senior approval.
3. Must not commit directly unless acting through Commit Gate Script.
4. Must not push.
5. Must not merge.
6. Must not delete local data.
7. Must not run shell commands outside the allowlist.

Important rule:

```text
Agent Runner is the executor. It does not make technical approval decisions.
```

---

## 8. Commit Gate Script

Commit Gate Script is the final safety layer before `git commit`.

Primary function:

```text
Validate branch, diff, changelog, verification, approval, and then create a local commit.
```

Required checks:

1. Active branch is `feature/self-develop-agents`.
2. Working tree has only allowed changes.
3. Denied paths are untouched.
4. `CHANGELOG.md` is modified.
5. Verification report exists.
6. Required verification commands passed.
7. Senior Agent approval exists.
8. File change count is within task limit.
9. Line change count is within task limit.
10. Commit message follows the approved format.

Forbidden actions:

1. Must not push.
2. Must not merge.
3. Must not rebase.
4. Must not reset hard without Human Owner approval.
5. Must not commit if any required gate fails.

Important rule:

```text
Commit Gate Script is the only component that may execute git commit.
```

---

## 9. Human Owner

Human Owner is the repository owner or active developer.

Authority:

1. Create tasks.
2. Edit tasks.
3. Stop the agent system.
4. Approve or reject generated changes.
5. Reset local branch if needed.
6. Push to remote.
7. Merge to `master` or `main`.
8. Release a version.
9. Override agent recommendations.
10. Decide long-term architecture.

Important rule:

```text
Human Owner is the only actor allowed to push, merge, and release.
```

---

## 10. Patch Ownership

Patch ownership must be explicit.

Official rule:

```text
Junior Agent creates the draft patch.
Senior Agent reviews, revises, rejects, or rewrites the patch.
Agent Runner applies the Senior-approved final patch.
Commit Gate Script commits the verified result.
```

Detailed responsibility matrix:

| Activity | Junior Agent | Senior Agent | Agent Runner | Commit Gate Script | Human Owner |
|---|---:|---:|---:|---:|---:|
| Create task | No | No | No | No | Yes |
| Read task | Yes | Yes | Yes | Yes | Yes |
| Scan repository | Yes | Yes | Yes | No | Optional |
| Draft plan | Yes | Optional | No | No | Optional |
| Review plan | No | Yes | No | No | Optional |
| Draft patch | Yes | Optional | No | No | Optional |
| Review patch | No | Yes | No | No | Optional |
| Rewrite patch | No | Yes | No | No | Optional |
| Approve patch | No | Yes | No | No | Optional |
| Apply patch | No | No | Yes | No | Optional |
| Run verification | No | No | Yes | Optional | Optional |
| Draft changelog | Yes | Yes | Optional | No | Optional |
| Validate changelog | No | Yes | No | Yes | Optional |
| Approve commit | No | Yes | No | No | Optional |
| Execute commit | No | No | No | Yes | Optional |
| Push remote | No | No | No | No | Yes |
| Merge branch | No | No | No | No | Yes |

---

## 11. Operating Modes

The system must support three operating modes.

---

### 11.1 Read-only Planning Mode

Environment value:

```env
RAG_SELF_DEVELOP_MODE=plan
```

Allowed:

1. Read selected repository files.
2. Create repository scan report.
3. Create Junior Agent plan.
4. Create Senior Agent review.
5. Create risk assessment.

Not allowed:

1. Apply patch.
2. Modify repository files.
3. Commit.
4. Push.
5. Merge.

Recommended for:

1. Initial system testing.
2. Large task decomposition.
3. Architecture review.
4. Risk discovery.

---

### 11.2 Patch Proposal Mode

Environment value:

```env
RAG_SELF_DEVELOP_MODE=patch
```

Allowed:

1. Create draft patch.
2. Save patch to workspace.
3. Senior Agent reviews patch.
4. Senior Agent may rewrite patch.
5. Save final patch to workspace.

Not allowed:

1. Apply patch automatically.
2. Commit.
3. Push.
4. Merge.

Recommended for:

1. Safe patch preview.
2. Human review before apply.
3. Testing model output quality.

---

### 11.3 Guarded Commit Mode

Environment value:

```env
RAG_SELF_DEVELOP_MODE=commit
```

Allowed:

1. Senior Agent approves final patch.
2. Agent Runner applies final patch.
3. Agent Runner runs verification commands.
4. Changelog is updated.
5. Verification report is created.
6. Senior Agent approves commit.
7. Commit Gate Script creates a local commit.

Not allowed:

1. Push.
2. Merge.
3. Skip changelog.
4. Skip verification.
5. Commit if tests fail.
6. Commit if denied paths are touched.
7. Commit if branch is incorrect.

Recommended for:

1. Small, low-risk changes.
2. Documentation changes.
3. Test additions.
4. Isolated refactors.
5. Small bug fixes.

---

## 12. Directory Structure

Recommended new files and directories:

```text
docs/
├── SELF_DEVELOPMENT_PLAN.md
├── SELF_DEVELOPMENT_AGENT_POLICY.md
├── SELF_DEVELOPMENT_WORKFLOW.md
├── SELF_DEVELOPMENT_RESOURCE_LIMITS.md
├── SELF_DEVELOPMENT_CHANGELOG_RULES.md
├── SELF_DEVELOPMENT_VERIFICATION.md
└── templates/
    └── agent_task_manifest.template.yaml

app/
└── agents/
    ├── __init__.py
    ├── agent_runner.py
    ├── junior_agent.py
    ├── senior_agent.py
    ├── patch_manager.py
    ├── commit_gate.py
    ├── resource_guard.py
    ├── verification_runner.py
    └── task_manifest.py

data/
└── agent_workspace/
    ├── tasks/
    ├── plans/
    ├── patches/
    ├── final_patches/
    ├── reviews/
    ├── verification/
    ├── commit_notes/
    └── logs/
```

Runtime workspace should not be committed by default.

Add to `.gitignore`:

```gitignore
data/agent_workspace/
data/agent_runtime/
*.agent.log
*.patch.tmp
```

---

## 13. Allowed Paths

By default, agents may only change these paths:

```text
app/
docs/
tests/
scripts/
CHANGELOG.md
.env.sample
docker-compose.agent.yml
Dockerfile.agent
```

Path access must still depend on the task manifest.

A task may narrow allowed paths.

A task must not expand allowed paths without Human Owner approval.

---

## 14. Denied Paths

Agents must never modify these paths:

```text
.env
.env.local
.env.production
*.key
*.pem
*.crt
*.p12
data/chroma/
data/indexes/
data/quality/
data/cache/
data/answers/
data/evidence/
data/uploads/
data/raw/
```

If a diff touches any denied path, the Commit Gate Script must stop the commit.

---

## 15. Shell Command Policy

Agents must not run arbitrary shell commands.

Allowed command categories:

1. Git inspection.
2. Python validation.
3. Test execution.
4. Formatting if explicitly approved.
5. Safe file listing.

Initial allowlist:

```text
git status
git diff
git diff --stat
git branch --show-current
git log --oneline -n 10
python -m app.validate_models
python -m app.rag_regression_bench
python -m app.benchmarks.chunking_v2_smoke
python -m app.benchmarks.html_parser_smoke
python -m app.benchmarks.web_staging_smoke
python -m app.benchmarks.quality_gate_smoke
pytest
```

Forbidden commands:

```text
git push
git merge
git rebase
git reset --hard
git clean -fd
git checkout master
git checkout main
rm -rf
del /s
rmdir /s
docker system prune
docker volume rm
```

Destructive commands require explicit Human Owner approval.

---

## 16. Resource Limits

Target resource limits:

| Component | Model or Process | RAM Target | CPU Target | Notes |
|---|---|---:|---:|---|
| Junior Agent | Qwen2.5 Coder 1.5B | 4 GB | 2 CPU | Drafting and scanning |
| Senior Agent | Qwen3 Coder 4B Q5_K_M | 8 GB | 4 CPU | Review and final decision |
| Agent Runner | Python process | 2 GB | 2 CPU | Orchestration |

Recommended model parameters:

| Component | num_ctx | max_tokens | keep_alive |
|---|---:|---:|---|
| Junior Agent | 2048 | 700 | 0 or 1m |
| Senior Agent | 4096 | 1200 | 0 or 1m |

Runtime rules:

1. Run only one agent task at a time.
2. Do not run large ingestion while agents are active.
3. Do not rebuild Chroma or FTS indexes while Senior Agent is active.
4. Unload model after completion using short `keep_alive`.
5. Pause if RAM usage exceeds 80 percent.
6. Pause if CPU usage exceeds 85 percent.
7. Prefer small task batches.
8. Avoid long-context prompts unless required.

---

## 17. Container Strategy

Because the computer may still be used for other work, run the models in separate containers.

Recommended containers:

```text
ollama-junior
ollama-senior
agent-runner
```

Recommended ports:

```text
ollama-junior: 11435
ollama-senior: 11436
```

Recommended memory caps:

```text
ollama-junior: 4 GB
ollama-senior: 8 GB
agent-runner: 2 GB
```

Recommended CPU caps:

```text
ollama-junior: 2 CPUs
ollama-senior: 4 CPUs
agent-runner: 2 CPUs
```

Example `docker-compose.agent.yml`:

```yaml
services:
  ollama-junior:
    image: ollama/ollama:latest
    container_name: rag_ollama_junior
    ports:
      - "11435:11434"
    volumes:
      - ollama_junior:/root/.ollama
    mem_limit: 4g
    memswap_limit: 4g
    cpus: 2.0
    restart: unless-stopped

  ollama-senior:
    image: ollama/ollama:latest
    container_name: rag_ollama_senior
    ports:
      - "11436:11434"
    volumes:
      - ollama_senior:/root/.ollama
    mem_limit: 8g
    memswap_limit: 8g
    cpus: 4.0
    restart: unless-stopped

  agent-runner:
    build:
      context: .
      dockerfile: Dockerfile.agent
    container_name: rag_agent_runner
    working_dir: /workspace
    volumes:
      - .:/workspace
    environment:
      RAG_AGENT_JUNIOR_BASE_URL: http://ollama-junior:11434
      RAG_AGENT_SENIOR_BASE_URL: http://ollama-senior:11434
      RAG_SELF_DEVELOP_BRANCH: feature/self-develop-agents
      RAG_SELF_DEVELOP_ALLOW_COMMIT: "true"
      RAG_SELF_DEVELOP_ALLOW_PUSH: "false"
    depends_on:
      - ollama-junior
      - ollama-senior
    mem_limit: 2g
    memswap_limit: 2g
    cpus: 2.0

volumes:
  ollama_junior:
  ollama_senior:
```

---

## 18. Environment Variables

Add these values to `.env.sample`, not to private `.env` files.

```env
# Self development
RAG_SELF_DEVELOP_ENABLED=false
RAG_SELF_DEVELOP_MODE=plan
RAG_SELF_DEVELOP_BRANCH=feature/self-develop-agents
RAG_SELF_DEVELOP_ALLOW_COMMIT=true
RAG_SELF_DEVELOP_ALLOW_PUSH=false

# Junior agent
RAG_AGENT_JUNIOR_PROVIDER=ollama
RAG_AGENT_JUNIOR_BASE_URL=http://127.0.0.1:11435
RAG_AGENT_JUNIOR_MODEL=qwen2.5-coder:1.5b
RAG_AGENT_JUNIOR_MAX_RAM_GB=4
RAG_AGENT_JUNIOR_NUM_CTX=2048
RAG_AGENT_JUNIOR_MAX_TOKENS=700
RAG_AGENT_JUNIOR_KEEP_ALIVE=0

# Senior agent
RAG_AGENT_SENIOR_PROVIDER=ollama
RAG_AGENT_SENIOR_BASE_URL=http://127.0.0.1:11436
RAG_AGENT_SENIOR_MODEL=qwen3-coder-4b-q5km:latest
RAG_AGENT_SENIOR_MAX_RAM_GB=8
RAG_AGENT_SENIOR_NUM_CTX=4096
RAG_AGENT_SENIOR_MAX_TOKENS=1200
RAG_AGENT_SENIOR_KEEP_ALIVE=0

# Commit gate
RAG_AGENT_REQUIRE_CHANGELOG=true
RAG_AGENT_REQUIRE_VERIFICATION=true
RAG_AGENT_REQUIRE_TEST_PASS=true
RAG_AGENT_REQUIRE_CLEAN_BRANCH=true
RAG_AGENT_MAX_FILES_PER_TASK=8
RAG_AGENT_MAX_LINES_CHANGED=400

# Safety
RAG_AGENT_DENY_PATHS=.env,.env.local,.env.production,data/chroma,data/indexes,data/quality,data/cache,data/answers,data/evidence,data/uploads,data/raw
RAG_AGENT_ALLOW_PUSH=false

# Background mode
RAG_AGENT_BACKGROUND_MODE=true
RAG_AGENT_MAX_PARALLEL_TASKS=1
RAG_AGENT_PAUSE_ON_HIGH_RAM=true
RAG_AGENT_PAUSE_RAM_THRESHOLD_PERCENT=80
RAG_AGENT_PAUSE_CPU_THRESHOLD_PERCENT=85
```

---

## 19. Task Manifest

Every agent task must start with a task manifest.

Template path:

```text
docs/templates/agent_task_manifest.template.yaml
```

Template:

```yaml
task_id: "agent-YYYYMMDD-001"
branch: "feature/self-develop-agents"
title: ""
goal: ""
mode: "plan"
risk_level: "low"

allowed_paths:
  - "app/"
  - "docs/"
  - "tests/"
  - "scripts/"
  - "CHANGELOG.md"
  - ".env.sample"
  - "docker-compose.agent.yml"
  - "Dockerfile.agent"

denied_paths:
  - ".env"
  - ".env.local"
  - ".env.production"
  - "data/chroma/"
  - "data/indexes/"
  - "data/quality/"
  - "data/cache/"
  - "data/answers/"
  - "data/evidence/"
  - "data/uploads/"
  - "data/raw/"

max_files_changed: 8
max_lines_changed: 400

agents:
  junior:
    enabled: true
    can_create_patch: true
    can_apply_patch: false
    can_commit: false

  senior:
    enabled: true
    can_create_patch: true
    can_rewrite_patch: true
    can_approve_patch: true
    can_commit: false
    can_approve_commit: true

runner:
  can_apply_patch: true
  can_run_tests: true

commit_gate:
  can_commit: true
  can_push: false
  require_changelog: true
  require_verification_report: true
  require_test_pass: true

required_verification:
  - "python -m app.validate_models"
  - "python -m app.rag_regression_bench"

commit:
  type: "feat"
  scope: "agent"
  summary: ""
  allow_commit: true
  allow_push: false
```

---

## 20. Workflow Overview

Workflow:

```text
Human Task
→ Task Manifest
→ Branch Check
→ Repository Scan
→ Junior Plan
→ Senior Plan Review
→ Junior Draft Patch
→ Senior Patch Review
→ Senior Final Patch
→ Agent Runner Apply Patch
→ Verification Runner
→ Changelog Update
→ Verification Report
→ Senior Commit Approval
→ Commit Gate
→ Local Commit
```

---

## 21. Workflow Detail

### Step 1: Create Task

Human Owner creates a task manifest.

Output:

```text
data/agent_workspace/tasks/agent-YYYYMMDD-001.yaml
```

Required fields:

1. `task_id`
2. `branch`
3. `title`
4. `goal`
5. `mode`
6. `allowed_paths`
7. `denied_paths`
8. `required_verification`

---

### Step 2: Branch Check

Agent Runner checks the active branch.

Command:

```bash
git branch --show-current
```

If output is not:

```text
feature/self-develop-agents
```

The workflow stops.

---

### Step 3: Repository Scan

Agent Runner scans selected files.

Recommended scan inputs:

```text
README.md
CHANGELOG.md
pyproject.toml
requirements.txt
app/
tests/
docs/
```

Output:

```text
data/agent_workspace/plans/agent-YYYYMMDD-001.repo_scan.md
```

Scan report should include:

1. Relevant files.
2. Existing commands.
3. Existing tests.
4. Existing config patterns.
5. Potential risk areas.

---

### Step 4: Junior Plan

Junior Agent creates a development plan.

Output:

```text
data/agent_workspace/plans/agent-YYYYMMDD-001.junior_plan.md
```

Junior plan must include:

1. Task interpretation.
2. Files likely to change.
3. Proposed change list.
4. Expected tests.
5. Expected changelog entry.
6. Risk notes.
7. Whether patch generation is safe.

---

### Step 5: Senior Plan Review

Senior Agent reviews the Junior Plan.

Output:

```text
data/agent_workspace/reviews/agent-YYYYMMDD-001.senior_plan_review.md
```

Allowed Senior decisions:

```text
approve_plan
request_revision
reject_plan
rewrite_plan
```

A plan must be approved before patch generation in guarded workflows.

---

### Step 6: Junior Draft Patch

Junior Agent creates a draft patch if mode allows it.

Output:

```text
data/agent_workspace/patches/agent-YYYYMMDD-001.junior.patch
```

Junior draft patch must include:

1. Unified diff.
2. File list.
3. Expected behavior change.
4. Test suggestion.
5. Changelog suggestion.

This patch must not be applied directly.

---

### Step 7: Senior Patch Review

Senior Agent reviews the Junior patch.

Output:

```text
data/agent_workspace/reviews/agent-YYYYMMDD-001.senior_patch_review.md
```

Allowed Senior decisions:

```text
approve_patch
request_revision
rewrite_patch
reject_patch
```

If Senior chooses `rewrite_patch`, the Senior Agent produces a final patch.

---

### Step 8: Final Patch

Final patch path:

```text
data/agent_workspace/final_patches/agent-YYYYMMDD-001.final.patch
```

Final patch must include:

1. Only allowed paths.
2. No denied paths.
3. Limited file count.
4. Limited line count.
5. Changelog change.
6. Test or verification change if required.

Only final patch may be applied by Agent Runner.

---

### Step 9: Apply Patch

Agent Runner applies the final patch after safety checks.

Required pre-apply checks:

1. Branch is correct.
2. Working tree status is acceptable.
3. Patch does not touch denied paths.
4. Patch touches only allowed paths.
5. File count is within limit.
6. Line count is within limit.
7. Senior patch approval exists.

If any check fails, the workflow stops.

---

### Step 10: Verification

Agent Runner runs required verification commands.

Minimal commands:

```bash
python -m app.validate_models
python -m app.rag_regression_bench
```

Conditional commands:

If task touches chunking:

```bash
python -m app.benchmarks.chunking_v2_smoke
```

If task touches HTML parser:

```bash
python -m app.benchmarks.html_parser_smoke
```

If task touches web staging:

```bash
python -m app.benchmarks.web_staging_smoke
```

If task touches quality gate:

```bash
python -m app.benchmarks.quality_gate_smoke
```

If task touches tests:

```bash
pytest
```

Verification output path:

```text
data/agent_workspace/verification/agent-YYYYMMDD-001.verification.md
```

---

### Step 11: Changelog Update

Every commit must update `CHANGELOG.md`.

Required section:

```md
## Unreleased

### Added
- ...

### Changed
- ...

### Fixed
- ...

### Verification
- `command`: passed
```

If `CHANGELOG.md` is not changed, commit must be blocked.

---

### Step 12: Verification Report

Verification report must be generated before commit approval.

Report path:

```text
data/agent_workspace/verification/agent-YYYYMMDD-001.verification.md
```

Required content:

1. Task ID.
2. Branch.
3. Mode.
4. Changed files.
5. Patch ownership.
6. Commands run.
7. Test result.
8. Risk review.
9. Changelog status.
10. Senior approval.
11. Commit decision.

---

### Step 13: Senior Commit Approval

Senior Agent reviews the final state.

Senior Agent must review:

1. Final diff.
2. Changelog entry.
3. Verification report.
4. Test results.
5. Risk table.
6. Denied path status.

Allowed Senior decisions:

```text
approve_commit
request_fix
reject_commit
```

Commit may proceed only if decision is:

```text
approve_commit
```

---

### Step 14: Commit Gate

Commit Gate Script runs final checks.

Required checks:

1. Correct branch.
2. No denied paths.
3. Changelog updated.
4. Verification report exists.
5. Required tests passed.
6. Senior commit approval exists.
7. File change count is within limit.
8. Line change count is within limit.
9. Commit message is valid.

If all checks pass:

```bash
git add <allowed files>
git commit -m "type(scope): summary"
```

Push is still forbidden.

---

## 22. Changelog Rules

Every local agent commit must update `CHANGELOG.md`.

Required entry format:

```md
## Unreleased

### Added
- Added ...

### Changed
- Changed ...

### Fixed
- Fixed ...

### Verification
- `python -m app.validate_models`: passed
- `python -m app.rag_regression_bench`: passed
```

Rules:

1. Changelog must be factual.
2. Changelog must not exaggerate changes.
3. Changelog must mention verification commands.
4. Changelog must use clear categories.
5. Changelog must be updated in the same commit.
6. Changelog update must be validated by Senior Agent.
7. Commit Gate Script must block commit if changelog is unchanged.

---

## 23. Commit Message Format

Allowed commit types:

```text
feat
fix
docs
test
refactor
chore
ci
```

Format:

```text
type(scope): short summary

Verification:
- command 1: passed
- command 2: passed
- changelog: updated
- branch: feature/self-develop-agents
```

Example:

```text
feat(agent): add guarded self development task manifest

Verification:
- python -m app.validate_models: passed
- python -m app.rag_regression_bench: passed
- changelog: updated
- branch: feature/self-develop-agents
```

Rules:

1. Summary must be short and specific.
2. Scope should match the changed area.
3. Verification must list executed commands.
4. Commit message must not include secrets.
5. Commit message must not claim tests passed if they failed.

---

## 24. Verification Report Template

```md
# Agent Verification Report

## Task
- Task ID:
- Branch:
- Mode:
- Goal:

## Agent Roles
- Junior Agent:
- Senior Agent:
- Agent Runner:
- Commit Gate Script:

## Patch Ownership
- Draft patch created by:
- Final patch approved by:
- Patch applied by:
- Commit executed by:

## Changed Files
- file 1
- file 2

## Commands Run

| Command | Result | Notes |
|---|---|---|
| python -m app.validate_models | passed/failed | |
| python -m app.rag_regression_bench | passed/failed | |

## Risk Review

| Risk Area | Status | Notes |
|---|---|---|
| Runtime | low/medium/high | |
| Data | low/medium/high | |
| Security | low/medium/high | |
| Regression | low/medium/high | |
| Resource | low/medium/high | |

## Changelog
- CHANGELOG.md updated: yes/no

## Senior Approval
- Decision:
- Reason:

## Commit Decision
- Commit allowed: yes/no
- Commit message:
```

---

## 25. Resource Guard

Resource Guard should protect the host machine.

Responsibilities:

1. Check RAM usage before starting a task.
2. Check CPU usage before starting a task.
3. Pause if RAM exceeds threshold.
4. Pause if CPU exceeds threshold.
5. Enforce one active task.
6. Prefer short model keep-alive.
7. Avoid loading Senior Agent unless required.
8. Stop if system is under pressure.

Recommended thresholds:

```text
RAM pause threshold: 80%
CPU pause threshold: 85%
```

Recommended behavior:

```text
If system pressure is high, stop new task creation.
If Junior Agent is active, finish current short request then unload.
If Senior Agent is needed, wait until resource pressure is safe.
If verification is heavy, run only when explicitly required.
```

---

## 26. Background Usage Rules

Because the computer may be used for other tasks, agent runtime must be conservative.

Rules:

1. Run only one agent task at a time.
2. Do not run Senior Agent continuously.
3. Use short model keep-alive.
4. Avoid large context unless necessary.
5. Avoid large repository-wide analysis.
6. Avoid large indexing jobs.
7. Avoid heavy benchmarks unless task requires them.
8. Pause when RAM or CPU threshold is exceeded.
9. Save partial outputs before stopping.
10. Never continue a destructive action when system pressure is high.

---

## 27. Rollback Policy

If patch is applied but not committed:

```bash
git restore .
```

If commit exists but has not been pushed:

```bash
git reset --soft HEAD~1
```

If Human Owner explicitly wants to discard commit and changes:

```bash
git reset --hard HEAD~1
```

Agent restrictions:

1. Agent must not run `git reset --hard` without Human Owner approval.
2. Agent must not run `git clean -fd` without Human Owner approval.
3. Agent must not remove data directories.
4. Agent must not delete generated indexes.
5. Agent must not delete local databases.

---

## 28. Risk Controls

| Risk | Impact | Control |
|---|---|---|
| Agent modifies important files | Repository damage | Denied path gate |
| Agent commits bad code | Regression | Verification gate |
| Agent makes large changes | Hard to review | File and line limits |
| Changelog missing | Poor audit trail | Changelog gate |
| Verification missing | False confidence | Verification report gate |
| Model consumes too much RAM | Host slowdown | Container memory cap |
| Senior model stays loaded | Resource pressure | Short keep-alive |
| Agent pushes to remote | Unsafe propagation | Push disabled |
| Agent merges branch | Main branch contamination | Merge forbidden |
| Agent changes secrets | Security issue | Secret path denial |

---

## 29. Implementation Phases

### Phase 0: Documentation Foundation

Goal:

1. Create branch.
2. Add self-development plan.
3. Add policy documents.
4. Add initial changelog entry.

Commit:

```text
docs(agent): add self development planning documents
```

Expected files:

```text
docs/SELF_DEVELOPMENT_PLAN.md
docs/SELF_DEVELOPMENT_AGENT_POLICY.md
docs/SELF_DEVELOPMENT_WORKFLOW.md
CHANGELOG.md
```

---

### Phase 1: Task Manifest and Policy

Goal:

1. Add task manifest template.
2. Define allowed paths.
3. Define denied paths.
4. Define commit rules.
5. Define patch ownership.

Commit:

```text
docs(agent): define task manifest and policy rules
```

Expected files:

```text
docs/templates/agent_task_manifest.template.yaml
docs/SELF_DEVELOPMENT_AGENT_POLICY.md
docs/SELF_DEVELOPMENT_CHANGELOG_RULES.md
```

---

### Phase 2: Resource and Container Setup

Goal:

1. Add `.env.sample` agent values.
2. Add `docker-compose.agent.yml`.
3. Add resource limit documentation.
4. Add optional senior model Modelfile.

Commit:

```text
chore(agent): add resource-limited agent runtime config
```

Expected files:

```text
.env.sample
docker-compose.agent.yml
Dockerfile.agent
docs/SELF_DEVELOPMENT_RESOURCE_LIMITS.md
```

---

### Phase 3: Read-only Agent Runner

Goal:

1. Add Agent Runner in plan mode.
2. Read task manifest.
3. Check branch.
4. Create repository scan.
5. Produce Junior Plan.
6. Produce Senior Review.
7. No file modification.

Commit:

```text
feat(agent): add read-only planning runner
```

Expected files:

```text
app/agents/agent_runner.py
app/agents/task_manifest.py
app/agents/junior_agent.py
app/agents/senior_agent.py
```

---

### Phase 4: Patch Proposal Workflow

Goal:

1. Junior Agent creates draft patch.
2. Senior Agent reviews patch.
3. Patch is saved to workspace.
4. Patch is not automatically applied.

Commit:

```text
feat(agent): add patch proposal workflow
```

Expected files:

```text
app/agents/patch_manager.py
app/agents/junior_agent.py
app/agents/senior_agent.py
```

---

### Phase 5: Guarded Patch Apply

Goal:

1. Senior Agent creates final patch.
2. Agent Runner validates final patch.
3. Agent Runner applies final patch.
4. Denied path gate is active.
5. File and line limits are active.

Commit:

```text
feat(agent): add guarded patch apply workflow
```

Expected files:

```text
app/agents/patch_manager.py
app/agents/agent_runner.py
app/agents/resource_guard.py
```

---

### Phase 6: Verification Runner

Goal:

1. Run required verification commands.
2. Save verification output.
3. Create verification report.
4. Stop workflow if verification fails.

Commit:

```text
feat(agent): add verification runner
```

Expected files:

```text
app/agents/verification_runner.py
docs/SELF_DEVELOPMENT_VERIFICATION.md
```

---

### Phase 7: Guarded Commit

Goal:

1. Validate changelog.
2. Validate verification report.
3. Validate Senior approval.
4. Create local commit.
5. Keep push disabled.

Commit:

```text
feat(agent): add guarded commit workflow
```

Expected files:

```text
app/agents/commit_gate.py
docs/SELF_DEVELOPMENT_CHANGELOG_RULES.md
```

---

## 30. Definition of Done

A self-development task is done only if:

1. Task manifest exists.
2. Branch is correct.
3. Repository scan exists.
4. Junior Plan exists.
5. Senior Plan Review exists.
6. Draft patch exists if mode is `patch` or `commit`.
7. Final patch exists if mode is `commit`.
8. Patch does not touch denied paths.
9. Patch stays within file and line limits.
10. Verification commands passed.
11. `CHANGELOG.md` is updated.
12. Verification report exists.
13. Senior Agent approved commit.
14. Commit Gate Script created local commit.
15. No push occurred.
16. No merge occurred.
17. Human Owner can review all outputs.

---

## 31. Merge Policy

Agent commits must not be merged automatically.

Before Human Owner merges to `master` or `main`:

1. Read all agent commits.
2. Read changelog.
3. Read verification reports.
4. Re-run regression checks.
5. Confirm no denied paths changed.
6. Confirm no secrets leaked.
7. Confirm runtime behavior is safe.
8. Confirm resource configuration is acceptable.
9. Squash or clean commits if necessary.
10. Merge manually.

Agent has no merge authority.

---

## 32. Final Safety Rule

The final safety rule is:

```text
No changelog, no commit.
No verification report, no commit.
No Senior approval, no commit.
Wrong branch, no commit.
Denied path touched, no commit.
Human Owner only for push and merge.
```
