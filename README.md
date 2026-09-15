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
- Database: **MYSQL** (`instance/netflix.db`)
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
│   └── netflix.db          
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

Hoàng Hải Đăng N25DCAT071 (EMAIL: n25dcat071@student.ptithcm.edu.vn) (hnam61617-art)

Châu Thanh Bình N25DCAT070 (EMAIL: n25dcat070@student.ptithcm.edu.vn) (bnhchu313207)

Huỳnh Hữu Diên N25DCAT072  (EMAIL: n25dcat072@student.ptithcm.edu.vn)(HDIEN2802)



