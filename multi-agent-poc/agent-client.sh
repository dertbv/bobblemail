#!/bin/bash

# Agent Communication Client for Message Broker
# Easy-to-use functions for agents to communicate

BROKER_URL="${BROKER_URL:-http://localhost:3000}"
AGENT_ID="${AGENT_ID:-agent-$$}"

# Send a message (fire and forget)
send_message() {
    local description="$1"
    local content="$2"
    local tags="${3:-status}"
    
    curl -s -X POST "$BROKER_URL/send" \
        -H "Content-Type: application/json" \
        -d "{
            \"agent_id\": \"$AGENT_ID\",
            \"description\": \"$description\",
            \"content\": $content,
            \"tags\": [\"$tags\"]
        }" | jq -r '.'
}

# Send and wait for response
send_and_wait() {
    local description="$1"
    local content="$2"
    local tags="${3:-request}"
    
    curl -s -X POST "$BROKER_URL/send-and-wait" \
        -H "Content-Type: application/json" \
        -d "{
            \"agent_id\": \"$AGENT_ID\",
            \"description\": \"$description\",
            \"content\": $content,
            \"tags\": [\"$tags\"]
        }" | jq -r '.'
}

# Receive next message
receive_message() {
    local tags="${1:-}"
    local filter=""
    
    if [[ -n "$tags" ]]; then
        filter=", \"tags\": [\"$tags\"]"
    fi
    
    curl -s -X POST "$BROKER_URL/receive" \
        -H "Content-Type: application/json" \
        -d "{
            \"agent_id\": \"$AGENT_ID\"
            $filter
        }" | jq -r '.'
}

# Check messages without consuming
check_messages() {
    local tags="${1:-}"
    local filter=""
    
    if [[ -n "$tags" ]]; then
        filter=", \"tags\": [\"$tags\"]"
    fi
    
    curl -s -X POST "$BROKER_URL/check" \
        -H "Content-Type: application/json" \
        -d "{
            \"agent_id\": \"$AGENT_ID\"
            $filter
        }" | jq -r '.'
}

# Respond to a request
respond_to() {
    local request_id="$1"
    local response="$2"
    
    curl -s -X POST "$BROKER_URL/respond" \
        -H "Content-Type: application/json" \
        -d "{
            \"request_id\": \"$request_id\",
            \"responder_id\": \"$AGENT_ID\",
            \"response_content\": $response
        }" | jq -r '.'
}

# Get broker status
broker_status() {
    curl -s "$BROKER_URL/status" | jq -r '.'
}

# Example usage
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    echo "Agent Client Test"
    echo "Agent ID: $AGENT_ID"
    echo ""
    
    case "${1:-help}" in
        send)
            send_message "Test message" '{"test": true}' "test"
            ;;
        receive)
            receive_message "${2:-}"
            ;;
        check)
            check_messages "${2:-}"
            ;;
        status)
            broker_status
            ;;
        *)
            echo "Usage: $0 [send|receive|check|status]"
            echo ""
            echo "Functions available when sourced:"
            echo "  send_message <description> <json_content> [tags]"
            echo "  send_and_wait <description> <json_content> [tags]"
            echo "  receive_message [tags]"
            echo "  check_messages [tags]"
            echo "  respond_to <request_id> <json_response>"
            echo "  broker_status"
            ;;
    esac
fi