FROM python:3.11-slim

# Install required packages
RUN pip install --no-cache-dir requests urllib3

# Set working directory
WORKDIR /app

# Copy the setup script
COPY elk_setup.py .

# Make sure the script is executable
RUN chmod +x elk_setup.py

# Run the setup script
CMD ["python", "elk_setup.py"]
