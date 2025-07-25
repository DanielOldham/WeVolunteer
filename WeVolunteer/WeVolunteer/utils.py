"""
utils.py

Various utility functions
"""
from datastar_py.consts import FragmentMergeMode
from datastar_py.sse import ServerSentEventGenerator
from django.http import HttpResponse


def respond_via_sse(
    html_response,
    signals=None,
    selector=None,
    merge_mode: FragmentMergeMode=None,
    url=None,
):
    """
    Respond to a request with a Server-Sent Event (SSE) response by merging fragments.

    :param html_response: The HTML content to send as an SSE
    :param signals: include these signals
    :param selector: Optional selector used to select fragments
    :param merge_mode: Optional merge mode used to merge fragments
    :param url: Optional URL for saving URL state
    :return: A ServerSentEventGenerator that yields the HTML response
    """
    sse_response = ServerSentEventGenerator.merge_fragments(
        html_response.content.decode("utf-8"), selector=selector, merge_mode=merge_mode
    )
    if signals:
        sse_response = sse_response + ServerSentEventGenerator.merge_signals(signals)
    if url:
        sse_response = sse_response + ServerSentEventGenerator.execute_script(
            'window.history.replaceState({}, "", "' + url + '")'
        )

    response = HttpResponse(sse_response)
    response["Content-Type"] = "text/event-stream"
    response["Cache-Control"] = "no-cache"
    # response["Connection"] = "keep-alive"

    return response


def remove_respond_via_sse(selector):
    """
    Respond to a request with a Server-Sent Event (SSE) response by removing fragments.

    :param selector: Selector used to select fragments.
    :return: A ServerSentEventGenerator that yields the HTML response.
    """

    sse_response = ServerSentEventGenerator.remove_fragments(selector)

    response = HttpResponse(sse_response)
    response["Content-Type"] = "text/event-stream"
    response["Cache-Control"] = "no-cache"
    # response["Connection"] = "keep-alive"
    return response