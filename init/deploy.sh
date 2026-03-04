#!/bin/bash

set -e

ENV=${1:-dev}
REGION=ap-northeast-1
STACK_NAME=stack-sgp-${ENV}-infra-cfn-execution-policies

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

echo "=== Deploying CloudFormation Execution Policies Stack ==="
echo "Stack: $STACK_NAME"
echo "Region: $REGION"
echo ""

aws cloudformation deploy \
  --region "$REGION" \
  --template-file "$SCRIPT_DIR/cfn-execution-policies.yaml" \
  --stack-name "$STACK_NAME" \
  --capabilities CAPABILITY_NAMED_IAM

echo ""
echo "✓ Done"
