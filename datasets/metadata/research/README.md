# Rà lại bốn cổng nguồn

Snapshot nghiên cứu phục vụ bản Sourced Final, 16/11/2026. Không khẳng định dữ liệu không tồn tại ở mọi nơi; chỉ ghi nguồn đã tiếp cận/xác minh được trong lần rà này.

| Cổng | Tìm kiếm/đối chiếu | Kết quả dùng cho dự án |
|---|---|---|
| Kaggle | Netflix watch log, viewing activity, userbase, subscription transactions, history | Nhập catalog + hai log có progress/profile; giữ history Roshan chưa nhập. Userbase/hành vi tổng hợp có nguồn mô phỏng, không coi là khách thật; giao dịch KKbox khác miền nhạc và hạn chế truy cập |
| Hugging Face | netflix watch, netflix user, TVmaze episode; API query JSON kèm thư mục | Chưa xác minh nguồn tài khoản/giao dịch đủ trường. Catalog mirror không cần nhập trùng. TVmaze scraper chủ yếu show metadata, truy upstream API TVmaze để có tập |
| Google Dataset Search | netflix viewing history; movie watchlist users; streaming subscription transactions; netflix my list dataset; streaming profiles watchlist dataset; netflix payment history dataset | Dẫn tới các log Kaggle, thêm Roshan. Kết quả metadata Letterboxd không chứng minh có dòng watchlist; Datarade receipt là chào bán thương mại chưa có file hợp lệ. Không gán Google làm chủ dữ liệu |
| Database Star | sample-data-sql, movie database | Mẫu movie/cast/crew, không có ledger Netflix/hồ sơ/watchlist phù hợp schema và liên kết |

Chi tiết quyết định nhập/không nhập, tác giả và URL: ../../../SOURCE_INVENTORY.md. Các truy vấn API và metadata lưu cạnh tài liệu; các trang tìm kiếm có thể đổi kết quả theo thời gian. Không thu thập tài khoản, mật khẩu hoặc thông tin thanh toán riêng tư.
