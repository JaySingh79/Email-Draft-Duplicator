# Use official Python image
FROM python:3.12-slim

# Set working directory inside the container
WORKDIR /app

# Copy backend code into the container
COPY backend_server ./backend_server/

# Install dependencies
RUN pip install --no-cache-dir -r backend_server/requirements.txt

# Expose the Flask port
EXPOSE 5000

# Set environment variables for Flask
ENV FLASK_APP=backend_server/duplicator.py
ENV FLASK_RUN_HOST=0.0.0.0

# Run Flask app
CMD ["flask", "run"]
