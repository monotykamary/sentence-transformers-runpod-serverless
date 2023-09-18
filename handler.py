import os, glob
import logging
from typing import Generator, Union
import runpod
from sentence_transformers import SentenceTransformer
import json
import numpy as np

logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))

class NumpyArrayEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        return json.JSONEncoder.default(self, obj)

def load_model():
    model_repo = os.getenv("MODEL_REPO", "sentence-transformers/all-mpnet-base-v2")
    models_cache = os.getenv("MODELS_CACHE", "/runpod-volume/sentence-transformers-cache/models")
    model = SentenceTransformer(model_repo, cache_folder=models_cache)
    return model

def handler(job):
    job_input = job['input']
    sentences = job_input.pop("sentences")
    model = load_model()

    embeddings = model.encode(sentences)
    encoded_embeddings = json.dumps(embeddings, cls=NumpyArrayEncoder)
    return encoded_embeddings

runpod.serverless.start({
    "handler": handler,
})