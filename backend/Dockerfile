# Use an official, slim Python base image. 'slim' is smaller than the default.
FROM python:3.11-slim

# Set the working directory inside the container. All subsequent commands run here.
WORKDIR /app

# Copy the requirements file first. This is a Docker caching optimization.
# It won't re-install packages unless this file changes.
COPY requirements.txt .

# Install the Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the backend code and the data folder
COPY backend/ .
COPY data/ ./data

# Tell Docker that your application listens on port 8000
EXPOSE 8000

# The command to run your application.
# We use --host 0.0.0.0 to make it accessible from outside the container.
# Using 127.0.0.1 would NOT work.
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]