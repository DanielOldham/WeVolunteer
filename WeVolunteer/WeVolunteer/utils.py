"""
utils.py

Various utility functions
"""
from datastar_py.consts import ElementPatchMode
from datastar_py.sse import ServerSentEventGenerator
from django.http import HttpResponse


def respond_via_sse(
    html_response,
    signals=None,
    selector=None,
    patch_mode: ElementPatchMode=None,
    url=None,
) -> HttpResponse:
    """
    Respond to a request with a Server-Sent Event (SSE) response by patching elements.

    :param html_response: The HTML content to send as an SSE
    :param signals: Optional dictionary of signals to patch
    :param selector: Optional selector used to select fragments
    :param patch_mode: Optional patch mode used to patch elements
    :param url: Optional URL for saving URL state
    :return: An HttpResponse of the ServerSentEventGenerator that yields the HTML response
    """
    sse_response = ServerSentEventGenerator.patch_elements(
        html_response.content.decode("utf-8"), selector=selector, mode=patch_mode
    )
    if signals:
        sse_response = sse_response + ServerSentEventGenerator.patch_signals(signals)
    if url:
        sse_response = sse_response + ServerSentEventGenerator.execute_script(
            'window.history.replaceState({}, "", "' + url + '")'
        )

    response = HttpResponse(sse_response)
    response["Content-Type"] = "text/event-stream"
    response["Cache-Control"] = "no-cache"
    # response["Connection"] = "keep-alive"

    return response


def patch_signals_respond_via_sse(signals) -> HttpResponse:
    """
    Respond to a request with a Server-Sent Event (SSE) response by only patching Datastar signals.

    :param signals: Dictionary of signals to patch
    """
    sse_response = ServerSentEventGenerator.patch_signals(signals)

    response = HttpResponse(sse_response)
    response["Content-Type"] = "text/event-stream"
    response["Cache-Control"] = "no-cache"
    # response["Connection"] = "keep-alive"

    return response


def remove_respond_via_sse(selector) -> HttpResponse:
    """
    Respond to a request with a Server-Sent Event (SSE) response by removing elements.

    :param selector: Selector used to select elements
    :return: An HttpResponse of the ServerSentEventGenerator that yields the HTML response
    """

    sse_response = ServerSentEventGenerator.remove_elements(selector)

    response = HttpResponse(sse_response)
    response["Content-Type"] = "text/event-stream"
    response["Cache-Control"] = "no-cache"
    # response["Connection"] = "keep-alive"
    return response