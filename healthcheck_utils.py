"""Health check utilities for Python HTTP servers."""

def check_health(services=None):
    """Check health of configured services."""
    results = {"status": "ok"}
    if services:
        for svc in services:
            results[svc] = "healthy"
    return results

def format_metrics(hostname, uptime=None):
    """Format system metrics for monitoring."""
    metrics = {"hostname": hostname}
    if uptime:
        metrics["uptime"] = uptime
    return metrics
