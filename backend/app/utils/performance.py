"""
Performance monitoring and metrics utilities.
"""
import time
import functools
import logging
from typing import Dict, Any, Callable, Optional
from contextlib import contextmanager

logger = logging.getLogger(__name__)


class PerformanceMonitor:
    """Simple performance monitoring utility."""
    
    def __init__(self):
        self.metrics = {}
    
    def record_metric(self, name: str, value: float, tags: Optional[Dict[str, str]] = None):
        """Record a performance metric."""
        if name not in self.metrics:
            self.metrics[name] = []
        
        self.metrics[name].append({
            "value": value,
            "timestamp": time.time(),
            "tags": tags or {}
        })
        
        # Keep only last 1000 measurements
        if len(self.metrics[name]) > 1000:
            self.metrics[name] = self.metrics[name][-1000:]
    
    def get_metrics(self, name: str) -> Dict[str, Any]:
        """Get metrics summary for a specific metric."""
        if name not in self.metrics:
            return {}
        
        values = [m["value"] for m in self.metrics[name]]
        
        return {
            "count": len(values),
            "min": min(values),
            "max": max(values),
            "avg": sum(values) / len(values),
            "recent": values[-10:] if len(values) >= 10 else values
        }
    
    def get_all_metrics(self) -> Dict[str, Dict[str, Any]]:
        """Get summary of all metrics."""
        return {name: self.get_metrics(name) for name in self.metrics.keys()}


# Global performance monitor instance
performance_monitor = PerformanceMonitor()


def monitor_performance(metric_name: str):
    """Decorator to monitor function execution time."""
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                success = True
            except Exception as e:
                success = False
                raise
            finally:
                execution_time = (time.time() - start_time) * 1000  # Convert to milliseconds
                
                performance_monitor.record_metric(
                    metric_name,
                    execution_time,
                    {"success": str(success), "function": func.__name__}
                )
                
                if execution_time > 1000:  # Log slow operations (> 1 second)
                    logger.warning(f"Slow operation detected: {func.__name__} took {execution_time:.2f}ms")
            
            return result
        return wrapper
    return decorator


@contextmanager
def performance_context(metric_name: str, tags: Optional[Dict[str, str]] = None):
    """Context manager for monitoring code block performance."""
    start_time = time.time()
    try:
        yield
        success = True
    except Exception:
        success = False
        raise
    finally:
        execution_time = (time.time() - start_time) * 1000
        
        final_tags = {"success": str(success)}
        if tags:
            final_tags.update(tags)
        
        performance_monitor.record_metric(metric_name, execution_time, final_tags)


class DatabaseQueryMonitor:
    """Monitor database query performance."""
    
    def __init__(self):
        self.slow_queries = []
        self.query_count = 0
        self.total_time = 0
    
    def record_query(self, query: str, execution_time: float, result_count: Optional[int] = None):
        """Record database query metrics."""
        self.query_count += 1
        self.total_time += execution_time
        
        # Record slow queries (> 100ms)
        if execution_time > 0.1:
            self.slow_queries.append({
                "query": query[:200] + "..." if len(query) > 200 else query,
                "execution_time": execution_time,
                "result_count": result_count,
                "timestamp": time.time()
            })
            
            # Keep only last 100 slow queries
            if len(self.slow_queries) > 100:
                self.slow_queries = self.slow_queries[-100:]
    
    def get_stats(self) -> Dict[str, Any]:
        """Get database query statistics."""
        avg_time = self.total_time / self.query_count if self.query_count > 0 else 0
        
        return {
            "total_queries": self.query_count,
            "total_time": self.total_time,
            "average_time": avg_time,
            "slow_queries_count": len(self.slow_queries),
            "recent_slow_queries": self.slow_queries[-5:] if self.slow_queries else []
        }


# Global database monitor instance
db_monitor = DatabaseQueryMonitor()
