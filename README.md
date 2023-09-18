# sentence-transformers-runpod-serverless

## Summary
This Docker image is a simple wrapper that runs `SentenceTransformer`` on a serverless RunPod instance.

## Set Up
1. Create a RunPod account and navigate to the [RunPod Serverless Console](https://www.runpod.io/console/serverless).
2. (Optional) Create a Network Volume to cache your model to speed up cold starts (but will incur some cost per hour for storage).
    - *Note: Only certain Network Volume regions are compatible with certain instance types on RunPod, so try out if your Network Volume makes your desired instance type Unavailable, try other regions for your Network Volume.*

3. Navigate to `My Templates` and click on the `New Template` button.
4. Enter in the following fields and click on the `Save Template` button:

    | Template Field | Value |
    | --- | --- |
    | Template Name | `sentence-transformers-runpod-serverless` |
    | Container Image | `monotykamary/sentence-transformers-runpod-serverless:latest` |
    | Container Disk | A size large enough to store your libraries + your desired model in 4bit. 1GB should be enough for most embedding models. |

    - Environment Variables:

        | Environment Variable | Example Value |
        | --- | --- |
        | (Required) `MODEL_REPO` | `sentence-transformers/all-mpnet-base-v2` or any other repo by `sentence-transformers` for your embeddings. |
        | (If using Network Volumes) `MODELS_CACHE` | `/runpod-volume/sentence-transformers-cache/models` |

4. Now click on `My Endpoints` and click on the `New Endpoint` button.
5. Fill in the following fields and click on the `Create` button:
    | Endpoint Field | Value |
    | --- | --- |
    | Endpoint Name | `sentence-transformers-runpod-serverless` |
    | Select Template | `sentence-transformers-runpod-serverless` |
    | Min Provisioned Workers | `0` |
    | Max Workers | `1` |
    | Idle Timeout | `5` seconds |
    | FlashBoot | Checked/Enabled |
    | GPU Type(s) | Use the `Container Disk` section of step 3 to determine the smallest GPU that can load the entire 4 bit model. In our example's case, use 16 GB GPU. Make smaller if using Network Volume instead. |

## Inference Usage
See the `predict.py` file for an example. For convenience we also copy the code below.

```py
import os
import requests
from time import sleep
import logging
import argparse
import sys
import json

endpoint_id = os.environ["RUNPOD_ENDPOINT_ID"]
URI = f"https://api.runpod.ai/v2/{endpoint_id}/run"


def run(prompt, params={}, stream=False):
    request = {
        'sentences': sentences,
    }

    request.update(params)

    response = requests.post(URI, json=dict(input=request), headers = {
        "Authorization": f"Bearer {os.environ['RUNPOD_AI_API_KEY']}"
    })

    if response.status_code == 200:
        data = response.json()
        task_id = data.get('id')
        return stream_output(task_id, stream=stream)


def stream_output(task_id, stream=False):
    # try:
    url = f"https://api.runpod.ai/v2/{endpoint_id}/stream/{task_id}"
    headers = {
        "Authorization": f"Bearer {os.environ['RUNPOD_AI_API_KEY']}"
    }

    previous_output = ''

    try:
        while True:
            response = requests.get(url, headers=headers)
            if response.status_code == 200:
                data = response.json()
                if len(data['stream']) > 0:
                    new_output = data['stream'][0]['output']

                    if stream:
                        sys.stdout.write(new_output[len(previous_output):])
                        sys.stdout.flush()
                    previous_output = new_output

                if data.get('status') == 'COMPLETED':
                    if not stream:
                        return previous_output
                    break

            elif response.status_code >= 400:
                print(response)
            # Sleep for 0.1 seconds between each request
            sleep(0.1 if stream else 1)
    except Exception as e:
        print(e)
        cancel_task(task_id)


def cancel_task(task_id):
    url = f"https://api.runpod.ai/v2/{endpoint_id}/cancel/{task_id}"
    headers = {
        "Authorization": f"Bearer {os.environ['RUNPOD_AI_API_KEY']}"
    }
    response = requests.get(url, headers=headers)
    return response


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Runpod AI CLI')
    parser.add_argument('-s', '--stream', action='store_true', help='Stream output')
    parser.add_argument('-p', '--params_json', type=str, help='JSON string of generation params')

    sentences = [
        "Explain The Great Gatsby in 4000 words.",
        "What is The Great Gatsby about?"
    ]
    args = parser.parse_args()
    params = json.loads(args.params_json) if args.params_json else "{}"
    import time
    start = time.time()
    print(run(sentences, params=params, stream=args.stream))
    print("Time taken: ", time.time() - start, " seconds")
```

Run the above code using the following command in terminal with the runpoint endpoint id assigned to your endpoint in step 5.
```bash
RUNPOD_AI_API_KEY='**************' RUNPOD_ENDPOINT_ID='*******' python predict.py
```
To run with streaming enabled, use the `--stream` option. To set generation parameters, use the `--params_json` option to pass a JSON string of parameters:
```bash
RUNPOD_AI_API_KEY='**************' RUNPOD_ENDPOINT_ID='*******' python predict.py --params_json '{"sentences": ["Explain The Great Gatsby in 4000 words.", "What is The Great Gatsby about?"], normalize_embeddings: true}'
```
You can generate the API key [here](https://www.runpod.io/console/serverless/user/settings) under API Keys.
