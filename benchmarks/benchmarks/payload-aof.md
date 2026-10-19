# AOF-enabled payload-size sweep

[← Overview](../BENCHMARK.md)

**Exploratory single-run measurements** on October 19, 2026. Each server was measured once at 300, 3,000, and 30,000-byte values, with `-n 10000 -c 50 -t set,get`. Redis reported `appendonly: yes`, but `appendfsync` was not captured; Kelvin AOF mode was likewise not printed in these logs. The servers cannot be assumed to have matching durability semantics.

## Throughput

| Payload | Operation | Kelvin req/s | Redis req/s | Kelvin / Redis |
|---|---|---:|---:|---:|
| 300 B | SET | 602.95 | 17,094.02 | 3.5% |
| 300 B | GET | 27,397.26 | 27,247.96 | 100.5% |
| 3,000 B | SET | 408.78 | 13,495.28 | 3.0% |
| 3,000 B | GET | 15,527.95 | 13,717.42 | 113.2% |
| 30,000 B | SET | 191.81 | 5,027.65 | 3.8% |
| 30,000 B | GET | 2,807.41 | 2,778.55 | 101.0% |

## Latency (ms)

| Payload | Operation | Server | Avg | p50 | p95 | p99 |
|---|---|---|---:|---:|---:|---:|
| 300 B | SET | Kelvin | 82.801 | 76.799 | 89.663 | 298.495 |
| 300 B | SET | Redis | 2.861 | 2.807 | 4.023 | 5.935 |
| 300 B | GET | Kelvin | 1.781 | 1.743 | 2.391 | 3.391 |
| 300 B | GET | Redis | 1.791 | 1.647 | 3.007 | 5.527 |
| 3,000 B | SET | Kelvin | 121.949 | 95.487 | 212.607 | 788.991 |
| 3,000 B | SET | Redis | 3.609 | 3.367 | 5.735 | 9.759 |
| 3,000 B | GET | Kelvin | 2.345 | 2.207 | 4.279 | 5.935 |
| 3,000 B | GET | Redis | 2.690 | 2.503 | 4.735 | 8.319 |
| 30,000 B | SET | Kelvin | 260.257 | 212.095 | 428.543 | 915.455 |
| 30,000 B | SET | Redis | 9.771 | 8.695 | 17.183 | 22.047 |
| 30,000 B | GET | Kelvin | 4.040 | 2.919 | 11.711 | 18.303 |
| 30,000 B | GET | Redis | 3.949 | 3.135 | 10.023 | 16.527 |

## Interpretation

- In this single sweep, Kelvin GET throughput was approximately tied at 300 B and 30 KB, and higher at 3 KB. **The 3 KB advantage is not a repeated-sample finding**.
- Kelvin AOF-enabled SET throughput deteriorated markedly as payloads increased. Profiling is needed to attribute the cause.
- At 30 KB, Kelvin recorded much higher SET tail latency than Redis.
- Payload-size scaling is based on one run per workload per server; rerun each condition at least five times, randomize order, and record hardware, versions and fsync settings before claiming reproducible wins.

## Reproduce

```powershell
docker run --rm redis:latest redis-benchmark `
  -h host.docker.internal -p 6380 `
  -t set,get -n 10000 -c 50 -d 300
```

Repeat with `-d 3000` and `-d 30000`. Change to `-p 6381` for Redis.

Source data: [`run_summaries.csv`](run_summaries.csv) and the original terminal uploads.
