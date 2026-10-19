Across your 5 new Redis benchmark runs (port 6380), with 10,000 requests per operation and 50 concurrent clients:
Median benchmark results
Metric	SET median	GET median
Latency (p50)	273.407 ms	1.959 ms
Average latency	283.921 ms	2.055 ms
p95 latency	361.471 ms	2.791 ms
p99 latency	462.335 ms	3.287 ms
Throughput	175.69 req/s	23,809.53 req/s
Comparison with previous results (port 6381)
Metric	Port 6381	Port 6380
SET p50	2.727 ms	273.407 ms
GET p50	1.599 ms	1.959 ms
SET throughput	17,667.85	175.69
GET throughput	28,818.44	23,809.53
Key findings:
- SET latency: Port 6380 is approximately 100.3× slower.
- GET latency: Port 6380 is approximately 22.5% slower.
- SET throughput: Port 6381 achieves approximately 100.6× higher throughput.
- GET throughput: Port 6381 achieves approximately 21.0% higher throughput.
The largest performance discrepancy is clearly in SET operations. Your port 6380 instance exhibits dramatically higher write latency while read performance remains relatively comparable.
These figures represent the medians of the five benchmark summaries for each configuration, rather than pooled request-level medians.