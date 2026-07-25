from PIL import Image
import os

src = r'D:\CODE\Database\protpupam_icon.png'
pub = r'D:\CODE\P_projects\protpupam_app\public'

img = Image.open(src)

# Create output dirs
os.makedirs(pub, exist_ok=True)

# 1. PWA icons
sizes = {
    'pwa-192x192.png': 192,
    'pwa-512x512.png': 512,
}
for name, size in sizes.items():
    resized = img.resize((size, size), Image.LANCZOS)
    path = os.path.join(pub, name)
    resized.save(path, 'PNG')
    print(f'✅ {name} ({size}x{size})')

# 2. Favicon (ico)
# Create multiple sizes for favicon
favicon_sizes = [16, 32, 48, 64, 128, 256]
icons = []
for s in favicon_sizes:
    rsz = img.resize((s, s), Image.LANCZOS)
    icons.append(rsz)

favicon_path = os.path.join(pub, 'favicon.ico')
icons[0].save(favicon_path, format='ICO', sizes=[(s, s) for s in favicon_sizes])
print(f'✅ favicon.ico (multi-size: {favicon_sizes})')

# 3. apple-touch-icon
apple = img.resize((180, 180), Image.LANCZOS)
apple_path = os.path.join(pub, 'apple-touch-icon.png')
apple.save(apple_path, 'PNG')
print(f'✅ apple-touch-icon.png (180x180)')

print('\n🎉 All icons created!')
