# Kelvin — Performance Benchmarks

Comparison of [Kelvin](https://github.com/mansoorhash/kelvin) against Redis, measured with `redis-benchmark` on **October 19, 2026**. These are **local exploratory microbenchmarks**, not production performance claims or proof of equivalent durability.

## Reports

| Report | Workload | Evidence |
|---|---|---|
| [Persistence modes — 3 B](benchmarks/persistence-3b.md) | SET/GET, 3-byte values, no AOF / AOF everysec session / AOF always session | Repeated-run medians |
| [AOF-enabled payload sweep](benchmarks/payload-aof.md) | 300 B, 3 KB, 30 KB values | **Single run** per server per payload |
| [No-AOF 30 KB comparison](benchmarks/payload-no-aof-30kb.md) | SET/GET, 30 KB values | Repeated-run medians; some source headers clipped |
| [Run summaries (CSV)](benchmarks/run_summaries.csv) | Machine-readable throughput and latency summaries | Extracted from intact sections of the original logs |

## Headline results

### 3-byte payload, 50 concurrent clients (run-level medians)

| Test session | Kelvin SET req/s | Redis SET req/s | Kelvin GET req/s | Redis GET req/s |
|---|---:|---:|---:|---:|
| No AOF | 20,833.33 | 29,325.51 | 26,315.79 | 28,571.43 |
| AOF `everysec` session | 4,096.96 | 29,325.51 | 27,286.40 | 29,154.52 |
| AOF `always` session | 691.49 | 17,182.13 | 26,426.62 | 28,169.02 |

### 30 KB payload, no AOF (run-level medians)

| Operation | Kelvin req/s | Redis req/s | Kelvin / Redis |
|---|---:|---:|---:|
| SET | 4,372.54 | 4,456.74 | 98.1% |
| GET | 1,994.42 | 2,013.47 | 99.1% |

## Methodology

- **Client:** `redis-benchmark` from Docker image `redis:latest`, executed from Windows PowerShell.
- **Network:** `-h host.docker.internal`; Kelvin on **6380**, Redis on **6381**.
- **Workload:** `-t set,get -n 10000 -c 50`, without pipelining. `SET` and `GET` are measured separately by the tool.
- **Payloads:** 3 B, 300 B, 3,000 B and 30,000 B as documented in each report.
- **Aggregation:** When repeated, use the **median of each run's throughput / average / p50 / p95 / p99**. Percentiles are not recomputed from pooled request traces. One-off payload sweep results remain labeled single-run.
- **Scope:** No measured CPU model, commit SHA, Docker image digest, warmed-state protocol, or sustained-load phase was captured. Results are not directly generalizable to other hosts.

### Reproduction command (PowerShell)

```powershell
docker run --rm redis:latest redis-benchmark `
  -h host.docker.internal -p 6380 `
  -t set,get -n 10000 -c 50 -d 3
```

Set `-p 6381` for Redis. Replace `-d 3` with `-d 300`, `-d 3000`, or `-d 30000` for the payload tests.

### Verify Redis persistence before claiming matched modes

```powershell
docker run --rm redis:latest redis-cli `
  -h host.docker.internal -p 6381 `
  CONFIG GET appendonly appendfsync save
```

**Critical qualification:** The supplied Redis logs show `appendonly` on/off but **not** `appendfsync`, so the `everysec`/`always` Redis columns refer to benchmark *sessions*, not independently verified fsync settings. Redis's RDB snapshots remained configured (`save` rules) even in the no-AOF runs. Kelvin's SQLite-backed live storage also means that disabling its AOF does not necessarily disable disk persistence. **Do not describe these comparisons as durability-equivalent without separate verification.**

## Takeaways

1. **Reads:** Kelvin's 3-byte GET throughput was within ~6–8% of Redis across the sampled sessions.
2. **Writes:** Kelvin's AOF-enabled SET throughput lagged sharply, suggesting the persistent write path as a priority for profiling and further investigation.
3. **Larger payloads:** Kelvin approached Redis's measured throughput for 30 KB values in the repeated no-AOF session, but some higher-latency percentiles remained worse. The AOF-enabled 3 KB read advantage was measured **once** and needs repetition.
4. **Reliability not established:** `redis-benchmark` alone does not test crash consistency, concurrent correctness, recovery, or equivalent acknowledgment durability.

## Suggested follow-up tests

Verify the Redis fsync policy and Kelvin persistence semantics; disable or explicitly control Redis RDB snapshots where suitable; pin exact versions and commit hashes; repeat each payload condition five or more times; benchmark multiple client counts, pipelining, mixed operations and sustained load; and profile AOF / SQLite write costs.

All results were taken from the supplied terminal logs. This repository document intentionally retains caveats where the logs do not prove a configuration or a result's repeatability.
