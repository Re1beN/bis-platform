from fastapi import FastAPI, Request, Response, Cookie
from fastapi.responses import HTMLResponse, JSONResponse
import uvicorn
import requests
import uuid
import json
import os
from datetime import datetime
from dotenv import load_dotenv

from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime
from sqlalchemy.orm import declarative_base, sessionmaker

load_dotenv()

app = FastAPI(title="БИС Platform")

# ========== КЛЮЧИ ==========
GIGACHAT_AUTH_KEY = "MDE5ZDMzYzItNGY5NS03MGY4LThjOTktYzk5ZDIyMzYyZTk3OmI5OWRhMTVjLTNmMGQtNDFlOS04Yjc3LTdhMWQ2YzU5NzBiNg=="
PEXELS_API_KEY = "99lzySAP7wyWqzFaBGPQQbcJWPwXZVaR6H6KbILjvJ5Au6iV6YnrxXM5"
UNSPLASH_API_KEY = "NpF_z6xsa39ov1PS4Bq_AqIoabRJphW1s30RvnOGCMY"
gigachat_access_token = None

# ========== DATABASE ==========
DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///./bis_local.db")

# SQLAlchemy requires postgresql:// scheme; Railway provides postgres://
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class UserProfile(Base):
    __tablename__ = "user_profiles"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String(64), unique=True, index=True, nullable=False)
    niche = Column(String(256), default="")
    tone = Column(String(256), default="")
    city = Column(String(128), default="")
    goal = Column(String(64), default="expert")
    vk_token = Column(Text, default="")
    group_id = Column(String(64), default="")


class Post(Base):
    __tablename__ = "posts"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String(64), index=True, nullable=False)
    text = Column(Text, nullable=False)
    image_url = Column(Text, default="")
    created_at = Column(DateTime, default=datetime.utcnow)


# Create tables on startup
Base.metadata.create_all(bind=engine)


def _get_user_id(request: Request) -> str:
    """Return the session user_id from cookie, creating one if absent."""
    user_id = request.cookies.get("bis_user_id")
    if not user_id:
        user_id = str(uuid.uuid4())
    return user_id


def _db_get_profile(db, user_id: str) -> dict:
    profile = db.query(UserProfile).filter(UserProfile.user_id == user_id).first()
    if not profile:
        return {}
    return {
        "niche": profile.niche,
        "tone": profile.tone,
        "city": profile.city,
        "goal": profile.goal,
        "vk_token": profile.vk_token,
        "group_id": profile.group_id,
    }


def _db_save_profile(db, user_id: str, data: dict):
    profile = db.query(UserProfile).filter(UserProfile.user_id == user_id).first()
    if not profile:
        profile = UserProfile(user_id=user_id)
        db.add(profile)
    profile.niche = data.get("niche", "")
    profile.tone = data.get("tone", "")
    profile.city = data.get("city", "")
    profile.goal = data.get("goal", "expert")
    profile.vk_token = data.get("vk_token", "")
    profile.group_id = data.get("group_id", "")
    db.commit()


def _db_get_posts(db, user_id: str) -> list:
    posts = db.query(Post).filter(Post.user_id == user_id).order_by(Post.created_at).all()
    return [
        {
            "id": p.id,
            "text": p.text,
            "image_url": p.image_url or "",
            "date": p.created_at.strftime("%Y-%m-%d %H:%M") if p.created_at else "",
        }
        for p in posts
    ]


def _db_add_post(db, user_id: str, text: str, image_url: str, date_str: str = None):
    created_at = datetime.utcnow()
    if date_str:
        try:
            created_at = datetime.strptime(date_str, "%Y-%m-%d %H:%M")
        except Exception:
            pass
    post = Post(user_id=user_id, text=text, image_url=image_url or "", created_at=created_at)
    db.add(post)
    db.commit()
    db.refresh(post)
    return post


def _db_get_post_by_index(db, user_id: str, index: int):
    posts = db.query(Post).filter(Post.user_id == user_id).order_by(Post.created_at).all()
    if index < 0 or index >= len(posts):
        return None
    return posts[index]


def _db_delete_post_by_index(db, user_id: str, index: int) -> bool:
    posts = db.query(Post).filter(Post.user_id == user_id).order_by(Post.created_at).all()
    if index < 0 or index >= len(posts):
        return False
    db.delete(posts[index])
    db.commit()
    return True


# ========== MIGRATE LEGACY JSON ==========
USER_DATA_FILE = "user_data.json"


