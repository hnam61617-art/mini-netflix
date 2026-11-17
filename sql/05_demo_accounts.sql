-- Chỉ dành cho máy demo cục bộ / Docker. Các mật khẩu này là công khai.
CREATE USER 'mn_service'@'%' IDENTIFIED BY 'DemoViewer1313!';
GRANT 'mn_app' TO 'mn_service'@'%';
SET DEFAULT ROLE 'mn_app' TO 'mn_service'@'%';
CREATE USER 'mn_presenter'@'%' IDENTIFIED BY 'DemoReport1313!';
GRANT 'mn_report' TO 'mn_presenter'@'%';
SET DEFAULT ROLE 'mn_report' TO 'mn_presenter'@'%';
CREATE USER 'mn_editor'@'%' IDENTIFIED BY 'DemoCatalog1313!';
GRANT 'mn_catalog' TO 'mn_editor'@'%';
SET DEFAULT ROLE 'mn_catalog' TO 'mn_editor'@'%';
