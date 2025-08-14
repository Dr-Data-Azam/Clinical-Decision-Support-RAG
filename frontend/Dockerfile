# Use an official Python base image
FROM python:3.11-slim

# Set the working directory
WORKDIR /app

# Copy requirements and install them
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the frontend code
COPY frontend/ .
# Expose the port Streamlit runs on (default is 8501)
EXPOSE 8501

# The command to run the Streamlit app
CMD ["streamlit", "run", "frontend.py"]