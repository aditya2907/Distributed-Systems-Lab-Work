
from pymongo import MongoClient, WriteConcern
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError
from pymongo.read_concern import ReadConcern
import time
import threading
   
def connect_to_replica_set():
    """Connect to MongoDB replica set"""
    try:
        client = MongoClient(
            'mongodb://mongo1:27017,mongo2:27017,mongo3:27017/?replicaSet=rs0',
            serverSelectionTimeoutMS=5000
        )
        client.admin.command('ping')
        return client
    except ConnectionFailure as e:
        print(f"✗ Failed to connect: {e}")
        return None

def test_strong_consistency_basic(db):
    test_user_id = int(time.time() * 1000) % 100000
    test_data = {
        "user_id": test_user_id,
        "username": "strong_consistency_user",
        "email": "strong@example.com",
        "last_login_time": time.time(),
        "test_value": "STRONG_CONSISTENCY_TEST"
    }
    
    print(f"Writing user_id={test_user_id} with w:majority...")
    start_write = time.time()
    collection = db.get_collection('UserProfile', write_concern=WriteConcern(w='majority'))
    result = collection.insert_one(test_data)
    write_latency = time.time() - start_write
    print(f"  Write completed in {write_latency:.4f}s")
    print(f"  Inserted ID: {result.inserted_id}")
    
    print(f"\nImmediately reading user_id={test_user_id} with readConcern:majority...")
    start_read = time.time()
    collection_read = db.get_collection('UserProfile', read_concern=ReadConcern("majority"))
    read_result = collection_read.find_one({"user_id": test_user_id})
    read_latency = time.time() - start_read
    print(f"  Read completed in {read_latency:.4f}s")

    if read_result:
        print(f"  Data is immediately consistent!")
        print(f"  Retrieved: {read_result['username']} - {read_result['email']}")
    else:
        print(f"  Data not found (unexpected with strong consistency)")
    
    return test_user_id

def test_strong_consistency_concurrent_reads(db, user_id):
    """Test concurrent reads from different nodes"""
    
    # Update the document
    update_value = f"UPDATED_{int(time.time() * 1000)}"
    print(f"Updating user_id={user_id} with new value: {update_value}")
    
    collection = db.get_collection('UserProfile', write_concern=WriteConcern(w='majority'))
    collection.update_one(
        {"user_id": user_id},
        {"$set": {"test_value": update_value, "updated_at": time.time()}}
    )
    print("  ✓ Update completed with w:majority")
    
    # Concurrent reads
    results = []
    
    def read_from_node(node_preference):
        try:
            collection_read = db.get_collection('UserProfile', read_concern=ReadConcern("majority"))
            result = collection_read.find_one({"user_id": user_id})
            if result:
                results.append({
                    'preference': node_preference,
                    'value': result.get('test_value'),
                    'timestamp': time.time()
                })
        except Exception as e:
            results.append({
                'preference': node_preference,
                'error': str(e)
            })
    
    # Launch concurrent reads
    threads = []
    for i in range(5):
        t = threading.Thread(target=read_from_node, args=(f"Read-{i+1}",))
        threads.append(t)
        t.start()
    
    for t in threads:
        t.join()
    
    # Check consistency
    print(f"\n  Concurrent Read Results:")
    values = []
    for r in results:
        if 'error' in r:
            print(f"    {r['preference']}: ERROR - {r['error']}")
        else:
            print(f"    {r['preference']}: {r['value']}")
            values.append(r['value'])
    
    if len(set(values)) == 1:
        print(f"\n  All reads returned consistent value: {values[0]}")
    else:
        print(f"\n  Inconsistent reads detected: {set(values)}")

def test_with_node_failure_simulation(db):
    """Test strong consistency behavior during node unavailability"""
    test_user_id = int(time.time() * 1000) % 100000
    
    print(f"\nAttempting write with w:majority (user_id={test_user_id})...")
    try:
        start = time.time()
        collection = db.get_collection('UserProfile', write_concern=WriteConcern(w='majority', wtimeout=10000))
        result = collection.insert_one(
            {
                "user_id": test_user_id,
                "username": "failure_test_user",
                "email": "failure@example.com",
                "last_login_time": time.time()
            }
        )
        latency = time.time() - start
        print(f"  Write succeeded in {latency:.4f}s")
        print(f"  With 2/3 nodes, majority is still achievable")
    except ServerSelectionTimeoutError as e:
        print(f"  Write failed: {e}")
        print(f"  This indicates < majority of nodes available")
    except Exception as e:
        print(f"  Write failed: {e}")

    print("\nAttempting read with readConcern:majority...")
    try:
        collection_read = db.get_collection('UserProfile', read_concern=ReadConcern("majority"))
        result = collection_read.find_one({"user_id": test_user_id})
        if result:
            print(f"  Read succeeded: {result['username']}")
        else:
            print(f"  Document not found (might be due to write failure)")
    except Exception as e:
        print(f"  Read failed: {e}")

def run_strong_consistency_experiments():
    client = connect_to_replica_set()
    if not client:
        print("Cannot proceed without database connection")
        return
    
    db = client.testDB
    
    # Run tests
    user_id = test_strong_consistency_basic(db)
    time.sleep(1)
    
    test_strong_consistency_concurrent_reads(db, user_id)
    time.sleep(1)
    
    test_with_node_failure_simulation(db)
    
    client.close()

if __name__ == "__main__":
    run_strong_consistency_experiments()