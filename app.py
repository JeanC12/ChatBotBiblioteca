from flask import Flask, render_template, request, jsonify
import os
import google.generativeai as genai
from dotenv import load_dotenv
import requests  # Para realizar la solicitud a la API
import socket
from flask_cors import CORS

# DOTENV
load_dotenv()
API_KEY = os.getenv("GEMINI_API_KEY")


# Lee el archivo que contiene las instrucciones
def read_instruction_from_file(file_path):
    with open(file_path, "r", encoding="utf-8") as file:
        return file.read()


# Obtiene el catálogo de libros desde la API
def fetch_catalog(api_url):
    try:
        response = requests.get(api_url)
        response.raise_for_status()  # Lanza un error si la respuesta no es 200
        books = response.json()
        # Formatea el catálogo en una cadena legible
        catalog_string = "\n".join(
            [
                f"{book['title']} por {book['author']} (Stock: {book['stock']})"
                for book in books
            ]
        )
        return catalog_string
    except Exception as e:
        print(f"Error al obtener el catálogo: {e}")
        return "No se pudo obtener el catálogo en este momento."


# Servidor Flask
app = Flask(__name__)
CORS(app)

# Configuración inicial
genai.configure(api_key=API_KEY)
api_url = "https://book-service-6t5i.onrender.com/api/books"
catalog = fetch_catalog(api_url)
instruction_base = read_instruction_from_file("knowledge.txt")
instruction = (
    f"{instruction_base}\nPor si acaso, el catálogo es el siguiente, por si preguntan:\n"
    f"{catalog}\nA continuación la pregunta:\n"
)
model = genai.GenerativeModel("gemini-pro")
chat = model.start_chat(history=[])


# Routes
@app.route("/")
def index():
    return render_template("index.html")


@app.route("/pregunta", methods=["POST"])
def pregunta():
    try:
        data = request.get_json()
        if "user" in data:
            user_input = data["user"]
            print(f"User: {user_input}")
            response = chat.send_message(instruction + user_input)
            print(f"Bot: {response.text}")
            return jsonify({"response": response.text})
        else:
            return (
                jsonify({"response": "No se proporcionó 'user_input' en el JSON."}),
                400,
            )
    except Exception as e:
        print(f"Error en /pregunta: {e}")
        return jsonify({"response": "Hubo un error al procesar la pregunta."}), 500


@app.route("/ask", methods=["POST"])
def ask():
    try:
        user_input = request.form["user_input"]
        print(f"User: {user_input}")
        response = chat.send_message(instruction + user_input)
        print(f"Bot: {response.text}")
        return jsonify({"response": response.text})
    except Exception as e:
        print(f"Bot: {e}")
        return jsonify(
            {"response": "¿Podrías volver a formular tu pregunta?, no entendí bien."}
        )


# Main
if __name__ == "__main__":
    ip_address = socket.gethostbyname(socket.gethostname())
    _port = os.getenv("PORT", "5001")
    _host = os.getenv("HOST", "0.0.0.0")
    print(f"Servidor Flask corriendo en http://{ip_address}:{_port}")
    app.run(debug=False, host=_host, port=_port)
