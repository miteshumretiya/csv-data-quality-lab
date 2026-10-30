# Task 13 - Git development workflow

The delivered ZIP is **not** presented as the friend's personal Git history. Git should be used during their real study and development work. The lecturer requires repository initialization, .gitignore, meaningful commits, at least one branch, merge, conflict resolution and remote activity where permitted.

In VS Code's project terminal:

```powershell
git init
git add .
git commit -m "Create CSV dashboard and CSV profiling model"
git switch -c feature/profile-improvements
# Make an actual change in analyser.py and add tests.
git add .
git commit -m "Improve validation rules and profile tests"
git switch main
git merge feature/profile-improvements
git log --all --oneline --graph --decorate
```

**Conflict example:** On a dedicated teaching branch, modify a line of `README.md` differently from main, commit both changes and attempt to merge. Inspect conflict markers, select a sensible combined sentence, remove markers, stage the file and commit the resolution. Keep command output or screenshots. Do not silently create false conflicts in the submitted report.

If GitHub is available to the student:

```powershell
git remote add origin https://github.com/USERNAME/REPOSITORY.git
git push -u origin main
git pull origin main
```

Replace `USERNAME/REPOSITORY` with the student's own repository, and use a real pull request or documented review where appropriate. Avoid using another student's project history.
