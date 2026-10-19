# No-AOF 30 KB repeated comparison

[← Overview](../BENCHMARK.md)

October 19, 2026. `redis-benchmark -t set,get -n 10000 -c 50 -d 30000` against Kelvin (6380) and Redis (6381). Unlike the AOF-enabled payload sweep, this dataset contains **multiple runs**.

## Median results

| Metric | Kelvin SET | Redis SET | Kelvin GET | Redis GET |
|---|---:|---:|---:|---:|
| Throughput (req/s) | 4,372.54 | 4,456.74 | 1,994.42 | 2,013.47 |
| Average latency (ms) | 11.268 | 10.998 | 4.835 | 7.235 |
| p50 latency (ms) | 9.007 | 10.091 | 3.311 | 5.363 |
| p95 latency (ms) | 25.535 | 18.247 | 13.471 | 18.351 |
| p99 latency (ms) | 36.255 | 24.399 | 29.487 | 27.703 |

**Summary:** Kelvin reached ~98.1% of Redis SET throughput and ~99.1% of Redis GET throughput. Kelvin had lower median-of-runs GET p50, but worse SET p95/p99.

**Collection note:** These medians include full summaries that appear at the beginning of the pasted logs, where the benchmark header was clipped. The normalized CSV includes only summaries with intact operation headers, so it is **not** a complete raw-data reconstruction for this particular comparison; consult the original uploaded terminal captures for those unheaded summaries.

## Important caveats

- Redis printed `appendonly: no` but still had RDB `save` rules configured; this is **not** a fully persistence-free comparison.
- Kelvin uses SQLite-backed live storage, so disabling AOF does not automatically disable persistence.
- Workload is only 30 KB values, 50 clients, brief durations, Docker-to-host networking. Near parity here should not be extrapolated to other workloads.
- The source logs began mid-output, so this section deliberately preserves the previously established six-Redis-run and five-Kelvin-run aggregated metrics rather than silently treating partial output as a new standalone trial.

## Reproduce

```powershell
docker run --rm redis:latest redis-benchmark `
  -h host.docker.internal -p 6380 `
  -t set,get -n 10000 -c 50 -d 30000
```

Repeat on port `6381` for Redis, and run at least five repetitions per server.
