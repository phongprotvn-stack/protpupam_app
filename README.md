# 🐮 PROT PUPAM — Bò Bụ Bẫm Video Analytics

> App phân tích video TikTok của **Bò Bụ Bẫm** (@bobubammm).  
> Tự động phát hiện video mới, AI phân tích trang phục, kiểu tóc, bối cảnh,... và hiển thị dashboard thống kê.

## 🏗️ Kiến trúc

```
TikTok @bobubammm
       │
GitHub Actions (cron 30 phút/lần)
       │
  yt-dlp → check video mới
       │
  Nếu có → download + FFmpeg extract frames
       │
  Gemini 2.5 Flash → phân tích AI
       │
  Firebase Firestore → lưu kết quả
       │
  React + Vite + Tailwind → Dashboard (Vercel)
```

## ✨ Chức năng

### Phase 1 (✅ Đã xong)
- [x] Tự động phát hiện video mới từ @bobubammm
- [x] AI phân tích: màu áo, kiểu tóc, bối cảnh (trong nhà/ngoài trời)
- [x] Dashboard thống kê với biểu đồ tròn, cột
- [x] Danh sách video kèm phân tích
- [x] Thông báo Telegram khi có video mới
- [x] Realtime cập nhật từ Firestore

### Phase 2 (Tương lai)
- [ ] Phân tích nhạc nền (buồn/vui/thể loại)
- [ ] Thống kê tương tác (màu áo nào nhiều view nhất?)
- [ ] AI Insight (xu hướng, gợi ý)
- [ ] Heatmap thời gian đăng video

## 🚀 Hướng dẫn Setup

### 1. Firebase Console

1. Vào [Firebase Console](https://console.firebase.google.com/) → **Tạo project**
2. **Firestore Database** → Tạo database (mode `test` hoặc `production`)
3. **Authentication** → Bật phương thức `Anonymous` (chỉ 1 mình bạn dùng)
4. **Project Settings → Web App** → Đăng ký app → Copy config

### 2. Cấu hình Frontend

Tạo file `.env` trong thư mục project:

```env
VITE_FIREBASE_API_KEY=AIz...
VITE_FIREBASE_AUTH_DOMAIN=xxx.firebaseapp.com
VITE_FIREBASE_PROJECT_ID=xxx
VITE_FIREBASE_STORAGE_BUCKET=xxx.appspot.com
VITE_FIREBASE_MESSAGING_SENDER_ID=123456
VITE_FIREBASE_APP_ID=1:123456:web:abc
```

Chạy local:

```bash
npm install
npm run dev
```

### 3. Deploy lên Vercel

```bash
npm i -g vercel
vercel --prod
```

Thêm các biến môi trường `VITE_FIREBASE_*` trong Vercel Dashboard → Project Settings → Environment Variables.

### 4. GitHub Actions (Backend tự động)

#### Lấy Gemini API Key (MIỄN PHÍ)

1. Vào [Google AI Studio](https://aistudio.google.com/apikey)
2. Click **Get API Key** → Tạo key mới
3. Copy key

#### Lấy Firebase Service Account

1. Firebase Console → **Project Settings → Service Accounts**
2. **Generate new private key** → Download file JSON
3. Copy **toàn bộ nội dung** file JSON

#### Lấy Telegram Bot Token (tùy chọn — cho notification)

1. Mở Telegram, tìm **@BotFather**
2. Gửi `/newbot` → Đặt tên → Copy token
3. Tìm **@userinfobot** → `/start` → Copy ID của bạn

#### Thêm Secrets vào GitHub

Vào GitHub repo của bạn → **Settings → Secrets and variables → Actions** → Thêm các secrets:

| Secret | Giá trị |
|--------|---------|
| `FIREBASE_SERVICE_ACCOUNT_JSON` | Toàn bộ nội dung file JSON từ Firebase |
| `GEMINI_API_KEY` | Key từ Google AI Studio |
| `TELEGRAM_BOT_TOKEN` | Token từ BotFather (optional) |
| `TELEGRAM_CHAT_ID` | ID Telegram của bạn (optional) |

Sau khi push code lên GitHub, workflow sẽ tự động chạy mỗi 30 phút. 🎉

## 📁 Cấu trúc thư mục

```
src/
├── components/
│   ├── BottomNav.jsx      # Navigation dưới
│   ├── StatCard.jsx       # Card thống kê
│   ├── VideoCard.jsx      # Card video
│   ├── PieChartWidget.jsx # Biểu đồ tròn
│   └── BarChartWidget.jsx # Biểu đồ cột
├── contexts/
│   └── AppContext.jsx     # State + Firestore listener
├── firebase/
│   └── firebase.js       # Firebase config
├── screens/
│   ├── Home.jsx           # Dashboard tổng quan
│   ├── Videos.jsx         # Danh sách video
│   └── Stats.jsx          # Thống kê chi tiết
├── App.jsx
├── index.css
└── main.jsx

.github/workflows/
└── check-tiktok.yml       # GitHub Actions workflow

scripts/
├── analyze.py             # Python script chính
└── requirements.txt       # Python dependencies
```

## 💰 Chi phí vận hành

| Thành phần | Giải pháp | Chi phí |
|-----------|-----------|---------|
| Frontend Hosting | Vercel Free | **$0** |
| Database | Firebase Spark Plan | **$0** |
| AI Analysis | Gemini 2.5 Flash (Free tier) | **$0** (1500 req/ngày) |
| Backend | GitHub Actions (cron) | **$0** (~48 phút/tháng) |
| Video check | yt-dlp | **$0** |
| Notification | Telegram Bot | **$0** |

**Tổng: $0/tháng** ✅

---

Made with ❤️ for Phong
