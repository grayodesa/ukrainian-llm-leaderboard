#!/bin/bash
# API-compatible evaluation script for Ukrainian LLM Leaderboard
# Supports OpenAI-compatible APIs, native OpenAI, and Anthropic
#
# Usage:
#   ./eval_api.sh                    # Interactive mode - prompts for settings
#   ./eval_api.sh openai gpt-4o      # OpenAI with specific model
#   ./eval_api.sh anthropic claude-3-5-sonnet-20241022
#   ./eval_api.sh local model-name http://localhost:8000/v1
#
# Environment variables (can be set in .env file):
#   OPENAI_API_KEY     - Required for OpenAI
#   OPENAI_BASE_URL    - Optional: Custom base URL for OpenAI-compatible APIs
#   ANTHROPIC_API_KEY  - Required for Anthropic

set -e

# Load .env file if it exists
if [ -f .env ]; then
    echo "Loading environment from .env file..."
    set -a
    source .env
    set +a
fi

# Export HF_TOKEN for HuggingFace gated datasets (if set)
if [ -n "$HF_TOKEN" ]; then
    export HF_TOKEN
    echo "HuggingFace token configured"
fi

# Default settings
NUM_CONCURRENT="${NUM_CONCURRENT:-8}"
MAX_RETRIES="${MAX_RETRIES:-3}"
OUTPUT_PATH="${OUTPUT_PATH:-./eval-results}"
TASKS="${TASKS:-ukrainian_bench}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

print_usage() {
    echo "Usage: $0 <provider> <model> [base_url]"
    echo ""
    echo "Providers:"
    echo "  openai     - OpenAI API (requires OPENAI_API_KEY, uses OPENAI_BASE_URL if set)"
    echo "  anthropic  - Anthropic API (requires ANTHROPIC_API_KEY)"
    echo "  local      - OpenAI-compatible local API (requires base_url as 3rd argument)"
    echo ""
    echo "Examples:"
    echo "  $0 openai gpt-4o"
    echo "  $0 anthropic claude-3-5-sonnet-20241022"
    echo "  $0 local meta-llama/Llama-3.1-8B-Instruct http://localhost:8000/v1"
    echo ""
    echo "Environment variables (can be set in .env file):"
    echo "  OPENAI_API_KEY    - API key for OpenAI"
    echo "  OPENAI_BASE_URL   - Custom base URL (e.g., https://api.openai.com/v1)"
    echo "  ANTHROPIC_API_KEY - API key for Anthropic"
    echo "  NUM_CONCURRENT    - Concurrent requests (default: $NUM_CONCURRENT)"
    echo "  MAX_RETRIES       - Max retries per request (default: $MAX_RETRIES)"
    echo "  OUTPUT_PATH       - Output directory (default: $OUTPUT_PATH)"
    echo "  TASKS             - Task group to run (default: $TASKS)"
}

check_api_key() {
    local provider=$1
    case $provider in
        openai)
            if [ -z "$OPENAI_API_KEY" ]; then
                echo -e "${RED}Error: OPENAI_API_KEY environment variable not set${NC}"
                exit 1
            fi
            ;;
        anthropic)
            if [ -z "$ANTHROPIC_API_KEY" ]; then
                echo -e "${RED}Error: ANTHROPIC_API_KEY environment variable not set${NC}"
                exit 1
            fi
            ;;
    esac
}

run_openai_eval() {
    local model=$1
    # Support both OPENAI_BASE_URL and legacy OPENAI_API_BASE
    local base_url="${OPENAI_BASE_URL:-${OPENAI_API_BASE:-https://api.openai.com/v1/chat/completions}}"

    # Ensure URL ends with /chat/completions for lm-eval compatibility
    if [[ ! "$base_url" == */chat/completions ]]; then
        base_url="${base_url%/}/chat/completions"
    fi

    echo -e "${GREEN}Running evaluation with OpenAI API${NC}"
    echo "Model: $model"
    echo "Base URL: $base_url"
    echo "Concurrent requests: $NUM_CONCURRENT"
    echo ""

    lm_eval --model local-chat-completions \
        --model_args "model=$model,base_url=$base_url,num_concurrent=$NUM_CONCURRENT,max_retries=$MAX_RETRIES,tokenized_requests=False" \
        --tasks "$TASKS" \
        --include_path ./tasks \
        --apply_chat_template \
        --output_path "$OUTPUT_PATH" \
        --log_samples
}

run_anthropic_eval() {
    local model=$1

    echo -e "${GREEN}Running evaluation with Anthropic API${NC}"
    echo "Model: $model"
    echo ""

    lm_eval --model anthropic \
        --model_args "model=$model" \
        --tasks "$TASKS" \
        --include_path ./tasks \
        --apply_chat_template \
        --output_path "$OUTPUT_PATH" \
        --log_samples
}

run_local_eval() {
    local model=$1
    local base_url=$2

    # Ensure URL ends with /chat/completions for lm-eval compatibility
    if [[ ! "$base_url" == */chat/completions ]]; then
        base_url="${base_url%/}/chat/completions"
    fi

    echo -e "${GREEN}Running evaluation with local OpenAI-compatible API${NC}"
    echo "Model: $model"
    echo "Base URL: $base_url"
    echo "Concurrent requests: $NUM_CONCURRENT"
    echo ""

    lm_eval --model local-chat-completions \
        --model_args "model=$model,base_url=$base_url,num_concurrent=$NUM_CONCURRENT,max_retries=$MAX_RETRIES,tokenized_requests=False" \
        --tasks "$TASKS" \
        --include_path ./tasks \
        --apply_chat_template \
        --output_path "$OUTPUT_PATH" \
        --log_samples
}

# Main script
if [ "$1" == "-h" ] || [ "$1" == "--help" ]; then
    print_usage
    exit 0
fi

PROVIDER=$1
MODEL=$2
BASE_URL=$3

# Interactive mode if no arguments
if [ -z "$PROVIDER" ]; then
    echo "Select provider:"
    echo "1) OpenAI"
    echo "2) Anthropic"
    echo "3) Local OpenAI-compatible API"
    read -p "Choice [1-3]: " choice

    case $choice in
        1) PROVIDER="openai" ;;
        2) PROVIDER="anthropic" ;;
        3) PROVIDER="local" ;;
        *) echo "Invalid choice"; exit 1 ;;
    esac

    read -p "Model name: " MODEL

    if [ "$PROVIDER" == "local" ]; then
        read -p "Base URL (e.g., http://localhost:8000/v1/chat/completions): " BASE_URL
    fi
fi

# Validate inputs
if [ -z "$MODEL" ]; then
    echo -e "${RED}Error: Model name is required${NC}"
    print_usage
    exit 1
fi

# Run evaluation based on provider
case $PROVIDER in
    openai)
        check_api_key openai
        run_openai_eval "$MODEL"
        ;;
    anthropic)
        check_api_key anthropic
        run_anthropic_eval "$MODEL"
        ;;
    local)
        if [ -z "$BASE_URL" ]; then
            echo -e "${RED}Error: Base URL is required for local provider${NC}"
            print_usage
            exit 1
        fi
        run_local_eval "$MODEL" "$BASE_URL"
        ;;
    *)
        echo -e "${RED}Error: Unknown provider '$PROVIDER'${NC}"
        print_usage
        exit 1
        ;;
esac

echo -e "${GREEN}Evaluation complete!${NC}"
echo "Results saved to: $OUTPUT_PATH"
