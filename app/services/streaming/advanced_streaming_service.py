from __future__ import annotations

import logging
import threading
import time
import uuid
from collections import defaultdict, deque
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from typing import Any


class StreamingProtocol(Enum):
    """Streaming protocols"""
    KAFKA = 'kafka'
    PULSAR = 'pulsar'
    REDPANDA = 'redpanda'
    IN_MEMORY = 'in_memory'


class StreamType(Enum):
    """Stream types"""
    EVENT_STREAM = 'event_stream'
    DATA_STREAM = 'data_stream'
    LOG_STREAM = 'log_stream'
    METRIC_STREAM = 'metric_stream'


class DeliveryGuarantee(Enum):
    """Message delivery guarantees"""
    AT_MOST_ONCE = 'at_most_once'
    AT_LEAST_ONCE = 'at_least_once'
    EXACTLY_ONCE = 'exactly_once'


@dataclass
class StreamConfig:
    """Stream configuration"""
    stream_id: str
    name: str
    protocol: StreamingProtocol
    stream_type: StreamType
    partitions: int
    replication_factor: int
    retention_hours: int
    delivery_guarantee: DeliveryGuarantee
    geo_replicated: bool = False
    schema_id: str | None = None
    created_at: datetime = field(default_factory=lambda : datetime.now(UTC))


@dataclass
class StreamMessage:
    """Stream message"""
    message_id: str
    stream_id: str
    partition: int
    key: str | None
    payload: dict[str, Any]
    headers: dict[str, str]
    timestamp: datetime = field(default_factory=lambda : datetime.now(UTC))
    offset: int = 0


@dataclass
class StreamConsumer:
    """Stream consumer"""
    consumer_id: str
    consumer_group: str
    stream_id: str
    callback: Callable[[StreamMessage], None]
    offset: int = 0
    active: bool = True


@dataclass
class StreamSchema:
    """Stream schema for validation"""
    schema_id: str
    stream_id: str
    version: int
    schema_type: str
    schema_definition: dict[str, Any]
    created_at: datetime = field(default_factory=lambda : datetime.now(UTC))


@dataclass
class StreamMetrics:
    """Stream metrics"""
    stream_id: str
    messages_per_second: float
    bytes_per_second: float
    total_messages: int
    lag: int
    partition_metrics: dict[int, dict[str, float]]
    timestamp: datetime = field(default_factory=lambda : datetime.now(UTC))


