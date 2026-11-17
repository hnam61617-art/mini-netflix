"""Hai thao tác danh mục minh họa CT-07/CT-09, chạy bằng mn_catalog."""
from app import db

def create_content(title,content_type,genre_ids,video_url=None,duration=None,connection_factory=None):
    if content_type not in ('MOVIE','TV_SERIES') or not title.strip() or not genre_ids:
        raise ValueError('Cần tiêu đề, đúng một loại và ít nhất một thể loại')
    c=(connection_factory or db)()
    try:
        with c.cursor() as q:
            q.execute('INSERT INTO contents(title,content_type) VALUES(%s,%s)',(title,content_type));cid=q.lastrowid
            if content_type=='MOVIE':
                q.execute('INSERT INTO movies(content_id,video_url,duration) VALUES(%s,%s,%s)',(cid,video_url,duration))
            else:q.execute('INSERT INTO tv_series(content_id) VALUES(%s)',(cid,))
            for gid in set(genre_ids):q.execute('INSERT INTO content_genres(content_id,genre_id) VALUES(%s,%s)',(cid,gid))
            q.execute('SELECT (SELECT COUNT(*) FROM movies WHERE content_id=%s)+(SELECT COUNT(*) FROM tv_series WHERE content_id=%s) AS subclasses,(SELECT COUNT(*) FROM content_genres WHERE content_id=%s) AS genres',(cid,cid,cid));r=q.fetchone()
            if (r['subclasses'] if isinstance(r,dict) else r[0])!=1 or (r['genres'] if isinstance(r,dict) else r[1])<1:raise ValueError('Nội dung thiếu lớp con hoặc thể loại')
            c.commit();return cid
    except Exception:c.rollback();raise
    finally:c.close()

def remove_genre(content_id,genre_id):
    c=db()
    try:
        with c.cursor() as q:
            q.execute('SELECT content_id FROM contents WHERE content_id=%s FOR UPDATE',(content_id,))
            if not q.fetchone():raise ValueError('Nội dung không tồn tại')
            q.execute('DELETE FROM content_genres WHERE content_id=%s AND genre_id=%s',(content_id,genre_id))
            q.execute('SELECT COUNT(*) AS n FROM content_genres WHERE content_id=%s',(content_id,))
            if q.fetchone()['n']<1:raise ValueError('Không được gỡ thể loại cuối cùng')
            c.commit()
    except Exception:c.rollback();raise
    finally:c.close()
