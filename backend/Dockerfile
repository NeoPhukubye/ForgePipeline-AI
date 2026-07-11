# Use an official, lightweight Python runtime as a parent image
FROM python:3.11-slim

# Set the working directory inside the container
WORKDIR /app

# Copy only the backend requirements and install dependencies
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the backend application code
COPY backend/app /app/app

# Make port 8080 available to the world outside this container
EXPOSE 8080

# Run the FastAPI application using uvicorn
# The command should be 'uvicorn app.main:app --host 0.0.0.0 --port 8080'
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]