def _migrate_json_to_db():
    """One-time migration: import user_data.json into the DB under a legacy user_id."""
    if not os.path.exists(USER_DATA_FILE):
        return
    try:
        with open(USER_DATA_FILE, "r", encoding="utf-8") as f:
            legacy = json.load(f)
    except Exception:
        return
    if not legacy:
        return
    legacy_user_id = "legacy_migration_user"
    db = SessionLocal()
    try:
        existing = db.query(UserProfile).filter(UserProfile.user_id == legacy_user_id).first()
        if existing:
            return  # already migrated
        profile_data = legacy.get("profile", {})
        if profile_data:
            _db_save_profile(db, legacy_user_id, profile_data)
        for post in legacy.get("posts", []):
            _db_add_post(db, legacy_user_id, post.get("text", ""), post.get("image_url", ""), post.get("date"))
        os.rename(USER_DATA_FILE, USER_DATA_FILE + ".migrated")
    except Exception as e:
        print(f"Migration error: {e}")
    finally:
        db.close()


_migrate_json_to_db()


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


# ========== ПОИСК ФОТО ==========
def search_image(query):
    try:
        r = requests.get(
            f"https://api.unsplash.com/search/photos?query={query}&per_page=1&client_id={UNSPLASH_API_KEY}", timeout=10)
        if r.status_code == 200 and r.json().get('results'):
            return r.json()['results'][0]['urls']['regular']
    except:
        pass
    try:
        r = requests.get(f"https://api.pexels.com/v1/search?query={query}&per_page=1",
                         headers={"Authorization": PEXELS_API_KEY}, timeout=10)
        if r.status_code == 200 and r.json().get('photos'):
            return r.json()['photos'][0]['src']['medium']
    except:
        pass
    return None


# ========== АВТОПОСТИНГ В VK ==========
def publish_to_vk_wall(text, image_url, vk_token, group_id):
    if not vk_token:
        return "❌ VK токен не указан. Добавьте его в настройках аккаунта."

    params = {
        "owner_id": -int(group_id),
        "message": text,
        "access_token": vk_token,
        "v": "5.199"
    }

    if image_url:
        try:
            img_data = requests.get(image_url, timeout=30).content
            upload_server_resp = requests.get("https://api.vk.com/method/photos.getWallUploadServer",
                                              params={"group_id": group_id, "access_token": vk_token,
                                                      "v": "5.199"}).json()
            if "response" in upload_server_resp:
                upload_url = upload_server_resp["response"]["upload_url"]
                files = {"photo": ("image.jpg", img_data, "image/jpeg")}
                upload_result = requests.post(upload_url, files=files).json()
                save_params = {
                    "group_id": group_id,
                    "photo": upload_result["photo"],
                    "server": upload_result["server"],
                    "hash": upload_result["hash"],
                    "access_token": vk_token,
                    "v": "5.199"
                }
                save_resp = requests.get("https://api.vk.com/method/photos.saveWallPhoto", params=save_params).json()
                if "response" in save_resp:
                    photo = save_resp["response"][0]
                    params["attachments"] = f"photo{photo['owner_id']}_{photo['id']}"
        except Exception as e:
            print(f"Ошибка загрузки фото: {e}")

    try:
        response = requests.post("https://api.vk.com/method/wall.post", data=params)
        result = response.json()
        if "error" in result:
            return f"❌ Ошибка VK: {result['error']['error_msg']}"
        return f"✅ Пост опубликован! ID: {result['response']['post_id']}"
    except Exception as e:
        return f"❌ Ошибка: {str(e)}"


# ========== HTML СТРАНИЦЫ ==========
COMMON_STYLES = """
<style>
    * { margin: 0; padding: 0; box-sizing: border-box; }
    body {
        font-family: 'Inter', 'Montserrat', sans-serif;
        background: radial-gradient(ellipse at center, #0a0a0a 0%, #000000 100%);
        color: #fff;
        min-height: 100vh;
    }
    .stars { position: fixed; top: 0; left: 0; width: 100%; height: 100%; pointer-events: none; z-index: 0; }
    .star { position: absolute; background-color: #fff; border-radius: 50%; opacity: 0; animation: twinkle 3s infinite; }
    @keyframes twinkle { 0%, 100% { opacity: 0; } 50% { opacity: 0.8; } }
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
    .logo { display: flex; align-items: center; gap: 12px; }
    .logo-icon { width: 36px; height: 36px; background: linear-gradient(135deg, #ff6600, #ffaa00); border-radius: 50%; box-shadow: 0 0 15px #ff6600; }
    .logo-text { font-size: 20px; font-weight: 700; background: linear-gradient(135deg, #ff6600, #ffaa00); -webkit-background-clip: text; background-clip: text; color: transparent; }
    .nav-menu { display: flex; gap: 32px; }
    .nav-menu a { color: #fff; text-decoration: none; font-size: 14px; opacity: 0.8; transition: 0.3s; }
    .nav-menu a:hover { opacity: 1; color: #ff6600; }
    .nav-right { display: flex; gap: 24px; align-items: center; }
    .lang-switch { display: flex; gap: 6px; background: rgba(26,26,26,0.8); padding: 4px 8px; border-radius: 20px; }
    .lang-switch span { cursor: pointer; font-size: 12px; color: #888; }
    .lang-switch span.active { color: #ff6600; }
    .main-container { flex: 1; padding: 40px 48px; }
    h1 { font-size: 32px; font-weight: 700; margin-bottom: 30px; background: linear-gradient(135deg, #fff, #ffaa00); -webkit-background-clip: text; background-clip: text; color: transparent; }
    h2 { font-size: 22px; font-weight: 600; margin-bottom: 20px; color: #ffaa00; }
    .card { background: rgba(20,20,30,0.7); backdrop-filter: blur(10px); border-radius: 20px; padding: 24px; margin-bottom: 24px; border: 1px solid rgba(255,102,0,0.2); }
    .btn-primary { background: linear-gradient(135deg, #ff6600, #ffaa00); color: #000; padding: 12px 28px; border-radius: 30px; font-size: 14px; font-weight: 600; border: none; cursor: pointer; transition: 0.3s; }
    .btn-primary:hover { transform: scale(1.02); box-shadow: 0 0 20px rgba(255,102,0,0.5); }
    .btn-secondary { background: transparent; border: 1px solid #ff6600; color: #ff6600; padding: 10px 24px; border-radius: 30px; cursor: pointer; transition: 0.3s; }
    .btn-secondary:hover { background: rgba(255,102,0,0.2); }
    .footer { text-align: center; padding: 30px; border-top: 1px solid #222; font-size: 12px; color: #666; }
    .workspace-layout { display: flex; gap: 30px; }
    .left-panel, .right-panel { background: rgba(20,20,30,0.7); backdrop-filter: blur(10px); border-radius: 20px; padding: 24px; border: 1px solid rgba(255,102,0,0.2); }
    .left-panel { flex: 1; }
    .right-panel { flex: 1.5; }
    .format-buttons { display: flex; gap: 15px; margin: 20px 0; }
    .format-btn { background: rgba(50,50,60,0.5); border: 1px solid #444; border-radius: 30px; padding: 10px 24px; cursor: pointer; color: #fff; }
    .format-btn.active { background: #ff6600; border-color: #ff6600; color: #000; }
    .result-area { background: rgba(0,0,0,0.5); border-radius: 16px; padding: 20px; margin-top: 20px; border: 1px solid #333; min-height: 300px; }
    .checkbox-group { display: flex; gap: 20px; margin: 15px 0; flex-wrap: wrap; }
    .checkbox-group label { display: flex; align-items: center; gap: 8px; color: #ddd; }
    textarea { width: 100%; background: rgba(30,30,40,0.8); border: 1px solid #333; border-radius: 12px; padding: 12px; color: #fff; margin: 15px 0; }
    .workspace-nav { display: flex; gap: 20px; margin-bottom: 25px; border-bottom: 1px solid #333; padding-bottom: 15px; }
    .workspace-nav a { color: #aaa; text-decoration: none; padding: 8px 16px; border-radius: 20px; cursor: pointer; }
    .workspace-nav a:hover, .workspace-nav a.active { background: rgba(255,102,0,0.2); color: #ff6600; }
    .form-group { margin-bottom: 15px; }
    .form-group label { display: block; margin-bottom: 5px; color: #ffaa00; font-size: 14px; }
    .form-group input, .form-group select { width: 100%; padding: 10px; background: rgba(30,30,40,0.8); border: 1px solid #333; border-radius: 8px; color: #fff; }
    .post-item {
        background: rgba(30,30,40,0.5);
        border-radius: 12px;
        padding: 15px;
        margin-bottom: 15px;
        border: 1px solid #444;
    }
    .post-text { color: #ddd; margin-bottom: 10px; font-size: 14px; }
    .post-actions { display: flex; gap: 10px; }
    .post-actions button { padding: 5px 12px; font-size: 12px; }
    .empty-plan { text-align: center; padding: 40px; color: #888; }
</style>
"""

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
                        <button class="btn-secondary" onclick="generateImage()">🎨 Найти изображение</button>
                        <button class="btn-secondary" onclick="addToPlan()">📅 Добавить в контент-план</button>
                    </div>
                    <div id="imageResult" class="result-area" style="display:none; margin-top:20px;"></div>
                </div>
                <div class="right-panel">
                    <h2>Результат</h2>
                    <div class="result-area" id="resultContent"><p id="resultText" style="color:#aaa;">Здесь появится результат...</p></div>
                    <div style="display:flex;gap:15px;margin-top:20px;">
                        <button class="btn-secondary" onclick="regenerate()">🔄 Другой вариант</button>
                    </div>
                </div>
            </div>
        </div>
        <div id="plan-section" style="display:none;">
            <div class="card">
                <h2>📅 Контент-план</h2>
                <div id="postsList"></div>
            </div>
        </div>
        <div id="analytics-section" style="display:none;"><div class="card" style="text-align:center;"><h2>📊 Аналитика</h2><p style="margin:20px 0;">Здесь будут метрики и AI-гипотезы</p><button class="btn-secondary" onclick="switchSection('studio')">Вернуться</button></div></div>
        <div id="settings-section" style="display:none;">
            <div class="card"><h2>⚙️ Настройки аккаунта</h2>
            <form id="profileForm">
                <div class="form-group"><label>🏢 Ниша</label><input type="text" id="niche" placeholder="туризм по Томску"></div>
                <div class="form-group"><label>🎭 Тональность</label><input type="text" id="tone" placeholder="вдохновляющий и экспертный"></div>
                <div class="form-group"><label>🏙️ Город</label><input type="text" id="city" placeholder="Томск"></div>
                <div class="form-group"><label>🎯 Цель бренда</label><select id="goal"><option value="expert">🎓 Эксперт</option><option value="influencer">⭐ Лидер мнений</option><option value="sales">💰 Продажи</option></select></div>
                <div class="form-group"><label>🔑 VK Access Token (права wall)</label><input type="text" id="vk_token" placeholder="vk1.a.xxxx... получите на vkhost.github.io"></div>
                <div class="form-group"><label>📱 ID группы VK</label><input type="text" id="group_id" placeholder="237128228"></div>
                <button type="button" class="btn-primary" onclick="saveProfile()">💾 Сохранить настройки</button>
                <button type="button" class="btn-secondary" onclick="loadProfile()">🔄 Загрузить настройки</button>
            </form>
            <div id="profileStatus" style="margin-top:20px;color:#ffaa00;"></div>
            </div>
        </div>
    </div>
    <div class="footer"><p>© 2026 БИС — Бренд. Имидж. Стратегия.</p></div>
</div>
<script>
    let currentFormat = 'post', currentText = '', currentImageUrl = '';
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
        if(!topic){alert('Введите тему');return;}
        let imageDiv=document.getElementById('imageResult');
        imageDiv.style.display='block';
        imageDiv.innerHTML='🎨 Поиск...';
        try{
            let resp=await fetch(`/api/generate-image?prompt=${encodeURIComponent(topic)}`);
            if(resp.status==404){imageDiv.innerHTML='❌ Не найдено';return;}
            let data=await resp.json();
            currentImageUrl=data.url;
            imageDiv.innerHTML=`<img src="${data.url}" style="max-width:100%;border-radius:12px;">`;
        }catch(e){imageDiv.innerHTML='❌ Ошибка';}
    }
    async function addToPlan(){
        if(!currentText){alert('Сначала сгенерируйте пост');return;}
        let postData = {
            text: currentText,
            image_url: currentImageUrl,
            date: new Date().toLocaleString()
        };
        let resp=await fetch('/api/add-to-plan',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(postData)});
        let data=await resp.json();
        alert(data.message);
        if(switchSection) loadPosts();
    }
    async function loadPosts(){
        let resp=await fetch('/api/get-posts');
        let posts=await resp.json();
        let container=document.getElementById('postsList');
        if(!posts.length){
            container.innerHTML='<div class="empty-plan">📭 Нет добавленных постов. Создайте пост в Контент-студии и нажмите "Добавить в контент-план"</div>';
            return;
        }
        container.innerHTML=posts.map((p,i)=>`
            <div class="post-item">
                <div class="post-text">${p.text.substring(0,300)}${p.text.length>300?'...':''}</div>
                ${p.image_url ? `<img src="${p.image_url}" style="max-width:100%;border-radius:12px;margin-bottom:10px;">` : ''}
                <div class="post-actions">
                    <button class="btn-secondary" onclick="publishPost(${i})">📤 Опубликовать</button>
                    <button class="btn-secondary" onclick="deletePost(${i})">🗑️ Удалить</button>
                </div>
            </div>
        `).join('');
    }
    async function publishPost(index){
        let vk_token=document.getElementById('vk_token').value;
        let group_id=document.getElementById('group_id').value;
        if(!vk_token || !group_id){
            alert('❌ Сначала укажите VK токен и ID группы в настройках аккаунта');
            return;
        }
        let resp=await fetch('/api/publish-post-from-plan',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({index:index, vk_token:vk_token, group_id:group_id})});
        let data=await resp.json();
        alert(data.message);
        if(data.success) loadPosts();
    }
    async function deletePost(index){
        if(confirm('Удалить пост из контент-плана?')){
            let resp=await fetch('/api/delete-post',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({index:index})});
            let data=await resp.json();
            alert(data.message);
            loadPosts();
        }
    }
    async function publishToVK(){
        if(!currentText){alert('Сначала сгенерируйте пост');return;}
        let vk_token=document.getElementById('vk_token').value;
        let group_id=document.getElementById('group_id').value;
        if(!vk_token || !group_id){
            alert('❌ Сначала укажите VK токен и ID группы в настройках аккаунта');
            return;
        }
        let btn=event.target;
        btn.innerText='⏳ Публикация...';
        btn.disabled=true;
        let resp=await fetch('/api/publish-to-vk',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({text:currentText, image_url:currentImageUrl, vk_token:vk_token, group_id:group_id})});
        let data=await resp.json();
        alert(data.message);
        btn.innerText='📤 Опубликовать в VK';
        btn.disabled=false;
    }
    function regenerate(){generatePost();}
    function switchSection(s){
        document.getElementById('studio-section').style.display='none';
        document.getElementById('plan-section').style.display='none';
        document.getElementById('analytics-section').style.display='none';
        document.getElementById('settings-section').style.display='none';
        if(s==='studio') document.getElementById('studio-section').style.display='block';
        else if(s==='plan'){
            document.getElementById('plan-section').style.display='block';
            loadPosts();
        }
        else if(s==='analytics') document.getElementById('analytics-section').style.display='block';
        else if(s==='settings') document.getElementById('settings-section').style.display='block';
        document.querySelectorAll('.workspace-nav a').forEach(l=>l.classList.remove('active'));
        event.target.classList.add('active');
        if(s==='settings') loadProfile();
    }
    async function saveProfile(){
        let profile={niche:document.getElementById('niche').value,tone:document.getElementById('tone').value,city:document.getElementById('city').value,goal:document.getElementById('goal').value,vk_token:document.getElementById('vk_token').value,group_id:document.getElementById('group_id').value};
        let resp=await fetch('/api/save-profile',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(profile)});
        let data=await resp.json();
        document.getElementById('profileStatus').innerHTML=data.message;
        setTimeout(()=>document.getElementById('profileStatus').innerHTML='',3000);
    }
    async function loadProfile(){
        let resp=await fetch('/api/get-profile');
        let profile=await resp.json();
        document.getElementById('niche').value=profile.niche||'';
        document.getElementById('tone').value=profile.tone||'';
        document.getElementById('city').value=profile.city||'';
        document.getElementById('goal').value=profile.goal||'expert';
        document.getElementById('vk_token').value=profile.vk_token||'';
        document.getElementById('group_id').value=profile.group_id||'';
        document.getElementById('profileStatus').innerHTML='✅ Настройки загружены';
        setTimeout(()=>document.getElementById('profileStatus').innerHTML='',2000);
    }
</script>
</body>
</html>
"""

from pydantic import BaseModel
from typing import Optional


class GenerateRequest(BaseModel):
    prompt: str


class PublishRequest(BaseModel):
    text: str
    image_url: Optional[str] = None
    vk_token: Optional[str] = None
    group_id: Optional[str] = None


class AddPostRequest(BaseModel):
    text: str
    image_url: Optional[str] = None
    date: Optional[str] = None


class PublishFromPlanRequest(BaseModel):
    index: int
    vk_token: str
    group_id: str


class DeletePostRequest(BaseModel):
    index: int


# ========== API ENDPOINTS ==========

@app.post("/api/generate")
async def generate(req: GenerateRequest, request: Request, response: Response):
    user_id = _get_user_id(request)
    response.set_cookie(key="bis_user_id", value=user_id, max_age=60 * 60 * 24 * 365, httponly=True, samesite="lax")
    db = SessionLocal()
    try:
        profile = _db_get_profile(db, user_id)
    finally:
        db.close()
    result = call_gigachat(req.prompt, profile)
    return JSONResponse(content={"result": result})


@app.get("/api/generate-image")
async def generate_image(prompt: str):
    url = search_image(prompt)
    if not url:
        return JSONResponse(content={"error": "Не найдено"}, status_code=404)
    return JSONResponse(content={"url": url})


@app.post("/api/add-to-plan")
async def add_to_plan(req: AddPostRequest, request: Request, response: Response):
    user_id = _get_user_id(request)
    response.set_cookie(key="bis_user_id", value=user_id, max_age=60 * 60 * 24 * 365, httponly=True, samesite="lax")
    db = SessionLocal()
    try:
        _db_add_post(db, user_id, req.text, req.image_url or "", req.date)
    finally:
        db.close()
    return JSONResponse(content={"message": "✅ Пост добавлен в контент-план!"})


@app.get("/api/get-posts")
async def get_posts(request: Request, response: Response):
    user_id = _get_user_id(request)
    response.set_cookie(key="bis_user_id", value=user_id, max_age=60 * 60 * 24 * 365, httponly=True, samesite="lax")
    db = SessionLocal()
    try:
        posts = _db_get_posts(db, user_id)
    finally:
        db.close()
    return JSONResponse(content=posts)


@app.post("/api/publish-post-from-plan")
async def publish_post_from_plan(req: PublishFromPlanRequest, request: Request, response: Response):
    user_id = _get_user_id(request)
    response.set_cookie(key="bis_user_id", value=user_id, max_age=60 * 60 * 24 * 365, httponly=True, samesite="lax")
    db = SessionLocal()
    try:
        post = _db_get_post_by_index(db, user_id, req.index)
        if not post:
            return JSONResponse(content={"message": "❌ Пост не найден", "success": False})
        result = publish_to_vk_wall(post.text, post.image_url, req.vk_token, req.group_id)
        if "✅" in result:
            db.delete(post)
            db.commit()
            return JSONResponse(content={"message": result, "success": True})
        return JSONResponse(content={"message": result, "success": False})
    finally:
        db.close()


@app.post("/api/delete-post")
async def delete_post(req: DeletePostRequest, request: Request, response: Response):
    user_id = _get_user_id(request)
    response.set_cookie(key="bis_user_id", value=user_id, max_age=60 * 60 * 24 * 365, httponly=True, samesite="lax")
    db = SessionLocal()
    try:
        deleted = _db_delete_post_by_index(db, user_id, req.index)
    finally:
        db.close()
    if deleted:
        return JSONResponse(content={"message": "✅ Пост удалён"})
    return JSONResponse(content={"message": "❌ Пост не найден"})


@app.post("/api/publish-to-vk")
async def publish_to_vk(req: PublishRequest):
    if not req.vk_token:
        return JSONResponse(content={"message": "❌ VK токен не указан. Добавьте его в настройках аккаунта."})
    if not req.group_id:
        return JSONResponse(content={"message": "❌ ID группы не указан. Добавьте его в настройках аккаунта."})
    result = publish_to_vk_wall(req.text, req.image_url, req.vk_token, req.group_id)
    return JSONResponse(content={"message": result})


@app.post("/api/save-profile")
async def save_profile(request: Request, response: Response):
    user_id = _get_user_id(request)
    response.set_cookie(key="bis_user_id", value=user_id, max_age=60 * 60 * 24 * 365, httponly=True, samesite="lax")
    data = await request.json()
    db = SessionLocal()
    try:
        _db_save_profile(db, user_id, data)
    finally:
        db.close()
    return JSONResponse(content={"message": "✅ Настройки сохранены!"})


@app.get("/api/get-profile")
async def get_profile(request: Request, response: Response):
    user_id = _get_user_id(request)
    response.set_cookie(key="bis_user_id", value=user_id, max_age=60 * 60 * 24 * 365, httponly=True, samesite="lax")
    db = SessionLocal()
    try:
        profile = _db_get_profile(db, user_id)
    finally:
        db.close()
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
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
