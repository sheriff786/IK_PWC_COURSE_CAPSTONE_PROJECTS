from fastapi import FastAPI

app = FastAPI(title='ContractIQ API')

@app.get('/')
def root():
    return {'service': 'ContractIQ API', 'status': 'ok', 'health': '/health'}

@app.get('/health')
def health():
    return {'status': 'ok'}
