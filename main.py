from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
import uvicorn
import requests
import uuid
import json
import os
import random

app = FastAPI(title="БИС Platform")

# ========== КЛЮЧИ ==========
GIGACHAT_AUTH_KEY = "MDE5ZDMzYzItNGY5NS03MGY4LThjOTktYzk5ZDIyMzYyZTk3OmI5OWRhMTVjLTNmMGQtNDFlOS04Yjc3LTdhMWQ2YzU5NzBiNg=="
PEXELS_API_KEY = "99lzySAP7wyWqzFaBGPQQbcJWPwXZVaR6H6KbILjvJ5Au6iV6YnrxXM5"
UNSPLASH_API_KEY = "NpF_z6xsa39ov1PS4Bq_AqIoabRJphW1s30RvnOGCMY"
gigachat_access_token = None

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


# ========== GIGACHAT ==========
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


def call_gigachat(prompt, user_profile=None):
    global gigachat_access_token
    if not gigachat_access_token:
        if not get_gigachat_token():
            return "❌ Ошибка подключения к ИИ"

    url = "https://gigachat.devices.sberbank.ru/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {gigachat_access_token}",
        "Content-Type": "application/json"
    }

    profile_context = ""
    if user_profile:
        goal_map = {"expert": "🎓 Эксперт", "influencer": "⭐ Лидер мнений", "sales": "💰 Продажи"}
        profile_context = f"""
Ниша: {user_profile.get('niche', 'не указана')}
Тональность: {user_profile.get('tone', 'дружелюбная')}
Город: {user_profile.get('city', 'Москва')}
Цель: {goal_map.get(user_profile.get('goal', 'expert'), 'Эксперт')}
"""

    system_prompt = f"""Ты — AI-ассистент БИС. Ты помогаешь создавать контент для соцсетей.
{profile_context}
Правила:
1. Отвечай кратко, дружелюбно, используй эмодзи
2. Если просят пост — сразу давай текст с хештегами
3. Учитывай нишу, тональность и цель бренда
4. Пиши от первого лица

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
            return call_gigachat(prompt, user_profile)
        return f"❌ Ошибка: {response.status_code}"
    except Exception as e:
        return f"❌ Ошибка: {str(e)}"


# ========== ГЕНЕРАЦИЯ ИЗОБРАЖЕНИЙ ЧЕРЕЗ API ==========
def search_pexels(query):
    url = f"https://api.pexels.com/v1/search?query={query}&per_page=3"
    headers = {"Authorization": PEXELS_API_KEY}
    try:
        response = requests.get(url, headers=headers, timeout=10)
        print(f"[Pexels] Статус: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            photos = data.get('photos', [])
            if photos:
                return photos[0]['src']['medium']
        return None
    except Exception as e:
        print(f"[Pexels] Ошибка: {e}")
        return None


def search_unsplash(query):
    url = f"https://api.unsplash.com/search/photos?query={query}&per_page=1&client_id={UNSPLASH_API_KEY}"
    try:
        response = requests.get(url, timeout=10)
        print(f"[Unsplash] Статус: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            results = data.get('results', [])
            if results:
                return results[0]['urls']['regular']
        return None
    except Exception as e:
        print(f"[Unsplash] Ошибка: {e}")
        return None


@app.get("/api/generate-image")
async def generate_image(prompt: str):
    # 1. Пробуем Pexels
    image_url = search_pexels(prompt)

    # 2. Если Pexels не сработал — пробуем Unsplash
    if not image_url:
        image_url = search_unsplash(prompt)

    # 3. Если оба API не сработали — демо-режим
    if not image_url:
        demo_images = [
            "https://images.pexels.com/photos/417074/pexels-photo-417074.jpeg?w=600",
            "https://images.pexels.com/photos/459225/pexels-photo-459225.jpeg?w=600",
            "https://images.pexels.com/photos/355465/pexels-photo-355465.jpeg?w=600",
        ]
        image_url = random.choice(demo_images)
        print("[Demo] Использую демо-фото")

    return JSONResponse(content={"url": image_url})


# ========== ЕДИНЫЙ СТИЛЬ ==========
COMMON_STYLES = """
<style>
    * { margin: 0; padding: 0; box-sizing: border-box; }
    body {
        font-family: 'Inter', 'Montserrat', sans-serif;
        background: radial-gradient(ellipse at center, #0a0a0a 0%, #000000 100%);
        color: #fff;
        min-height: 100vh;
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
        background-color: #fff;
        border-radius: 50%;
        opacity: 0;
        animation: twinkle 3s infinite;
    }
    @keyframes twinkle {
        0%, 100% { opacity: 0; }
        50% { opacity: 0.8; }
    }
    .content { position: relative; z-index: 10; min-height: 100vh; display: flex; flex-direction: column; }
    .header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 20px 48px;
        background: rgba(0,0,0,0.7);
        backdrop-filter: blur(10px);
        border-bottom: 1px solid rgba(255,102,0,0.3);
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
        background: linear-gradient(135deg, #ff6600, #ffaa00);
        -webkit-background-clip: text;
        background-clip: text;
        color: transparent;
    }
    .nav-menu { display: flex; gap: 32px; }
    .nav-menu a { color: #fff; text-decoration: none; font-size: 14px; opacity: 0.8; transition: 0.3s; }
    .nav-menu a:hover { opacity: 1; color: #ff6600; }
    .nav-right { display: flex; gap: 24px; align-items: center; }
    .lang-switch {
        display: flex;
        gap: 6px;
        background: rgba(26,26,26,0.8);
        padding: 4px 8px;
        border-radius: 20px;
    }
    .lang-switch span { cursor: pointer; font-size: 12px; color: #888; }
    .lang-switch span.active { color: #ff6600; }
    .main-container { flex: 1; padding: 40px 48px; }
    h1 {
        font-size: 32px;
        font-weight: 700;
        margin-bottom: 30px;
        background: linear-gradient(135deg, #fff, #ffaa00);
        -webkit-background-clip: text;
        background-clip: text;
        color: transparent;
    }
    h2 { font-size: 22px; font-weight: 600; margin-bottom: 20px; color: #ffaa00; }
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
        transition: 0.3s;
    }
    .btn-primary:hover { transform: scale(1.02); box-shadow: 0 0 20px rgba(255,102,0,0.5); }
    .btn-secondary {
        background: transparent;
        border: 1px solid #ff6600;
        color: #ff6600;
        padding: 10px 24px;
        border-radius: 30px;
        cursor: pointer;
        transition: 0.3s;
    }
    .btn-secondary:hover { background: rgba(255,102,0,0.2); }
    .footer {
        text-align: center;
        padding: 30px;
        border-top: 1px solid #222;
        font-size: 12px;
        color: #666;
    }
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
        color: #fff;
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
        color: #fff;
        margin: 15px 0;
    }
    .workspace-nav {
        display: flex;
        gap: 20px;
        margin-bottom: 25px;
        border-bottom: 1px solid #333;
        padding-bottom: 15px;
    }
    .workspace-nav a {
        color: #aaa;
        text-decoration: none;
        padding: 8px 16px;
        border-radius: 20px;
        cursor: pointer;
    }
    .workspace-nav a:hover, .workspace-nav a.active {
        background: rgba(255,102,0,0.2);
        color: #ff6600;
    }
    .form-group { margin-bottom: 15px; }
    .form-group label { display: block; margin-bottom: 5px; color: #ffaa00; font-size: 14px; }
    .form-group input, .form-group select {
        width: 100%;
        padding: 10px;
        background: rgba(30,30,40,0.8);
        border: 1px solid #333;
        border-radius: 8px;
        color: #fff;
    }
    .photo-grid {
        display: grid;
        grid-template-columns: repeat(auto-fill, minmax(100px, 1fr));
        gap: 10px;
        margin-top: 15px;
    }
    .photo-item { cursor: pointer; border-radius: 8px; overflow: hidden; }
    .photo-item img { width: 100%; height: 80px; object-fit: cover; }
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
    }
    .pricing-card h3 { font-size: 24px; }
    .price { font-size: 42px; font-weight: 800; color: #ffaa00; margin: 20px 0; }
    .price span { font-size: 16px; font-weight: 400; color: #888; }
    .features-list { list-style: none; margin: 20px 0; }
    .features-list li { padding: 8px 0; border-bottom: 1px solid rgba(255,255,255,0.1); }
    .contact-info { text-align: center; margin-top: 20px; }
    .contact-item {
        display: inline-block;
        margin: 10px 20px;
        padding: 10px 20px;
        background: rgba(255,102,0,0.1);
        border-radius: 30px;
    }
    .contact-item a { color: #ffaa00; text-decoration: none; }
</style>
"""

# ========== HTML СТРАНИЦЫ ==========
LANDING_PAGE = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>БИС — Космический AI</title>
    """ + COMMON_STYLES + """
    <style>
        .hero { flex: 1; display: flex; align-items: center; justify-content: center; padding: 40px 20px; min-height: 70vh; text-align: center; }
        #canvas-container { position: fixed; top: 0; left: 0; width: 100%; height: 100%; z-index: 1; pointer-events: none; }
        .hero-content { position: relative; z-index: 2; }
        .title h1 { font-size: 48px; font-weight: 800; text-transform: uppercase; margin-bottom: 24px; }
        .title h1 span { color: #ff6600; }
        .title p { font-size: 18px; opacity: 0.7; max-width: 700px; margin: 0 auto 30px; }
    </style>
</head>
<body>
<div class="stars" id="stars"></div>
<div id="canvas-container"></div>
<div class="content">
    <header class="header">
        <div class="logo"><div class="logo-icon"></div><span class="logo-text">БИС</span></div>
        <nav class="nav-menu">
            <a href="/">Главная</a>
            <a href="/workspace">Рабочая зона</a>
            <a href="/feedback">Обратная связь</a>
            <a href="/tariffs">Тарифы</a>
        </nav>
        <div class="nav-right"><div class="lang-switch"><span class="active">Lvo</span><span>Ru</span></div></div>
    </header>
    <div class="hero"><div class="hero-content"><div class="title"><h1>БИС — <span>БРЕНД. ИМИДЖ. СТРАТЕГИЯ.</span><br>ВСЕ НЕОБХОДИМЫЕ НЕЙРОСЕТИ<br>В ОДНОМ МЕСТЕ!</h1><p>Искусственный интеллект нового поколения для работы с текстом, изображениями и данными</p><a href="/workspace" class="btn-primary">Начать работу!</a></div></div></div>
    <div class="footer"><p>© 2026 БИС — Бренд. Имидж. Стратегия.</p></div>
</div>
<script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>
<script>
    function createStars() {
        for (let i = 0; i < 300; i++) {
            let s = document.createElement('div');
            s.classList.add('star');
            let size = Math.random() * 3 + 1;
            s.style.cssText = `width:${size}px;height:${size}px;left:${Math.random()*100}%;top:${Math.random()*100}%;animation-delay:${Math.random()*5}s`;
            document.getElementById('stars').appendChild(s);
        }
    }
    createStars();
    const c = document.getElementById('canvas-container'), scene = new THREE.Scene(), cam = new THREE.PerspectiveCamera(45, window.innerWidth/window.innerHeight, 0.1, 1000);
    cam.position.z = 5;
    const renderer = new THREE.WebGLRenderer({ alpha: true });
    renderer.setSize(window.innerWidth, window.innerHeight);
    renderer.setClearColor(0x000000, 0);
    c.appendChild(renderer.domElement);
    const tex = new THREE.TextureLoader().load('https://threejs.org/examples/textures/planets/earth_atmos_2048.jpg');
    const earth = new THREE.Mesh(new THREE.SphereGeometry(1.5, 128, 128), new THREE.MeshStandardMaterial({ map: tex, roughness: 0.5, metalness: 0.1 }));
    scene.add(earth);
    scene.add(new THREE.AmbientLight(0x404060));
    let light = new THREE.DirectionalLight(0xffffff, 1);
    light.position.set(5,5,5);
    scene.add(light);
    let mx=0,my=0;
    document.addEventListener('mousemove', e => { mx = (e.clientX/window.innerWidth)*2-1; my = (e.clientY/window.innerHeight)*2-1; });
    function animate() {
        requestAnimationFrame(animate);
        earth.rotation.y += 0.003;
        earth.rotation.x = my * 0.2;
        earth.rotation.y += mx * 0.2;
        renderer.render(scene, cam);
    }
    animate();
    window.addEventListener('resize', () => { cam.aspect = window.innerWidth/window.innerHeight; cam.updateProjectionMatrix(); renderer.setSize(window.innerWidth, window.innerHeight); });
</script>
</body>
</html>
"""

TARIFFS_PAGE = """
<!DOCTYPE html>
<html>
<head><meta charset="UTF-8"><title>БИС — Тарифы</title>""" + COMMON_STYLES + """</head>
<body>
<div class="stars" id="stars"></div>
<div class="content">
    <header class="header">
        <div class="logo"><div class="logo-icon"></div><span class="logo-text">БИС</span></div>
        <nav class="nav-menu"><a href="/">Главная</a><a href="/workspace">Рабочая зона</a><a href="/feedback">Обратная связь</a><a href="/tariffs">Тарифы</a></nav>
        <div class="nav-right"><div class="lang-switch"><span class="active">Lvo</span><span>Ru</span></div></div>
    </header>
    <div class="main-container"><h1>💎 Выберите свой тариф</h1><p style="margin-bottom:30px;opacity:0.8;">Подберите оптимальный план для вашего бизнеса</p>
    <div class="pricing-grid">
        <div class="pricing-card"><h3>🌟 Базовый</h3><div class="price">1 190 ₽<span>/мес</span></div><ul class="features-list"><li>📝 2 поста в день</li><li>🎬 Без генерации видео</li><li>💬 Ответы — 20 шт/мес</li></ul><button class="btn-primary" onclick="alert('Базовый')">Выбрать</button></div>
        <div class="pricing-card"><h3>🚀 Pro</h3><div class="price">4 990 ₽<span>/мес</span></div><ul class="features-list"><li>📝 4 поста в день</li><li>🎬 Генерация видео</li><li>💬 Ответы — 35 шт/мес</li></ul><button class="btn-primary" onclick="alert('Pro')">Выбрать</button></div>
        <div class="pricing-card"><h3>👑 Premium</h3><div class="price">9 990 ₽<span>/мес</span></div><ul class="features-list"><li>📝 Безлимит постов</li><li>🎬 Генерация видео</li><li>💬 Ответы — 100 шт/мес</li></ul><button class="btn-primary" onclick="alert('Premium')">Выбрать</button></div>
    </div></div>
    <div class="footer"><p>© 2026 БИС — Бренд. Имидж. Стратегия.</p></div>
</div>
<script>for(let i=0;i<200;i++){let s=document.createElement('div');s.classList.add('star');let size=Math.random()*2+1;s.style.cssText=`width:${size}px;height:${size}px;left:${Math.random()*100}%;top:${Math.random()*100}%;animation-delay:${Math.random()*5}s`;document.getElementById('stars').appendChild(s);}</script>
</body>
</html>
"""

FEEDBACK_PAGE = """
<!DOCTYPE html>
<html>
<head><meta charset="UTF-8"><title>БИС — Обратная связь</title>""" + COMMON_STYLES + """</head>
<body>
<div class="stars" id="stars"></div>
<div class="content">
    <header class="header">
        <div class="logo"><div class="logo-icon"></div><span class="logo-text">БИС</span></div>
        <nav class="nav-menu"><a href="/">Главная</a><a href="/workspace">Рабочая зона</a><a href="/feedback">Обратная связь</a><a href="/tariffs">Тарифы</a></nav>
        <div class="nav-right"><div class="lang-switch"><span class="active">Lvo</span><span>Ru</span></div></div>
    </header>
    <div class="main-container"><h1>📞 Обратная связь</h1><div class="card" style="text-align:center;"><h2>Наши контакты</h2><div class="contact-info"><div class="contact-item">📨 <strong>Telegram:</strong> <a href="https://t.me/T5bank" target="_blank">@T5bank</a></div><div class="contact-item">📘 <strong>VK:</strong> <a href="https://vk.com/tbank_russia" target="_blank">tbank_russia</a></div><div class="contact-item">✉️ <strong>Email:</strong> <a href="mailto:apogosan135@gmail.com">apogosan135@gmail.com</a></div></div></div></div>
    <div class="footer"><p>© 2026 БИС — Бренд. Имидж. Стратегия.</p></div>
</div>
<script>for(let i=0;i<200;i++){let s=document.createElement('div');s.classList.add('star');s.style.cssText=`width:${Math.random()*2+1}px;height:${Math.random()*2+1}px;left:${Math.random()*100}%;top:${Math.random()*100}%;animation-delay:${Math.random()*5}s`;document.getElementById('stars').appendChild(s);}</script>
</body>
</html>
"""

WORKSPACE_PAGE = """
<!DOCTYPE html>
<html>
<head><meta charset="UTF-8"><title>БИС — Рабочая зона</title>""" + COMMON_STYLES + """</head>
<body>
<div class="stars" id="stars"></div>
<div class="content">
    <header class="header">
        <div class="logo"><div class="logo-icon"></div><span class="logo-text">БИС</span></div>
        <nav class="nav-menu"><a href="/">Главная</a><a href="/workspace">Рабочая зона</a><a href="/feedback">Обратная связь</a><a href="/tariffs">Тарифы</a></nav>
        <div class="nav-right"><div class="lang-switch"><span class="active">Lvo</span><span>Ru</span></div></div>
    </header>
    <div class="main-container">
        <h1>БИС AI</h1>
        <p style="margin-bottom:30px;opacity:0.8;">Перед общением заполните контент-студию</p>
        <div class="workspace-nav">
            <a class="active" onclick="switchSection('studio')">🎨 Контент-студия</a>
            <a onclick="switchSection('plan')">📅 Контент-план</a>
            <a onclick="switchSection('analytics')">📊 Аналитика</a>
            <a onclick="switchSection('settings')">⚙️ Настройки аккаунта</a>
        </div>
        <div id="studio-section">
            <div class="workspace-layout">
                <div class="left-panel">
                    <h2>Контент-студия</h2>
                    <p>Выберите формат:</p>
                    <div class="format-buttons">
                        <button class="format-btn active" onclick="selectFormat('post')">📝 Пост</button>
                        <button class="format-btn" onclick="selectFormat('story')">📸 Сторис</button>
                        <button class="format-btn" onclick="selectFormat('article')">📰 Статья</button>
                    </div>
                    <div class="checkbox-group"><label><input type="checkbox" id="useStyle" checked> Использование вашего стиля</label></div>
                    <h2>Что хотите создать?</h2>
                    <div class="checkbox-group">
                        <label><input type="radio" name="contentType" value="images"> Пост с изображениями</label>
                        <label><input type="radio" name="contentType" value="video"> Пост с видео</label>
                        <label><input type="radio" name="contentType" value="text" checked> Пост только с текстом</label>
                    </div>
                    <div class="checkbox-group">
                        <label><input type="checkbox" id="useStock"> Использовать стоковый материал</label>
                        <label><input type="checkbox" id="useAI"> Использовать генеративный ИИ</label>
                    </div>
                    <h2>Ваш запрос</h2>
                    <textarea id="topicInput" rows="3" placeholder="Напишите тему поста... например: Напиши пост про Москву!"></textarea>
                    <div style="display:flex;gap:15px;flex-wrap:wrap;">
                        <button class="btn-primary" onclick="generatePost()">✨ Сгенерировать</button>
                        <button class="btn-secondary" onclick="generateImage()">🎨 Сгенерировать изображение</button>
                        <button class="btn-secondary" onclick="publishToVK()">📤 Опубликовать в VK</button>
                    </div>
                    <div id="imageResult" class="result-area" style="display:none; margin-top:20px;"></div>
                </div>
                <div class="right-panel">
                    <h2>Результат</h2>
                    <div class="result-area" id="resultContent"><p id="resultText" style="color:#aaa;">Здесь появится результат...</p></div>
                    <div style="display:flex;gap:15px;margin-top:20px;">
                        <button class="btn-secondary" onclick="addToPlan()">📅 Добавить в контент-план</button>
                        <button class="btn-secondary" onclick="regenerate()">🔄 Другой вариант</button>
                    </div>
                </div>
            </div>
        </div>
        <div id="plan-section" style="display:none;"><div class="card" style="text-align:center;"><h2>📅 Контент-план</h2><p style="margin:20px 0;">Здесь будет контент-план на неделю</p><button class="btn-primary" onclick="switchSection('studio')">➕ Добавить пост</button></div></div>
        <div id="analytics-section" style="display:none;"><div class="card" style="text-align:center;"><h2>📊 Аналитика</h2><p style="margin:20px 0;">Здесь будут метрики и AI-гипотезы</p><button class="btn-secondary" onclick="switchSection('studio')">Вернуться</button></div></div>
        <div id="settings-section" style="display:none;">
            <div class="card"><h2>⚙️ Настройки профиля бренда</h2>
            <form id="profileForm">
                <div class="form-group"><label>🏢 Ниша</label><input type="text" id="niche" placeholder="туризм по Томску"></div>
                <div class="form-group"><label>🎭 Тональность</label><input type="text" id="tone" placeholder="вдохновляющий и экспертный"></div>
                <div class="form-group"><label>🏙️ Город</label><input type="text" id="city" placeholder="Томск"></div>
                <div class="form-group"><label>🎯 Цель бренда</label><select id="goal"><option value="expert">🎓 Эксперт</option><option value="influencer">⭐ Лидер мнений</option><option value="sales">💰 Продажи</option></select></div>
                <button type="button" class="btn-primary" onclick="saveProfile()">💾 Сохранить профиль</button>
                <button type="button" class="btn-secondary" onclick="loadProfile()">🔄 Загрузить профиль</button>
            </form>
            <div id="profileStatus" style="margin-top:20px;color:#ffaa00;"></div>
            </div>
        </div>
    </div>
    <div class="footer"><p>© 2026 БИС — Бренд. Имидж. Стратегия.</p></div>
</div>
<script>
    let currentFormat = 'post', currentText = '';
    function createStars(){for(let i=0;i<200;i++){let s=document.createElement('div');s.classList.add('star');s.style.cssText=`width:${Math.random()*2+1}px;height:${Math.random()*2+1}px;left:${Math.random()*100}%;top:${Math.random()*100}%;animation-delay:${Math.random()*5}s`;document.getElementById('stars').appendChild(s);}}
    createStars();
    function selectFormat(f){currentFormat=f;document.querySelectorAll('.format-btn').forEach(b=>b.classList.remove('active'));event.target.classList.add('active');}
    async function generatePost(){
        let topic=document.getElementById('topicInput').value, resDiv=document.getElementById('resultText');
        if(!topic){resDiv.innerHTML='⚠️ Введите тему';return;}
        resDiv.innerHTML='🤔 Генерация...';
        try{
            let resp=await fetch('/api/generate',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({prompt:topic})});
            let data=await resp.json();
            currentText=data.result;
            resDiv.innerHTML=currentText.replace(/\\n/g,'<br>');
        }catch(e){resDiv.innerHTML='❌ Ошибка';}
    }
    async function generateImage(){
        let topic=document.getElementById('topicInput').value;
        if(!topic){alert('Введите тему для генерации изображения');return;}
        let imageDiv=document.getElementById('imageResult');
        imageDiv.style.display='block';
        imageDiv.innerHTML='🎨 Поиск изображения по запросу...';
        try{
            let resp=await fetch(`/api/generate-image?prompt=${encodeURIComponent(topic)}`);
            let data=await resp.json();
            if(data.url){imageDiv.innerHTML=`<img src="${data.url}" style="max-width:100%;border-radius:12px;">`;}
            else{imageDiv.innerHTML='❌ Не удалось найти изображение';}
        }catch(e){imageDiv.innerHTML='❌ Ошибка поиска';}
    }
    async function publishToVK(){if(!currentText){alert('Сначала сгенерируйте пост');return;}if(confirm('Опубликовать в VK?')){let resp=await fetch('/api/publish-to-vk',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({text:currentText})});let data=await resp.json();alert(data.message);}}
    function regenerate(){generatePost();}
    function addToPlan(){alert('✅ Добавлено в план!');}
    function switchSection(s){
        document.getElementById('studio-section').style.display='none';document.getElementById('plan-section').style.display='none';document.getElementById('analytics-section').style.display='none';document.getElementById('settings-section').style.display='none';
        if(s==='studio')document.getElementById('studio-section').style.display='block';
        else if(s==='plan')document.getElementById('plan-section').style.display='block';
        else if(s==='analytics')document.getElementById('analytics-section').style.display='block';
        else if(s==='settings')document.getElementById('settings-section').style.display='block';
        document.querySelectorAll('.workspace-nav a').forEach(l=>l.classList.remove('active'));event.target.classList.add('active');
        if(s==='settings')loadProfile();
    }
    async function saveProfile(){
        let profile={niche:document.getElementById('niche').value,tone:document.getElementById('tone').value,city:document.getElementById('city').value,goal:document.getElementById('goal').value};
        let resp=await fetch('/api/save-profile',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(profile)});
        let data=await resp.json();document.getElementById('profileStatus').innerHTML=data.message;setTimeout(()=>document.getElementById('profileStatus').innerHTML='',3000);
    }
    async function loadProfile(){
        let resp=await fetch('/api/get-profile');let profile=await resp.json();
        document.getElementById('niche').value=profile.niche||'';document.getElementById('tone').value=profile.tone||'';document.getElementById('city').value=profile.city||'';document.getElementById('goal').value=profile.goal||'expert';
        document.getElementById('profileStatus').innerHTML='✅ Профиль загружен';setTimeout(()=>document.getElementById('profileStatus').innerHTML='',2000);
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
    profile = user_data.get("profile", {})
    result = call_gigachat(request.prompt, profile)
    return JSONResponse(content={"result": result})


@app.post("/api/publish-to-vk")
async def publish_to_vk(request: Request):
    data = await request.json()
    text = data.get("text", "")
    return JSONResponse(
        content={"message": "✅ Пост отправлен в VK (демо-режим). Для реальной публикации настройте VK API."})


@app.post("/api/save-profile")
async def save_profile(request: Request):
    data = await request.json()
    user_data["profile"] = data
    save_user_data(user_data)
    return JSONResponse(content={"message": "✅ Профиль сохранён!"})


@app.get("/api/get-profile")
async def get_profile():
    return JSONResponse(content=user_data.get("profile", {}))


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
