"""Query routing application service."""
import logging
from typing import Any

from ..domain.models import QueryRoute, ShardingConfig
from ..domain.ports import ShardingRouter

logger = logging.getLogger(__name__)


class QueryRoutingService:
    """Routes queries to appropriate shards."""

    def __init__(self, router: ShardingRouter):
        self.router = router

    def route_single_key(self, shard_key_value: Any, config: ShardingConfig
        ) ->QueryRoute:
        """Route query for a single shard key."""
        route = self.router.route_query(shard_key_value, config)
        logger.debug(
            f'Routed key {shard_key_value} to shards: {route.shard_ids}')
        return route

    def route_range(self, start: Any, end: Any, config: ShardingConfig
        ) ->QueryRoute:
        """Route range query."""
        route = self.router.route_range_query(start, end, config)
        if route.is_cross_shard:
            logger.warning(
                f'Cross-shard query detected: {len(route.shard_ids)} shards involved'
                )
        return route
