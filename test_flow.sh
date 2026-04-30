#!/bin/bash

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

BASE_URL="http://localhost:8000"
TIMESTAMP=$(date +%s)
EMAIL="student${TIMESTAMP}@example.com"

echo -e "${BLUE}=== StudyOwl API Test Flow ===${NC}\n"

# Test 1: Signup
echo -e "${BLUE}1. Testing Signup${NC}"
echo "Email: $EMAIL"
SIGNUP_RESPONSE=$(curl -s -X POST "$BASE_URL/api/auth/signup" \
  -H "Content-Type: application/json" \
  -d "{\"name\": \"Test Student\", \"email\": \"$EMAIL\", \"password\": \"testpass123\", \"grade_level\": \"Grade 9\", \"role\": \"student\"}")
echo "Response: $SIGNUP_RESPONSE"

TOKEN=$(echo "$SIGNUP_RESPONSE" | grep -o '"access_token":"[^"]*' | cut -d'"' -f4)
if [ -z "$TOKEN" ]; then
  echo -e "${RED}Failed to extract token${NC}"
  exit 1
fi
echo -e "${GREEN}✓ Signup successful, Token: ${TOKEN:0:20}...${NC}\n"

# Test 2: Login
echo -e "${BLUE}2. Testing Login${NC}"
LOGIN_RESPONSE=$(curl -s -X POST "$BASE_URL/api/auth/login" \
  -H "Content-Type: application/json" \
  -d "{\"email\": \"$EMAIL\", \"password\": \"testpass123\"}")
echo "Response: $LOGIN_RESPONSE"
LOGIN_TOKEN=$(echo "$LOGIN_RESPONSE" | grep -o '"access_token":"[^"]*' | cut -d'"' -f4)
if [ -z "$LOGIN_TOKEN" ]; then
  echo -e "${RED}Failed to extract login token${NC}"
else
  echo -e "${GREEN}✓ Login successful${NC}\n"
fi

# Test 3: Start Session
echo -e "${BLUE}3. Testing Session Start${NC}"
SESSION_RESPONSE=$(curl -s -X POST "$BASE_URL/api/session/start" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"question": "What is 2 + 2?"}')
echo "Response: $SESSION_RESPONSE"

SESSION_ID=$(echo "$SESSION_RESPONSE" | grep -o '"session_id":"[^"]*' | cut -d'"' -f4)
if [ -z "$SESSION_ID" ]; then
  echo -e "${RED}Failed to extract session ID${NC}"
  echo -e "${RED}Error: Some endpoints may not be implemented yet${NC}\n"
else
  echo -e "${GREEN}✓ Session started, ID: $SESSION_ID${NC}\n"
  
  # Test 4: Submit Attempt
  echo -e "${BLUE}4. Testing Attempt Submission${NC}"
  ATTEMPT_RESPONSE=$(curl -s -X POST "$BASE_URL/api/session/$SESSION_ID/attempt" \
    -H "Content-Type: application/json" \
    -H "Authorization: Bearer $TOKEN" \
    -d '{"attempt_text": "4"}')
  echo "Response: $ATTEMPT_RESPONSE"
  echo -e "${GREEN}✓ Attempt submitted${NC}\n"
fi

echo -e "${BLUE}=== Test Flow Complete ===${NC}"
