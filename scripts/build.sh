#!/bin/bash
# Dùng PyInstaller đóng gói main.py thành file binary thực thi duy nhất,
# di chuyển file xuất ra vào assets/bin/.

# Đường dẫn đến thư mục chứa file spec và các file tạm thời
WORKPATH="./build"
# Đường dẫn thư mục chứa file binary sau khi build
DISTPATH="./dist"
# Tên của file thực thi (không có phần mở rộng trên Linux/macOS)
APP_NAME="lossless_videotool"

# Xóa các thư mục build cũ để tránh lỗi
rm -rf $WORKPATH
rm -rf $DISTPATH
rm -f "./${APP_NAME}.spec"

# Chạy PyInstaller
pyinstaller --onefile main.py --name $APP_NAME --distpath $DISTPATH --workpath $WORKPATH

# Kiểm tra xem build có thành công không
if [ -f "$DISTPATH/$APP_NAME" ]; then
  echo "PyInstaller build successful."
  # Di chuyển file binary vào assets/bin/
  mv "$DISTPATH/$APP_NAME" "assets/bin/"
  echo "Moved binary to assets/bin/"
else
  echo "PyInstaller build failed."
  exit 1
fi

# Xóa các file và thư mục tạm thời
rm -rf $WORKPATH
rm -rf $DISTPATH
rm -f "./${APP_NAME}.spec"

echo "Build process completed."
