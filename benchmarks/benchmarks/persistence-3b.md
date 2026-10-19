# 3-byte persistence benchmark

[← Overview](../BENCHMARK.md)

## Test setup

10,000 requests per command (`SET` and `GET`), 50 concurrent clients, 3-byte values, no pipelining, Docker `redis-benchmark` running from Windows and contacting `host.docker.internal` (`6380` Kelvin, `6381` Redis). October 19, 2026.

All results are **medians of run-level summary metrics**, not percentiles pooled across multiple runs. Lower latency is better; higher throughput is better.

## Throughput

| Session | Command | Kelvin req/s | Redis req/s | Kelvin / Redis | Runs (Kelvin / Redis) |
|---|---|---:|---:|---:|---:|
| No AOF | SET | 20,833.33 | 29,325.51 | 71.0% | 5 / 5 |
| No AOF | GET | 26,315.79 | 28,571.43 | 92.1% | 5 / 5 |
| AOF `everysec` session | SET | 4,096.96 | 29,325.51 | 14.0% | 4 / 5 |
| AOF `everysec` session | GET | 27,286.40 | 29,154.52 | 93.6% | 4 / 5 |
| AOF `always` session | SET | 691.49 | 17,182.13 | 4.0% | 6 / 5 |
| AOF `always` session | GET | 26,426.62 | 28,169.02 | 93.8% | 6 / 5 |

## Detailed latency

All latencies are in milliseconds. Each metric is independently aggregated over runs.

### No AOF

| Metric | Kelvin SET | Redis SET | Kelvin GET | Redis GET |
|---|---:|---:|---:|---:|
| Throughput (req/s) | 20,833.33 | 29,325.51 | 26,315.79 | 28,571.43 |
| avg | 2.348 | 1.662 | 1.860 | 1.689 |
| p50 | 2.279 | 1.583 | 1.799 | 1.591 |
| p95 | 3.079 | 2.519 | 2.543 | 2.599 |
| p99 | 4.095 | 4.383 | 3.727 | 4.335 |

### AOF `everysec` session

| Metric | Kelvin SET | Redis SET | Kelvin GET | Redis GET |
|---|---:|---:|---:|---:|
| Throughput (req/s) | 4,096.96 | 29,325.51 | 27,286.40 | 29,154.52 |
| avg | 12.139 | 1.655 | 1.796 | 1.668 |
| p50 | 11.727 | 1.575 | 1.747 | 1.575 |
| p95 | 15.363 | 2.463 | 2.447 | 2.559 |
| p99 | 18.927 | 4.383 | 3.447 | 4.487 |

### AOF `always` session

| Metric | Kelvin SET | Redis SET | Kelvin GET | Redis GET |
|---|---:|---:|---:|---:|
| Throughput (req/s) | 691.49 | 17,182.13 | 26,426.62 | 28,169.02 |
| avg | 72.183 | 2.861 | 1.852 | 1.721 |
| p50 | 71.711 | 2.799 | 1.795 | 1.631 |
| p95 | 83.231 | 3.743 | 2.483 | 2.615 |
| p99 | 99.487 | 6.575 | 3.115 | 4.351 |

## Durability and fairness notes

- Redis benchmark output confirmed `appendonly: no` in the no-AOF session and `appendonly: yes` in the AOF sessions, **but did not print `appendfsync`**. Thus the Redis `everysec` and `always` labels denote the test session, not independently verified Redis fsync configurations.
- Redis reported RDB `save` rules even when AOF was disabled. Kelvin uses SQLite-backed live storage according to the repository; **no AOF is not necessarily no disk persistence**. The durability and implementation costs are not guaranteed to be equivalent.
- The AOF-always Kelvin log includes one refused connection attempt, excluded because it yielded no results.
- The Kelvin benchmark tool prints `WARNING: Could not fetch server CONFIG`; this indicates missing config introspection from the benchmark client but does not invalidate completed request measurements.
- Very short runs, unpinned `redis:latest`, no host CPU or disk specifications, and no environment isolation limit generalization.

## Interpretation

- Kelvin GET throughput is near Redis in the 3-byte sessions (~92–94% of Redis).
- Kelvin SET throughput drops steeply when AOF is enabled; this is a **profiling target**, not proof of any particular internal bottleneck.
- Smaller p99 latency in a few samples is insufficient to claim generally lower tail latency.

Source data: [`run_summaries.csv`](run_summaries.csv), and the original terminal uploads.
