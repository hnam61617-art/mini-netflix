# Danh mục nguồn đã tìm và quyết định sử dụng

| Nguồn | Quyết định | Cách sử dụng / lý do |
|---|---|---|
| Kaggle shivamb/netflix-shows | ĐÃ NHẬP | 8.807 nội dung, mô tả, loại, phút phim lẻ, thể loại; thiếu ngày chính xác để NULL |
| Kaggle arjunajn/netflix-watch-log | ĐÃ NHẬP CÓ LỌC | 9 hồ sơ nguồn và các sự kiện chính ghép chắc nội dung/runtime; giữ vị trí xem và thời gian nguồn, gộp lượt cuối |
| Kaggle paccysangmailcom/netflix-viewing-activity | ĐÃ NHẬP CÓ LỌC | 4 alias hồ sơ và log ghép đủ căn cứ. Chỉ dùng một trong hai CSV trùng nhau |
| TVmaze API | ĐÃ NHẬP CÓ LỌC | Metadata 2.468 tập cho 34 bộ; xác minh tên, diễn viên/quốc gia/năm khi cần; không dùng chỉ số mùa làm số tập |
| Kaggle roshanegohar/netflix-history-dataset | GIỮ RAW, CHƯA NHẬP | Có Title/Date, thiếu hồ sơ và progress bắt buộc. Không bịa khóa liên kết hoặc phần trăm |
| Kaggle smayanj/netflix-users-database | KHẢO SÁT, KHÔNG NHẬP | 25.000 người dùng vốn là dữ liệu tổng hợp; không có email/phone/password và khóa liên kết với các log trên |
| Kaggle rhythmghai/netflix-user-watching-behavior-dataset | KHẢO SÁT, KHÔNG NHẬP | 50.000 user mô phỏng; completion_rate là chỉ số tổng hợp, không phải progress cho từng phim; monthly_fee/payment_method không phải ledger |
| Netflix Userbase (arnavsmayan) | CHƯA KIỂM TRA ĐƯỢC FILE | Endpoint trả 403 trong lần khảo sát; không coi như dữ liệu đã nhập |
| Kaggle IMDb Non-Commercial Datasets | KHẢO SÁT, KHÔNG NHẬP | Cần giữ điều kiện nguồn IMDb, chưa có map IMDb ID trong catalog này. Dùng TVmaze có attribution và quyền dẫn xuất rõ thay vì ghép bừa |
| KKBox / Customer Retention in the Media Industry | KHẢO SÁT, KHÔNG NHẬP | Dịch vụ âm nhạc, tiền NTD và điều kiện truy cập/competition; không gán thành hóa đơn Netflix |
| Datarade Netflix email receipt data | CHƯA XÁC MINH ĐƯỢC QUYỀN TẢI/FILE | Chỉ có kết quả mô tả thương mại, chưa có dataset hợp lệ để nhập |
| Hugging Face hugginglearners/netflix-shows | ĐỐI CHIẾU | Cùng 8.807 dòng nhưng khác 2 giá trị so bản Kaggle; không trộn hai snapshot |
| HF reapxdev/tvmaze-scraper | KHẢO SÁT | Sample có thông tin show, không thay thế API episode cần dùng; truy ngược TVmaze gốc |
| Database Star Movies | THAM KHẢO | Không nhập schema khác (cast/crew/company) vào mô hình báo cáo |
| KION dataset | KHẢO SÁT, KHÔNG NHẬP | Có tương tác xem, nhưng chưa xác minh quyền tái phân phối và map nội dung với catalog đang dùng; không ép ghép |

Tất cả URL, tác giả, giấy phép, snapshot và các phép biến đổi của nguồn đã nhập có trong DATA_SOURCES.md. “Tìm thấy”, “đã tải” và “đã nhập” là ba trạng thái khác nhau; bản này không tuyên bố dùng mọi kết quả tìm kiếm chỉ vì chúng có tên liên quan Netflix.
