# Changelog — Fantasy Optimizer
**Maintained by:** KyRockHunter  
**Repository:** `KyRockHunter/fantasy_v4`  
**Version Format:** Semantic Versioning (vMAJOR.MINOR.PATCH)  
**Python:** 3.13.7  

---

## [v4.3.0] — 2025-10-16
### Added
- HybridLineupSelector (integrated optimizer + simulator)
- Modular project structure (`src/` cleanup and imports)
- Centralized `ARCHITECTURE.md` with data flow diagrams

### Changed
- `optimizer.py` refactored for new `run()` + `optimize()` aliases
- `correlated_simulator.py` updated with `p95` output and correlation priors
- Roster rules now true to DK Classic (FLEX = RB/WR/TE)

### Fixed
- Compatibility with updated tests and fallback lineup generator
- Proper column alignment in simulation outputs

### Documentation
- Added `/docs/` directory with CONTRIBUTING and CHANGELOG
- Added doc index at top of `ARCHITECTURE.md`

---

## [v4.2.0] — 2025-09-30
- Early hybrid testing version with partial modular integration

## [v4.1.0] — 2025-08-10
- Stable optimizer and simulator baseline

---
