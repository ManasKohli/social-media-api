from fastapi import FastAPI, HTTPException, File, UploadFile, Form, Depends
from app.schemas import PostCreate, PostResponse, UserCreate, UserRead, UserUpdate
from app.db import Post, create_async_engine, create_db_and_tables, get_async_session
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from contextlib import asynccontextmanager
from app.images import imagekit
from imagekitio import ImageKit
import shutil 
import os
import uuid
import tempfile
import httpx
from app.users import auth_backend, current_active_user, fastapi_users



@asynccontextmanager
async def lifespan(app: FastAPI):
    await create_db_and_tables()
    yield

app = FastAPI(lifespan=lifespan)

app.include_router(fastapi_users.get_auth_router(auth_backend), prefix="/auth/jwt", tags=["auth"])
app.include_router(fastapi_users.get_register_router(UserRead, UserCreate), prefix="/auth", tags=["auth"])
app.include_router(fastapi_users.get_reset_password_router(), prefix="/auth", tags=["auth"])
app.include_router(fastapi_users.get_verify_router(UserRead), prefix="/auth", tags=["auth"])
app.include_router(fastapi_users.get_users_router(UserRead, UserUpdate), prefix="/users", tags=["users"])

# Endpoint to upload a post
import base64

@app.post("/upload")
async def upload_post(
    caption: str = Form(...),
    file: UploadFile = File(...),
    session: AsyncSession = Depends(get_async_session)
):
    temp_file_path = None

    try:
        # 1) Save upload to temp file
        with tempfile.NamedTemporaryFile(
            delete=False,
            suffix=os.path.splitext(file.filename)[1]
        ) as temp_file:
            temp_file_path = temp_file.name
            shutil.copyfileobj(file.file, temp_file)

        # 2) Upload to ImageKit via REST API
        upload_url = "https://upload.imagekit.io/api/v1/files/upload"

        async with httpx.AsyncClient(timeout=60) as client:
            with open(temp_file_path, "rb") as f:
                resp = await client.post(
                    upload_url,
                    auth=(os.getenv("IMAGEKIT_PRIVATE_KEY"), ""),  # Basic auth
                    data={
                        "fileName": file.filename,
                        "useUniqueFileName": "true",
                        "tags": "post_upload",
                    },
                    files={
                        "file": (
                            file.filename,
                            f,
                            file.content_type or "application/octet-stream",
                        )
                    },
                )

        if resp.status_code not in (200, 201):
            raise HTTPException(
                status_code=502,
                detail=f"ImageKit upload failed: {resp.text}",
            )

        result = resp.json()

        # 3) Save to DB
        post = Post(
            caption=caption,
            url=result["url"],
            file_type="video"
            if (file.content_type or "").startswith("video/")
            else "image",
            file_name=result["name"],
        )

        session.add(post)
        await session.commit()
        await session.refresh(post)
        return post

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    finally:
        if temp_file_path and os.path.exists(temp_file_path):
            os.unlink(temp_file_path)
        file.file.close()


#Feed
@app.get("/feed")
async def get_feed(session: AsyncSession = Depends(get_async_session)):
    result = await session.execute(select(Post).order_by(Post.created_at.desc()))
    posts = [row[0] for row in result.all()]

    post_data = []
    for post in posts:
        post_data.append({
            "id": str(post.id),
            "caption": post.caption,
            "url": post.url,
            "file_type": post.file_type,
            "file_name": post.file_name,
            "created_at": post.created_at.isoformat()
        })  
    return {"posts": post_data}

# Delete a post
@app.delete("/post/{post_id}")
async def delete_post(post_id: str, session: AsyncSession = Depends(get_async_session)): 
    try:
        post_uuid = uuid.UUID(post_id)

        post = await session.get(Post, post_uuid)

        if not post:
            raise HTTPException(status_code=404, detail="Post not found")
        
        await session.delete(post)
        await session.commit()

        return {"detail": "Post deleted successfully"}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

#health check endpoint
@app.get('/')
def health():
    return {
        'status': 'healthy'
    }


