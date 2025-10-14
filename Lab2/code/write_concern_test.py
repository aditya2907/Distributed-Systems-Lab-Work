from pymongo import MongoClient, WriteConcern
from pymongo.errors import ConnectionFailure, WriteConcernError
import time
import statistics

def connect_to_replica_set():
    """Connect to MongoDB replica set
    
    Uses replica set connection string for proper write concern support.
    """
    try:
        # Connect to replica set (works when run from inside Docker network)
        client = MongoClient(
            'mongodb://mongo1:27017,mongo2:27017,mongo3:27017/?replicaSet=rs0',
            serverSelectionTimeoutMS=5000
        )
        client.admin.command('ping')
        return client
    except ConnectionFailure as e:
        print(f"✗ Failed to connect: {e}")
        return None

def test_write_concern(db, w, user_id):
    """Test a specific write concern and measure latency"""
    try:
        start = time.time()
        collection = db.get_collection('UserProfile', write_concern=WriteConcern(w=w))
        result = collection.insert_one(
            {
                "user_id": user_id,
                "username": f"user_{w}_{user_id}",
                "email": f"user_{w}_{user_id}@example.com",
                "last_login_time": time.time(),
                "write_concern": str(w)
            }
        )
        latency = time.time() - start
        return latency, True, result.acknowledged
    except WriteConcernError as e:
        return None, False, str(e)
    except Exception as e:
        return None, False, str(e)

def run_write_concern_experiments():
    client = connect_to_replica_set()
    if not client:
        print("Cannot proceed without database connection")
        return
    
    db = client.testDB
    
    write_concerns = [1, "majority", 3]  # 3 = all nodes in our setup
    iterations = 5  # Run multiple times for statistical analysis
    
    results = {}
    
    for w in write_concerns:
        print(f"\n--- Testing Write Concern: w={w} ---")
        latencies = []
        
        for i in range(iterations):
            user_id = 100 + int(time.time() * 1000) % 100000  # Unique ID
            latency, success, info = test_write_concern(db, w, user_id)
            
            if success:
                latencies.append(latency)
                print(f"  Iteration {i+1}: {latency:.4f}s (Acknowledged: {info})")
            else:
                print(f"  Iteration {i+1}: FAILED - {info}")
        
        if latencies:
            results[w] = {
                'mean': statistics.mean(latencies),
                'min': min(latencies),
                'max': max(latencies),
                'stdev': statistics.stdev(latencies) if len(latencies) > 1 else 0
            }
    
    # Summary
    print("SUMMARY: Write Concern Performance Comparison")
    print(f"{'Write Concern':<15} {'Mean (s)':<12} {'Min (s)':<12} {'Max (s)':<12} {'Std Dev':<12}")

    
    for w, stats in results.items():
        print(f"w={w:<13} {stats['mean']:<12.4f} {stats['min']:<12.4f} {stats['max']:<12.4f} {stats['stdev']:<12.4f}")
    
    client.close()

if __name__ == "__main__":
    run_write_concern_experiments()