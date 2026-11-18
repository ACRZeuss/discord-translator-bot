FROM python:3.12-slim

# Python çıktılarını tamponlamadan doğrudan Docker loglarına yazdır
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Önce bağımlılıkları kopyala ve kur (Docker katman önbelleği için)
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Uygulama kodunu kopyala
COPY main.py .

# Güvenlik için root olmayan kullanıcı oluştur
RUN useradd -m appuser && chown -R appuser:appuser /app
USER appuser

CMD ["python", "main.py"]
