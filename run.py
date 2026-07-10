import uvicorn
import threading
import sys
import os

def start_ngrok(port):
    try:
        from pyngrok import ngrok
        token = os.environ.get("NGROK_AUTH_TOKEN", "")
        if token:
            ngrok.set_auth_token(token)
        tunnel = ngrok.connect(port, "http")
        print("\n" + "="*50)
        print(f"🌐 PUBLIC URL: {tunnel.public_url}")
        print(f"📋 SHARE THIS: {tunnel.public_url}")
        print(f"📄 API DOCS:   {tunnel.public_url}/docs")
        print("="*50 + "\n")
    except Exception as e:
        print(f"Ngrok failed: {e}")
        print("Run manually: ngrok http 8000")

if __name__ == "__main__":
    port = 8000
    if "--ngrok" in sys.argv:
        threading.Thread(target=start_ngrok, args=(port,), daemon=True).start()
    
    print(f"\nStarting at http://localhost:{port}\n")
    uvicorn.run("app.main:app", host="0.0.0.0", port=port, reload=False)