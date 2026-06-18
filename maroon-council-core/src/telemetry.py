"""
Maroon Council Core — Telemetry Module
Implements the Palantir Mandate (Codex §5.1).
Every orchestration decision is emitted as a telemetry event.
"""
import json
import logging
from typing import Dict, Any
from datetime import datetime, timezone

logger = logging.getLogger("maroon.telemetry")


class TelemetryEmitter:
    """Emits structured telemetry events to Palantir Lake.
    
    In production this writes to the Kafka `bronze_raw_ingress` topic.
    When Kafka is unavailable it falls back to structured logging so
    telemetry is never silently lost.
    """

    def __init__(self, source: str, kafka_servers: list = None):
        self.source = source
        self._producer = None
        if kafka_servers:
            try:
                from kafka import KafkaProducer
                self._producer = KafkaProducer(
                    bootstrap_servers=kafka_servers,
                    value_serializer=lambda v: json.dumps(v, default=str).encode("utf-8"),
                )
            except Exception as exc:
                logger.warning("Kafka unavailable (%s). Falling back to log-based telemetry.", exc)

    def emit(self, event_type: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        envelope = {
            "source": self.source,
            "event_type": event_type,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "data": payload,
            "verification_status": "PENDING_MERKLE_HASH",
        }
        if self._producer:
            self._producer.send("bronze_raw_ingress", value=envelope)
            self._producer.flush()
        else:
            logger.info("[TELEMETRY] %s", json.dumps(envelope, default=str))
        return envelope
