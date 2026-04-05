from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
import uvicorn
import requests
import uuid
import json
import os

app = FastAPI(title="БИС Platform")

# ========== ТВОЙ КЛЮЧ GIGACHAT ==========
GIGACHAT_AUTH_KEY = "MDE5ZDMzYzItNGY5NS03MGY4LThjOTktYzk5ZDIyMzYyZTk3OmI5OWRhMTVjLTNmMGQtNDFlOS04Yjc3LTdhMWQ2YzU5NzBiNg=="
gigachat_access_token = None

# Файл для хранения данных пользователя
USER_DATA_FILE = "user_data.json"


def load_user_data():
    if os.path.exists(USER_DATA_FILE):
        try:
            with open(USER_DATA_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return {}
    return {}


def save_user_data(data):
    with open(USER_DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


user_data = load_user_data()


def get_gigachat_token():
    global gigachat_access_token
    url = "https://ngw.devices.sberbank.ru:9443/api/v2/oauth"
    headers = {
        "Authorization": f"Basic {GIGACHAT_AUTH_KEY}",
        "RqUID": str(uuid.uuid4()),
        "Content-Type": "application/x-www-form-urlencoded"
    }
    data = {"scope": "GIGACHAT_API_PERS"}
    try:
        response = requests.post(url, headers=headers, data=data, verify=False, timeout=30)
        if response.status_code == 200:
            gigachat_access_token = response.json().get('access_token')
            return gigachat_access_token
        return None
    except:
        return None


def call_gigachat(prompt):
    global gigachat_access_token
    if not gigachat_access_token:
        if not get_gigachat_token():
            return "❌ Ошибка подключения к ИИ"
    url = "https://gigachat.devices.sberbank.ru/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {gigachat_access_token}",
        "Content-Type": "application/json"
    }
    system_prompt = f"""Ты — AI-ассистент БИС. Ты помогаешь создавать контент для соцсетей. Отвечай кратко, дружелюбно, используй эмодзи. Если просят пост — сразу давай текст с хештегами. Пиши от первого лица.
Запрос: {prompt}
Ответ:"""
    payload = {
        "model": "GigaChat",
        "messages": [{"role": "user", "content": system_prompt}],
        "temperature": 0.7,
        "max_tokens": 1500
    }
    try:
        response = requests.post(url, headers=headers, json=payload, verify=False, timeout=60)
        if response.status_code == 200:
            return response.json()['choices'][0]['message']['content']
        elif response.status_code == 401:
            gigachat_access_token = None
            return call_gigachat(prompt)
        return f"❌ Ошибка: {response.status_code}"
    except Exception as e:
        return f"❌ Ошибка: {str(e)}"


# ========== ЕДИНЫЙ СТИЛЬ ==========
COMMON_STYLES = """
<style>
    * { margin: 0; padding: 0; box-sizing: border-box; }
    body {
        font-family: 'Inter', 'Montserrat', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
        background: radial-gradient(ellipse at center, #0a0a0a 0%, #000000 100%);
        color: #ffffff;
        min-height: 100vh;
        overflow-x: hidden;
    }
    .stars {
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        pointer-events: none;
        z-index: 0;
    }
    .star {
        position: absolute;
        background-color: #ffffff;
        border-radius: 50%;
        opacity: 0;
        animation: twinkle 3s infinite ease-in-out;
    }
    @keyframes twinkle {
        0%, 100% { opacity: 0; transform: scale(1); }
        50% { opacity: 0.8; transform: scale(1.2); }
    }
    .content {
        position: relative;
        z-index: 10;
        min-height: 100vh;
        display: flex;
        flex-direction: column;
    }
    .header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 20px 48px;
        background: rgba(0,0,0,0.7);
        backdrop-filter: blur(10px);
        border-bottom: 1px solid rgba(255,102,0,0.3);
        position: sticky;
        top: 0;
        z-index: 100;
    }
    .logo {
        display: flex;
        align-items: center;
        gap: 12px;
    }
    .logo-icon {
        width: 36px;
        height: 36px;
        background: linear-gradient(135deg, #ff6600, #ffaa00);
        border-radius: 50%;
        box-shadow: 0 0 15px #ff6600;
    }
    .logo-text {
        font-size: 20px;
        font-weight: 700;
        letter-spacing: 2px;
        background: linear-gradient(135deg, #ff6600, #ffaa00);
        -webkit-background-clip: text;
        background-clip: text;
        color: transparent;
    }
    .nav-menu {
        display: flex;
        gap: 32px;
    }
    .nav-menu a {
        color: #ffffff;
        text-decoration: none;
        font-size: 14px;
        opacity: 0.8;
        transition: all 0.3s;
    }
    .nav-menu a:hover {
        opacity: 1;
        color: #ff6600;
    }
    .nav-right {
        display: flex;
        gap: 24px;
        align-items: center;
    }
    .lang-switch {
        display: flex;
        gap: 6px;
        background: rgba(26,26,26,0.8);
        padding: 4px 8px;
        border-radius: 20px;
    }
    .lang-switch span {
        cursor: pointer;
        font-size: 12px;
        color: #888;
    }
    .lang-switch span.active {
        color: #ff6600;
    }
    .main-container {
        flex: 1;
        padding: 40px 48px;
    }
    .planet-decoration {
        position: fixed;
        bottom: 20px;
        right: 20px;
        width: 150px;
        height: 150px;
        background: radial-gradient(circle, rgba(255,102,0,0.1) 0%, rgba(0,0,0,0) 70%);
        border-radius: 50%;
        pointer-events: none;
        z-index: 1;
    }
    h1 {
        font-size: 32px;
        font-weight: 700;
        margin-bottom: 30px;
        background: linear-gradient(135deg, #ffffff, #ffaa00);
        -webkit-background-clip: text;
        background-clip: text;
        color: transparent;
    }
    h2 {
        font-size: 22px;
        font-weight: 600;
        margin-bottom: 20px;
        color: #ffaa00;
    }
    .card {
        background: rgba(20,20,30,0.7);
        backdrop-filter: blur(10px);
        border-radius: 20px;
        padding: 24px;
        margin-bottom: 24px;
        border: 1px solid rgba(255,102,0,0.2);
    }
    .btn-primary {
        background: linear-gradient(135deg, #ff6600, #ffaa00);
        color: #000;
        padding: 12px 28px;
        border-radius: 30px;
        font-size: 14px;
        font-weight: 600;
        border: none;
        cursor: pointer;
        transition: all 0.3s;
    }
    .btn-primary:hover {
        transform: scale(1.02);
        box-shadow: 0 0 20px rgba(255,102,0,0.5);
    }
    .btn-secondary {
        background: transparent;
        border: 1px solid #ff6600;
        color: #ff6600;
        padding: 10px 24px;
        border-radius: 30px;
        cursor: pointer;
        transition: all 0.3s;
    }
    .footer {
        text-align: center;
        padding: 30px;
        border-top: 1px solid #222;
        font-size: 12px;
        color: #666;
    }
    /* Тарифы */
    .pricing-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
        gap: 30px;
        margin-top: 30px;
    }
    .pricing-card {
        background: rgba(20,20,30,0.8);
        backdrop-filter: blur(10px);
        border-radius: 24px;
        padding: 32px;
        text-align: center;
        border: 1px solid rgba(255,102,0,0.3);
        transition: all 0.3s;
    }
    .pricing-card:hover {
        transform: translateY(-5px);
        border-color: #ff6600;
        box-shadow: 0 0 30px rgba(255,102,0,0.2);
    }
    .pricing-card h3 { font-size: 24px; margin-bottom: 10px; }
    .price { font-size: 42px; font-weight: 800; color: #ffaa00; margin: 20px 0; }
    .price span { font-size: 16px; font-weight: 400; color: #888; }
    .features-list { list-style: none; margin: 20px 0; }
    .features-list li { padding: 8px 0; border-bottom: 1px solid rgba(255,255,255,0.1); font-size: 14px; }
    .features-list li::before { content: "✨"; margin-right: 8px; }
    /* Рабочая зона */
    .workspace-layout { display: flex; gap: 30px; }
    .left-panel, .right-panel {
        background: rgba(20,20,30,0.7);
        backdrop-filter: blur(10px);
        border-radius: 20px;
        padding: 24px;
        border: 1px solid rgba(255,102,0,0.2);
    }
    .left-panel { flex: 1; }
    .right-panel { flex: 1.5; }
    .format-buttons { display: flex; gap: 15px; margin: 20px 0; }
    .format-btn {
        background: rgba(50,50,60,0.5);
        border: 1px solid #444;
        border-radius: 30px;
        padding: 10px 24px;
        cursor: pointer;
        color: #ffffff;
    }
    .format-btn.active { background: #ff6600; border-color: #ff6600; color: #000; }
    .result-area {
        background: rgba(0,0,0,0.5);
        border-radius: 16px;
        padding: 20px;
        margin-top: 20px;
        border: 1px solid #333;
        min-height: 300px;
    }
    .checkbox-group { display: flex; gap: 20px; margin: 15px 0; flex-wrap: wrap; }
    .checkbox-group label { display: flex; align-items: center; gap: 8px; color: #ddd; }
    textarea {
        width: 100%;
        background: rgba(30,30,40,0.8);
        border: 1px solid #333;
        border-radius: 12px;
        padding: 12px;
        color: white;
        margin: 15px 0;
    }
    .workspace-nav {
        display: flex;
        gap: 20px;
        margin-bottom: 25px;
        border-bottom: 1px solid #333;
        padding-bottom: 15px;
        flex-wrap: wrap;
    }
    .workspace-nav a {
        color: #aaa;
        text-decoration: none;
        padding: 8px 16px;
        border-radius: 20px;
        transition: all 0.3s;
        cursor: pointer;
    }
    .workspace-nav a:hover, .workspace-nav a.active {
        background: rgba(255,102,0,0.2);
        color: #ff6600;
    }
    .contact-info { text-align: center; margin-top: 20px; }
    .contact-item {
        display: inline-block;
        margin: 10px 20px;
        padding: 10px 20px;
        background: rgba(255,102,0,0.1);
        border-radius: 30px;
        border: 1px solid rgba(255,102,0,0.3);
    }
    .contact-item a { color: #ffaa00; text-decoration: none; }
    /* Форма профиля бренда */
    .form-group { margin-bottom: 15px; }
    .form-group label { display: block; margin-bottom: 5px; color: #ffaa00; font-size: 14px; }
    .form-group input, .form-group select {
        width: 100%;
        padding: 10px;
        background: rgba(30,30,40,0.8);
        border: 1px solid #333;
        border-radius: 8px;
        color: white;
    }
</style>
"""

# ========== ГЛАВНАЯ СТРАНИЦА ==========
LANDING_PAGE = """
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, user-scalable=no">
    <title>БИС — Космический AI</title>
    """ + COMMON_STYLES + """
    <style>
        .hero {
            flex: 1;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            padding: 20px 20px 80px;
            position: relative;
            min-height: 70vh;
        }
        #canvas-container {
            position: absolute;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            z-index: 1;
            pointer-events: none;
        }
        .hero-content {
            position: relative;
            z-index: 2;
            text-align: center;
        }
        .title h1 {
            font-size: 48px;
            font-weight: 800;
            text-transform: uppercase;
            letter-spacing: 2px;
            line-height: 1.3;
            margin-bottom: 24px;
        }
        .title h1 span { color: #ff6600; }
        .title p {
            font-size: 18px;
            opacity: 0.7;
            max-width: 700px;
            margin: 0 auto 30px;
        }
    </style>
</head>
<body>
<div class="stars" id="stars"></div>
<div id="canvas-container"></div>

<div class="content">
    <header class="header">
        <div class="logo">
            <div class="logo-icon"></div>
            <span class="logo-text">БИС</span>
        </div>
        <nav class="nav-menu">
            <a href="/">Главная</a>
            <a href="/workspace">Рабочая зона</a>
            <a href="/feedback">Обратная связь</a>
            <a href="/tariffs">Тарифы</a>
        </nav>
        <div class="nav-right">
            <div class="lang-switch">
                <span class="active">Lvo</span>
                <span>Ru</span>
            </div>
        </div>
    </header>

    <div class="hero">
        <div class="hero-content">
            <div class="title">
                <h1>БИС — <span>БРЕНД. ИМИДЖ. СТРАТЕГИЯ.</span><br>ВСЕ НЕОБХОДИМЫЕ НЕЙРОСЕТИ<br>В ОДНОМ МЕСТЕ!</h1>
                <p>Искусственный интеллект нового поколения для работы с текстом, изображениями и данными</p>
                <a href="/workspace" class="btn-primary">Начать работу!</a>
            </div>
        </div>
    </div>

    <div class="footer">
        <p>© 2026 БИС — Бренд. Имидж. Стратегия.</p>
    </div>
</div>

<script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>
<script>
    function createStars() {
        const starsContainer = document.getElementById('stars');
        for (let i = 0; i < 300; i++) {
            const star = document.createElement('div');
            star.classList.add('star');
            const size = Math.random() * 3 + 1;
            star.style.width = size + 'px';
            star.style.height = size + 'px';
            star.style.left = Math.random() * 100 + '%';
            star.style.top = Math.random() * 100 + '%';
            star.style.animationDelay = Math.random() * 5 + 's';
            star.style.animationDuration = (Math.random() * 3 + 2) + 's';
            starsContainer.appendChild(star);
        }
    }
    createStars();

    const container = document.getElementById('canvas-container');
    const scene = new THREE.Scene();
    const camera = new THREE.PerspectiveCamera(45, window.innerWidth / window.innerHeight, 0.1, 1000);
    camera.position.z = 5;
    const renderer = new THREE.WebGLRenderer({ alpha: true });
    renderer.setSize(window.innerWidth, window.innerHeight);
    renderer.setClearColor(0x000000, 0);
    container.appendChild(renderer.domElement);

    const textureLoader = new THREE.TextureLoader();
    const earthTexture = textureLoader.load('https://threejs.org/examples/textures/planets/earth_atmos_2048.jpg');
    const geometry = new THREE.SphereGeometry(1.5, 128, 128);
    const material = new THREE.MeshStandardMaterial({ map: earthTexture, roughness: 0.5, metalness: 0.1 });
    const earth = new THREE.Mesh(geometry, material);
    scene.add(earth);

    const ambientLight = new THREE.AmbientLight(0x404060);
    scene.add(ambientLight);
    const directionalLight = new THREE.DirectionalLight(0xffffff, 1);
    directionalLight.position.set(5, 5, 5);
    scene.add(directionalLight);

    let mouseX = 0, mouseY = 0;
    document.addEventListener('mousemove', (event) => {
        mouseX = (event.clientX / window.innerWidth) * 2 - 1;
        mouseY = (event.clientY / window.innerHeight) * 2 - 1;
    });

    function animate() {
        requestAnimationFrame(animate);
        earth.rotation.y += 0.003;
        earth.rotation.x = mouseY * 0.2;
        earth.rotation.y += mouseX * 0.2;
        renderer.render(scene, camera);
    }
    animate();

    window.addEventListener('resize', () => {
        camera.aspect = window.innerWidth / window.innerHeight;
        camera.updateProjectionMatrix();
        renderer.setSize(window.innerWidth, window.innerHeight);
    });
</script>
</body>
</html>
"""

# ========== ТАРИФЫ ==========
TARIFFS_PAGE = """
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>БИС — Тарифы</title>
    """ + COMMON_STYLES + """
</head>
<body>
<div class="stars" id="stars"></div>
<div class="planet-decoration"></div>

<div class="content">
    <header class="header">
        <div class="logo">
            <div class="logo-icon"></div>
            <span class="logo-text">БИС</span>
        </div>
        <nav class="nav-menu">
            <a href="/">Главная</a>
            <a href="/workspace">Рабочая зона</a>
            <a href="/feedback">Обратная связь</a>
            <a href="/tariffs">Тарифы</a>
        </nav>
        <div class="nav-right">
            <div class="lang-switch">
                <span class="active">Lvo</span>
                <span>Ru</span>
            </div>
        </div>
    </header>

    <div class="main-container">
        <h1>💎 Выберите свой тариф</h1>
        <p style="margin-bottom: 30px; opacity: 0.8;">Подберите оптимальный план для вашего бизнеса</p>

        <div class="pricing-grid">
            <div class="pricing-card">
                <h3>🌟 Базовый</h3>
                <div class="price">1 190 ₽<span>/мес</span></div>
                <ul class="features-list">
                    <li>📝 2 поста в день</li>
                    <li>🎬 Отсутствие генерации видео и изображений</li>
                    <li>💬 Ответы на комментарии — 20 шт/мес</li>
                </ul>
                <button class="btn-primary" onclick="alert('Выбор тарифа Базовый')">Выбрать</button>
            </div>
            <div class="pricing-card">
                <h3>🚀 Pro</h3>
                <div class="price">4 990 ₽<span>/мес</span></div>
                <ul class="features-list">
                    <li>📝 4 поста в день</li>
                    <li>🎬 Генерация видео и изображений</li>
                    <li>💬 Ответы на комментарии — 35 шт/мес</li>
                </ul>
                <button class="btn-primary" onclick="alert('Выбор тарифа Pro')">Выбрать</button>
            </div>
            <div class="pricing-card">
                <h3>👑 Premium</h3>
                <div class="price">9 990 ₽<span>/мес</span></div>
                <ul class="features-list">
                    <li>📝 Безлимитное количество постов</li>
                    <li>🎬 Генерация видео и изображений</li>
                    <li>💬 Ответы на комментарии — 100 шт/мес</li>
                </ul>
                <button class="btn-primary" onclick="alert('Выбор тарифа Premium')">Выбрать</button>
            </div>
        </div>
    </div>

    <div class="footer">
        <p>© 2026 БИС — Бренд. Имидж. Стратегия.</p>
    </div>
</div>

<script>
    function createStars() {
        const starsContainer = document.getElementById('stars');
        for (let i = 0; i < 200; i++) {
            const star = document.createElement('div');
            star.classList.add('star');
            const size = Math.random() * 2 + 1;
            star.style.width = size + 'px';
            star.style.height = size + 'px';
            star.style.left = Math.random() * 100 + '%';
            star.style.top = Math.random() * 100 + '%';
            star.style.animationDelay = Math.random() * 5 + 's';
            star.style.animationDuration = (Math.random() * 3 + 2) + 's';
            starsContainer.appendChild(star);
        }
    }
    createStars();
</script>
</body>
</html>
"""

# ========== ОБРАТНАЯ СВЯЗЬ ==========
FEEDBACK_PAGE = """
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>БИС — Обратная связь</title>
    """ + COMMON_STYLES + """
</head>
<body>
<div class="stars" id="stars"></div>
<div class="planet-decoration"></div>

<div class="content">
    <header class="header">
        <div class="logo">
            <div class="logo-icon"></div>
            <span class="logo-text">БИС</span>
        </div>
        <nav class="nav-menu">
            <a href="/">Главная</a>
            <a href="/workspace">Рабочая зона</a>
            <a href="/feedback">Обратная связь</a>
            <a href="/tariffs">Тарифы</a>
        </nav>
        <div class="nav-right">
            <div class="lang-switch">
                <span class="active">Lvo</span>
                <span>Ru</span>
            </div>
        </div>
    </header>

    <div class="main-container">
        <h1>📞 Обратная связь</h1>
        <p style="margin-bottom: 30px; opacity: 0.8;">Свяжитесь с нами любым удобным способом</p>

        <div class="card" style="text-align: center;">
            <h2>Наши контакты</h2>
            <div class="contact-info">
                <div class="contact-item">
                    📨 <strong>Telegram:</strong> <a href="https://t.me/T5bank" target="_blank">@T5bank</a>
                </div>
                <div class="contact-item">
                    📘 <strong>VK:</strong> <a href="https://vk.com/tbank_russia" target="_blank">tbank_russia</a>
                </div>
                <div class="contact-item">
                    ✉️ <strong>Email:</strong> <a href="mailto:apogosan135@gmail.com">apogosan135@gmail.com</a>
                </div>
            </div>
            <p style="margin-top: 30px; color: #888;">Мы ответим вам в ближайшее время!</p>
        </div>
    </div>

    <div class="footer">
        <p>© 2026 БИС — Бренд. Имидж. Стратегия.</p>
    </div>
</div>

<script>
    function createStars() {
        const starsContainer = document.getElementById('stars');
        for (let i = 0; i < 200; i++) {
            const star = document.createElement('div');
            star.classList.add('star');
            const size = Math.random() * 2 + 1;
            star.style.width = size + 'px';
            star.style.height = size + 'px';
            star.style.left = Math.random() * 100 + '%';
            star.style.top = Math.random() * 100 + '%';
            star.style.animationDelay = Math.random() * 5 + 's';
            star.style.animationDuration = (Math.random() * 3 + 2) + 's';
            starsContainer.appendChild(star);
        }
    }
    createStars();
</script>
</body>
</html>
"""

# ========== РАБОЧАЯ ЗОНА (с правильными настройками аккаунта) ==========
WORKSPACE_PAGE = """
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>БИС — Рабочая зона</title>
    """ + COMMON_STYLES + """
</head>
<body>
<div class="stars" id="stars"></div>
<div class="planet-decoration"></div>

<div class="content">
    <header class="header">
        <div class="logo">
            <div class="logo-icon"></div>
            <span class="logo-text">БИС</span>
        </div>
        <nav class="nav-menu">
            <a href="/">Главная</a>
            <a href="/workspace">Рабочая зона</a>
            <a href="/feedback">Обратная связь</a>
            <a href="/tariffs">Тарифы</a>
        </nav>
        <div class="nav-right">
            <div class="lang-switch">
                <span class="active">Lvo</span>
                <span>Ru</span>
            </div>
        </div>
    </header>

    <div class="main-container">
        <h1>БИС AI</h1>
        <p style="margin-bottom: 30px; opacity: 0.8;">Перед общением заполните контент-студию</p>

        <div class="workspace-nav">
            <a class="active" onclick="switchSection('studio')">🎨 Контент-студия</a>
            <a onclick="switchSection('plan')">📅 Контент-план</a>
            <a onclick="switchSection('analytics')">📊 Аналитика</a>
            <a onclick="switchSection('settings')">⚙️ Настройки аккаунта</a>
        </div>

        <!-- Контент-студия -->
        <div id="studio-section">
            <div class="workspace-layout">
                <div class="left-panel">
                    <h2>Контент-студия</h2>
                    <p style="margin: 15px 0;">Выберите формат:</p>
                    <div class="format-buttons">
                        <button class="format-btn active" onclick="selectFormat('post')">📝 Пост</button>
                        <button class="format-btn" onclick="selectFormat('story')">📸 Сторис</button>
                        <button class="format-btn" onclick="selectFormat('article')">📰 Статья</button>
                    </div>
                    <div class="checkbox-group">
                        <label><input type="checkbox" id="useStyle" checked> Использование вашего стиля</label>
                    </div>
                    <h2 style="margin-top: 20px;">Что хотите создать?</h2>
                    <div class="checkbox-group">
                        <label><input type="radio" name="contentType" value="images"> Пост с изображениями</label>
                        <label><input type="radio" name="contentType" value="video"> Пост с видео</label>
                        <label><input type="radio" name="contentType" value="text" checked> Пост только с текстом</label>
                    </div>
                    <div class="checkbox-group">
                        <label><input type="checkbox" id="useStock"> Использовать стоковый материал</label>
                        <label><input type="checkbox" id="useAI"> Использовать генеративный ИИ</label>
                    </div>
                    <h2 style="margin-top: 20px;">Ваш запрос</h2>
                    <textarea id="topicInput" rows="3" placeholder="Напишите тему поста или вопрос... например: Напиши пост про Москву!"></textarea>
                    <div style="display: flex; gap: 15px; margin-top: 15px;">
                        <button class="btn-primary" onclick="generatePost()">✨ Сгенерировать</button>
                    </div>
                </div>
                <div class="right-panel">
                    <h2>Результат</h2>
                    <div class="result-area" id="resultContent">
                        <p id="resultText" style="color: #aaa;">Здесь появится результат после генерации...</p>
                    </div>
                    <div style="display: flex; gap: 15px; margin-top: 20px;">
                        <button class="btn-secondary" onclick="addToPlan()">📅 Добавить в контент-план</button>
                        <button class="btn-secondary" onclick="regenerate()">🔄 Другой вариант</button>
                    </div>
                </div>
            </div>
        </div>

        <!-- Контент-план (заглушка) -->
        <div id="plan-section" style="display: none;">
            <div class="card" style="text-align: center;">
                <h2>📅 Контент-план</h2>
                <p style="margin: 20px 0;">Здесь будет отображаться ваш контент-план на неделю с возможностью редактирования.</p>
                <button class="btn-primary" onclick="switchSection('studio')">➕ Добавить пост</button>
            </div>
        </div>

        <!-- Аналитика (заглушка) -->
        <div id="analytics-section" style="display: none;">
            <div class="card" style="text-align: center;">
                <h2>📊 Аналитика</h2>
                <p style="margin: 20px 0;">Здесь будут отображаться метрики, графики и AI-гипотезы по вашим публикациям.</p>
                <button class="btn-secondary" onclick="switchSection('studio')">Вернуться в студию</button>
            </div>
        </div>

        <!-- НАСТРОЙКИ АККАУНТА (ПРОФИЛЬ БРЕНДА) -->
        <div id="settings-section" style="display: none;">
            <div class="card">
                <h2>⚙️ Настройки профиля бренда</h2>
                <form id="profileForm">
                    <div class="form-group">
                        <label>🏢 Ниша</label>
                        <input type="text" id="niche" placeholder="Например: туризм по Томску">
                    </div>
                    <div class="form-group">
                        <label>🎭 Тональность</label>
                        <input type="text" id="tone" placeholder="Например: вдохновляющий и экспертный">
                    </div>
                    <div class="form-group">
                        <label>🏙️ Город</label>
                        <input type="text" id="city" placeholder="Например: Томск">
                    </div>
                    <div class="form-group">
                        <label>🎯 Цель бренда</label>
                        <select id="goal">
                            <option value="expert">🎓 Эксперт</option>
                            <option value="influencer">⭐ Лидер мнений</option>
                            <option value="sales">💰 Продажи</option>
                        </select>
                    </div>
                    <button type="button" class="btn-primary" onclick="saveProfile()">💾 Сохранить профиль</button>
                    <button type="button" class="btn-secondary" style="margin-left: 15px;" onclick="loadProfile()">🔄 Загрузить профиль</button>
                </form>
                <div id="profileStatus" style="margin-top: 20px; color: #ffaa00;"></div>
            </div>
        </div>
    </div>

    <div class="footer">
        <p>© 2026 БИС — Бренд. Имидж. Стратегия.</p>
    </div>
</div>

<script>
    function createStars() {
        const starsContainer = document.getElementById('stars');
        for (let i = 0; i < 200; i++) {
            const star = document.createElement('div');
            star.classList.add('star');
            const size = Math.random() * 2 + 1;
            star.style.width = size + 'px';
            star.style.height = size + 'px';
            star.style.left = Math.random() * 100 + '%';
            star.style.top = Math.random() * 100 + '%';
            star.style.animationDelay = Math.random() * 5 + 's';
            star.style.animationDuration = (Math.random() * 3 + 2) + 's';
            starsContainer.appendChild(star);
        }
    }
    createStars();

    let currentFormat = 'post';

    function selectFormat(format) {
        currentFormat = format;
        document.querySelectorAll('.format-btn').forEach(btn => btn.classList.remove('active'));
        event.target.classList.add('active');
    }

    async function generatePost() {
        const topic = document.getElementById('topicInput').value;
        const resultDiv = document.getElementById('resultText');

        if (!topic) {
            resultDiv.innerHTML = '⚠️ Пожалуйста, введите тему поста или вопрос.';
            return;
        }

        resultDiv.innerHTML = '🤔 Генерация...';

        try {
            const response = await fetch('/api/generate', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ prompt: topic })
            });
            const data = await response.json();
            resultDiv.innerHTML = data.result.replace(/\\n/g, '<br>');
        } catch (error) {
            resultDiv.innerHTML = '❌ Ошибка связи с сервером. Попробуйте позже.';
        }
    }

    function regenerate() {
        generatePost();
    }

    function addToPlan() {
        alert('✅ Пост добавлен в контент-план!');
    }

    function switchSection(section) {
        document.getElementById('studio-section').style.display = 'none';
        document.getElementById('plan-section').style.display = 'none';
        document.getElementById('analytics-section').style.display = 'none';
        document.getElementById('settings-section').style.display = 'none';

        if (section === 'studio') document.getElementById('studio-section').style.display = 'block';
        else if (section === 'plan') document.getElementById('plan-section').style.display = 'block';
        else if (section === 'analytics') document.getElementById('analytics-section').style.display = 'block';
        else if (section === 'settings') document.getElementById('settings-section').style.display = 'block';

        document.querySelectorAll('.workspace-nav a').forEach(link => link.classList.remove('active'));
        event.target.classList.add('active');

        if (section === 'settings') loadProfile();
    }

    async function saveProfile() {
        const profile = {
            niche: document.getElementById('niche').value,
            tone: document.getElementById('tone').value,
            city: document.getElementById('city').value,
            goal: document.getElementById('goal').value
        };

        try {
            const response = await fetch('/api/save-profile', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(profile)
            });
            const data = await response.json();
            document.getElementById('profileStatus').innerHTML = data.message;
            setTimeout(() => { document.getElementById('profileStatus').innerHTML = ''; }, 3000);
        } catch (error) {
            document.getElementById('profileStatus').innerHTML = '❌ Ошибка сохранения';
        }
    }

    async function loadProfile() {
        try {
            const response = await fetch('/api/get-profile');
            const profile = await response.json();
            document.getElementById('niche').value = profile.niche || '';
            document.getElementById('tone').value = profile.tone || '';
            document.getElementById('city').value = profile.city || '';
            document.getElementById('goal').value = profile.goal || 'expert';
            document.getElementById('profileStatus').innerHTML = '✅ Профиль загружен';
            setTimeout(() => { document.getElementById('profileStatus').innerHTML = ''; }, 2000);
        } catch (error) {
            document.getElementById('profileStatus').innerHTML = '❌ Ошибка загрузки';
        }
    }
</script>
</body>
</html>
"""

from pydantic import BaseModel


class GenerateRequest(BaseModel):
    prompt: str


@app.post("/api/generate")
async def generate(request: GenerateRequest):
    result = call_gigachat(request.prompt)
    return JSONResponse(content={"result": result})


@app.post("/api/save-profile")
async def save_profile(request: Request):
    data = await request.json()
    user_data["profile"] = data
    save_user_data(user_data)
    return JSONResponse(content={"message": "✅ Профиль сохранён!"})


@app.get("/api/get-profile")
async def get_profile():
    profile = user_data.get("profile", {})
    return JSONResponse(content=profile)


@app.get("/", response_class=HTMLResponse)
async def landing():
    return HTMLResponse(content=LANDING_PAGE)


@app.get("/workspace", response_class=HTMLResponse)
async def workspace():
    return HTMLResponse(content=WORKSPACE_PAGE)


@app.get("/tariffs", response_class=HTMLResponse)
async def tariffs():
    return HTMLResponse(content=TARIFFS_PAGE)


@app.get("/feedback", response_class=HTMLResponse)
async def feedback():
    return HTMLResponse(content=FEEDBACK_PAGE)


if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8080)
