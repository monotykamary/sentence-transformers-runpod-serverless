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
    normalize_embeddings = job_input.pop("normalize_embeddings", False)
    model = load_model()

    embeddings = model.encode(sentences, normalize_embeddings=normalize_embeddings)
    encoded_embeddings = json.dumps(embeddings, cls=NumpyArrayEncoder)
    decoded_embeddings = json.loads(encoded_embeddings)
    yield decoded_embeddings

runpod.serverless.start({
    "handler": handler,
})
