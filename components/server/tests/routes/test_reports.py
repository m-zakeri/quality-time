"""Unit tests for the reports routes."""

import unittest
from unittest.mock import Mock, patch

from routes.reports import get_reports, post_reports_attribute

from .fixtures import METRIC_ID, REPORT_ID, SOURCE_ID, SUBJECT_ID


class ReportsTest(unittest.TestCase):
    """Unit tests for the reports routes."""

    def setUp(self):
        self.database = Mock()
        self.database.sessions.find_one.return_value = dict(user="Jenny")

    @patch("bottle.request")
    def test_post_reports_attribute_title(self, request):
        """Test that a reports (overview) attribute can be changed."""
        self.database.reports_overviews.find_one.return_value = dict(_id="id", title="Reports")
        request.json = dict(title="All the reports")
        self.assertEqual(dict(ok=True), post_reports_attribute("title", self.database))
        inserted = self.database.reports_overviews.insert.call_args_list[0][0][0]
        self.assertEqual(
            "Jenny changed the title of the reports overview from 'Reports' to 'All the reports'.",
            inserted["delta"]["description"])

    @patch("bottle.request")
    def test_post_reports_attribute_layout(self, request):
        """Test that a reports (overview) layout can be changed."""
        self.database.reports_overviews.find_one.return_value = dict(_id="id", title="Reports")
        request.json = dict(layout=[dict(x=1, y=2)])
        self.assertEqual(dict(ok=True), post_reports_attribute("layout", self.database))
        inserted = self.database.reports_overviews.insert.call_args_list[0][0][0]
        self.assertEqual("Jenny changed the layout of the reports overview.", inserted["delta"]["description"])

    def test_get_report(self):
        """Test that a report can be retrieved."""
        self.database.datamodels.find_one.return_value = dict(
            _id="id", metrics=dict(metric_type=dict(default_scale="count")))
        self.database.reports_overviews.find_one.return_value = dict(_id="id", title="Reports", subtitle="")
        self.database.measurements.find.return_value = [
            dict(
                _id="id", metric_uuid=METRIC_ID, status="red",
                sources=[dict(source_uuid=SOURCE_ID, parse_error=None, connection_error=None, value="42")])]
        self.database.reports.distinct.return_value = [REPORT_ID]
        report = dict(
            _id="id", report_uuid=REPORT_ID,
            subjects={
                SUBJECT_ID: dict(
                    metrics={
                        METRIC_ID: dict(
                            type="metric_type", addition="sum", target="0", near_target="10", debt_target="0",
                            accept_debt=False, tags=["a"])})})
        self.database.reports.find_one.return_value = report
        report["summary"] = dict(red=0, green=0, yellow=0, grey=0, white=1)
        report["summary_by_subject"] = {SUBJECT_ID: dict(red=0, green=0, yellow=0, grey=0, white=1)}
        report["summary_by_tag"] = {}
        self.assertEqual(dict(_id="id", title="Reports", subtitle="", reports=[report]), get_reports(self.database))