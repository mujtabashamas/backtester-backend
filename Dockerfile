FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set the working directory in the container
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    libpq-dev gcc

# Install pipenv and compile dependencies
RUN pip install --upgrade pip
RUN pip install pipenv

# Copy the Pipfile and Pipfile.lock to the container
COPY Pipfile Pipfile.lock /app/

# Install Python dependencies using pipenv
RUN pipenv install --deploy --ignore-pipfile

# Copy the current directory contents into the container at /app
COPY . /app/

# Expose port 8000 for Django
EXPOSE 8000

# Run migrations and start the Django development server
CMD ["sh", "-c", "pipenv run python manage.py migrate && pipenv run python manage.py runserver 0.0.0.0:8000"]
