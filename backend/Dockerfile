# Use an official, lightweight Python layer
FROM python:3.11-slim

# Set working directory inside the container
WORKDIR /workspace

# Copy dependencies first to maximize build caching
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application source code into the workspace
COPY ./app ./app

# Expose the internal port that Uvicorn runs on
EXPOSE 8000

# Specify the launch command, navigating into the app execution path
CMD ["python", "app/main.py"]