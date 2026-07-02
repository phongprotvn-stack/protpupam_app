"""
PROT PUPAM — TikTok Video Analyzer
Chạy trên GitHub Actions, kiểm tra video mới từ @bobubammm,
phân tích bằng Gemini 2.5 Flash, lưu vào Firestore (REST API).

Cách dùng local:
  pip install -r scripts/requirements.txt
  export $(cat .env | xargs)
  python scripts/analyze.py

Biến môi trường cần:
  - FIREBASE_API_KEY: Firebase Web App API key (từ firebaseConfig)
  - FIREBASE_PROJECT_ID: Firebase project ID (mặc định: protpupam)
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
import urllib.request
import urllib.parse
import urllib.error
import datetime
from pathlib import Path

# ─── Config ────────────────────────────────────────────────
TIKTOK_USERNAME = os.environ.get('TIKTOK_USERNAME', 'bobubammm')
PROFILE_URL = f'https://www.tiktok.com/@{TIKTOK_USERNAME}'
GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY', '')
FIREBASE_API_KEY = os.environ.get('FIREBASE_API_KEY', '')
FIREBASE_PROJECT_ID = os.environ.get('FIREBASE_PROJECT_ID', 'protpupam')
TELEGRAM_BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN', '')
TELEGRAM_CHAT_ID = os.environ.get('TELEGRAM_CHAT_ID', '')
MAX_VIDEOS_PER_RUN = int(os.environ.get('MAX_VIDEOS_PER_RUN', '3'))
MIN_INTERVAL_HOURS = int(os.environ.get('MIN_INTERVAL_HOURS', '1'))

print(f"🔍 Target: {PROFILE_URL}")


# ─── 1. Init Firestore REST client ─────────────────────────
FIRESTORE_BASE_URL = None  # Set by init_firestore()

def init_firestore():
    """Init Firestore via REST API (no service account needed)."""
    global FIRESTORE_BASE_URL
    if not FIREBASE_API_KEY:
        print("⚠️  FIREBASE_API_KEY chưa set. Bỏ qua Firestore.")
        return None
    FIRESTORE_BASE_URL = (
        f"https://firestore.googleapis.com/v1/"
        f"projects/{FIREBASE_PROJECT_ID}/databases/(default)/documents"
    )
    print(f"✅ Firestore REST ready — project: {FIREBASE_PROJECT_ID}")
    return True


def _fs_list(collection):
    """GET documents from a collection."""
    url = f"{FIRESTORE_BASE_URL}/{collection}?key={FIREBASE_API_KEY}"
    try:
        req = urllib.request.Request(url, method='GET')
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read())
        return data.get('documents', [])
    except Exception as e:
        print(f"  ⚠️  Firestore list error: {e}")
        return []


def _fs_set(collection, doc_id, doc_dict):
    """Create/overwrite a document. Returns True on success."""
    fields = _to_fs_fields(doc_dict)
    body = {"fields": fields}
    url = (
        f"{FIRESTORE_BASE_URL}/{collection}"
        f"?documentId={doc_id}&key={FIREBASE_API_KEY}"
    )
    data = json.dumps(body).encode('utf-8')
    req = urllib.request.Request(
        url, data=data,
        headers={'Content-Type': 'application/json'},
        method='POST'
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            return True
    except urllib.error.HTTPError as e:
        body = e.read().decode()[:300]
        print(f"  ❌ Firestore POST error {e.code}: {body}")
        return False
    except Exception as e:
        print(f"  ❌ Firestore error: {e}")
        return False


def _to_fs_fields(d):
    """Convert Python dict to Firestore REST field format."""
    fields = {}
    for k, v in d.items():
        if v is None:
            fields[k] = {"nullValue": None}
        elif isinstance(v, bool):
            fields[k] = {"booleanValue": v}
        elif isinstance(v, int):
            fields[k] = {"integerValue": str(v)}
        elif isinstance(v, float):
            fields[k] = {"doubleValue": v}
        elif isinstance(v, dict):
            fields[k] = {"mapValue": {"fields": _to_fs_fields(v)}}
        elif isinstance(v, str):
            fields[k] = {"stringValue": v}
        else:
            fields[k] = {"stringValue": str(v)}
    return fields


def _fs_get_existing_ids(collection):
    """Return set of all document IDs (or videoId field values) in collection."""
    docs = _fs_list(collection)
    ids = set()
    for doc in docs:
        f = doc.get('fields', {})
        vid = f.get('videoId', {}).get('stringValue', '')
        did = f.get('id', {}).get('stringValue', '')
        ids.add(str(vid) if vid else str(did) if did else doc.get('name', '').split('/')[-1])
    return ids


# ─── 2. Check new videos via yt-dlp ───────────────────────
def check_ytdlp():
    """Dùng yt-dlp --flat-playlist --dump-json để lấy danh sách video."""
    print(f"\n📥 Đang check TikTok bằng yt-dlp...")

    if not shutil.which('yt-dlp') and not shutil.which('yt-dlp.exe'):
        print("⚠️  yt-dlp chưa cài. Thử cài qua pip...")
        subprocess.run([sys.executable, '-m', 'pip', 'install', '-q', 'yt-dlp'], check=False)
        if not shutil.which('yt-dlp') and not shutil.which('yt-dlp.exe'):
            print("❌ Không thể cài yt-dlp. Bỏ qua.")
            return []

    cmd = [
        'yt-dlp',
        '--flat-playlist',
        '--dump-json',
        '--no-warnings',
        '--extractor-args', 'tiktok:api=web',
        '--playlist-end', '20',
        PROFILE_URL,
    ]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        if result.returncode != 0:
            print(f"⚠️  yt-dlp stderr: {result.stderr[:500]}")
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

    existing_ids = _fs_get_existing_ids('videos')
    new_videos = [v for v in fetched_videos if v['id'] not in existing_ids]
    print(f"🆕 Video mới: {len(new_videos)} (trong {len(fetched_videos)} fetched)")
    return new_videos


# ─── 4. Download video + Extract frames ───────────────────
def download_and_extract(video_id, duration):
    """Download video từ TikTok, extract frames bằng FFmpeg.
    Trả về list đường dẫn ảnh và đường dẫn audio."""
    temp_dir = tempfile.mkdtemp(prefix='protpupam_')
    video_path = os.path.join(temp_dir, f'{video_id}.mp4')

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
        '-vf', 'fps=1/3',
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
  "peopleCount": "number of people visible (number as string)",
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

    content_parts = [prompt]

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

        # Clean response
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


# ─── 6. Save to Firestore (REST) ──────────────────────────────
def save_to_firestore(db, video_info, analysis):
    """Lưu kết quả phân tích vào Firestore qua REST API."""
    if not db:
        print("  ⚠️  No Firestore, skip save")
        return False

    now = datetime.datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')

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
        'createdAt': now,
        'fetchedAt': now,
    }

    if analysis:
        doc_data['analysis'] = analysis
        doc_data['analyzedAt'] = now

    ok = _fs_set('videos', video_info['id'], doc_data)
    if ok:
        print(f"  ✅ Saved to Firestore: {video_info['id']}")
    return ok


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

        duration = video.get('duration', 30)
        frames, audio_path, temp_dir = download_and_extract(video['id'], duration)

        analysis = None
        if frames:
            analysis = analyze_with_gemini(frames, audio_path, duration)

        save_to_firestore(db, video, analysis)

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

        shutil.rmtree(temp_dir, ignore_errors=True)
        processed += 1

        if processed < len(new_videos[:MAX_VIDEOS_PER_RUN]):
            time.sleep(5)

    print(f"\n✅ Done! Đã xử lý {processed} video mới.")


if __name__ == '__main__':
    main()
