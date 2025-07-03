# Flowers

Чтобы воспользоваться интерфейсом необходимо открыть браузер и перейти по ссылке:

👉 http://localhost:5000

Загрузить изображение цветка и получить самые похожие изображения.

## Как запустить проект?
#### 1. Клонируй репозиторий:

git clone https://github.com/yourusername/flower-search.git 

cd flower-search

#### 2. Установи Docker

sudo apt update && sudo apt install docker.io

#### 3. Собери и запусти контейнер:

docker build -t flower-search .

docker run -p 5000:5000 -v $(pwd)/models:/app/models flower-search


## Через API:

curl -X POST http://localhost:5000/api/search \

-F "file=@test_images/sunflower.jpg"

#### Пример ответа:
{
  "results": [
    {"path": "flowers/daisy/123.jpg", "similarity": 0.97},
    {"path": "flowers/daisy/456.jpg", "similarity": 0.95}
  ]
}


## Репозиторий содержит:
Все исходники, документацию, отчет, Dockerfile, Jupyter Notebook с обучением модели, веса модели и данные.

![Пример поиска](Flowers/Image/skrin.png)

