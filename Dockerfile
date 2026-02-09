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

# Make entrypoint executable
RUN chmod +x entrypoint.sh

# Expose port 5000
EXPOSE 5000

CMD ["./entrypoint.sh"]
