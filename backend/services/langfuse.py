import os
from langfuse import Langfuse

public_key = os.getenv("LANGFUSE_PUBLIC_KEY")
secret_key = os.getenv("LANGFUSE_SECRET_KEY")
host = os.getenv("LANGFUSE_HOST", "https://cloud.langfuse.com")

enabled = False
if public_key and secret_key:
    enabled = True

# Initialize Langfuse without the 'enabled' parameter
# Langfuse will be disabled if keys are not provided
if enabled:
    langfuse = Langfuse(
        public_key=public_key,
        secret_key=secret_key,
        host=host
    )
else:
    # Create a dummy langfuse object when disabled
    class DummyTrace:
        def update(self, *args, **kwargs):
            pass
        def span(self, *args, **kwargs):
            return self
        def end(self, *args, **kwargs):
            pass
        def __getattr__(self, name):
            return lambda *args, **kwargs: self
    
    class DummyLangfuse:
        enabled = False
        def trace(self, *args, **kwargs):
            return DummyTrace()
        def generation(self, *args, **kwargs):
            return DummyTrace()
        def __getattr__(self, name):
            return lambda *args, **kwargs: None
    
    langfuse = DummyLangfuse()
