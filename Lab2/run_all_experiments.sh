#!/bin/bash

echo "=========================================="
echo "Running All Lab 2 Experiments"
echo "=========================================="
echo ""

# Array of test scripts
tests=(
    "code/write_concern_test.py"
    "code/leader_follower_test.py"
    "code/strong_consistency_test.py"
    "code/eventual_consistency_test.py"
)

# Run each test
for test in "${tests[@]}"; do
    echo ""
    echo "=========================================="
    echo "Running: $test"
    echo "=========================================="
    echo ""
    
    ./run_test_in_docker.sh "$test"
    
    if [ $? -eq 0 ]; then
        echo "✓ $test completed successfully"
    else
        echo "✗ $test failed"
    fi
    
    echo ""
    echo "Press Enter to continue to next test..."
    read
done

echo ""
echo "=========================================="
echo "All experiments completed!"
echo "=========================================="
echo ""
echo "Check the output above for results."
echo "Take screenshots for your lab report."
