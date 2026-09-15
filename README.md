# Mini-Netflix

> Đồ án môn Cơ sở dữ liệu – Hệ thống phát video theo yêu cầu (*On-demand Streaming Platform*).

## Giới thiệu

Mini-Netflix mô phỏng một nền tảng xem phim trực tuyến. Hệ thống quản lý tài khoản người dùng, hồ sơ xem phim, gói đăng ký, nội dung phim và các hoạt động tương tác như lịch sử xem, danh sách yêu thích và đánh giá.

## Chức năng chính

- Quản lý tài khoản người dùng và nhiều hồ sơ (*profile*) cho mỗi tài khoản.
- Quản lý các gói dịch vụ: giá, thời hạn, số profile và số thiết bị tối đa.
- Quản lý nội dung phim: phim lẻ (*Movie*), phim bộ (*TV Series*) và tập phim (*Episode*).
- Lưu lịch sử xem, vị trí xem gần nhất và trạng thái đã xem xong.
- Thêm hoặc xoá nội dung khỏi danh sách yêu thích (*Watchlist*).
- Đánh giá nội dung theo thang điểm 1–5.
- Phân loại nội dung theo thể loại và diễn viên.

## Công nghệ

- Backend: **Python Flask**
- Database: **SQLite** (`instance/netflix.db`)
- Frontend: HTML, CSS, JavaScript

## Mô hình dữ liệu

Các bảng chính:

`users`, `profiles`, `subscription_tier`, `subscription`, `content`, `movie`, `tv_series`, `episode`, `genre`, `actor`, `content_genre`, `content_actor`, `watch_history`, `watchlist`, `rating`.

`content` là thực thể cha; `movie` và `episode` là hai thực thể con. Mỗi `episode` thuộc về một `tv_series`.

## Cấu trúc thư mục

```text
mini-netflix/
├── app.py                  # Flask application
├── README.md
├── database/
│   ├── sample_data.sql     # Dữ liệu mẫu
│   └── schema.sql          # Script tạo cấu trúc dữ liệu
├── instance/
│   └── netflix.db          # SQLite database
├── static/
│   ├── images/
│   └── file.txt
│   ├── css/
│   │   └── style.css
│   └── js/
│       └── main.js
├── templates/
│   ├── index.html
│   ├── login.html
│   ├── movies.html
│   ├── profile.html
│   └── register.html
```

## Cài đặt cơ sở dữ liệu

1. Cài Python 3 và Flask:

```bash
pip install flask
```

2. Chạy ứng dụng:

```bash
python app.py
```

3. Mở trình duyệt tại địa chỉ Flask hiển thị trong terminal (thường là `http://127.0.0.1:5000`).

## Chức năng giao diện

- Đăng ký và đăng nhập tài khoản.
- Xem danh sách phim và thông tin profile.
- Tách giao diện HTML trong `templates/` và tài nguyên CSS/JS/ảnh trong `static/`.

## Quy tắc nghiệp vụ nổi bật

- Một user có thể có nhiều profile, nhưng mỗi profile chỉ thuộc một user.
- Mỗi user chỉ có một gói đăng ký còn hiệu lực tại một thời điểm.
- Một profile chỉ được đánh giá một nội dung một lần.
- Mỗi tập phim là duy nhất theo `series_id`, `season_number`, `episode_number`.
- Chỉ user có subscription còn hiệu lực mới được xem nội dung.

## Thành viên nhóm

- Hoàng Hải Đăng
- Huỳnh Hữu Diên
- Châu Thanh Bình

## Ghi chú làm việc nhóm

- Không push trực tiếp lên nhánh `main` khi chưa thống nhất.
- Mỗi thành viên làm phần việc trên branch riêng: `database`, `backend`, `frontend`, hoặc `docs`.
- Tạo Pull Request trước khi merge vào `main`.
