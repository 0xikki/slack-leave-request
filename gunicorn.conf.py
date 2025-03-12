import multiprocessing

# Gunicorn configuration for production
bind = "127.0.0.1:8000"
workers = multiprocessing.cpu_count() * 2 + 1
worker_class = "sync"
worker_connections = 1000
timeout = 30
keepalive = 2

# Access log - records incoming HTTP requests
accesslog = "/var/log/slack-leave-system/access.log"
# Error log - records Gunicorn server goings-on
errorlog = "/var/log/slack-leave-system/error.log"
# Whether to send Django output to the error log 
capture_output = True
# How verbose the Gunicorn error logs should be 
loglevel = "info"

# SSL Configuration (if needed)
# keyfile = "/etc/ssl/private/server.key"
# certfile = "/etc/ssl/certs/server.crt"

# Security configurations
limit_request_line = 4094
limit_request_fields = 100
limit_request_field_size = 8190 