#!/usr/bin/env bash
set -e

NAMESPACE="lakewatch"
POD="kafka-0"
KAFKA_BIN="/opt/kafka/bin"

case "${1:-help}" in
  status)
    kubectl get pods,svc,pvc -n "$NAMESPACE"
    ;;
  logs)
    kubectl logs "$POD" -n "$NAMESPACE" --tail=50
    ;;
  topics)
    kubectl exec -n "$NAMESPACE" "$POD" -- \
      "$KAFKA_BIN/kafka-topics.sh" \
      --bootstrap-server kafka:9092 --list
    ;;
  describe)
    kubectl exec -n "$NAMESPACE" "$POD" -- \
      "$KAFKA_BIN/kafka-topics.sh" \
      --bootstrap-server kafka:9092 \
      --describe --topic "${2:-sensor-readings}"
    ;;
  produce)
    kubectl exec -it -n "$NAMESPACE" "$POD" -- \
      "$KAFKA_BIN/kafka-console-producer.sh" \
      --bootstrap-server kafka:9092 \
      --topic "${2:-sensor-readings}"
    ;;
  consume)
    kubectl exec -n "$NAMESPACE" "$POD" -- \
      "$KAFKA_BIN/kafka-console-consumer.sh" \
      --bootstrap-server kafka:9092 \
      --topic "${2:-sensor-readings}" \
      --from-beginning --max-messages "${3:-5}"
    ;;
  help|*)
    echo "Lakewatch Kafka shortcuts"
    echo "  bash scripts/kafka.sh status"
    echo "  bash scripts/kafka.sh logs"
    echo "  bash scripts/kafka.sh topics"
    echo "  bash scripts/kafka.sh describe [topic]"
    echo "  bash scripts/kafka.sh produce [topic]"
    echo "  bash scripts/kafka.sh consume [topic] [count]"
    ;;
esac
