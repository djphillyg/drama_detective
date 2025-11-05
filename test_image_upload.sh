TEST_IMAGE="iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8/5+hHgAHggJ/PchI7wAAAABJRU5ErkJggg=="

curl -X POST http://localhost:5000/api/investigate \
  -H "Content-Type: application/json" \
  -d '{
    "incident_name": "Test Image Upload",
    "summary": "Testing image processing",
    "images": ["'"$TEST_IMAGE"'"],
    "interviewee_name": "Tester",
    "interviewee_role": "participant"
  }'
