from rucio.client.client import Client
import os
import subprocess
import six
import json
import requests
from requests.exceptions import HTTPError


class RucioManager(object):
    def __init__(self):
        self.setup_rucio_account()
        self.client = Client()
        self.scope = "cms"

    def setup_rucio_account(self):
        os.environ["RUCIO_CONFIG"] = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), "rucio.cfg"
        )
        if "RUCIO_ACCOUNT" not in os.environ:
            dn = subprocess.check_output(["grid-proxy-info", "-identity"]).strip()
            dn = dn.decode("utf-8")
            os.environ["RUCIO_ACCOUNT"] = os.environ.get("USER", "")
            print(
                f"Warning! 'RUCIO_ACCOUNT' was set to {os.environ.get("USER", "")}. This might be wrong."
                "Set the 'RUCIO_ACCOUNT' env variable to the correct name if it is different."
            )


        # warn if account not found
        if "RUCIO_ACCOUNT" not in os.environ:
            print(
                "Warning! Could not identify correct RUCIO_ACCOUNT: no person mapped "
                "to certificate DN ({dn}). Requests to Rucio API will likely fail.".format(
                    dn=dn
                )
            )
        else:
            print("Using rucio account %s" % os.environ["RUCIO_ACCOUNT"])

    def get_rucio_blocks(self, samplename):
        # in rucio, different naming is used:
        # containers -> datasets
        # datasets -> blocks
        # get the full list of available blocks
        # first get the container containing the dids
        blocks = self.client.list_content(
            scope=self.scope,
            name=samplename,
        )
        blocks = [block["name"] for block in blocks]
        filelist = []
        for block in list(blocks):
            files = list(self.client.list_files(scope=self.scope, name=block))
            filelist.extend([details["name"] for details in files])
        return filelist


def readJSON(url, params=None, headers={}, cert=None, method="GET"):
    url = readURL(url, params, headers, cert, method)
    print("Read JSON from", url)
    return json.loads(url)


def readURL(url, params=None, headers={}, cert=None, method="GET"):
    headers.setdefault("User-Agent", "toolKIT/0.1")

    rest_client = RESTClient(cert=cert, default_headers=headers)

    print("Starting http query: %r %r" % (url, params))
    print("Connecting with header: %r" % headers)

    try:
        if method in ("POST", "PUT"):
            return getattr(rest_client, method.lower())(url=url, data=params)
        else:
            return getattr(rest_client, method.lower())(url=url, params=params)
    except:
        print("Unable to open", url, "with arguments", params, "and header", headers)
        raise


class RESTClient(object):
    def __init__(
        self, cert=None, default_headers=None, result_process_func=lambda x: x
    ):
        self._session = RequestSession(cert=cert, default_headers=default_headers)
        self._result_process_func = result_process_func

    def _request(self, request_method, url, api, headers, **kwargs):
        if api:
            url = "%s/%s" % (url, api)
        return self._result_process_func(
            self._session.request(request_method, url, headers=headers, **kwargs)
        )

    def get(self, url, api=None, headers=None, params=None):
        return self._request("GET", url, api=api, headers=headers, params=params)

    def post(self, url, api=None, headers=None, data=None):
        return self._request("POST", url, api=api, headers=headers, data=data)

    def put(self, url, api=None, headers=None, data=None):
        return self._request("PUT", url, api=api, headers=headers, data=data)

    def delete(self, url, api=None, headers=None, params=None):
        return self._request("DELETE", url, api=api, headers=headers, params=params)


class JSONRESTClient(RESTClient):
    def __init__(self, cert=None, default_headers=None, result_process_func=None):
        default_headers = default_headers or {}
        default_headers.update(
            {"Content-Type": "application/json", "Accept": "application/json"}
        )
        if not result_process_func:

            def result_process_func(result):
                return json.loads(result)

        super(JSONRESTClient, self).__init__(
            cert=cert,
            default_headers=default_headers,
            result_process_func=result_process_func,
        )


class RequestSession(object):
    _requests_client_session = None

    def __init__(self, cert=None, default_headers=None):
        self._cert, self._default_headers = cert, default_headers or {}

        # disable ssl ca verification errors
        from requests.packages.urllib3.exceptions import InsecureRequestWarning

        requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

        if not self._requests_client_session:
            self._create_session()

    @classmethod
    def _create_session(cls):
        cls._requests_client_session = requests.Session()

    def _raise_for_status(self, response):
        """
        checks for status not ok and raises corresponding http error
        """
        try:
            response.raise_for_status()
        except HTTPError as http_error:
            if six.PY2:
                raise HTTPError(
                    "Server response: %s\nInfos: %s"
                    % (str(http_error).encode("utf-8"), response.text.encode("utf-8"))
                )
            elif six.PY3:
                raise HTTPError(
                    "Server response: %s\nInfos: %s" % (str(http_error), response.text)
                )
            else:
                assert False

    def request(self, request_method, url, headers, **kwargs):
        headers = (headers or {}).update(self._default_headers)
        request_func = getattr(self._requests_client_session, request_method.lower())
        response = request_func(
            url=url, verify=False, cert=self._cert, headers=headers, **kwargs
        )
        self._raise_for_status(response)
        # str() to avoid codec problems
        return str(response.text)
