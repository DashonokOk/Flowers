from flask import Flask, request, jsonify, render_template
from PIL import Image
import torch
import torchvision.models as models
import torchvision.transforms as transforms
import pickle
import numpy as np
import os
from io import BytesIO
import base64

app = Flask(__name__)

# Функция для создания шаблонов на русском языке
def create_templates():
    templates = {
        'index.html': '''
        <!DOCTYPE html>
        <html>
        <head>
            <title>Поиск похожих растений</title>
            <style>
                body { font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; }
                h1 { color: #2e8b57; }
                .upload-box { border: 2px dashed #ccc; padding: 20px; text-align: center; margin: 20px 0; }
                .btn { background: #4CAF50; color: white; padding: 10px 15px; border: none; cursor: pointer; }
                .results { display: grid; grid-template-columns: repeat(3, 1fr); gap: 15px; margin-top: 20px; }
                .result-item { border: 1px solid #ddd; padding: 10px; text-align: center; }
                .result-item img { max-width: 100%; height: 150px; object-fit: cover; }
            </style>
        </head>
        <body>
            <h1>Поиск похожих растений</h1>
            <div class="upload-box">
                <form action="/search" method="post" enctype="multipart/form-data">
                    <input type="file" name="file" accept="image/*" required>
                    <button type="submit" class="btn">Найти похожие цветы</button>
                </form>
            </div>
        </body>
        </html>
        ''',

        'results.html': '''
        <!DOCTYPE html>
        <html>
        <head>
            <title>Результаты поиска</title>
            <style>
                body { font-family: Arial, sans-serif; max-width: 1000px; margin: 0 auto; padding: 20px; }
                .result-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 20px; }
                .result-card { border: 1px solid #ddd; padding: 15px; text-align: center; }
                .result-card img { max-width: 100%; height: 200px; object-fit: cover; }
                .similarity { color: #2e8b57; font-weight: bold; }
                .input-image { grid-column: span 3; text-align: center; margin-bottom: 30px; }
                .input-image img { max-width: 300px; border: 3px solid #2e8b57; }
            </style>
        </head>
        <body>
            <h1>Результаты поиска</h1>
            <div class="result-grid">
                <div class="input-image">
                    <h2>Ваше изображение</h2>
                    <img src="data:image/jpeg;base64,{{ input_image }}" alt="Ваш цветок">
                </div>
                {% for result in results %}
                <div class="result-card">
                    <img src="data:image/jpeg;base64,{{ result.image_base64 }}" alt="Похожий цветок">
                    <p class="similarity">Сходство: {{ "%.2f"|format(result.similarity) }}</p>
                    <p>{{ result.path }}</p>
                </div>
                {% endfor %}
            </div>
            <div style="text-align: center; margin-top: 30px;">
                <a href="/" style="background: #4CAF50; color: white; padding: 10px 20px; text-decoration: none;">Новый поиск</a>
            </div>
        </body>
        </html>
        ''',

        'error.html': '''
        <!DOCTYPE html>
        <html>
        <head>
            <title>Ошибка</title>
            <style>
                body { font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; }
                .error-box { background: #ffebee; border: 1px solid #f44336; padding: 20px; margin: 20px 0; }
            </style>
        </head>
        <body>
            <h1>Ошибка</h1>
            <div class="error-box">
                <p>{{ error }}</p>
            </div>
            <a href="/" style="background: #4CAF50; color: white; padding: 10px 20px; text-decoration: none;">Назад к поиску</a>
        </body>
        </html>
        '''
    }

    os.makedirs('templates', exist_ok=True)
    for name, content in templates.items():
        path = os.path.join('templates', name)
        with open(path, 'w', encoding='utf-8') as f:
            f.write(content)

# Создаем шаблоны при запуске
create_templates()

# Загрузка модели и данных
model = models.resnet50(pretrained=True)
model = torch.nn.Sequential(*list(model.children())[:-1])
model.eval()

with open('models/nbrs.pkl', 'rb') as f:
    nbrs = pickle.load(f)
with open('models/image_paths.pkl', 'rb') as f:
    image_paths = pickle.load(f)

transform = transforms.Compose([
    transforms.Resize((224, 224)),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
])

def image_to_base64(img):
    buffered = BytesIO()
    img.save(buffered, format="JPEG")
    return base64.b64encode(buffered.getvalue()).decode('utf-8')

@app.route('/')
def home():
    """Главная страница с формой загрузки"""
    return render_template('index.html')

@app.route('/search', methods=['POST'])
def search():
    """Обработка поиска похожих цветов через веб-интерфейс"""
    if 'file' not in request.files:
        return render_template('error.html', error="Файл не загружен")

    file = request.files['file']
    if not file or file.filename == '':
        return render_template('error.html', error="Файл не выбран")

    try:
        img = Image.open(file.stream).convert('RGB')
        img_t = transform(img).unsqueeze(0)

        with torch.no_grad():
            features = model(img_t).squeeze().numpy()

        distances, indices = nbrs.kneighbors([features], n_neighbors=5)

        results = []
        for i, idx in enumerate(indices[0]):
            similarity = float(1 - distances[0][i])
            result_img = Image.open(image_paths[idx])
            results.append({
                "path": image_paths[idx],
                "similarity": similarity,
                "image_base64": image_to_base64(result_img)
            })

        results.sort(key=lambda x: x['similarity'], reverse=True)

        input_img_base64 = image_to_base64(img.resize((300, 300)))

        return render_template('results.html',
                               input_image=input_img_base64,
                               results=results)

    except Exception as e:
        return render_template('error.html', error=str(e))

@app.route('/api/search', methods=['POST'])
def api_search():
    """API для поиска по изображению, возвращает JSON"""
    if 'file' not in request.files:
        return jsonify({"error": "Файл не загружен"}), 400

    file = request.files['file']
    if not file or file.filename == '':
        return jsonify({"error": "Файл не выбран"}), 400

    try:
        img = Image.open(file.stream).convert('RGB')
        img_t = transform(img).unsqueeze(0)

        with torch.no_grad():
            features = model(img_t).squeeze().numpy()

        distances, indices = nbrs.kneighbors([features], n_neighbors=5)

        results = []
        for i, idx in enumerate(indices[0]):
            similarity = float(1 - distances[0][i])
            results.append({
                "path": image_paths[idx],
                "similarity": similarity,
            })

        results.sort(key=lambda x: x['similarity'], reverse=True)

        return jsonify({"results": results})

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)