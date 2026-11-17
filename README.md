# Mini-Netflix · Nhóm G2 — bản dữ liệu có nguồn

Đọc [DATA_SOURCES.md](DATA_SOURCES.md) về nguồn và cách sử dụng; [SOURCE_INVENTORY.md](SOURCE_INVENTORY.md) về nguồn đã xét;. báo cáo đề tài nằm tại [Bao_Cao_Mini_Netflix_G2.pdf](Bao_Cao_Mini_Netflix_G2.pdf) ; 

## Thông tin nhóm và repo

- Tên đề tài: **On-Demand Streaming Platform (Mini-Netflix)**.
- Repo nhóm: https://github.com/hnam61617-art/mini-netflix
- Mã nhóm: **G2**; mã môn **INT1313**; lớp **D25CQAT02-N**.

THÀNH VIÊN NHÓM 
| Họ và tên | MSSV | Email trường | GitHub |
|---|---|---|---|
| Hoàng Hải Đăng | N25DCAT071 | n25dcat071@student.ptithcm.edu.vn | [hnam61617-art](https://github.com/hnam61617-art) |
| Châu Thanh Bình | N25DCAT070 | n25dcat070@student.ptithcm.edu.vn | [bnhchu313207](https://github.com/bnhchu313207) |
| Huỳnh Hữu Diên | N25DCAT072 | n25dcat072@student.ptithcm.edu.vn | [HDIEN2802](https://github.com/HDIEN2802) |

GIẢNG VIÊN HƯỚNG DẪN : Lê Hà Thanh (lehathanh@ptithcm.edu.vn)


## 1. Chạy demo bằng Docker Desktop
### 1. Cài Git trên Windows

Nếu máy chưa có Git, mở PowerShell và chạy:

```powershell
winget install --id Git.Git -e
```

Cài xong, đóng PowerShell rồi mở lại. Kiểm tra bằng lệnh:

```powershell
git --version
```

### 2. Tải mã nguồn

Chạy các lệnh sau trong PowerShell:

```powershell

git clone https://github.com/hnam61617-art/mini-netflix.git
cd mini-netflix

  mở thư mục có `compose.yaml` bằng VS Code. Bật Docker Desktop, chọn Linux containers; ở terminal:

```powershell
docker compose up --build -d
docker compose logs -f init
```

Lần đầu đợi MySQL khởi tạo và dòng `INIT VERIFIED`. Ctrl+C chỉ thoát xem log. Kiểm tra:

```powershell
docker compose ps -a
```

`db` healthy, `init` Exited (0), `web` Up là bình thường. Mở **http://localhost:5000**. Đăng nhập **student001@gmail.com**, mật khẩu **MiniNetflix1313!**. Các tài khoản student001 đến student013 dùng cùng mật khẩu demo.


Nếu báo không tìm thấy dockerDesktopLinuxEngine, bật Docker Desktop, đợi Engine running rồi chạy lại. Nếu cổng 13306 bận, đổi **cổng bên trái** `127.0.0.1:13306:3306` thành cổng trống và dùng cổng đó trong Workbench; Flask nội bộ vẫn dùng `db:3306`.

## 2. Thao tác demo

- Người dùng: tìm tiêu đề, lọc thể loại/phim lẻ/phim bộ; xem chi tiết, các tập có nguồn, lịch sử cá nhân và hồ sơ.
- Mới nạp **không có gói đăng ký, thanh toán hoặc xem sau**. Hồ sơ 1 vẫn xem được lịch sử nguồn đã nhập. Muốn ghi tiến độ xem mới, vào tài khoản chọn gói mô phỏng trước. Thanh toán phát sinh ở bước này là giao dịch demo do bạn thao tác.
- Nội dung thiếu tập sẽ hiện thông báo thiếu metadata, không tự tạo tập. URL video `example.com` không phát phim; ảnh SVG là minh họa.
- Trang quản lý: **http://localhost:5000/lab**, khóa demo **G2Demo1313!**. Chọn từng chức năng tra cứu, nhập điều kiện rồi tìm. Phần doanh thu/thanh toán trống trước khi bạn tạo giao dịch là đúng dữ liệu seed. Truy vấn SQL tự viết chạy trong Workbench.
- Danh mục quản lý cho phép thêm nội dung; nội dung, subtype và thể loại được ghi trong một transaction. Kiểm tra trigger và ràng buộc bằng SQL ở mục sau.

## 3. Kết nối MySQL Workbench

Tạo kết nối Standard (TCP/IP):

| Trường | Giá trị |
|---|---|
| Connection Name | Mini Netflix G2 |
| Hostname | 127.0.0.1 |
| Port | 13306 |
| Username | root |
| Password | LocalDemoRoot1313! |
| Default Schema | **mini_netflix** (đúng chữ thường), hoặc để trống |

Nếu báo Unknown database, xóa Default Schema, kết nối và chạy `SHOW DATABASES;`; xem `docker compose logs init` để chắc khởi tạo thành công. Không nhập tên kết nối làm tên schema.

```sql
USE mini_netflix;
SHOW TABLES;
SHOW TRIGGERS;
SELECT COUNT(*) FROM contents;
SELECT * FROM users WHERE email='student001@gmail.com';
SELECT * FROM movies LIMIT 20;
```

Mở `sql/03_queries.sql` hoặc sao từng Q trong `queries.json`, đặt `@profile_id=1` nếu câu dùng biến. Có thể chạy SELECT/INSERT khác với quyền tương ứng, không bị giới hạn 10 Q. Q tài chính có thể trả 0 dòng ở DB mới.

Ví dụ thêm phim hợp lệ (đủ subtype và thể loại, rollback nếu thao tác lỗi):

```sql
USE mini_netflix;
START TRANSACTION;
INSERT INTO contents(title,description,date_released,content_type)
VALUES ('Chuyến đi mùa hạ','Nội dung demo tự thêm',NULL,'MOVIE');
SET @new_content=LAST_INSERT_ID();
INSERT INTO movies(content_id,video_url,duration)
VALUES (@new_content,'https://example.com/no-video/demo',90);
INSERT INTO content_genres(content_id,genre_id)
SELECT @new_content,genre_id FROM genres ORDER BY genre_id LIMIT 1;
COMMIT;
SELECT * FROM contents WHERE content_id=@new_content;
```

`sql/01_schema.sql`: tạo bảng, ràng buộc, trigger, view, thủ tục; `02_seed.sql`: dữ liệu sinh từ snapshot; `03_queries.sql`: 10 truy vấn báo cáo; `04_roles.sql`: quyền; `05_demo_accounts.sql`: tài khoản dịch vụ MySQL. Không chạy lại toàn bộ schema trên DB đang dùng để tránh xóa dữ liệu. Docker dùng Python importer xử lý DELIMITER, tránh lỗi tách trigger trên Windows.

## 4. Nguồn dữ liệu và tái lập

Snapshot đầu vào ở `datasets/raw/`; metadata, giấy phép và SHA-256 ở `datasets/metadata/`; ánh xạ từng dòng và danh sách loại bỏ ở `datasets/generated/`. Không cần tài khoản Kaggle để khởi tạo bản ZIP.

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python scripts/build_sources.py
```

Lệnh ETL không cần mạng, kiểm checksum rồi tái tạo `02_seed.sql` và provenance. Không tự nhập seed vào DB đã có. `scripts/fetch_episode_sources.py` và `resolve_episode_sources.py` dùng khi chủ động cập nhật snapshot TVmaze; kết quả mới phải được rà soát và khóa checksum riêng. Dữ liệu Kaggle có thể thay đổi ngoài snapshot đã đóng gói.

Nếu chạy Flask ngoài Docker, đặt DB_HOST=127.0.0.1, DB_PORT=13306, DB_USER=mn_service, DB_PASSWORD=DemoViewer1313! trong môi trường rồi `python demo/app.py`; tránh trùng cổng 5000 với web container.

## 5. Kiểm chứng và đo tốc độ

Trên CSDL nguồn đang chạy:

```powershell
docker compose exec -e DB_USER=root -e DB_PASSWORD=LocalDemoRoot1313! web python scripts/run_checks.py --fresh
```

`--fresh` kiểm đúng số dòng ban đầu, chỉ dùng trước khi thêm dữ liệu. Sau thao tác demo, bỏ `--fresh`. Bộ này kiểm nguồn, ánh xạ, ràng buộc và HTTP Flask; benchmark SELECT Q1–Q10 với 5 lượt làm nóng + 30 lượt đo, kèm EXPLAIN ANALYZE. Kết quả `evidence/sourced_*.json`. Muốn lấy kết quả mới từ container về máy:

```powershell
docker compose cp web:/app/evidence ./evidence-latest
```

Bốn script gốc có giả định fixture cũ (100 người dùng, 25.000 lịch sử...), nên chạy trên **MySQL kiểm thử riêng**, không nạp giả vào DB nguồn:

```powershell
docker compose -p mn_verify -f compose.verify.yaml run --build --rm checks
docker compose -p mn_verify -f compose.verify.yaml down
```

Compose kiểm thử không mở cổng máy chủ, dùng tmpfs riêng; script có chốt chống chạy vào DB nguồn. Kết quả fixture được ghi `evidence/fixture/` trong container kiểm thử; bản kết quả bàn giao đã nằm trong ZIP. Việc vượt test fixture không chứng minh đây là dữ liệu khách hàng thật. Xem [KET_QUA_KIEM_CHUNG.md](KET_QUA_KIEM_CHUNG.md).


