# Contributing to AgriLink

## Git Workflow & Branch Strategy

### Branch Structure

- **`main`** - Production-ready code only (protected)
- **`development`** - Main development branch (all features merge here first)
- **`feature/*`** - Individual feature branches (e.g., `feature/login-ui`, `feature/product-listing`)

### Workflow Steps

#### 1. Start Working on a New Feature

```bash
# Make sure you're on development branch
git checkout development

# Pull latest changes
git pull origin development

# Create a new feature branch
git checkout -b feature/your-feature-name
```

#### 2. Make Your Changes

```bash
# Work on your code...

# Stage your changes
git add .

# Commit with a descriptive message
git commit -m "Add: description of what you added"
```

#### 3. Push Your Feature Branch

```bash
# Push your feature branch to GitHub
git push -u origin feature/your-feature-name
```

#### 4. Create a Pull Request (PR)

1. Go to GitHub: https://github.com/DeonHolo/AgriLink
2. Click "Compare & pull request"
3. Set base branch to `development`
4. Add description of your changes
5. Request review from teammates
6. Wait for approval and merge

#### 5. After Merge

```bash
# Switch back to development
git checkout development

# Pull the merged changes
git pull origin development

# Delete your local feature branch (optional)
git branch -d feature/your-feature-name
```

### Commit Message Format

Use descriptive commit messages:

- `Add: new feature or file`
- `Update: changes to existing functionality`
- `Fix: bug fixes`
- `Refactor: code restructuring without changing functionality`
- `Docs: documentation updates`
- `Style: formatting, missing semi-colons, etc.`

### Examples

```bash
# Good commit messages
git commit -m "Add: registration form validation"
git commit -m "Fix: login authentication error"
git commit -m "Update: user model with phone number field"

# Bad commit messages (avoid these)
git commit -m "changes"
git commit -m "update"
git commit -m "fix bug"
```

### Branch Naming Conventions

- **Features**: `feature/feature-name` (e.g., `feature/google-signin`)
- **Bug Fixes**: `fix/bug-description` (e.g., `fix/registration-error`)
- **Hotfixes**: `hotfix/critical-fix` (e.g., `hotfix/security-patch`)

### Current Branch

You are currently on: **`development`** ✅

All future work should be done on feature branches created from `development`.

### Team Workflow

1. **Orge, Christian**: Work on UI (create branches like `feature/registration-ui`)
2. **Taghoy**: Work on backend (create branches like `feature/api-integration`)
3. All branches merge to `development` first
4. After testing, `development` merges to `main` for deployment

### Need Help?

- Check current branch: `git branch`
- See all branches: `git branch -a`
- Switch branches: `git checkout branch-name`
- Pull latest changes: `git pull origin branch-name`

---

**Remember**: Never push directly to `main`! Always work on feature branches and create pull requests.

