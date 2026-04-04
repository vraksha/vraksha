import requests
import base64

from src.utils.extract_token import get_token
from src.utils.url_manipulator import manipulate

TOKEN = get_token()

headers = {
    "Authorization": f"Bearer {TOKEN}"
}


def fetcher(repo_url):
    api_url = manipulate(repo_url)
    res = requests.get(api_url, headers=headers)

    if res.status_code != 200:
        raise Exception(f"Request failed: {res.status_code}")


    data = res.json()

    # Case 1: File
    if isinstance(data, dict) and data.get("type") == "file":
        content = base64.b64decode(data["content"]).decode("utf-8")
        return content

    # Case 2: Directory
    elif isinstance(data, list):
        results = {}

        for item in data:
            file_url = item["url"]
            file_path = item["path"]

            if item["type"] == "file":
                file_res = requests.get(file_url, headers=headers)
                file_data = file_res.json()

                content = base64.b64decode(file_data["content"]).decode("utf-8")
                results[file_path] = content

            elif item["type"] == "dir":
                results.update(fetcher(file_url))

        return results

    else:
        raise Exception("Unknown response format")

