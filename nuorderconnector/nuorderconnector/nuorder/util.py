import json

import requests


def raise_for_status_with_body(resp):
    try:
        resp.raise_for_status()
    except requests.exceptions.HTTPError as exc:
        try:
            # Prettify output if possible
            body = json.dumps(resp.json(), indent=2)
        except Exception:
            body = resp.text
        exc.args = [
            'Got HTTP {}, with body:\n{}'.format(resp.status_code, body),
        ]
        raise exc
