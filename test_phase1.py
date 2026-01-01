import requests
import time
import sys

# Wait for server
time.sleep(3)

url = "http://127.0.0.1:8000/analyze"

offer_text = """
Buscamos desarrollador Backend Python Senior.
Requisitos OBLIGATORIOS:
- Experiencia demostrable con FastAPI.
- Conocimientos de LangChain y LangGraph.
- Uso de Docker para contenedores.
Requisitos DESEABLES:
- Conocimientos de AWS.
"""

# CV missing Docker and AWS
cv_text = """
Soy un desarrollador Python con 5 años de experiencia.
He trabajado intensivamente con FastAPI creando APIs REST.
He implementado agentes con LangChain y recientemente he empezado a usar LangGraph para flujos complejos.
"""

payload = {
    "offer_text": offer_text,
    "cv_text": cv_text
}

try:
    print(f"Testing {url}...")
    response = requests.post(url, json=payload)
    if response.status_code == 200:
        print("Success!")
        data = response.json()
        print("Score:", data.get("score"))
        print("Discarded:", data.get("discarded"))
        print("Not Found:", data.get("not_found_requirements"))
        
        # Verify Docker is in not_found or unmatching, and discarded is True (since Docker was mandatory)
        if "Docker" in str(data.get("not_found_requirements")) or "Docker" in str(data.get("unmatching_requirements")):
            print("Verified: Docker correctly identified as missing.")
        else:
             print("Warning: Docker not found in missing requirements.")
             
        if data.get("discarded") == True:
             print("Verified: Candidate discarded correctly.")
        else:
             print("Warning: Candidate NOT discarded (check logic).")

    else:
        print("Failed with status:", response.status_code)
        print("Response:", response.text)
        sys.exit(1)
except Exception as e:
    print(f"Error: {e}")
    sys.exit(1)
