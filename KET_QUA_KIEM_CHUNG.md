# Kết quả kiểm chứng — Sourced Final

Đã chạy trên **MySQL 8.0.46**, Python 3.12, Linux trong môi trường kiểm thử. Đây là kiểm tra MySQL thật và HTTP qua Flask test client; chưa kiểm tra thao tác trực tiếp bằng Chrome/Windows Docker Desktop trong lần build này. Compose được bàn giao với importer Python đã kiểm tra, không dùng mysql CLI để tách trigger.

## CSDL nguồn chính

- **66/66** kiểm tra đạt: hash báo cáo/schema/role/Q/bốn verify, hash raw, 13 bảng/13 trigger/4 view/1 thủ tục, số dòng seed, FK/subtype/thể loại/bộ đếm, provenance log/tập, phần trăm từ Bookmark, thời điểm xem, ba bảng trống, SELECT Q1–Q10, đăng nhập/hiển thị/phân trang/tra cứu và phân quyền hồ sơ.
- **7/7** bước demo ghi dữ liệu đạt: đăng nhập chủ 13, chọn gói từ trạng thái trống, tạo subscription/payment, thêm xem sau, lưu và đọc lại tiến độ 42,5%. Thử trên MySQL cục bộ dùng một lần; dựng lại schema từ seed sau thử để giữ trạng thái gốc. Trigger giữ thanh toán không bị tắt để dọn dữ liệu.
- ETL tái lập: SQL seed, manifest và toàn bộ CSV generated không đổi SHA-256 qua chạy lại offline.
- **48.338 dòng** trong 13 bảng. subscriptions/payments/watch_lists là **0** ngay sau khởi tạo. Không có 25.000 lịch sử mô phỏng trong CSDL nguồn.
- Báo cáo Word SHA-256: a6605c27bfabe6d0a9d028b97e293e0c279b0d1fc5eab4e71730db429ee47c77.

Bằng chứng: evidence/sourced_verification.json, sourced_demo_actions.json, sourced_etl_reproducibility.json, sourced_environment.json. Test snapshot có thể báo lệch nếu bạn sửa/xóa các bản ghi nguồn; đó là kiểm tra provenance, không phải cấm thêm dữ liệu mới.

## Bốn script nguyên bản: fixture độc lập

**106/106**: verify.py 76/76, verify_demo.py 20/20, verify_semantics.py 4/4, verify_renewal.py 6/6. Giữ nguyên byte các script. Chúng giả định tài khoản/hồ sơ/25.000 lịch sử của fixture cũ nên dùng compose.verify.yaml, không nạp fixture vào DB demo chính.

Bằng chứng riêng: evidence/fixture/*.json. Số liệu benchmark trong thư mục fixture không đại diện CSDL nguồn. Script chặn chạy nếu DB không đúng fixture ban đầu; fixture MySQL tạm không dùng volume/cổng chính.

## Benchmark Q1–Q10 trên CSDL nguồn

Mỗi SELECT 5 lượt làm nóng + 30 lượt đo; đo gồm fetch kết quả qua PyMySQL trong môi trường này. Không khẳng định tốc độ sẽ giống máy Windows của bạn. Một số Q tài chính hoặc ngày phát hành trả 0 dòng vì các bảng để trống/ngày chính xác còn thiếu; không bù bằng dữ liệu giả.

| Q | Số dòng kết quả | Median ms | p95 ms |
|---|---:|---:|---:|
| Q1 | 0 | 0.589 | 2.319 |
| Q2 | 0 | 1.064 | 2.99 |
| Q3 | 215 | 5.585 | 11.44 |
| Q4 | 2676 | 29.539 | 74.831 |
| Q5 | 0 | 0.905 | 1.552 |
| Q6 | 0 | 0.424 | 0.752 |
| Q7 | 3 | 0.549 | 0.867 |
| Q8 | 0 | 9.593 | 16.412 |
| Q9 | 8501 | 122.485 | 158.211 |
| Q10 | 0 | 0.307 | 0.853 |

Chi tiết và EXPLAIN ANALYZE: evidence/sourced_benchmark.json và sourced_explain_analyze.json. Đây là số đo một snapshot, không phải so sánh có/không chỉ mục hoặc kết luận hiệu năng sản xuất.

## Nguồn và phần trống

DATA_SOURCES.md ghi tác giả, URL, giấy phép, cách biến đổi. SOURCE_INVENTORY.md ghi cả nguồn đã tìm nhưng không nhập. DU_LIEU_CON_TRONG.md ghi dữ liệu còn thiếu và ngoại lệ NOT NULL dùng giá trị kỹ thuật.
