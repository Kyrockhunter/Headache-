# Contributing Guide — Fantasy Optimizer v4.3.0
**Maintained by:** KyRockHunter  
**Repository:** `KyRockHunter/fantasy_v4`  
**Python:** 3.13.7  

---

## 1. Branching Strategy
- `main` → stable, release-ready code only  
- `dev` → integration and staging branch  
- `feature/<name>` → for new modules or experiments  
- `fix/<issue>` → for patches or bug fixes  
- Always branch from the latest `dev`  

---

## 2. Commit Message Format
Follow **Conventional Commits** style:

```
<type>(<scope>): <summary>
```
Example:
```
feat(optimizer): add FLEX slot logic for hybrid selector
fix(simulator): correct covariance matrix fallback
docs(cleaner): update schema mapping section
```

**Types:**
- `feat` — new feature
- `fix` — bug fix
- `docs` — documentation only
- `test` — tests added or updated
- `refactor` — structure change, no behavior change
- `chore` — maintenance or housekeeping

---

## 3. Pull Request Flow
1. Sync latest `dev`
2. Create feature branch  
3. Push commits, open PR into `dev`
4. Ensure all **pytest** tests pass
5. Tag reviewers or maintainers if applicable

---

## 4. Testing Standards
- Use **pytest**
- Add tests under `/tests/`
- Ensure each module has at least one unit test per major function
- Run all tests before PR submission:
  ```bash
  pytest -q
  ```

---

## 5. Coding Standards
- Follow **PEP8** style
- Use **type hints** throughout
- Use **docstrings** with:
  - Short purpose line
  - Args / Returns
  - Invariants or assumptions

---

## 6. Versioning & Tags
- Semantic Versioning: `MAJOR.MINOR.PATCH`
- Tag releases from `main` branch:
  ```bash
  git tag -a v4.3.0 -m "Hybrid selector + modular structure"
  git push --tags
  ```

---

## 7. Review Guidelines
- Keep PRs focused and under ~300 lines of change
- Link issues in PR description if relevant
- Avoid committing large CSV or binary files

---

## 8. Communication & Documentation
- Update `ARCHITECTURE.md` when adding or modifying module interfaces
- Add a CHANGELOG entry for every tagged release
- Keep inline comments concise and meaningful (focus on *why*, not *what*)

---
