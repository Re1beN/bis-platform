from fastapi import FastAPI
from fastapi.responses import HTMLResponse
import uvicorn

app = FastAPI(title="BIS Platform")

# ГЛАВНАЯ СТРАНИЦА (Landing Page)
LANDING_PAGE = """
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, user-scalable=no">
    <title>BIS — Бренд. Имидж. Стратегия.</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        body {
            font-family: 'Inter', 'Montserrat', -apple-system, sans-serif;
            background-color: #000000;
            color: #ffffff;
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
            padding: 24px 48px;
            background: transparent;
        }
        .logo {
            display: flex;
            align-items: center;
            gap: 12px;
        }
        .logo-icon {
            width: 32px;
            height: 32px;
            background: linear-gradient(135deg, #ff6600, #ffaa00);
            border-radius: 50%;
            box-shadow: 0 0 15px #ff6600;
        }
        .logo-text {
            font-size: 18px;
            font-weight: 600;
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
            transition: opacity 0.3s;
            cursor: pointer;
        }
        .nav-menu a:hover {
            opacity: 1;
            color: #ff6600;
        }
        .nav-right {
            display: flex;
            gap: 24px;
        }
        .nav-right a {
            color: #ffffff;
            text-decoration: none;
            font-size: 14px;
            opacity: 0.8;
            cursor: pointer;
        }
        .nav-right .version {
            color: #ff6600;
            opacity: 1;
        }
        .hero {
            flex: 1;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            padding: 40px 20px 80px;
            position: relative;
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
        .title h1 span {
            color: #ff6600;
        }
        .title p {
            font-size: 18px;
            opacity: 0.7;
            max-width: 700px;
            margin: 0 auto;
        }
        .btn-primary {
            display: inline-block;
            background-color: #ffffff;
            color: #000000;
            padding: 16px 48px;
            font-size: 16px;
            font-weight: 600;
            text-decoration: none;
            transition: all 0.3s ease;
            cursor: pointer;
            border: none;
            margin-top: 40px;
        }
        .btn-primary:hover {
            background-color: #ff6600;
            color: #ffffff;
            transform: scale(1.05);
        }
        .footer {
            text-align: center;
            padding: 32px;
            opacity: 0.5;
            font-size: 12px;
        }
        /* Модальное окно */
        .modal {
            display: none;
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0,0,0,0.8);
            justify-content: center;
            align-items: center;
            z-index: 1000;
        }
        .modal-content {
            background: #1a1a1a;
            border: 1px solid #ff6600;
            border-radius: 16px;
            padding: 32px;
            max-width: 500px;
            width: 90%;
            text-align: center;
        }
        .modal-content h3 {
            color: #ff6600;
            margin-bottom: 16px;
        }
        .modal-content p {
            color: #ccc;
            line-height: 1.6;
            margin-bottom: 24px;
        }
        .modal-close {
            background: #ff6600;
            color: #000;
            border: none;
            padding: 10px 24px;
            border-radius: 8px;
            cursor: pointer;
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
            <span class="logo-text">BIS</span>
        </div>
        <nav class="nav-menu">
            <a onclick="openModal('guide')">Руководство</a>
            <a href="/workspace">Рабочая зона</a>
            <a onclick="openModal('feedback')">Обратная связь</a>
            <a onclick="openModal('news')">Новости</a>
        </nav>
        <div class="nav-right">
            <a onclick="openModal('account')">Аккаунт</a>
            <a onclick="openModal('tariff')">Тариф</a>
            <a href="#" class="version">BIS</a>
        </div>
    </header>
    <div class="hero">
        <div class="hero-content">
            <div class="title">
                <h1>BIS — <span>БРЕНД. ИМИДЖ. СТРАТЕГИЯ.</span><br>ВСЕ НЕОБХОДИМЫЕ НЕЙРОСЕТИ<br>В ОДНОМ МЕСТЕ!</h1>
                <p>Искусственный интеллект нового поколения для работы с текстом, изображениями и данными</p>
            </div>
            <a href="/workspace" class="btn-primary">Начать работу!</a>
        </div>
    </div>
    <div class="footer">
        <p>© 2026 BIS — Бренд. Имидж. Стратегия.</p>
    </div>
</div>

<!-- Модальные окна -->
<div id="guideModal" class="modal">
    <div class="modal-content">
        <h3>📖 Руководство</h3>
        <p>BIS (Бренд. Имидж. Стратегия) — это платформа на базе искусственного интеллекта, которая помогает создавать и управлять контентом для социальных сетей, анализировать аудиторию и автоматизировать публикации. Используйте вкладки «Текст» и «Изображение» для генерации контента, а «Рабочую зону» для управления результатами.</p>
        <button class="modal-close" onclick="closeModal('guideModal')">Закрыть</button>
    </div>
</div>

<div id="feedbackModal" class="modal">
    <div class="modal-content">
        <h3>💬 Обратная связь</h3>
        <p>По всем вопросам и предложениям пишите на почту: support@bis.ai<br>Telegram: @bis_support<br>Также вы можете оставить отзыв прямо в рабочей зоне через чат с ассистентом.</p>
        <button class="modal-close" onclick="closeModal('feedbackModal')">Закрыть</button>
    </div>
</div>

<div id="newsModal" class="modal">
    <div class="modal-content">
        <h3>📰 Новости</h3>
        <p>🔹 01.04.2026 — Запуск платформы BIS<br>🔹 15.04.2026 — Добавлена генерация изображений через AI<br>🔹 01.05.2026 — Интеграция с VK и Telegram<br>🔹 15.05.2026 — Новый тариф «Бизнес» с командной работой</p>
        <button class="modal-close" onclick="closeModal('newsModal')">Закрыть</button>
    </div>
</div>

<div id="accountModal" class="modal">
    <div class="modal-content">
        <h3>👤 Аккаунт</h3>
        <p>Войдите в свой аккаунт BIS, чтобы сохранять историю, настраивать профиль бренда и получать персональные рекомендации. В демо-режиме доступна только базовая функциональность.</p>
        <button class="modal-close" onclick="closeModal('accountModal')">Закрыть</button>
    </div>
</div>

<div id="tariffModal" class="modal">
    <div class="modal-content">
        <h3>💎 Тарифы</h3>
        <p>🔹 Бесплатный — 10 запросов/день<br>🔹 Базовый — 1 490 ₽/мес, 100 постов, автопостинг<br>🔹 Про — 3 490 ₽/мес, безлимит, аналитика<br>🔹 Бизнес — 7 990 ₽/мес, команда, API</p>
        <button class="modal-close" onclick="closeModal('tariffModal')">Закрыть</button>
    </div>
</div>

<script>
    function openModal(type) {
        const modalId = type + 'Modal';
        const modal = document.getElementById(modalId);
        if (modal) modal.style.display = 'flex';
    }
    function closeModal(modalId) {
        const modal = document.getElementById(modalId);
        if (modal) modal.style.display = 'none';
    }
    window.onclick = function(event) {
        if (event.target.classList.contains('modal')) {
            event.target.style.display = 'none';
        }
    }

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
</script>
<script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>
<script>
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

# РАБОЧАЯ ЗОНА (единый стиль)
WORKSPACE_PAGE = """
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>BIS — Рабочая зона</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        body {
            font-family: 'Inter', 'Montserrat', -apple-system, sans-serif;
            background-color: #000000;
            color: #ffffff;
            height: 100vh;
            display: flex;
            flex-direction: column;
            overflow: hidden;
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
            display: flex;
            flex-direction: column;
            height: 100%;
        }
        .header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 24px 48px;
            background: transparent;
        }
        .logo {
            display: flex;
            align-items: center;
            gap: 12px;
        }
        .logo-icon {
            width: 32px;
            height: 32px;
            background: linear-gradient(135deg, #ff6600, #ffaa00);
            border-radius: 50%;
            box-shadow: 0 0 15px #ff6600;
        }
        .logo-text {
            font-size: 18px;
            font-weight: 600;
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
            transition: opacity 0.3s;
            cursor: pointer;
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
        .nav-right a {
            color: #ffffff;
            text-decoration: none;
            font-size: 14px;
            opacity: 0.8;
            cursor: pointer;
        }
        .btn-outline {
            background: transparent;
            border: 1px solid #ffffff;
            color: #ffffff;
            padding: 6px 16px;
            border-radius: 20px;
            cursor: pointer;
            transition: all 0.2s;
        }
        .btn-outline:hover {
            background: rgba(255,255,255,0.1);
            border-color: #ff6600;
        }
        .lang-switch {
            display: flex;
            gap: 6px;
            background: #1a1a1a;
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
        .main-layout {
            display: flex;
            flex: 1;
            overflow: hidden;
        }
        .left-panel {
            width: 30%;
            background-color: rgba(15, 15, 15, 0.95);
            border-right: 1px solid #2a2a2a;
            display: flex;
            flex-direction: column;
            overflow: hidden;
        }
        .tabs {
            display: flex;
            border-bottom: 1px solid #2a2a2a;
        }
        .tab {
            flex: 1;
            padding: 16px;
            text-align: center;
            cursor: pointer;
            background: transparent;
            border: none;
            color: #666;
            font-size: 14px;
            transition: all 0.2s;
        }
        .tab.active {
            color: #ff6600;
            border-bottom: 2px solid #ff6600;
        }
        .chat-history {
            flex: 1;
            overflow-y: auto;
            padding: 20px;
            display: flex;
            flex-direction: column;
            gap: 16px;
        }
        .message {
            padding: 12px;
            border-radius: 12px;
            max-width: 90%;
        }
        .message.user {
            background: rgba(255,102,0,0.2);
            align-self: flex-end;
            border: 1px solid rgba(255,102,0,0.3);
        }
        .message.ai {
            background: rgba(255,255,255,0.05);
            align-self: flex-start;
            border: 1px solid #2a2a2a;
        }
        .message p {
            font-size: 13px;
            line-height: 1.5;
            color: #ddd;
        }
        .input-area {
            padding: 20px;
            border-top: 1px solid #2a2a2a;
        }
        textarea {
            width: 100%;
            background: #1a1a1a;
            border: 1px solid #333;
            border-radius: 16px;
            padding: 14px 16px;
            color: white;
            font-size: 14px;
            resize: none;
            font-family: inherit;
            outline: none;
        }
        textarea:focus {
            border-color: #ff6600;
        }
        .action-buttons {
            display: flex;
            flex-direction: column;
            gap: 12px;
            margin-top: 16px;
        }
        .btn-primary {
            background-color: #ffffff;
            color: #000000;
            padding: 12px;
            border-radius: 40px;
            font-size: 14px;
            font-weight: 600;
            border: none;
            cursor: pointer;
            width: 100%;
            transition: all 0.2s;
        }
        .btn-primary:hover {
            background-color: #ff6600;
            color: #ffffff;
        }
        .workspace {
            flex: 1;
            padding: 24px 32px;
            display: flex;
            flex-direction: column;
            overflow: hidden;
        }
        .workspace-header h2 {
            font-size: 20px;
            font-weight: 500;
            margin-bottom: 20px;
        }
        .workspace-content {
            flex: 1;
            border: 1px solid #333;
            border-radius: 16px;
            background: rgba(10,10,10,0.8);
            display: flex;
            align-items: center;
            justify-content: center;
            overflow: hidden;
        }
        .placeholder {
            text-align: center;
            color: #3a3a3a;
            font-size: 14px;
        }
        .result-content {
            width: 100%;
            height: 100%;
            padding: 24px;
            overflow-y: auto;
        }
        .result-text {
            color: #ddd;
            line-height: 1.6;
            font-size: 14px;
        }
        .result-image {
            max-width: 100%;
            max-height: 100%;
            object-fit: contain;
        }
        .back-link {
            position: fixed;
            bottom: 20px;
            left: 20px;
            background: rgba(0,0,0,0.7);
            padding: 8px 16px;
            border-radius: 20px;
            font-size: 12px;
            color: #888;
            text-decoration: none;
            z-index: 100;
        }
        .back-link:hover {
            color: #ff6600;
        }
        .modal {
            display: none;
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0,0,0,0.8);
            justify-content: center;
            align-items: center;
            z-index: 1000;
        }
        .modal-content {
            background: #1a1a1a;
            border: 1px solid #ff6600;
            border-radius: 16px;
            padding: 32px;
            max-width: 500px;
            width: 90%;
            text-align: center;
        }
        .modal-content h3 {
            color: #ff6600;
            margin-bottom: 16px;
        }
        .modal-content p {
            color: #ccc;
            line-height: 1.6;
            margin-bottom: 24px;
        }
        .modal-close {
            background: #ff6600;
            color: #000;
            border: none;
            padding: 10px 24px;
            border-radius: 8px;
            cursor: pointer;
        }
    </style>
</head>
<body>
<div class="stars" id="stars"></div>
<a href="/" class="back-link">← На главную</a>
<div class="content">
    <header class="header">
        <div class="logo">
            <div class="logo-icon"></div>
            <span class="logo-text">BIS</span>
        </div>
        <nav class="nav-menu">
            <a onclick="openModal('guide')">Руководство</a>
            <a href="/">Главная</a>
            <a onclick="openModal('feedback')">Обратная связь</a>
            <a onclick="openModal('news')">Новости</a>
        </nav>
        <div class="nav-right">
            <a onclick="openModal('account')">Аккаунты</a>
            <button class="btn-outline" onclick="openModal('install')">Установка</button>
            <a onclick="openModal('tariff')">Тарифы</a>
            <div class="lang-switch">
                <span class="active">Lvo</span>
                <span>Ru</span>
            </div>
        </div>
    </header>
    <div class="main-layout">
        <div class="left-panel">
            <div class="tabs">
                <button class="tab active" data-tab="text" onclick="switchTab('text')">Текст</button>
                <button class="tab" data-tab="image" onclick="switchTab('image')">Изображение</button>
            </div>
            <div class="chat-history" id="chatHistory">
                <div class="message ai">
                    <p>🤖 Привет! Я BIS AI. Напишите текст или задайте вопрос.</p>
                </div>
            </div>
            <div class="input-area">
                <textarea id="userInput" rows="3" placeholder="Напишите ваш запрос..."></textarea>
                <div class="action-buttons">
                    <button class="btn-primary" onclick="sendToAssistant()">📝 Написать ассистенту</button>
                    <button class="btn-outline" onclick="sendRequest()">🚀 Отправить запрос</button>
                </div>
            </div>
        </div>
        <div class="workspace">
            <div class="workspace-header">
                <h2>Рабочая зона</h2>
            </div>
            <div class="workspace-content" id="workspaceContent">
                <div class="placeholder">
                    <p>✨ Здесь будет результат</p>
                </div>
            </div>
        </div>
    </div>
</div>

<!-- Модальные окна -->
<div id="guideModal" class="modal">
    <div class="modal-content">
        <h3>📖 Руководство</h3>
        <p>BIS — платформа для создания контента с помощью AI. Выбирайте вкладку «Текст» или «Изображение», пишите запрос, и ассистент сгенерирует результат. Вкладка «Изображение» создаст визуал по вашему описанию.</p>
        <button class="modal-close" onclick="closeModal('guideModal')">Закрыть</button>
    </div>
</div>

<div id="feedbackModal" class="modal">
    <div class="modal-content">
        <h3>💬 Обратная связь</h3>
        <p>Почта: support@bis.ai<br>Telegram: @bis_support</p>
        <button class="modal-close" onclick="closeModal('feedbackModal')">Закрыть</button>
    </div>
</div>

<div id="newsModal" class="modal">
    <div class="modal-content">
        <h3>📰 Новости</h3>
        <p>🔹 01.04.2026 — Запуск BIS<br>🔹 15.04.2026 — Генерация изображений<br>🔹 01.05.2026 — Интеграция с VK</p>
        <button class="modal-close" onclick="closeModal('newsModal')">Закрыть</button>
    </div>
</div>

<div id="accountModal" class="modal">
    <div class="modal-content">
        <h3>👤 Аккаунт</h3>
        <p>Войдите, чтобы сохранять историю и настраивать профиль бренда.</p>
        <button class="modal-close" onclick="closeModal('accountModal')">Закрыть</button>
    </div>
</div>

<div id="tariffModal" class="modal">
    <div class="modal-content">
        <h3>💎 Тарифы</h3>
        <p>🔹 Бесплатный — 10 запросов/день<br>🔹 Базовый — 1 490 ₽/мес<br>🔹 Про — 3 490 ₽/мес<br>🔹 Бизнес — 7 990 ₽/мес</p>
        <button class="modal-close" onclick="closeModal('tariffModal')">Закрыть</button>
    </div>
</div>

<div id="installModal" class="modal">
    <div class="modal-content">
        <h3>📲 Установка</h3>
        <p>Скачайте приложение BIS для Windows, macOS или Android. Доступно в официальных магазинах.</p>
        <button class="modal-close" onclick="closeModal('installModal')">Закрыть</button>
    </div>
</div>

<script>
    function openModal(type) {
        const modalId = type + 'Modal';
        const modal = document.getElementById(modalId);
        if (modal) modal.style.display = 'flex';
    }
    function closeModal(modalId) {
        const modal = document.getElementById(modalId);
        if (modal) modal.style.display = 'none';
    }
    window.onclick = function(event) {
        if (event.target.classList.contains('modal')) {
            event.target.style.display = 'none';
        }
    }

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

    let currentTab = 'text';
    function switchTab(tab) {
        currentTab = tab;
        document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
        document.querySelector(`.tab[data-tab="${tab}"]`).classList.add('active');
        const textarea = document.getElementById('userInput');
        if (tab === 'text') {
            textarea.placeholder = 'Напишите ваш запрос или вопрос...';
        } else {
            textarea.placeholder = 'Опишите изображение, которое хотите создать...';
        }
    }

    function addMessage(text, type) {
        const history = document.getElementById('chatHistory');
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${type}`;
        messageDiv.innerHTML = `<p>${type === 'user' ? '👤 ' : '🤖 '}${text}</p>`;
        history.appendChild(messageDiv);
        history.scrollTop = history.scrollHeight;
    }

    function showResult(content, type) {
        const workspace = document.getElementById('workspaceContent');
        if (type === 'text') {
            workspace.innerHTML = `<div class="result-content"><div class="result-text">${content}</div></div>`;
        } else {
            workspace.innerHTML = `<div class="result-content" style="display: flex; align-items: center; justify-content: center;"><img src="${content}" class="result-image"></div>`;
        }
    }

    async function sendToAssistant() {
        const input = document.getElementById('userInput').value.trim();
        if (!input) {
            addMessage('Пожалуйста, напишите что-нибудь', 'ai');
            return;
        }
        addMessage(input, 'user');
        document.getElementById('userInput').value = '';
        addMessage('Думаю... 🤔', 'ai');
        setTimeout(() => {
            const messages = document.querySelectorAll('.message');
            messages[messages.length - 1].remove();
            if (currentTab === 'text') {
                const response = `Вот ответ на ваш запрос: "${input}"\\n\\nДемо-режим. В полной версии здесь будет ответ от AI.`;
                showResult(response, 'text');
                addMessage(response, 'ai');
            } else {
                const demoImage = 'https://placehold.co/800x400/1a1a1a/ff6600?text=BIS+Image';
                showResult(demoImage, 'image');
                addMessage(`Изображение по запросу: "${input}"`, 'ai');
            }
        }, 1000);
    }

    async function sendRequest() {
        await sendToAssistant();
    }
</script>
</body>
</html>
"""

@app.get("/", response_class=HTMLResponse)
async def landing():
    return HTMLResponse(content=LANDING_PAGE)

@app.get("/workspace", response_class=HTMLResponse)
async def workspace():
    return HTMLResponse(content=WORKSPACE_PAGE)

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8080)