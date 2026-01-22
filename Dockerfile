# 1️⃣ Use official Python image
FROM python:3.11-slim

# 2️⃣ Set working directory inside container
WORKDIR /app

# 3️⃣ Copy requirements first (better caching)
COPY requirements.txt .

# 4️⃣ Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# 5️⃣ Copy project files
COPY . .

# 6️⃣ Expose Flask port
EXPOSE 5000

# 7️⃣ Run the Flask app
CMD ["python", "app.py"]
