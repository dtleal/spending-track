# Contributing to SpendTrack

Thank you for your interest in contributing to SpendTrack! This document outlines the development workflow and guidelines for contributing to this project.

## 🚀 Development Workflow

### Branch Structure

- **`main`** - Production branch (protected)
  - Contains stable, production-ready code
  - Only accessible via Pull Requests from `dev`
  - Requires code review and approval

- **`dev`** - Development branch (default)
  - Main development branch
  - All feature branches merge here first
  - Integration testing happens here

- **`feature/*`** - Feature branches
  - Created from `dev` for new features
  - Naming convention: `feature/feature-name`
  - Merged back to `dev` via Pull Request

- **`bugfix/*`** - Bug fix branches
  - Created from `dev` for bug fixes
  - Naming convention: `bugfix/issue-description`
  - Merged back to `dev` via Pull Request

- **`hotfix/*`** - Emergency fixes
  - Created from `main` for critical production fixes
  - Naming convention: `hotfix/issue-description`
  - Merged to both `main` and `dev`

## 🔄 Getting Started

### 1. Clone the Repository
```bash
git clone git@github.com:dtleal/spending-track.git
cd spending-track
```

### 2. Set Up Development Environment
```bash
# Copy environment files
cp backend/.env.example backend/.env
cp frontend/.env.local.example frontend/.env.local  # if exists

# Edit the .env files with your local configuration
# Add your API keys, database credentials, etc.

# Start the development environment
docker-compose -f docker-compose.dev.yml up -d
```

### 3. Verify Setup
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs

## 📝 Development Process

### For New Features

1. **Create Feature Branch**
   ```bash
   git checkout dev
   git pull origin dev
   git checkout -b feature/your-feature-name
   ```

2. **Develop Your Feature**
   ```bash
   # Make your changes
   # Write tests
   # Update documentation if needed
   ```

3. **Test Your Changes**
   ```bash
   # Run backend tests
   cd backend && python -m pytest

   # Run frontend tests (if available)
   cd frontend && npm test

   # Test the application manually
   docker-compose -f docker-compose.dev.yml up -d
   ```

4. **Commit Your Changes**
   ```bash
   git add .
   git commit -m "Add: description of your feature
   
   - Detailed explanation of what was added
   - Any breaking changes
   - Related issue number if applicable
   
   🤖 Generated with [Claude Code](https://claude.ai/code)
   
   Co-Authored-By: Claude <noreply@anthropic.com>"
   ```

5. **Push and Create Pull Request**
   ```bash
   git push origin feature/your-feature-name
   ```
   Then create a Pull Request from `feature/your-feature-name` → `dev`

### For Bug Fixes

1. **Create Bug Fix Branch**
   ```bash
   git checkout dev
   git pull origin dev
   git checkout -b bugfix/issue-description
   ```

2. **Follow the same process as features**

### For Hotfixes (Emergency Production Fixes)

1. **Create Hotfix Branch**
   ```bash
   git checkout main
   git pull origin main
   git checkout -b hotfix/critical-issue
   ```

2. **Fix and Test**
   ```bash
   # Make minimal changes to fix the issue
   # Test thoroughly
   ```

3. **Create Pull Requests**
   ```bash
   git push origin hotfix/critical-issue
   ```
   Create PRs: `hotfix/critical-issue` → `main` AND `hotfix/critical-issue` → `dev`

## 📋 Pull Request Guidelines

### Before Creating a PR

- [ ] Code follows the project's coding standards
- [ ] All tests pass
- [ ] Documentation is updated if needed
- [ ] No sensitive data (API keys, passwords) is included
- [ ] Branch is up to date with target branch

### PR Template

```markdown
## Description
Brief description of the changes

## Type of Change
- [ ] Bug fix (non-breaking change which fixes an issue)
- [ ] New feature (non-breaking change which adds functionality)
- [ ] Breaking change (fix or feature that would cause existing functionality to not work as expected)
- [ ] Documentation update

## Testing
- [ ] Unit tests added/updated
- [ ] Manual testing completed
- [ ] All existing tests pass

## Screenshots (if applicable)
Add screenshots to help explain your changes

## Checklist
- [ ] Code follows style guidelines
- [ ] Self-review completed
- [ ] Documentation updated
- [ ] No sensitive data included
```

## 🧪 Testing Guidelines

### Backend Testing
```bash
cd backend
python -m pytest tests/
python -m pytest tests/ --cov=app --cov-report=html
```

### Frontend Testing
```bash
cd frontend
npm test
npm run test:coverage
```

### Integration Testing
```bash
# Start the full stack
docker-compose -f docker-compose.dev.yml up -d

# Run integration tests
# Test critical user flows manually
```

## 📊 Code Standards

### Python (Backend)
- Follow PEP 8
- Use type hints
- Write docstrings for functions and classes
- Maximum line length: 88 characters (Black formatter)

### TypeScript/React (Frontend)
- Use TypeScript for all new code
- Follow React best practices
- Use functional components with hooks
- Follow the existing component structure

### Git Commit Messages
```
Type: Brief description (50 chars max)

More detailed explanation if needed. Wrap at 72 characters.
Include the motivation for the change and contrast with previous behavior.

- Use bullet points for multiple changes
- Reference issues: Fixes #123, Closes #456

🤖 Generated with [Claude Code](https://claude.ai/code)

Co-Authored-By: Claude <noreply@anthropic.com>
```

**Commit Types:**
- `Add:` - New feature
- `Fix:` - Bug fix
- `Update:` - Modify existing feature
- `Remove:` - Delete code/feature
- `Refactor:` - Code restructuring
- `Docs:` - Documentation changes
- `Test:` - Add/update tests
- `Style:` - Code formatting changes

## 🚫 What NOT to Commit

- [ ] `.env` files with real credentials
- [ ] `node_modules/` directories
- [ ] IDE-specific files (.vscode/, .idea/)
- [ ] OS-specific files (.DS_Store, Thumbs.db)
- [ ] Build artifacts (`dist/`, `build/`, `.next/`)
- [ ] Log files
- [ ] Database files
- [ ] Personal configuration files

## 🔒 Security Guidelines

- Never commit API keys, passwords, or secrets
- Use environment variables for sensitive configuration
- Keep dependencies updated
- Review third-party packages before adding them
- Follow OWASP security practices

## 📞 Getting Help

- **Issues**: Create a GitHub issue for bugs or feature requests
- **Questions**: Use GitHub Discussions
- **Security Issues**: Email security concerns privately

## 🎯 Release Process

### Development to Production

1. **Feature Complete on `dev`**
   ```bash
   # All features tested and working on dev branch
   ```

2. **Create Release PR**
   ```bash
   # Create PR: dev → main
   # Title: "Release v1.x.x"
   # Include changelog in PR description
   ```

3. **Code Review & Approval**
   - Required reviewers approve the PR
   - All CI checks pass
   - Manual testing completed

4. **Merge to Main**
   ```bash
   # After approval, merge to main
   # This triggers production deployment
   ```

5. **Tag Release**
   ```bash
   git checkout main
   git pull origin main
   git tag -a v1.x.x -m "Release version 1.x.x"
   git push origin v1.x.x
   ```

## 📚 Additional Resources

- [Project README](README.md)
- [API Documentation](http://localhost:8000/docs)
- [Architecture Overview](docs/architecture.md) (if available)

---

Thank you for contributing to SpendTrack! 🙏