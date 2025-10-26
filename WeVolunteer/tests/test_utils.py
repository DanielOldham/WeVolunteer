from django.test import SimpleTestCase
from django.http import HttpResponse
from unittest.mock import patch, MagicMock
from datastar_py.consts import ElementPatchMode

from WeVolunteer.utils import (
    respond_via_sse,
    patch_signals_respond_via_sse,
    remove_respond_via_sse,
)


class RespondViaSseTests(SimpleTestCase):
    """
    Test class for the SSE response util function.
    """

    @patch("WeVolunteer.utils.ServerSentEventGenerator.patch_elements")
    @patch("WeVolunteer.utils.ServerSentEventGenerator.patch_signals")
    @patch("WeVolunteer.utils.ServerSentEventGenerator.execute_script")
    def test_respond_via_sse_full_parameters(
        self, mock_execute_script, mock_patch_signals, mock_patch_elements
    ):
        html_response = MagicMock()
        html_response.content.decode.return_value = "<div></div>"
        mock_patch_elements.return_value = "patched_html"
        mock_patch_signals.return_value = "patched_signals"
        mock_execute_script.return_value = "script_result"

        response = respond_via_sse(
            html_response=html_response,
            signals={"event": "signal"},
            selector="#example",
            patch_mode=ElementPatchMode.REPLACE,
            url="/updated/url",
        )

        mock_patch_elements.assert_called_once_with(
            "<div></div>", selector="#example", mode=ElementPatchMode.REPLACE
        )
        mock_patch_signals.assert_called_once_with({"event": "signal"})
        mock_execute_script.assert_called_once_with(
            'window.history.replaceState({}, "", "/updated/url")'
        )

        content = response.content.decode()
        self.assertIn("patched_html", content)
        self.assertIn("patched_signals", content)
        self.assertIn("script_result", content)

        self.assertIsInstance(response, HttpResponse)
        self.assertEqual(response["Content-Type"], "text/event-stream")
        self.assertEqual(response["Cache-Control"], "no-cache")

    @patch("WeVolunteer.utils.ServerSentEventGenerator.patch_elements", return_value="patched_html")
    def test_respond_via_sse_no_signals_or_url_uses_default_mode(self, mock_patch_elements):
        html_response = MagicMock()
        html_response.content.decode.return_value = "hello"

        result = respond_via_sse(html_response=html_response)
        mock_patch_elements.assert_called_once_with("hello", selector=None, mode=None)
        self.assertIsInstance(result, HttpResponse)
        self.assertEqual(result["Content-Type"], "text/event-stream")
        self.assertEqual(result["Cache-Control"], "no-cache")

    @patch("WeVolunteer.utils.ServerSentEventGenerator.patch_elements", return_value="patched_html")
    @patch("WeVolunteer.utils.ServerSentEventGenerator.patch_signals", return_value="signals_added")
    def test_respond_via_sse_with_signals_without_url(self, mock_patch_signals, mock_patch_elements):
        html_response = MagicMock()
        html_response.content.decode.return_value = "body"
        response = respond_via_sse(html_response, signals={"state": "active"})
        self.assertIn("signals_added", response.content.decode())
        mock_patch_signals.assert_called_once_with({"state": "active"})


class PatchSignalsRespondViaSseTests(SimpleTestCase):
    """
    Test class for the patch signals via SSE util function.
    """

    @patch("WeVolunteer.utils.ServerSentEventGenerator.patch_signals")
    def test_patch_signals_respond_function(self, mock_patch_signals):
        mock_patch_signals.return_value = "patched_signals_str"

        response = patch_signals_respond_via_sse({"item": 1})

        mock_patch_signals.assert_called_once_with({"item": 1})
        self.assertIsInstance(response, HttpResponse)
        self.assertEqual(response["Content-Type"], "text/event-stream")
        self.assertEqual(response["Cache-Control"], "no-cache")
        self.assertIn("patched_signals_str", response.content.decode())


class RemoveRespondViaSseTests(SimpleTestCase):
    """
    Test class for the remove via SSE util function.
    """
    @patch("WeVolunteer.utils.ServerSentEventGenerator.remove_elements")
    def test_remove_respond_function(self, mock_remove_elements):
        mock_remove_elements.return_value = "removed_string"

        response = remove_respond_via_sse("#old-element")

        mock_remove_elements.assert_called_once_with("#old-element")
        self.assertIsInstance(response, HttpResponse)
        self.assertEqual(response["Content-Type"], "text/event-stream")
        self.assertEqual(response["Cache-Control"], "no-cache")
        self.assertIn("removed_string", response.content.decode())
