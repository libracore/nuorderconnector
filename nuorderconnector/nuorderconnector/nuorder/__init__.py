"""Package for making HTTP requests to the NuOrder API"""
import gzip
import hashlib
import hmac
import json
import logging
import uuid
from datetime import datetime

import requests

from .util import raise_for_status_with_body

__all__ = [
    'logger',
    'NuOrder',
]

logger = logging.getLogger('nuorder')


class NuOrder:

    def __init__(
        self,
        hostname,
        consumer_key,
        consumer_secret,
        oauth_token,
        oauth_token_secret,
        *,
        requests_session=None
    ):
        self.hostname = hostname
        self.consumer_key = consumer_key
        self.consumer_secret = consumer_secret
        self.oauth_token = oauth_token
        self.oauth_token_secret = oauth_token_secret
        self.requests_session = requests_session or requests.Session()

    def _get_oauth_timestamp(self):
        return str(int(datetime.now().timestamp()))

    def _get_oauth_nonce(self):
        return uuid.uuid4().hex[0:16]

    def _get_oauth_args(self, timestamp, nonce, additional_args=None):
        return [
            ('oauth_consumer_key', self.consumer_key),
            ('oauth_token', self.oauth_token),
            ('oauth_timestamp', timestamp),
            ('oauth_nonce', nonce),
            ('oauth_version', '1.0'),
            ('oauth_signature_method', 'HMAC-SHA1'),
            *list(additional_args or []),
        ]

    def _get_oauth_hmac_key(self):
        return '{}&{}'.format(self.consumer_secret, self.oauth_token_secret)

    def _get_base_string(
        self,
        method,
        url,
        timestamp,
        nonce,
        *,
        additional_args=None
    ):
        oauth_args = self._get_oauth_args(
            timestamp,
            nonce,
            additional_args=list(additional_args or []),
        )
        joined_args = '&'.join('='.join((k, v)) for k, v in oauth_args)
        return '{}{}?{}'.format(method, url, joined_args)

    def _get_authorization_header(
        self,
        signature,
        timestamp,
        nonce,
        *,
        additional_args=None
    ):
        oauth_args = self._get_oauth_args(
            timestamp,
            nonce,
            additional_args=(
                [('oauth_signature', signature)] + list(additional_args or [])
            ),
        )
        joined_args = ','.join(
            '='.join((k, v)) for k, v
            in oauth_args,
        )
        return 'OAuth {}'.format(joined_args)

    def _request(
        self,
        method,
        endpoint,
        *,
        data=None,
        dry_run=None,
        gzip_data=False,
        _additional_oauth_base_string_args=None,
        _additional_oauth_header_args=None
    ):
        method = method.upper()
        url = 'https://{}{}'.format(self.hostname, endpoint)
        timestamp = self._get_oauth_timestamp()
        nonce = self._get_oauth_nonce()
        base_string = self._get_base_string(
            method,
            url,
            timestamp,
            nonce,
            additional_args=_additional_oauth_base_string_args,
        )

        hmac_text = base_string.encode('utf-8')
        hmac_key = self._get_oauth_hmac_key().encode('utf-8')

        obj = hmac.new(hmac_key, digestmod=hashlib.sha1)
        obj.update(hmac_text)
        signature = obj.hexdigest()

        logger.debug('HMAC text: {}'.format(hmac_text))
        logger.debug('HMAC key: {}'.format(hmac_key))
        logger.debug('HMAC hash: {}'.format(signature))

        authorization_header = self._get_authorization_header(
            signature,
            timestamp,
            nonce,
            additional_args=_additional_oauth_header_args,
        )
        headers = {
            'Authorization': authorization_header,
            'Content-Type': 'application/json',
        }
        if gzip_data:
            headers['Content-Encoding'] = 'gzip'

        if data is not None:
            if isinstance(data, bytes):
                data = data.decode()
            if not isinstance(data, str):
                data = json.dumps(data, indent=2)

        logger.debug(headers)

        if dry_run:
            return {
                'would_do': {
                    'method': method,
                    'url': url,
                    'headers': headers,
                    'data': None if data is None else '[as passed in]',
                }
            }

        if gzip_data:
            data = gzip.compress(data.encode('utf-8'))

        logger.info('{} {}'.format(method, url))

        resp = self.requests_session.request(
            method,
            url,
            headers=headers,
            data=data,
        )
        raise_for_status_with_body(resp)
        logger.info('Returned HTTP status {}'.format(resp.status_code))
        try:
            return resp.json()
        except json.decoder.JSONDecodeError as exc:
            if not resp.text:
                return {}
            else:
                return {
                    'response_status_code': resp.status_code,
                    'response_text': resp.text,
                    'error': str(exc),
                }

    def get(self, endpoint, *, dry_run=False):
        return self._request('GET', endpoint, dry_run=dry_run)

    def delete(self, endpoint, *, dry_run=False):
        return self._request('DELETE', endpoint, dry_run=dry_run)

    def post(self, endpoint, data=None, *, dry_run=False, gzip_data=False):
        return self._request(
            'POST',
            endpoint,
            data=data,
            dry_run=dry_run,
            gzip_data=gzip_data,
        )

    def put(self, endpoint, data=None, *, dry_run=False, gzip_data=False):
        return self._request(
            'PUT',
            endpoint,
            data=data,
            dry_run=dry_run,
            gzip_data=gzip_data,
        )

    def oauth_initiate(self, app_name, *, dry_run=False):
        return self._request(
            'GET',
            '/api/initiate',
            dry_run=dry_run,
            _additional_oauth_base_string_args=[
                ('oauth_callback', 'oob'),
            ],
            _additional_oauth_header_args=[
                ('application_name', app_name),
                ('oauth_callback', 'oob'),
            ],
        )

    def oauth_token_request(self, oauth_verifier, *, dry_run=False):
        additional_args = [
            ('oauth_verifier', oauth_verifier),
        ]
        return self._request(
            'GET',
            '/api/token',
            dry_run=dry_run,
            _additional_oauth_base_string_args=additional_args,
            _additional_oauth_header_args=additional_args,
        )
