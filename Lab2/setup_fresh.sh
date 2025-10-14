#!/bin/bash

echo "Starting MongoDB replica set..."
docker-compose up -d

echo "Waiting for containers to start..."
sleep 5

echo "Initializing replica set..."
docker exec -it mongo1 mongosh --eval "
rs.initiate({
  _id: 'rs0',
  members: [
    { _id: 0, host: 'mongo1:27017' },
    { _id: 1, host: 'mongo2:27017' },
    { _id: 2, host: 'mongo3:27017' }
  ]
});
"

echo "Waiting for replica set to stabilize..."
sleep 10

echo "Checking replica set status..."
docker exec -it mongo1 mongosh --eval "rs.status().members.forEach(m => print(m.name + ' - ' + m.stateStr))"

echo ""
echo "Inserting initial data..."
docker exec -it mongo1 mongosh --eval "
use testDB;
db.UserProfile.insertMany([
  { user_id: 1, username: 'Aditya', email: 'aditya@example.com', last_login_time: Date.now() },
  { user_id: 2, username: 'Abhay', email: 'abhay@example.com', last_login_time: Date.now() },
  { user_id: 3, username: 'Aditi', email: 'aditi@example.com', last_login_time: Date.now() }
]);
"

echo ""
echo "Setup complete! Verifying data..."
docker exec -it mongo1 mongosh --eval "use testDB; db.UserProfile.find().pretty()"
