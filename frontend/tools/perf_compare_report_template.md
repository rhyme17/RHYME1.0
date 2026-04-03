# Performance Comparison Report Template

## 1. Scope
- Feature under test:
- Commit / version (before):
- Commit / version (after):
- Test machine:
- OS / Python version:

## 2. Method
- Benchmark script: `frontend/tools/benchmark_scan.py`
- Command used:

```powershell
python "d:\Projects\PycharmProjects\RHYME\frontend\tools\benchmark_scan.py" "d:\Projects\PycharmProjects\RHYME" --repeat 5
```

- Dataset description (song count / formats / directory depth):
- Warm-up policy:
- Number of repeats:

## 3. Raw Results

| Version | songs | repeat | avg_seconds | min_seconds | max_seconds |
|---|---:|---:|---:|---:|---:|
| Before |  |  |  |  |  |
| After  |  |  |  |  |  |

## 4. Analysis
- Absolute improvement (avg):
- Relative improvement (%):
- Variability notes (min/max spread):
- Potential external noise factors:

## 5. Functional Checks
- Scan result count unchanged:
- Song metadata consistency spot-check:
- UI responsiveness observed:

## 6. Risks and Follow-ups
- Known limitations:
- Next optimization candidates:
- Rollback plan:

