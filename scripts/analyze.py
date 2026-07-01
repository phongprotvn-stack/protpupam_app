"""
PROT PUPAM — TikTok Video Analyzer
Chạy trên GitHub Actions, kiểm tra video mới từ @bobubammm,
phân tích bằng Gemini 2.5 Flash, lưu vào Firestore.

Cách dùng local:
  pip install -r scripts/requirements.txt
  export $(cat .env | xargs)
  python scripts/analyze.py

Biến môi trường cần:
  - FIREBASE_SERVICE_ACCOUNT_JSON: service account key (JSON string)
  - GEMINI_API_KEY: Google AI Studio API key
  - TIKTOK_USERNAME: bobubammm (mặc định)
  - TELEGRAM_BOT_TOKEN (optional): cho notification
  - TELEGRAM_CHAT_ID (optional): chat ID nhận notification
"""

import os
import json
import subprocess
import tempfile
import shutil
import time
import sys
from pathlib import Path

# Global cache cho Firestore client
FIRESTORE_MODULE = None

# ─── Config ────────────────────────────────────────────────
TIKTOK_USERNAME = os.environ.get('TIKTOK_USERNAME', 'bobubammm')
PROFILE_URL = f'https://www.tiktok.com/@{TIKTOK_USERNAME}'
GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY', '')
FIREBASE_SA_JSON = os.environ.get('FIREBASE_SERVICE_ACCOUNT_JSON', '')
TELEGRAM_BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN', '')
TELEGRAM_CHAT_ID = os.environ.get('TELEGRAM_CHAT_ID', '')
MAX_VIDEOS_PER_RUN = int(os.environ.get('MAX_VIDEOS_PER_RUN', '3'))  # Tối đa phân tích mỗi lần chạy
MIN_INTERVAL_HOURS = int(os.environ.get('MIN_INTERVAL_HOURS', '1'))   # Chỉ phân tích video cũ hơn 1h (tránh video chưa có đủ metadata)

print(f"🔍 Target: {PROFILE_URL}")


# ─── 1. Init Firebase ──────────────────────────────────────
def init_firestore():
    """Khởi tạo Firestore client từ service account JSON."""
    global FIRESTORE_MODULE
    try:
        import firebase_admin
        from firebase_admin import credentials
        import firebase_admin.firestore as _fs
        FIRESTORE_MODULE = _fs
    except ImportError:
        print("❌ firebase-admin chưa cài. Chạy: pip install firebase-admin")
        sys.exit(1)

    if not FIREBASE_SA_JSON:
        print("⚠️  FIREBASE_SERVICE_ACCOUNT_JSON chưa set. Bỏ qua Firestore.")
        return None

    try:
        sa_dict = json.loads(FIREBASE_SA_JSON)
        cred = credentials.Certificate(sa_dict)
        firebase_admin.initialize_app(cred)
        db = firestore.client()
        print("✅ Firebase Firestore connected")
        return db
    except Exception as e:
        print(f"❌ Firebase init error: {e}")
        return None


# ─── 2. Check new videos via yt-dlp ───────────────────────
def check_ytdlp():
    """Dùng yt-dlp --flat-playlist --dump-json để lấy danh sách video."""
    print(f"\n📥 Đang check TikTok bằng yt-dlp...")

    # Kiểm tra yt-dlp có sẵn không
    if not shutil.which('yt-dlp') and not shutil.which('yt-dlp.exe'):
        print("⚠️  yt-dlp chưa cài. Thử cài qua pip...")
        subprocess.run([sys.executable, '-m', 'pip', 'install', '-q', 'yt-dlp'], check=False)
        if not shutil.which('yt-dlp') and not shutil.which('yt-dlp.exe'):
            print("❌ Không thể cài yt-dlp. Bỏ qua.")
            return []

    cmd = [
        'yt-dlp',
        '--flat-playlist',          # Chỉ lấy metadata, không download
        '--dump-json',              # Xuất JSON
        '--no-warnings',
        '--extractor-args', 'tiktok:api=web',  # Dùng web API
        '--playlist-end', '20',     # Lấy 20 video gần nhất
        PROFILE_URL,
    ]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        if result.returncode != 0:
            print(f"⚠️  yt-dlp stderr: {result.stderr[:500]}")
            # Thử lại với mobile API
            cmd[cmd.index('--extractor-args') + 1] = 'tiktok:api=app'
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)

        videos = []
        for line in result.stdout.strip().split('\n'):
            line = line.strip()
            if not line:
                continue
            try:
                v = json.loads(line)
                videos.append({
                    'id': v.get('id', ''),
                    'url': f"https://www.tiktok.com/@{TIKTOK_USERNAME}/video/{v.get('id', '')}",
                    'title': v.get('title', '') or v.get('description', '') or '',
                    'caption': v.get('description', '') or v.get('title', '') or '',
                    'thumbnail': v.get('thumbnail', ''),
                    'viewCount': v.get('view_count', 0),
                    'likeCount': v.get('like_count', 0),
                    'commentCount': v.get('comment_count', 0),
                    'duration': v.get('duration', 0),
                    'createdAt': v.get('timestamp', None),
                })
            except json.JSONDecodeError:
                continue

        print(f"✅ Tìm thấy {len(videos)} video từ yt-dlp")
        return videos
    except subprocess.TimeoutExpired:
        print("❌ yt-dlp timeout")
        return []
    except Exception as e:
        print(f"❌ yt-dlp error: {e}")
        return []


# ─── 3. So sánh với Firestore ─────────────────────────────
def find_new_videos(db, fetched_videos):
    """So sánh video từ yt-dlp với Firestore, trả về video mới."""
    if not db or not fetched_videos:
        return fetched_videos

    existing_ids = set()
    try:
        docs = db.collection('videos').where('source', '==', 'tiktok').stream()
        for doc in docs:
            data = doc.to_dict()
            # Chấp nhận cả 'id' và 'videoId'
            vid = data.get('videoId') or data.get('id') or doc.id
            existing_ids.add(str(vid))
    except Exception as e:
        print(f"⚠️  Lỗi đọc Firestore: {e}")
        return fetched_videos

    new_videos = [v for v in fetched_videos if v['id'] not in existing_ids]
    print(f"🆕 Video mới: {len(new_videos)} (trong {len(fetched_videos)} fetched)")
    return new_videos


# ─── 4. Download video + Extract frames ───────────────────
def download_and_extract(video_id, duration):
    """Download video từ TikTok, extract frames bằng FFmpeg.
    Trả về list đường dẫn ảnh và đường dẫn audio."""
    temp_dir = tempfile.mkdtemp(prefix='protpupam_')
    video_path = os.path.join(temp_dir, f'{video_id}.mp4')

    # Download
    print(f"  ⬇️  Downloading video {video_id}...")
    dl_cmd = [
        'yt-dlp',
        '-f', 'best[height<=720]',
        '-o', video_path,
        '--no-warnings',
        f'https://www.tiktok.com/@{TIKTOK_USERNAME}/video/{video_id}',
    ]
    try:
        subprocess.run(dl_cmd, capture_output=True, text=True, timeout=120)
        if not os.path.exists(video_path) or os.path.getsize(video_path) == 0:
            print(f"  ⚠️  Download thất bại hoặc file rỗng")
            shutil.rmtree(temp_dir, ignore_errors=True)
            return [], None, temp_dir
    except Exception as e:
        print(f"  ⚠️  Download error: {e}")
        shutil.rmtree(temp_dir, ignore_errors=True)
        return [], None, temp_dir

    # Extract frames (mỗi 3 giây)
    frames = []
    frame_dir = os.path.join(temp_dir, 'frames')
    os.makedirs(frame_dir, exist_ok=True)

    print(f"  🖼️  Extracting frames...")
    ffmpeg_cmd = [
        'ffmpeg', '-i', video_path,
        '-vf', 'fps=1/3',          # 1 frame mỗi 3 giây
        '-q:v', '2',
        '-y',
        os.path.join(frame_dir, 'frame_%03d.jpg'),
    ]
    try:
        subprocess.run(ffmpeg_cmd, capture_output=True, text=True, timeout=120)
        frames = sorted([os.path.join(frame_dir, f) for f in os.listdir(frame_dir)
                         if f.startswith('frame_') and f.endswith('.jpg')])
        print(f"  ✅ {len(frames)} frames extracted")
    except Exception as e:
        print(f"  ⚠️  FFmpeg error: {e}")

    # Extract audio
    audio_path = os.path.join(temp_dir, 'audio.mp3')
    audio_cmd = [
        'ffmpeg', '-i', video_path,
        '-q:a', '0', '-map', 'a',
        '-y', audio_path,
    ]
    try:
        subprocess.run(audio_cmd, capture_output=True, text=True, timeout=60)
        if not os.path.exists(audio_path) or os.path.getsize(audio_path) < 1000:
            audio_path = None
    except:
        audio_path = None

    return frames, audio_path, temp_dir


# ─── 5. Gemini Analysis ────────────────────────────────────
def analyze_with_gemini(frames, audio_path, duration):
    """Gửi frames lên Gemini 2.5 Flash để phân tích."""
    if not GEMINI_API_KEY:
        print("  ⚠️  GEMINI_API_KEY chưa set. Bỏ qua phân tích.")
        return None

    try:
        import google.generativeai as genai
    except ImportError:
        print("  ⚠️  google-generativeai chưa cài. Chạy: pip install google-generativeai")
        return None

    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel('models/gemini-2.5-flash-002')

    # Chuẩn bị prompt
    prompt = """You are analyzing a TikTok video from the creator "Bò Bụ Bẫm" (a Vietnamese female creator).
Analyze the video frames and return ONLY a JSON object (no markdown, no explanation) with these fields:

{
  "shirtColor": "color of shirt/dress worn (in Vietnamese, e.g. 'đỏ', 'đen', 'trắng', 'xanh', 'hồng', 'vàng', 'nâu', 'xám', 'tím', 'cam', 'be', 'nhiều màu', 'không rõ')",
  "shirtType": "type of top (in Vietnamese: 'áo thun', 'áo sơ mi', 'hoodie', 'áo len', 'croptop', 'váy', 'áo khoác', 'không rõ')",
  "sleeveLength": "in Vietnamese: 'dài', 'ngắn', 'sát nách', 'không rõ'",
  "hairStyle": "in Vietnamese: 'tóc ngắn', 'tóc dài', 'tóc xoăn', 'tóc thẳng', 'tóc buộc', 'tóc tết', 'tóc đuôi ngựa', 'tóc búi', 'đội mũ', 'không rõ'",
  "hairColor": "in Vietnamese: 'đen', 'nâu', 'nhuộm', 'highlight', 'không rõ'",
  "scene": "in Vietnamese: 'trong nhà', 'ngoài trời', 'trong xe', 'không rõ'",
  "location": "specific location if identifiable (in Vietnamese: 'phòng ngủ', 'phòng khách', 'quán cafe', 'nhà hàng', 'công viên', 'đường phố', 'biển', 'phòng gym', 'không rõ')",
  "emotion": "in Vietnamese: 'vui vẻ', 'cười', 'bình thường', 'buồn', 'ngạc nhiên', 'khóc', 'không rõ'",
  "musicMood": "music mood: 'vui', 'buồn', 'sôi động', 'nhẹ nhàng', 'lo-fi', 'không rõ'",
  "peopleCount": number of people visible (number),
  "hasPet": "yes or no",
  "petType": "if hasPet, type in Vietnamese: 'mèo', 'chó', 'khác', 'không có'",
  "indoorOutdoor": "in Vietnamese: 'trong nhà' or 'ngoài trời'",
  "timeOfDay": "in Vietnamese: 'sáng', 'trưa', 'chiều', 'tối', 'không rõ'",
  "movementLevel": "in Vietnamese: 'đứng yên', 'đi bộ', 'chạy', 'nhảy', 'ngồi', 'không rõ'",
  "cameraAngle": "in Vietnamese: 'selfie', 'tripod', 'camera sau', 'không rõ'",
  "dominantColor": "in Vietnamese: 'ấm', 'lạnh', 'vintage', 'pastel', 'tự nhiên', 'không rõ'",
  "hasGlasses": "yes or no",
  "hasMask": "yes or no",
  "hasHat": "yes or no",
  "hasHeadphones": "yes or no"
}

Analyze carefully based on ALL frames provided. If unsure about any field, use the Vietnamese phrase 'không rõ'."""

    # Upload frames
    content_parts = [prompt]

    # Giới hạn số frames gửi đi (tối đa 8 frame)
    selected_frames = frames
    if len(frames) > 8:
        step = len(frames) / 8
        selected_frames = [frames[int(i * step)] for i in range(8)]

    for frame_path in selected_frames:
        try:
            uploaded = genai.upload_file(frame_path)
            content_parts.append(uploaded)
        except Exception as e:
            print(f"  ⚠️  Upload frame error: {e}")

    print(f"  🤖 Đang phân tích với Gemini ({len(selected_frames)} frames)...")

    try:
        response = model.generate_content(content_parts, request_options={'timeout': 120})
        text = response.text.strip()

        # Clean response (remove markdown code blocks)
        if text.startswith('```'):
            text = text.split('\n', 1)[1] if '\n' in text else text
        if text.endswith('```'):
            text = text.rsplit('```', 1)[0]
        text = text.strip()
        if text.startswith('json'):
            text = text[4:].strip()

        analysis = json.loads(text)
        print(f"  ✅ Phân tích xong")
        return analysis
    except json.JSONDecodeError:
        print(f"  ⚠️  JSON parse error. Raw: {text[:300]}")
        return None
    except Exception as e:
        print(f"  ⚠️  Gemini error: {e}")
        return None


# ─── 6. Save to Firestore ──────────────────────────────────
def save_to_firestore(db, video_info, analysis):
    """Lưu kết quả phân tích vào Firestore."""
    global FIRESTORE_MODULE
    if not db:
        print("  ⚠️  No Firestore, skip save")
        return False

    doc_data = {
        'id': video_info['id'],
        'videoId': video_info['id'],
        'url': video_info['url'],
        'caption': video_info.get('caption', ''),
        'title': video_info.get('title', ''),
        'thumbnail': video_info.get('thumbnail', ''),
        'viewCount': video_info.get('viewCount', 0),
        'likeCount': video_info.get('likeCount', 0),
        'commentCount': video_info.get('commentCount', 0),
        'duration': video_info.get('duration', 0),
        'source': 'tiktok',
        'viewed': False,
        'createdAt': FIRESTORE_MODULE.SERVER_TIMESTAMP if FIRESTORE_MODULE else None,
        'fetchedAt': FIRESTORE_MODULE.SERVER_TIMESTAMP if FIRESTORE_MODULE else None,
    }

    if analysis:
        doc_data['analysis'] = analysis
        doc_data['analyzedAt'] = FIRESTORE_MODULE.SERVER_TIMESTAMP if FIRESTORE_MODULE else None

    try:
        db.collection('videos').document(video_info['id']).set(doc_data)
        print(f"  ✅ Saved to Firestore: {video_info['id']}")
        return True
    except Exception as e:
        print(f"  ❌ Firestore save error: {e}")
        return False


# ─── 7. Telegram Notification ──────────────────────────────
def send_telegram(message):
    """Gửi notification qua Telegram bot."""
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        return

    try:
        import requests
        url = f'https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage'
        data = {'chat_id': TELEGRAM_CHAT_ID, 'text': message, 'parse_mode': 'HTML'}
        resp = requests.post(url, data=data, timeout=10)
        if resp.status_code == 200:
            print("  ✅ Telegram sent")
        else:
            print(f"  ⚠️  Telegram error: {resp.status_code}")
    except Exception as e:
        print(f"  ⚠️  Telegram error: {e}")


# ─── Main ──────────────────────────────────────────────────
def main():
    db = init_firestore()

    # 1. Fetch videos from TikTok
    fetched = check_ytdlp()
    if not fetched:
        print("⚠️  Không lấy được video nào từ TikTok.")
        # Nếu có Firestore, chỉ cập nhật
        if db:
            print("✅ Firestore sẵn sàng, chờ lần chạy sau có dữ liệu mới.")
        return

    # 2. Find new ones
    new_videos = find_new_videos(db, fetched)

    if not new_videos:
        print("✅ Không có video mới.")
        return

    # 3. Process new videos (giới hạn số lượng)
    processed = 0
    for video in new_videos[:MAX_VIDEOS_PER_RUN]:
        print(f"\n{'='*50}")
        print(f"📹 Video: {video['id']} — {video.get('caption', '')[:80]}")

        # Download + extract frames
        duration = video.get('duration', 30)
        frames, audio_path, temp_dir = download_and_extract(video['id'], duration)

        # Analyze
        analysis = None
        if frames:
            analysis = analyze_with_gemini(frames, audio_path, duration)

        # Save
        save_to_firestore(db, video, analysis)

        # Notify
        if analysis:
            msg = (
                f"🔴 <b>Bò Bụ Bẫm vừa đăng video mới!</b>\n"
                f"👕 Áo: {analysis.get('shirtColor', 'không rõ')} | "
                f"💇 Tóc: {analysis.get('hairStyle', 'không rõ')}\n"
                f"📍 {analysis.get('scene', 'không rõ')} | "
                f"🎵 {analysis.get('musicMood', 'không rõ')}\n"
                f"📺 <a href=\"{video['url']}\">Xem video</a>"
            )
            send_telegram(msg)

        # Cleanup
        shutil.rmtree(temp_dir, ignore_errors=True)
        processed += 1

        # Delay giữa các video để tránh rate limit
        if processed < len(new_videos[:MAX_VIDEOS_PER_RUN]):
            time.sleep(5)

    print(f"\n✅ Done! Đã xử lý {processed} video mới.")


if __name__ == '__main__':
    main()
