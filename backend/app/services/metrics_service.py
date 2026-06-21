"""
Metrics Service - Prometheus metrics for observability
This module provides metrics collection for monitoring and alerting.
"""
from typing import Dict, Optional
from time import time
from functools import wraps
import threading

# TODO: Install prometheus-client and configure Prometheus
# from prometheus_client import Counter, Histogram, Gauge, start_http_server


class MetricsService:
    """
    Prometheus metrics service for observability.
    Tracks application metrics for monitoring and alerting.
    """
    
    def __init__(self):
        # TODO: Initialize Prometheus metrics when prometheus-client is available
        self.enabled = False  # Disabled until Prometheus is configured
        
        # In-memory metrics (replace with actual Prometheus metrics)
        self.counters: Dict[str, int] = {}
        self.gauges: Dict[str, float] = {}
        self.histograms: Dict[str, list] = {}
        self.lock = threading.Lock()
    
    def increment_counter(self, name: str, labels: Optional[Dict[str, str]] = None, value: int = 1):
        """
        Increment a counter metric.
        Counters only increase and are used for things like request counts.
        """
        if not self.enabled:
            return
        
        key = self._make_key(name, labels)
        with self.lock:
            self.counters[key] = self.counters.get(key, 0) + value
        
        # TODO: Update actual Prometheus counter
        # counter.labels(**(labels or {})).inc(value)
    
    def set_gauge(self, name: str, value: float, labels: Optional[Dict[str, str]] = None):
        """
        Set a gauge metric.
        Gauges can go up or down and are used for things like current connections.
        """
        if not self.enabled:
            return
        
        key = self._make_key(name, labels)
        with self.lock:
            self.gauges[key] = value
        
        # TODO: Update actual Prometheus gauge
        # gauge.labels(**(labels or {})).set(value)
    
    def observe_histogram(self, name: str, value: float, labels: Optional[Dict[str, str]] = None):
        """
        Observe a histogram metric.
        Histograms track distributions of values (e.g., request durations).
        """
        if not self.enabled:
            return
        
        key = self._make_key(name, labels)
        with self.lock:
            if key not in self.histograms:
                self.histograms[key] = []
            self.histograms[key].append(value)
        
        # TODO: Update actual Prometheus histogram
        # histogram.labels(**(labels or {})).observe(value)
    
    def get_metrics(self) -> Dict:
        """
        Get current metrics values.
        Returns in-memory metrics (replace with Prometheus scrape endpoint).
        """
        with self.lock:
            return {
                'counters': self.counters.copy(),
                'gauges': self.gauges.copy(),
                'histograms': {
                    key: {
                        'count': len(values),
                        'sum': sum(values),
                        'avg': sum(values) / len(values) if values else 0,
                    }
                    for key, values in self.histograms.items()
                },
            }
    
    def _make_key(self, name: str, labels: Optional[Dict[str, str]] = None) -> str:
        """Create a key from metric name and labels."""
        if labels:
            label_str = ','.join(f"{k}={v}" for k, v in sorted(labels.items()))
            return f"{name}{{{label_str}}}"
        return name


# Global metrics service instance
metrics_service = MetricsService()


def track_counter(name: str, labels: Optional[Dict[str, str]] = None, value: int = 1):
    """
    Decorator to track counter metrics.
    Usage:
        @track_counter('api_requests', {'endpoint': '/songs'})
        def get_songs():
            return songs
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            metrics_service.increment_counter(name, labels, value)
            return func(*args, **kwargs)
        return wrapper
    return decorator


def track_histogram(name: str, labels: Optional[Dict[str, str]] = None):
    """
    Decorator to track histogram metrics (e.g., request duration).
    Usage:
        @track_histogram('request_duration', {'endpoint': '/songs'})
        def get_songs():
            return songs
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            start = time()
            try:
                result = func(*args, **kwargs)
                duration = time() - start
                metrics_service.observe_histogram(name, duration, labels)
                return result
            except Exception as e:
                duration = time() - start
                metrics_service.observe_histogram(name, duration, labels)
                raise
        return wrapper
    return decorator


# Pre-defined metric names
METRICS = {
    # API metrics
    'api_requests_total': 'Total number of API requests',
    'api_request_duration_seconds': 'API request duration in seconds',
    'api_errors_total': 'Total number of API errors',
    
    # Database metrics
    'db_queries_total': 'Total number of database queries',
    'db_query_duration_seconds': 'Database query duration in seconds',
    'db_connections_active': 'Number of active database connections',
    
    # Cache metrics
    'cache_hits_total': 'Total number of cache hits',
    'cache_misses_total': 'Total number of cache misses',
    'cache_hit_ratio': 'Cache hit ratio',
    
    # Business metrics
    'songs_played_total': 'Total number of songs played',
    'users_active': 'Number of active users',
    'revenue_total': 'Total revenue',
}
