import redis

try:
    client = redis.StrictRedis.from_url('redis://localhost:6379')
    response = client.ping()
    print(response)
except Exception as e:
    print(f"Error: {str(e)}")
