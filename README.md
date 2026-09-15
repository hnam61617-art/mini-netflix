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

- Database: **MySQL**
- Thiết kế dữ liệu: ER/EER Diagram, Business Rules và chuẩn hoá dữ liệu.
- Source control: Git/GitHub.

## Mô hình dữ liệu

Các bảng chính:

`users`, `profiles`, `subscription_tier`, `subscription`, `content`, `movie`, `tv_series`, `episode`, `genre`, `actor`, `content_genre`, `content_actor`, `watch_history`, `watchlist`, `rating`.

`content` là thực thể cha; `movie` và `episode` là hai thực thể con. Mỗi `episode` thuộc về một `tv_series`.

## Cấu trúc thư mục

```text
mini-netflix/
├── database/
│   ├── schema.sql          # Tạo database và các bảng
│   ├── seed.sql            # Dữ liệu mẫu
│   └── queries.sql         # Các câu truy vấn minh hoạ
├── backend/                # Xử lý API và nghiệp vụ (nếu có)
├── frontend/               # Giao diện web (nếu có)
├── docs/
│   ├── ERD.png             # Sơ đồ ER/EER
│   └── business-rules.md   # Business Rules và Constraints
└── README.md
```

## Cài đặt cơ sở dữ liệu

1. Cài đặt MySQL.
2. Tạo database và bảng:

```bash
mysql -u root -p < database/schema.sql
```

3. (Tuỳ chọn) Nạp dữ liệu mẫu:

```bash
mysql -u root -p mini_netflix < database/seed.sql
```

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
