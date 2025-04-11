# Gunicorn configuration file
timeout = 120  # Increase timeout to 120 seconds
workers = 1    # Reduce number of workers to avoid memory issues
worker_class = 'sync'
threads = 2
preload_app = False  # Don't preload the app to avoid initializing TensorFlow at master process