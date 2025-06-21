# Use the uv base image with Python 3.12 on Debian
FROM ghcr.io/astral-sh/uv:debian

# Set the working directory
WORKDIR /app/repo

# Copy only the requirements first to leverage Docker cache
COPY requirements.txt /app/repo

# Copy the rest of your application code into /app
COPY . /app/repo/

# Create a virtual environment using uv
RUN uv venv

# Activate the venv and install dependencies from PyPI
RUN . .venv/bin/activate && \
    apt-get update && \
    apt-get install -y git cmake build-essential libpq-dev python3-dev && \
    uv pip install --upgrade pip && \
    uv pip install -r requirements.txt -U

# (Optional) Verify uvicorn installation by displaying its version
RUN . .venv/bin/activate && uvicorn --version

# Expose port 80 for the application
EXPOSE 80

# Copy the entrypoint script and ensure it is executable
COPY entrypoint.sh /usr/local/bin/
RUN chmod +x /usr/local/bin/entrypoint.sh

# Set the entrypoint script to be executed on container start
ENTRYPOINT ["entrypoint.sh"]

# Run Uvicorn when the container launches, making sure to activate the virtual environment
#CMD ["/bin/sh", "-c", "source .venv/bin/activate && uvicorn main:app --host 0.0.0.0 --port 80 --reload --proxy-headers --log-level trace"]
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "80", "--reload", "--proxy-headers", "--log-level", "trace"]
