# Contributing

## Development Model

This project follows **trunk-based development**. All work is done on short-lived branches merged directly into `main`.

- Keep branches small and short-lived (ideally < 1 day)
- No long-lived feature branches
- Use feature flags for incomplete work that needs to be merged

## Branch Naming

Follow [Conventional Branch](https://conventional-branch.github.io/):

```
<type>/<description>
```

### Types

| Type       | Purpose                          | Example                          |
|------------|----------------------------------|----------------------------------|
| `feat/`    | New feature                      | `feat/add-review-dashboard`      |
| `fix/`     | Bug fix                          | `fix/webhook-payload-parsing`    |
| `hotfix/`  | Urgent production fix            | `hotfix/auth-token-expiry`       |
| `chore/`   | Maintenance, deps, config        | `chore/update-dependencies`      |
| `docs/`    | Documentation only               | `docs/api-usage-guide`           |
| `refactor/`| Code restructuring               | `refactor/extract-gitlab-client` |
| `ci/`      | CI/CD changes                    | `ci/add-lint-stage`              |
| `test/`    | Test additions or fixes          | `test/webhook-handler-coverage`  |

### Rules

- Lowercase only (a-z, 0-9, hyphens)
- No consecutive, leading, or trailing hyphens
- Include ticket number when applicable: `feat/issue-42-queue-priority`

## Commit Messages

Follow [Conventional Commits v1.0.0](https://www.conventionalcommits.org/en/v1.0.0/):

```
<type>[optional scope]: <description>

[optional body]

[optional footer(s)]
```

### Types

| Type       | Purpose                                |
|------------|----------------------------------------|
| `feat`     | New feature (MINOR in SemVer)          |
| `fix`      | Bug fix (PATCH in SemVer)              |
| `docs`     | Documentation only                     |
| `style`    | Formatting, no code change             |
| `refactor` | Neither fix nor feature                |
| `perf`     | Performance improvement                |
| `test`     | Adding or fixing tests                 |
| `build`    | Build system or external deps          |
| `ci`       | CI/CD configuration                    |
| `chore`    | Other maintenance                      |
| `revert`   | Reverts a previous commit              |

### Rules

- Subject line: max 72 characters
- Use imperative mood: "add feature" not "added feature"
- Scope is optional: `feat(dashboard): add queue panel`
- Breaking changes: append `!` before colon or add `BREAKING CHANGE:` footer

### Examples

```
feat(webhook): add gitlab merge request handler

fix: correct token refresh logic on expired sessions

refactor(squad)!: rename specialist roles

BREAKING CHANGE: specialist role keys changed from snake_case to kebab-case

chore(deps): bump fastapi to 0.115
```
