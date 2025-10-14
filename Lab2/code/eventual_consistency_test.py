from pymongo import MongoClient, WriteConcern
from pymongo.errors import ConnectionFailure
from pymongo.read_preferences import ReadPreference
import time

def connect_to_replica_set():
    """Connect to MongoDB replica set"""
    try:
        # Connect to replica set (works when run from inside Docker network)
        client = MongoClient(
            'mongodb://mongo1:27017,mongo2:27017,mongo3:27017/?replicaSet=rs0',
            serverSelectionTimeoutMS=5000
        )
        client.admin.command('ping')
        return client
    except ConnectionFailure as e:
        print(f"Failed to connect: {e}")
        return None

def test_eventual_consistency_basic(db):
    
    test_user_id = int(time.time() * 1000) % 100000
    test_value = f"EVENTUAL_{int(time.time() * 1000)}"
    
    print(f"Writing user_id={test_user_id} with w:1 (primary only)...")
    start_write = time.time()
    
    # Write to primary only - use collection with write concern
    collection = db.get_collection('UserProfile', write_concern=WriteConcern(w=1))
    result = collection.insert_one(
        {
            "user_id": test_user_id,
            "username": "eventual_user",
            "email": "eventual@example.com",
            "last_login_time": time.time(),
            "test_value": test_value
        }
    )
    write_latency = time.time() - start_write
    print(f"Write completed in {write_latency:.4f}s (very fast!)")

    return test_user_id, test_value

def test_stale_reads(db, user_id, expected_value):
    
    # Create a client that reads from secondaries
    secondary_client = MongoClient(
        'mongodb://mongo2:27017/?replicaSet=rs0',
        readPreference='secondary'
    )
    secondary_db = secondary_client.testDB
    
    print(f"Immediately reading user_id={user_id} from SECONDARY node...")
    attempts = 0
    max_attempts = 20
    found = False
    stale_read_detected = False
    
    while attempts < max_attempts:
        attempts += 1
        result = secondary_db.UserProfile.find_one({"user_id": user_id})
        
        if result:
            if result.get('test_value') == expected_value:
                print(f"Attempt {attempts}:Found with correct value")
                found = True
                break
            else:
                print(f"Attempt {attempts}: Stale data (old value: {result.get('test_value')})")
                stale_read_detected = True
        else:
            print(f"Attempt {attempts}: Document not yet replicated (stale/absent)")
            stale_read_detected = True
        
        time.sleep(0.1)  # 100ms between attempts
    
    if not found:
        print(f"Document not found after {attempts} attempts")
    
    elapsed = attempts * 0.1
    print(f"\nReplication Time: ~{elapsed:.2f}s")

    if stale_read_detected:
        print(f"Stale reads were detected (demonstrating eventual consistency)")
    else:
        print(f"Note: Replication was very fast, stale read not observed")
    
    secondary_client.close()

def test_eventual_propagation_loop(db, user_id):
    """Loop demonstrating eventual propagation"""
    
    update_value = f"UPDATED_{int(time.time() * 1000)}"
    print(f"Updating user_id={user_id} with w:1...")
    
    collection = db.get_collection('UserProfile', write_concern=WriteConcern(w=1))
    collection.update_one(
        {"user_id": user_id},
        {"$set": {"test_value": update_value, "updated_at": time.time()}}
    )
    print(f"Update sent to primary")
    
    # Read from secondary until propagated
    secondary_client = MongoClient(
        'mongodb://mongo2:27017/?replicaSet=rs0',
        readPreference='secondary'
    )
    secondary_db = secondary_client.testDB
    
    print(f"\n  Polling secondary for updated value '{update_value}'...")
    start_time = time.time()
    attempt = 0
    
    while True:
        attempt += 1
        result = secondary_db.UserProfile.find_one({"user_id": user_id})
        
        if result and result.get('test_value') == update_value:
            elapsed = time.time() - start_time
            print(f"Updated value propagated after {elapsed:.3f}s ({attempt} attempts)")
            break
        
        if attempt > 50:  # 5 seconds max
            print(f"Propagation taking longer than expected")
            break
        
        time.sleep(0.1)
    
    secondary_client.close()

def test_high_availability(db):
    """Demonstrate high availability with eventual consistency"""
    print("With w:1, writes succeed even if secondaries are down")
    
    test_user_id = int(time.time() * 1000) % 100000
    
    try:
        start = time.time()
        collection = db.get_collection('UserProfile', write_concern=WriteConcern(w=1, wtimeout=1000))
        result = collection.insert_one(
            {
                "user_id": test_user_id,
                "username": "high_availability_user",
                "email": "ha@example.com",
                "last_login_time": time.time()
            }
        )
        latency = time.time() - start
        print(f"Write succeeded in {latency:.4f}s")
        print(f"System remains highly available!")
    except Exception as e:
        print(f"Write failed: {e}")

def run_eventual_consistency_experiments():
    
    client = connect_to_replica_set()
    if not client:
        print("Cannot proceed without database connection")
        return
    
    db = client.testDB
    
    # Run tests
    user_id, expected_value = test_eventual_consistency_basic(db)
    time.sleep(0.2)  # Small delay
    
    test_stale_reads(db, user_id, expected_value)
    time.sleep(0.5)
    
    test_eventual_propagation_loop(db, user_id)
    time.sleep(0.5)
    
    test_high_availability(db)
    
    
    client.close()

if __name__ == "__main__":
    run_eventual_consistency_experiments()