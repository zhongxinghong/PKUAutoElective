#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# filename: client.py
# modified: 2019-09-09

from requests.models import Request
from requests.sessions import Session
from requests.cookies import extract_cookies_to_jar

class BaseClient(object):

    default_headers = {}
    default_client_timeout = 10

    def __init__(self, *args, **kwargs):
        if self.__class__ is __class__:
            raise NotImplementedError
        self._timeout = kwargs.get("timeout", self.__class__.default_client_timeout)
        self._session = Session()
        self._session.headers.update(self.__class__.default_headers)

    @property
    def user_agent(self):
        return self._session.headers.get('User-Agent')

    def _request(self, method, url,
            params=None, data=None, headers=None, cookies=None, files=None,
            auth=None, timeout=None, allow_redirects=True, proxies=None,
            hooks=None, stream=None, verify=None, cert=None, json=None):

        # Extended from requests/sessions.py  for '_client' kwargs

        req = Request(
            method=method.upper(),
            url=url,
            headers=headers,
            files=files,
            data=data or {},
            json=json,
            params=params or {},
            auth=auth,
            cookies=cookies,
            hooks=hooks,
        )
        prep = self._session.prepare_request(req)
        prep._client = self  # hold the reference to client


        proxies = proxies or {}

        settings = self._session.merge_environment_settings(
            prep.url, proxies, stream, verify, cert
        )

        # Send the request.
        send_kwargs = {
            'timeout': timeout or self._timeout, # set default timeout
            'allow_redirects': allow_redirects,
        }
        send_kwargs.update(settings)
        resp = self._session.send(prep, **send_kwargs)

        return resp

    def _get(self, url, params=None, **kwargs):
        return self._request('GET', url,  params=params, **kwargs)

    def _post(self, url, data=None, json=None, **kwargs):
        return self._request('POST', url, data=data, json=json, **kwargs)

    def set_user_agent(self, user_agent):
        self._session.headers["User-Agent"] = user_agent

    def persist_cookies(self, r):
        """
        From requests/sessions.py, Session.send()

        Session.send() 方法会首先 dispatch_hook 然后再 extract_cookies_to_jar

        在该项目中，对于返回信息异常的请求，在 hooks 校验时会将错误抛出，send() 之后的处理将不会执行。
        遇到的错误往往是 SystemException / TipsException ，而这些客户端认为是错误的情况，
        对于服务器端来说并不是错误请求，服务器端在该次请求结束后可能会要求 Set-Cookies
        但是由于 send() 在 dispatch_hook 时遇到错误而中止，导致后面的 extract_cookies_to_jar
        未能调用，因此 Cookies 并未更新。下一次再请求服务器的时候，就会遇到会话过期的情况。

        在这种情况下，需要在捕获错误后手动更新 cookies 以确保能够保持会话

        """
        if r.history:

            # If the hooks create history then we want those cookies too
            for resp in r.history:
                extract_cookies_to_jar(self._session.cookies, resp.request, resp.raw)

        extract_cookies_to_jar(self._session.cookies, r.request, r.raw)

    def clear_cookies(self):
        self._session.cookies.clear()
