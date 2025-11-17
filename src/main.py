import requests
from PIL import Image, ImageDraw, ImageFont
import os
import random
import datetime

try:
    MISTRAL_API_KEY = os.getenv("MISTRAL_API_KEY","")
    MODEL = os.getenv("MODEL", "mistral-small-latest")
    TOPICS = os.getenv("TOPICS", "History, Computers, Science, Technology, Art, Music, Literature, Sports, Nature, Food, Duck").split(",")
    for i in range(len(TOPICS)):
        TOPICS[i] = TOPICS[i].strip()
    TEMPERATURE = float(os.getenv("TEMPERATURE", 0.7))
    MAX_TOKENS = int(os.getenv("MAX_TOKENS", 1000))
    OUTPUT_PATH = os.getenv("OUTPUT_PATH", "output_image.png")
    # check if the output path have a .png extension
    if not OUTPUT_PATH.endswith(".png"):
        print("Error: OUTPUT_PATH must have a .png extension")
        exit(1)
    # check if the output path have parent directory
    DIRS = os.path.dirname(OUTPUT_PATH)
    if DIRS and not os.path.exists(DIRS):
        os.makedirs(DIRS)
        
    LANGUAGE = os.getenv("LANGUAGE", "en")
except:
    print("Error: Environment variables not set. Please set MISTRAL_API_KEY, MODEL, TOPICS, TEMPERATURE, and MAX_TOKENS.")
    exit(1)

# Dictionary of prompts in different languages
PROMPT_TEMPLATES = {
    "en": "Tell me an anecdote about {topic} in 3 REAL sentences that occurred on {date}.",
    "fr": "Raconte-moi une anecdote sur {topic} en 3 phrases REELLES et qui a comme date (hors année) {date}.",
    "es": "Cuéntame una anécdota sobre {topic} en 3 frases REALES que ocurrió el {date}.",
    "de": "Erzähle mir eine Anekdote über {topic} in 3 REALEN Sätzen, die am {date} stattfand.",
    "other": "Tell me an anecdote about {topic} that happened on {date}, written in exactly 3 real sentences. The response must be written in the language corresponding to this ISO code: {language}.",
}

def create_image_with_text(text, output_path, max_width=800, padding=20):
    # Charge une police
    try:
        font = ImageFont.truetype("arial.ttf", 36)
    except IOError:
        font = ImageFont.load_default()

    # Prépare un dessin temporaire pour mesurer le texte
    temp_image = Image.new('RGB', (max_width, 1))
    draw = ImageDraw.Draw(temp_image)

    # Découpe le texte en lignes pour respecter la largeur max
    words = text.split()
    lines = []
    current_line = ""

    for word in words:
        test_line = current_line + ' ' + word if current_line else word
        bbox = draw.textbbox((0, 0), test_line, font=font)
        line_width = bbox[2] - bbox[0]
        if line_width <= (max_width - 2 * padding):
            current_line = test_line
        else:
            lines.append(current_line)
            current_line = word
    if current_line:
        lines.append(current_line)

    # Calcule la hauteur totale nécessaire
    line_height = draw.textbbox((0, 0), "Ay", font=font)[3]
    total_text_height = line_height * len(lines) + 2 * padding

    # Crée une image avec la bonne hauteur
    image = Image.new('RGB', (max_width, total_text_height), 'black')
    draw = ImageDraw.Draw(image)

    # Position de départ verticale
    y = padding

    # Dessine chaque ligne centrée horizontalement
    for line in lines:
        bbox = draw.textbbox((0, 0), line, font=font)
        text_width = bbox[2] - bbox[0]
        x = (max_width - text_width) // 2
        draw.text((x, y), line, font=font, fill='white')
        y += line_height

    # Sauvegarde
    image.save(output_path)
    print(f"Image saved to {output_path}")



def submit_prompt_to_mistral_api(prompt):
    headers = {
        "Authorization": f"Bearer {MISTRAL_API_KEY}",
        "Content-Type": "application/json"
    }

    # use temperature and max_tokens from environment variables
    data = {
        "model": MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": TEMPERATURE,
        "max_tokens": MAX_TOKENS
    }

    # Appel à Mistral
    res = requests.post("https://api.mistral.ai/v1/chat/completions", headers=headers, json=data)
    # check if the request was successful
    if res.status_code != 200:
        print(f"Error: {res.status_code} - {res.text}")
        return None
    message = res.json()["choices"][0]["message"]["content"]
    return message


if __name__ == "__main__":

    random_topic = random.choice(TOPICS)
    today = datetime.datetime.now()
    formatted_date = today.strftime("%d %B")
    
    # Get prompt template for the selected language, fallback to English if not found
    prompt_template = PROMPT_TEMPLATES.get(LANGUAGE.lower(), PROMPT_TEMPLATES["other"])
    prompt = prompt_template.format(topic=random_topic, date=formatted_date, language=LANGUAGE)
    
    response = submit_prompt_to_mistral_api(prompt)

    # Create an image with the text
    create_image_with_text(response, OUTPUT_PATH)
