from fastapi import FastAPI, HTTPException
from app.schemas import PostCreate

app = FastAPI()

text_posts = {
    1: {
        "title": "First Post",
        "content": "This is the content of the first post."
    },
    2: {
        "title": "Learning FastAPI",
        "content": "FastAPI makes building APIs fast and intuitive."
    },
    3: {
        "title": "Why Python is Great",
        "content": "Python is readable, powerful, and widely used in backend development."
    },
    4: {
        "title": "APIs 101",
        "content": "An API lets different systems communicate with each other."
    },
    5: {
        "title": "Dictionaries in Python",
        "content": "Dictionaries store data as key-value pairs."
    }
}

@app.get('/posts')
def get_posts(limit: int = None):
    if limit:
        return list(text_posts.values())[:limit]
    
    return  text_posts

@app.get('/posts/{post_id}')
def get_post(post_id:int):
    if post_id not in text_posts:
        raise HTTPException(status_code=404, detail="Post not found")
    
    return text_posts.get(post_id)

@app.post('/posts')
def create_post(post: PostCreate):
    new_post = {'title': post.title, 'content': post.content}
    text_posts[len(text_posts) + 1] = new_post
    return new_post

#health check
@app.get('/')
def health():
    return {
        'status': 'healthy'
    }


