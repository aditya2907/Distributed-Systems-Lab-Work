from pymongo import MongoClient, WriteConcern
from pymongo.errors import ConnectionFailure, AutoReconnect
import time

def connect_to_replica_set():
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

def get_replica_set_status(client):
    try:
        status = client.admin.command('replSetGetStatus')
        return status
    except Exception as e:
        print(f"Error getting replica set status: {e}")
        return None

def display_replica_set_info(client):
    
    status = get_replica_set_status(client)
    if not status:
        return None
    
    print(f"Replica Set Name: {status['set']}")
    print(f"Members:")
    
    primary = None
    secondaries = []
    
    for member in status['members']:
        state = member['stateStr']
        name = member['name']
        health = "HEALTHY" if member['health'] == 1 else "UNHEALTHY"
        
        print(f"  - {name}: {state} ({health})")
        
        if state == 'PRIMARY':
            primary = name
        elif state == 'SECONDARY':
            secondaries.append(name)
    
    return {'primary': primary, 'secondaries': secondaries}

def test_write_to_primary(db):
    """Test writing to primary node"""
    print("\n--- Test 1: Write to Primary Node ---")
    
    test_user_id = int(time.time() * 1000) % 100000
    
    print(f"Writing user_id={test_user_id} to PRIMARY...")
    start = time.time()
    
    collection = db.get_collection('UserProfile', write_concern=WriteConcern(w=1))
    result = collection.insert_one(
        {
            "user_id": test_user_id,
            "username": "primary_write_user",
            "email": "primary@example.com",
            "last_login_time": time.time(),
            "write_time": time.time()
        }
    )
    
    latency = time.time() - start
    print(f"  ✓ Write completed in {latency:.4f}s")
    print(f"  Inserted ID: {result.inserted_id}")
    
    return test_user_id

def test_read_from_secondaries(db, user_id):
    """Test reading from secondary nodes"""
    print("\n--- Test 2: Read from Secondary Nodes ---")
    
    # Wait a moment for replication
    time.sleep(1)
    
    # Read from primary
    print(f"Reading user_id={user_id} from PRIMARY...")
    primary_client = MongoClient(
        'mongodb://mongo1:27017,mongo2:27017,mongo3:27017/?replicaSet=rs0',
        readPreference='primary'
    )
    primary_db = primary_client.testDB
    
    result_primary = primary_db.UserProfile.find_one({"user_id": user_id})
    if result_primary:
        print(f"  ✓ Found on PRIMARY: {result_primary['username']}")
    else:
        print(f"  ✗ Not found on PRIMARY")
    
    # Read from secondary
    print(f"\nReading user_id={user_id} from SECONDARY...")
    secondary_client = MongoClient(
        'mongodb://mongo1:27017,mongo2:27017,mongo3:27017/?replicaSet=rs0',
        readPreference='secondary'
    )
    secondary_db = secondary_client.testDB
    
    result_secondary = secondary_db.UserProfile.find_one({"user_id": user_id})
    if result_secondary:
        print(f"  ✓ Found on SECONDARY: {result_secondary['username']}")
        print(f"  ✓ Data successfully replicated to follower!")
    else:
        print(f"  ✗ Not found on SECONDARY (replication may be delayed)")
    
    primary_client.close()
    secondary_client.close()

def test_replication_lag(db):
    """Measure replication lag between primary and secondaries"""
    print("\n--- Test 3: Measuring Replication Lag ---")
    
    test_user_id = int(time.time() * 1000) % 100000
    
    # Write to primary
    print(f"Writing user_id={test_user_id} to primary...")
    write_time = time.time()
    
    collection = db.get_collection('UserProfile', write_concern=WriteConcern(w=1))
    collection.insert_one(
        {
            "user_id": test_user_id,
            "username": "lag_test_user",
            "email": "lag@example.com",
            "write_timestamp": write_time
        }
    )
    
    # Immediately check secondary
    secondary_client = MongoClient(
        'mongodb://mongo1:27017,mongo2:27017,mongo3:27017/?replicaSet=rs0',
        readPreference='secondary'
    )
    secondary_db = secondary_client.testDB
    
    print("Polling secondary until data appears...")
    attempts = 0
    found = False
    
    while attempts < 30:  # 3 seconds max
        attempts += 1
        result = secondary_db.UserProfile.find_one({"user_id": test_user_id})
        
        if result:
            lag = time.time() - write_time
            print(f"  ✓ Data appeared on secondary after {lag:.3f}s ({attempts} attempts)")
            found = True
            break
        
        time.sleep(0.1)
    
    if not found:
        print(f"  ! Data not replicated after 3 seconds")
    
    secondary_client.close()

def test_primary_failure_instructions():
    """Provide instructions for manual primary failure simulation"""
    print("\n--- Test 4: Primary Failure Simulation ---")
    print("To simulate primary failure, follow these steps:")
    print("")
    print("1. Identify the current primary node from the status above")
    print("2. In a new terminal, run:")
    print("   docker exec -it mongo1 mongosh")
    print("   rs.stepDown(60)  # Steps down primary for 60 seconds")
    print("")
    print("3. Or stop the primary container:")
    print("   docker stop <primary_container>")
    print("")
    print("4. Then re-run this script to observe:")
    print("   - New primary election (~10-12 seconds)")
    print("   - Automatic failover")
    print("   - No data loss")
    print("   - Brief downtime during election")
    print("")
    print("5. Restart the stopped container:")
    print("   docker start <container_name>")
    print("")

def test_automatic_reconnection(db):
    """Test client's automatic reconnection behavior"""
    print("\n--- Test 5: Client Automatic Reconnection ---")
    
    print("MongoDB drivers automatically reconnect to new primary")
    print("Testing write operation (will auto-reconnect if primary changed)...")
    
    try:
        test_user_id = int(time.time() * 1000) % 100000
        collection = db.get_collection('UserProfile', write_concern=WriteConcern(w='majority'))
        result = collection.insert_one(
            {
                "user_id": test_user_id,
                "username": "reconnect_test",
                "email": "reconnect@example.com",
                "last_login_time": time.time()
            }
        )
        print(f"  ✓ Write successful (connected to current primary)")
    except AutoReconnect as e:
        print(f"  ! Auto-reconnecting to new primary: {e}")
    except Exception as e:
        print(f"  ✗ Write failed: {e}")

def run_leader_follower_experiments():
   
    client = connect_to_replica_set()
    if not client:
        print("Cannot proceed without database connection")
        return
    
    db = client.testDB
    
    # Display replica set info
    rs_info = display_replica_set_info(client)
    
    if not rs_info:
        print("Failed to get replica set information")
        client.close()
        return
    
    # Run tests
    user_id = test_write_to_primary(db)
    test_read_from_secondaries(db, user_id)
    test_replication_lag(db)
    # test_primary_failure_instructions()
    # test_automatic_reconnection(db)
    

    
    client.close()

if __name__ == "__main__":
    run_leader_follower_experiments()
