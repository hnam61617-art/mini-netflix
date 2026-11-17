# Nguồn dữ liệu và cách sử dụng

Bản Sourced Final giữ nguyên báo cáo và schema 13 bảng. Số liệu snapshot sau ETL: **48.338 dòng**, gồm 8.807 nội dung, 2.468 tập, 1.694 lịch sử; không dùng lịch sử ngẫu nhiên để tăng số lượng.

## 1. Nguồn đã nhập

| Nguồn/tác giả | Giấy phép nhà cung cấp công bố | Dữ liệu và cách dùng |
|---|---|---|
| [Netflix Movies and TV Shows — Shivam Bansal](https://www.kaggle.com/datasets/shivamb/netflix-shows), Kaggle, v5 27/09/2021 | [CC0](https://creativecommons.org/publicdomain/zero/1.0/) | netflix_titles.csv, 8.807 dòng → contents, movies, tv_series, genres, content_genres |
| [Netflix watch log — Arjun M](https://www.kaggle.com/datasets/arjunajn/netflix-watch-log) | [CC BY-NC-SA 4.0](https://creativecommons.org/licenses/by-nc-sa/4.0/) | All_Profiles.csv: 9 bí danh hồ sơ; All_ViewingActivity.csv: 9.992 sự kiện → hồ sơ kỹ thuật và lịch sử đối chiếu được |
| [Netflix Viewing Activity — Sandrin Muramutsa](https://www.kaggle.com/datasets/paccysangmailcom/netflix-viewing-activity) | MIT (metadata Kaggle kèm snapshot) | ViewingActivity.csv: 905 sự kiện, 4 bí danh hồ sơ → hồ sơ tối thiểu và lịch sử đối chiếu được. Hai file trong ZIP trùng nhau, chỉ nhập một |
| [TVmaze API — TVmaze và cộng đồng đóng góp](https://www.tvmaze.com/api) | [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/), [điều kiện API](https://www.tvmaze.com/api#licensing) | 35 ứng viên series được tra; 34 khớp chắc → 2.468 tập thường có runtime dương, metadata ngày/tên/thời lượng. Không cung cấp video |

Lưu metadata giấy phép và nguồn tại datasets/metadata/, dữ liệu gốc tại datasets/raw/. Giữ các thành phần riêng; log Arjun có điều kiện phi thương mại và chia sẻ tương tự, metadata TVmaze có điều kiện ghi công/chia sẻ tương tự. Không tuyên bố cả dự án hoặc mọi bản ghi là CC0. Các bản biến đổi log và tập phải giữ ghi công và điều kiện giấy phép tương ứng khi phân phối lại.

## 2. Ánh xạ danh mục

- show_id nguồn → content_id nội bộ ổn định; tra từng dòng bằng `content_provenance.csv`. Không đổi tên phim thành tên giả.
- title/description/type → contents; loại Movie/TV Show đổi thành MOVIE/TV_SERIES theo schema; duration phim lẻ bỏ đơn vị min.
- listed_in tách nhiều thể loại và bảng nối; giữ các thể loại gốc, có 4 nhãn Việt tương thích demo. 46 genre, 26.487 liên kết.
- Ba phim s5542/s5795/s5814 bị đặt runtime vào cột rating được phục hồi lần lượt 74/84/66 phút, có provenance. Không suy đoán runtime còn thiếu.
- Nguồn Netflix chỉ có release_year, không có ngày phát hành chính xác. Giữ năm ở raw/provenance, để date_released NULL; chỉ 34 series có ngày premiere từ TVmaze. **8.773 date_released NULL**, không thay bằng 01/01. date_added không được coi là ngày phát hành.
- Nguồn có số mùa, không có số tập: total_episodes được đếm từ tập TVmaze thực nhập, 2.642 series còn thiếu tập là 0, không tạo tập thay thế.

## 3. Ánh xạ tập

TVmaze có thể có nhiều tác phẩm trùng tên. Script đối chiếu tên và cast/quốc gia/năm; ví dụ Suits trong danh mục là bản Hàn Quốc, không tự gắn tập Mỹ. Demon Slayer chưa khớp chắc nên không nhập.

Schema chỉ có episode_number, không có season: đánh số liên tiếp theo series; tên hiển thị `SxxExx · tên nguồn`, giữ ID TVmaze/season/số tập gốc trong `episode_provenance.csv`. Bỏ tập không thường, chưa phát hành hoặc thiếu runtime hợp lệ, ghi `rejected_episodes.csv`. video_url NOT NULL dùng URL minh họa example.com, không phải nguồn video. Scripts fetch/resolve giữ JSON phản hồi để kiểm tra lại, không gọi mạng khi build snapshot.

## 4. Hồ sơ và lịch sử

Nguồn log không có email/mật khẩu hay quan hệ chủ tài khoản. Tạo 13 chủ kỹ thuật, mỗi chủ một hồ sơ nguồn; không suy đoán các hồ sơ có cùng người sở hữu. Tên Việt là bí danh, email/điện thoại/mật khẩu demo là giá trị kỹ thuật đáp ứng NOT NULL/UNIQUE; không phải thông tin khách hàng thật. 9 thời điểm tạo hồ sơ lấy nguồn; 4 hồ sơ Sandrin Muramutsa dùng mốc quan sát đầu tiên và ghi rõ suy ra.

`profile_provenance.csv` lưu file/dòng/bí danh nguồn và ID kỹ thuật. Tài khoản student001 gắn hồ sơ User4 của log Arjun nên đăng nhập thấy lịch sử đã nhập.

10.897 sự kiện đầu vào → bỏ trailer/hook/quảng cáo và sự kiện không đủ tên/tập/runtime. Ghép tên chuẩn hóa chính xác; không fuzzy đoán nội dung. 3.743 sự kiện hợp lệ, collapse 2.049 lượt lặp thành **1.694 dòng mới nhất theo hồ sơ + phim/tập**, đúng UNIQUE trong báo cáo. 7.154 sự kiện không nhập: 4.900 không khớp chắc và 2.254 bổ sung/quảng bá; có lý do trong `rejected_watch_events.csv`.

`last_watch_at = Start Time + Duration`; `watch_progress = Bookmark / (runtime phút × 60) × 100`, làm tròn 2 số, giới hạn 0–100 theo CHECK. **Duration là độ dài phiên xem, không phải phần trăm hoàn thành.** Giữ phần trăm trước giới hạn, runtime và file/dòng gốc tại `history_provenance.csv`; datetime lưu theo quy ước UTC của pipeline, schema không chứa timezone.
.

## 5. Trống và phần cấu hình demo

subscriptions/payments/watch_lists: 0 dòng ban đầu do chưa có nguồn đáp ứng schema, liên kết và quyền sử dụng. 3 tier là cấu hình bài làm, không phải dữ liệu thu phí Netflix. Tên Việt/login/URL video/ảnh minh họa là giá trị kỹ thuật, không tuyên bố lấy từ nguồn. Xem [DU_LIEU_CON_TRONG.md](DU_LIEU_CON_TRONG.md) để biết đầy đủ phần thiếu và vì sao một số trường NOT NULL không thể để NULL mà vẫn giữ schema gốc.

## 7. Tái lập và nghiên cứu

`python scripts/build_sources.py` kiểm toàn bộ SHA-256 snapshot, rồi tạo sql/02_seed.sql, build_manifest và CSV provenance/rejected theo thuật toán xác định. `datasets/metadata/raw_sha256.json` khóa đầu vào. Không cần mạng. Mã schema/report/Q/verify gốc có hash tại preserved_files_sha256.json.

