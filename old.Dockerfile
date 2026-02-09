# Grab the official python image
FROM python:3.12

# Set the working directory inside the container
WORKDIR /app

# Copy the requirements.txt
COPY requirements.txt requirements.txt

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the entire app directory and config files
COPY . .

# Expose port 5000
EXPOSE 5000

CMD ["sh", "-c", "alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 5000 --workers 4"]
