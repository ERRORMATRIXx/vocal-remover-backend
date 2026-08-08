from fastapi import FastAPI, UploadFile, File
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
import subprocess, os, uuid, shutil

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def health():
    return {"status": "Vocal Remover API is running"}

@app.post("/separate")
async def separate(file: UploadFile = File(...)):
    job_id = str(uuid.uuid4())
    input_dir = f"/tmp/{job_id}"
    os.makedirs(input_dir, exist_ok=True)
    input_path = f"{input_dir}/input.mp3"

    with open(input_path, "wb") as f:
        shutil.copyfileobj(file.file, f)

    # Run demucs separation (2-stem: vocals + no_vocals/instrumental)
    subprocess.run([
        "python", "-m", "demucs",
        "--two-stems", "vocals",
        "-o", input_dir,
        input_path
    ], check=True)

    # Demucs output structure: input_dir/htdemucs/input/vocals.wav & no_vocals.wav
    output_folder = f"{input_dir}/htdemucs/input"
    vocals_path = f"{output_folder}/vocals.wav"
    instrumental_path = f"{output_folder}/no_vocals.wav"

    return {
        "job_id": job_id,
        "vocals_ready": os.path.exists(vocals_path),
        "instrumental_ready": os.path.exists(instrumental_path)
    }

@app.get("/download/{job_id}/{stem}")
def download(job_id: str, stem: str):
    filename = "vocals.wav" if stem == "vocals" else "no_vocals.wav"
    path = f"/tmp/{job_id}/htdemucs/input/{filename}"
    if os.path.exists(path):
        return FileResponse(path, media_type="audio/wav", filename=filename)
    return {"error": "File not found"}
