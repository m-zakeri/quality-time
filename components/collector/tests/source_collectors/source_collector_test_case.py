"""Base class for source collector unit tests."""

import io
import json
import logging
import pathlib
import unittest
import sys
import zipfile
from typing import Union
from unittest.mock import AsyncMock, PropertyMock, patch

import aiohttp

from base_collectors import MetricCollector


MODULE_DIR = pathlib.Path(__file__).resolve().parent
SERVER_SRC_PATH = MODULE_DIR.parent.parent.parent / "server" / "src"
sys.path.insert(0, str(SERVER_SRC_PATH))
from data_model import DATA_MODEL_JSON  # pylint: disable=import-error,wrong-import-order,wrong-import-position

DATA_MODEL = json.loads(DATA_MODEL_JSON)


class SourceCollectorTestCase(unittest.IsolatedAsyncioTestCase):  # skipcq: PTC-W0046
    """Base class for source collector unit tests."""

    METRIC_TYPE = SOURCE_TYPE = "Subclass responsibility"
    METRIC_ADDITION = "sum"

    @classmethod
    def setUpClass(cls) -> None:  # pylint: disable=invalid-name
        """Override to disable logging and load the data model so it is available for all unit tests."""
        logging.disable(logging.CRITICAL)
        cls.data_model = DATA_MODEL

    @classmethod
    def tearDownClass(cls) -> None:  # pylint: disable=invalid-name
        """Override to reset logging."""
        logging.disable(logging.NOTSET)

    def setUp(self) -> None:  # pylint: disable=invalid-name
        """Extend to set up the source and metric under test."""
        self.sources = dict(source_id=dict(type=self.SOURCE_TYPE, parameters=dict(url=f"https://{self.SOURCE_TYPE}")))
        self.metric = dict(type=self.METRIC_TYPE, sources=self.sources, addition=self.METRIC_ADDITION)

    async def collect(
        self,
        *,
        get_request_json_return_value=None,
        get_request_json_side_effect=None,
        get_request_content="",
        get_request_text="",
        get_request_headers=None,
        get_request_links=None,
        post_request_side_effect=None,
        post_request_json_return_value=None,
    ):
        """Collect the metric."""
        get_request = self.__mock_get_request(
            self.__mock_get_request_json(get_request_json_return_value, get_request_json_side_effect),
            get_request_content,
            get_request_text,
            get_request_headers,
            get_request_links,
        )
        post_request = self.__mock_post_request(post_request_json_return_value)
        mocked_get = AsyncMock(return_value=get_request)
        mocked_post = AsyncMock(return_value=post_request, side_effect=post_request_side_effect)
        with patch("aiohttp.ClientSession.get", mocked_get), patch("aiohttp.ClientSession.post", mocked_post):
            async with aiohttp.ClientSession() as session:
                collector = MetricCollector(session, self.metric, self.data_model)
                return await collector.collect()

    @staticmethod
    def __mock_get_request(get_request_json, content, text, headers, links) -> AsyncMock:
        """Create the mock get request."""
        get_request = AsyncMock()
        get_request.json = get_request_json
        get_request.read.return_value = content
        get_request.text.return_value = text
        type(get_request).headers = PropertyMock(return_value=headers or {})
        type(get_request).links = PropertyMock(return_value={}, side_effect=[links, {}] if links else None)
        type(get_request).filename = PropertyMock(return_value="")
        return get_request

    @staticmethod
    def __mock_get_request_json(json_return_value, json_side_effect) -> AsyncMock:
        """Create the mock JSON."""
        get_request_json = AsyncMock()
        get_request_json.side_effect = json_side_effect
        get_request_json.return_value = json_return_value
        return get_request_json

    @staticmethod
    def __mock_post_request(json_return_value) -> AsyncMock:
        """Create the mock post request."""
        post_request = AsyncMock()
        post_request.json.return_value = json_return_value
        return post_request

    def assert_measurement(self, measurement, *, source_index: int = 0, **attributes) -> None:
        """Assert that the measurement has the expected attributes."""
        for attribute_key in ("connection_error", "parse_error"):
            if (attribute_value := attributes.get(attribute_key)) is not None:
                self.assertIn(attribute_value, getattr(measurement.sources[source_index], attribute_key))
            else:
                self.assertIsNone(getattr(measurement.sources[source_index], attribute_key))
        for attribute_key in ("value", "total", "entities", "api_url", "landing_url"):
            if (attribute_value := attributes.get(attribute_key, "value not specified")) != "value not specified":
                self.__assert_measurement_source_attribute(attribute_key, attribute_value, measurement, source_index)

    def __assert_measurement_source_attribute(self, attribute_key, attribute_value, measurement, source_index):
        """Assert that the measurement source attribute has the expected value."""
        if isinstance(attribute_value, list):
            for pair in zip(attribute_value, getattr(measurement.sources[source_index], attribute_key)):
                assert_equal = self.assertDictEqual if isinstance(pair[0], dict) else self.assertEqual
                assert_equal(pair[0], pair[1])
        else:
            self.assertEqual(attribute_value, getattr(measurement.sources[source_index], attribute_key))

    @staticmethod
    def zipped_report(*filenames_and_contents: tuple[str, str]) -> bytes:
        """Return a zipped report."""
        bytes_io = io.BytesIO()
        with zipfile.ZipFile(bytes_io, mode="w") as zipped_report:
            for filename, content in filenames_and_contents:
                zipped_report.writestr(filename, content)
        return bytes_io.getvalue()

    def set_source_parameter(self, key: str, value: Union[str, list[str]]) -> None:
        """Set a source parameter."""
        self.sources["source_id"]["parameters"][key] = value