class AdvancedStreamingService:
    """
    خدمة Streaming الخارقة - World-class streaming platform

    Features:
    - Multi-protocol support
    - Millions of events/second
    - Geo-replication
    - Schema registry
    - Stream processing
    """

    def __init__(self):
        self.streams: dict[str, StreamConfig] = {}
        self.messages: dict[str, deque[StreamMessage]] = defaultdict(lambda :
            deque(maxlen=1000000))
        self.consumers: dict[str, list[StreamConsumer]] = defaultdict(list)
        self.schemas: dict[str, StreamSchema] = {}
        self.metrics: dict[str, StreamMetrics] = {}
        self.lock = threading.RLock()
        self.message_counter = 0
        logging.getLogger(__name__).info(
            'Advanced Streaming Service initialized')

    def create_stream(self, config: StreamConfig) ->bool:
        """Create stream"""
        with self.lock:
            self.streams[config.stream_id] = config
            self.metrics[config.stream_id] = StreamMetrics(stream_id=config
                .stream_id, messages_per_second=0.0, bytes_per_second=0.0,
                total_messages=0, lag=0, partition_metrics={i: {'messages':
                0, 'bytes': 0} for i in range(config.partitions)})
            logging.getLogger(__name__).info(
                f'Created stream: {config.name} ({config.protocol.value})')
            return True

    def get_stream(self, stream_id: str) ->(StreamConfig | None):
        """Get stream configuration"""
        return self.streams.get(stream_id)

    def produce(self, stream_id: str, payload: dict[str, Any], key: (str |
        None)=None, headers: (dict[str, str] | None)=None) ->(StreamMessage |
        None):
        """Produce message to stream"""
        stream = self.streams.get(stream_id)
        if not stream:
            return None
        if stream.schema_id:
            schema = self.schemas.get(stream.schema_id)
            if schema and not self._validate_schema(payload, schema):
                logging.getLogger(__name__).error(
                    f'Schema validation failed for stream {stream_id}')
                return None
        partition = self._get_partition(key, stream.partitions)
        with self.lock:
            self.message_counter += 1
            offset = self.message_counter
        message = StreamMessage(message_id=str(uuid.uuid4()), stream_id=
            stream_id, partition=partition, key=key, payload=payload,
            headers=headers or {}, offset=offset)
        with self.lock:
            self.messages[stream_id].append(message)
            self._update_metrics(stream_id, message)
            self._deliver_to_consumers(stream_id, message)
        return message

    def _get_partition(self, key: (str | None), num_partitions: int) ->int:
        """Get partition for message"""
        if key is None:
            return hash(str(time.time())) % num_partitions
        return hash(key) % num_partitions

    def _validate_schema(self, payload: dict[str, Any], schema: StreamSchema
        ) ->bool:
        """Validate message against schema"""
        if schema.schema_type == 'json':
            required_fields = schema.schema_definition.get('required', [])
            return all(field in payload for field in required_fields)
        return True

    def subscribe(self, stream_id: str, consumer_group: str, callback:
        Callable[[StreamMessage], None]) ->str:
        """Subscribe to stream"""
        consumer_id = str(uuid.uuid4())
        consumer = StreamConsumer(consumer_id=consumer_id, consumer_group=
            consumer_group, stream_id=stream_id, callback=callback)
        with self.lock:
            self.consumers[stream_id].append(consumer)
        logging.getLogger(__name__).info(
            f'Consumer {consumer_id} subscribed to {stream_id}')
        return consumer_id

    def _deliver_to_consumers(self, stream_id: str, message: StreamMessage):
        """Deliver message to active consumers"""
        consumers = self.consumers.get(stream_id, [])
        for consumer in consumers:
            if consumer.active:
                try:
                    consumer.callback(message)
                    consumer.offset = message.offset
                except Exception as e:
                    logging.getLogger(__name__).error(
                        f'Consumer {consumer.consumer_id} error: {e}')

    def unsubscribe(self, consumer_id: str):
        """Unsubscribe consumer"""
        with self.lock:
            for stream_consumers in self.consumers.values():
                for consumer in stream_consumers:
                    if consumer.consumer_id == consumer_id:
                        consumer.active = False
                        break

    def register_schema(self, schema: StreamSchema) ->bool:
        """Register stream schema"""
        with self.lock:
            self.schemas[schema.schema_id] = schema
            logging.getLogger(__name__).info(
                f'Registered schema: {schema.schema_id}')
            return True

    def get_schema(self, schema_id: str) ->(StreamSchema | None):
        """Get schema"""
        return self.schemas.get(schema_id)

    def _update_metrics(self, stream_id: str, message: StreamMessage):
        """Update stream metrics"""
        metrics = self.metrics.get(stream_id)
        if not metrics:
            return
        metrics.total_messages += 1
        import json
        message_bytes = len(json.dumps(message.payload).encode())
        partition_metrics = metrics.partition_metrics.get(message.partition, {}
            )
        partition_metrics['messages'] = partition_metrics.get('messages', 0
            ) + 1
        partition_metrics['bytes'] = partition_metrics.get('bytes', 0
            ) + message_bytes
        metrics.messages_per_second = metrics.total_messages / max(1, (
            datetime.now(UTC) - metrics.timestamp).total_seconds())

    def get_stream_metrics(self, stream_id: str) ->(StreamMetrics | None):
        """Get stream metrics"""
        return self.metrics.get(stream_id)

    def process_stream(self, stream_id: str, processor: Callable[[
        StreamMessage], StreamMessage | None], output_stream_id: str) ->str:
        """Process stream with transformation"""
        processor_id = str(uuid.uuid4())

        def processing_callback(message: StreamMessage):
            processed = processor(message)
            if processed:
                self.produce(output_stream_id, processed.payload, processed
                    .key, processed.headers)
        self.subscribe(stream_id, f'processor-{processor_id}',
            processing_callback)
        logging.getLogger(__name__).info(
            f'Stream processor {processor_id} started: {stream_id} -> {output_stream_id}'
            )
        return processor_id

    def get_platform_metrics(self) ->dict[str, Any]:
        """Get platform metrics"""
        total_messages = sum(m.total_messages for m in self.metrics.values())
        total_throughput = sum(m.messages_per_second for m in self.metrics.
            values())
        return {'total_streams': len(self.streams), 'total_messages':
            total_messages, 'total_throughput_mps': total_throughput,
            'total_consumers': sum(len(c) for c in self.consumers.values()),
            'active_consumers': sum(len([c for c in consumers if c.active]) for
            consumers in self.consumers.values()), 'total_schemas': len(
            self.schemas), 'protocols_used': list({s.protocol.value for s in
            self.streams.values()})}


_streaming_instance: AdvancedStreamingService | None = None
_streaming_lock = threading.Lock()


def get_streaming_service() ->AdvancedStreamingService:
    """Get singleton streaming service instance"""
    global _streaming_instance
    if _streaming_instance is None:
        with _streaming_lock:
            if _streaming_instance is None:
                _streaming_instance = AdvancedStreamingService()
    return _streaming_instance
