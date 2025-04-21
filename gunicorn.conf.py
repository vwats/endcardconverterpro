import multiprocessing
import os

# Server socket configuration
bind = "0.0.0.0:5000"
backlog = 2048

# Worker configuration optimized for Replit
workers = 2  # Replit has limited resources, so we keep this modest
worker_class = 'gthread'  # Thread-based workers for better performance
threads = 4  # Number of threads per worker
worker_connections = 250  # Reduced for Replit's environment
timeout = 120  # Increased timeout for file processing
keepalive = 5  # Keep connections alive longer
max_requests = 1000  # Restart workers after handling this many requests
max_requests_jitter = 50  # Add jitter to prevent all workers restarting at once

# SSL/TLS is handled by Replit's infrastructure
# We don't need to configure SSL at the Gunicorn level

# Security settings
proxy_protocol = True
proxy_allow_ips = ['127.0.0.1', '::1']
forwarded_allow_ips = '*'

# Logging
accesslog = '-'
errorlog = '-'
loglevel = 'info'
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s"'

# Process naming
proc_name = 'endcard-converter'

# Server mechanics
daemon = False
pidfile = None
umask = 0
user = None
group = None
tmp_upload_dir = None

# SSL session parameters
ssl_session_cache = None
ssl_session_timeout = None
