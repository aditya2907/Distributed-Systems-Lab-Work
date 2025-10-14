# Lab 2: Distributed Data Management and Consistency Models

## Quick Start (5 Minutes)

```bash
# 1. Setup MongoDB replica set
./setup_fresh.sh

# 2. Run all experiments
./run_all_experiments.sh
```

---

## Prerequisites

- Docker and Docker Compose installed
- That's it! Python runs in Docker containers automatically

---

## Lab Structure

### Core Scripts
- **setup_fresh.sh** - Sets up 3-node MongoDB replica set
- **run_test_in_docker.sh** - Runs Python tests from Docker network
- **run_all_experiments.sh** - Runs all 4 experiments with pauses

### Test Scripts (Part B & C)
1. **write_concern_test.py** - B.1: Write Concerns (w:1, w:majority, w:3)
2. **leader_follower_test.py** - B.2: Primary-Secondary Replication
3. **strong_consistency_test.py** - C.1: Strong Consistency (CP)
4. **eventual_consistency_test.py** - C.2: Eventual Consistency (AP)

### Documentation
- **README.md** - This file
- **QUICK_START.md** - Step-by-step instructions
- **DOCKER_TEST_GUIDE.md** - Technical Docker details
- **LAB_REPORT_TEMPLATE.md** - Complete report template

---

## Why Docker Network?

MongoDB replica set uses internal hostnames (mongo1, mongo2, mongo3) only accessible within Docker network. Tests must run from inside this network for proper replica set connectivity.

**The `run_test_in_docker.sh` script handles this automatically.**

---

## Running Individual Tests

```bash
./run_test_in_docker.sh write_concern_test.py
./run_test_in_docker.sh leader_follower_test.py  
./run_test_in_docker.sh strong_consistency_test.py
./run_test_in_docker.sh eventual_consistency_test.py
```

---

## Verification

```bash
# Check replica set status
docker exec -it mongo1 mongosh --eval "rs.status()" | grep "name\|state"

# Expected output:
# mongo1:27017 - PRIMARY
# mongo2:27017 - SECONDARY
# mongo3:27017 - SECONDARY

# Check data
docker exec -it mongo1 mongosh --eval "use testDB; db.UserProfile.find()"
```

---

## Troubleshooting

**"Failed to connect"** → Use `run_test_in_docker.sh`, not direct Python

**"cannot use 'w' > 1"** → Same as above, need replica set connection

**"not reachable/healthy"** → Run `docker-compose down -v && ./setup_fresh.sh`

---

## Cleanup

```bash
docker-compose down -v
```

---

## Lab Report

1. Run experiments and capture screenshots
2. Use **LAB_REPORT_TEMPLATE.md** as starting point
3. Fill in your experimental data
4. Analyze results and explain trade-offs

---

## Architecture

```
MongoDB Replica Set (rs0)
├── mongo1:27017 (PRIMARY)   → localhost:27017
├── mongo2:27017 (SECONDARY) → localhost:27018
└── mongo3:27017 (SECONDARY) → localhost:27019
```

---

## Key Concepts

### Write Concerns
- **w:1** - Fast, primary only (risk: data loss)
- **w:majority** - Balanced, 2/3 nodes (recommended)
- **w:3** - Slow, all nodes (maximum durability)

### Consistency Models
- **Strong (CP)** - w:majority + readConcern:majority → Sacrifices availability
- **Eventual (AP)** - w:1 + secondary reads → Sacrifices consistency

---

**Repository:** https://github.com/aditya2907/Distributed-Systems-Lab-Work

**Date:** October 14, 2025

