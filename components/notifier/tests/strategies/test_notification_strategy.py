""""Unit tests for the notification strategies."""

from datetime import datetime, timedelta, timezone
import unittest

from strategies.notification_strategy import NotificationFinder

from ..data_model import DATA_MODEL


class Base(unittest.TestCase):  # skipcq: PTC-W0046
    """Base data needed by the other test classes."""

    @classmethod
    def setUpClass(cls) -> None:
        """Provide the data_model to the class."""
        cls.data_model = DATA_MODEL

    @staticmethod
    def metric(name="metric1", status="target_met", scale="count", recent_measurements=None, status_start=None):
        """Create a metric."""
        return dict(
            name=name,
            scale=scale,
            status=status,
            type="tests",
            unit="units",
            recent_measurements=recent_measurements or [],
            status_start=status_start or "",
        )


class StrategiesTests(Base):
    """Unit tests for the 'amount of new red metrics per report' notification strategy."""

    def setUp(self):
        """Set variables for the other testcases."""
        self.most_recent_measurement_seen = datetime.min.replace(tzinfo=timezone.utc)
        self.old_timestamp = "2019-01-01T00:00:00+00:00"
        self.new_timestamp = "2020-01-01T00:00:00+00:00"
        self.report_url = "https://report1"
        self.white_metric_status = "unknown"
        self.notification_finder = NotificationFinder(self.data_model)
        count = dict(status="target_not_met", value="10")
        self.red_metric = self.metric(
            status="target_not_met",
            recent_measurements=[dict(start=self.old_timestamp, end=self.new_timestamp, count=count)],
            status_start=str(self.most_recent_measurement_seen),
        )

    def test_no_reports(self):
        """Test that there is nothing to notify when there are no reports."""
        self.assertEqual(
            [], self.notification_finder.get_notifications(dict(reports=[]), self.most_recent_measurement_seen)
        )

    def test_no_red_metrics(self):
        """Test that there is nothing to notify when there are no red metrics."""
        count = dict(status="target_met", value="0")
        green_metric = self.metric(
            recent_measurements=[dict(start=self.old_timestamp, end=self.new_timestamp, count=count)]
        )
        subject1 = dict(metrics=dict(metric1=green_metric))
        report1 = dict(report_uuid="report1", title="report_title", subjects=dict(subject1=subject1))
        reports_json = dict(reports=[report1])
        self.assertEqual(
            [], self.notification_finder.get_notifications(reports_json, self.most_recent_measurement_seen)
        )

    def test_old_red_metric(self):
        """Test that there is nothing to notify if the red metric was already red."""
        subject1 = dict(metrics=dict(metric1=self.red_metric))
        report1 = dict(report_uuid="report1", title="Title", subjects=dict(subject1=subject1))
        reports_json = dict(reports=[report1])
        self.assertEqual(
            [], self.notification_finder.get_notifications(reports_json, self.most_recent_measurement_seen)
        )

    def test_red_metric_without_recent_measurements(self):
        """Test that there is nothing to notify if the red metric has no recent measurements."""
        red_metric1 = self.metric(status="target_not_met")
        red_metric2 = self.metric(status="target_not_met")
        subject1 = dict(metrics=dict(metric1=red_metric1, metric2=red_metric2))
        report1 = dict(report_uuid="report1", title="Title", subjects=dict(subject1=subject1))
        reports_json = dict(reports=[report1])
        self.assertEqual(
            [], self.notification_finder.get_notifications(reports_json, self.most_recent_measurement_seen)
        )

    def test_new_red_metric(self):
        """Test that a metric that has become red is included."""
        old_count = dict(status="target_met", value="5")
        new_count = dict(status="target_not_met", value="10")
        red_metric = self.metric(
            status="target_not_met",
            recent_measurements=[
                dict(start=self.old_timestamp, end=self.new_timestamp, count=old_count),
                dict(start=self.new_timestamp, end=self.new_timestamp, count=new_count),
            ],
        )
        subject1 = dict(metrics=dict(metric1=red_metric))
        report1 = dict(
            title="Title",
            report_uuid="report1",
            subjects=dict(subject1=subject1),
            notification_destinations=dict(uuid1=dict(name="destination1")),
        )
        reports_json = dict(reports=[report1])
        result = self.notification_finder.get_notifications(reports_json, self.most_recent_measurement_seen)
        self.assertEqual(
            ["metric1", "red (target not met)"],
            [result[0].metrics[0].metric_name, result[0].metrics[0].new_metric_status],
        )

    def test_new_red_metric_without_count_scale(self):
        """Test that a metric that doesn't have a count scale that became red is included."""
        old_percentage = dict(status="target_met", value="5")
        new_percentage = dict(status="target_not_met", value="10")
        red_metric = self.metric(
            name="",
            scale="percentage",
            status="target_not_met",
            recent_measurements=[
                dict(start=self.old_timestamp, end=self.new_timestamp, percentage=old_percentage),
                dict(start=self.new_timestamp, end=self.new_timestamp, percentage=new_percentage),
            ],
        )
        subject1 = dict(metrics=dict(metric1=red_metric))
        report1 = dict(
            title="Title",
            report_uuid="report1",
            subjects=dict(subject1=subject1),
            notification_destinations=dict(name="destination1"),
        )
        reports_json = dict(reports=[report1])
        result = self.notification_finder.get_notifications(reports_json, self.most_recent_measurement_seen)[0].metrics
        self.assertEqual(
            ["Tests"],
            [result[0].metric_name],
        )

    def test_recently_changed_metric_status(self):
        """Test that a metric that turns white is added."""
        metric = self.metric(
            status=self.white_metric_status,
            recent_measurements=[
                dict(start=self.new_timestamp, count=dict(status="target_met")),
                dict(start=self.old_timestamp, count=dict(status=self.white_metric_status)),
            ],
        )
        self.assertTrue(self.notification_finder.status_changed(metric, self.most_recent_measurement_seen))

    def test_new_measurement_same_status(self):
        """Test that a metric that was already white isn't added."""
        metric = self.metric(
            status=self.white_metric_status,
            recent_measurements=[
                dict(start=self.new_timestamp, count=dict(status=self.white_metric_status)),
                dict(start=self.old_timestamp, count=dict(status=self.white_metric_status)),
            ],
        )
        self.assertFalse(self.notification_finder.status_changed(metric, self.most_recent_measurement_seen))

    def test_no_change_due_to_only_one_measurement(self):
        """Test that metrics with only one measurement (and therefore no changes in value) aren't added."""
        metric = self.metric(
            status=self.white_metric_status,
            recent_measurements=[dict(start=self.old_timestamp, count=dict(status=self.white_metric_status))],
        )
        self.assertFalse(self.notification_finder.status_changed(metric, self.most_recent_measurement_seen))

    def test_no_change_due_to_no_measurements(self):
        """Test that metrics without measurements (and therefore no changes in value) aren't added."""
        metric = self.metric(status=self.white_metric_status)
        self.assertFalse(self.notification_finder.status_changed(metric, self.most_recent_measurement_seen))

    def test_multiple_reports_with_same_destination(self):
        """Test that the correct metrics are notified when multiple reports notify the same destination."""
        old_count = dict(status="target_met", value="5")
        new_count = dict(status="target_not_met", value="10")

        red_metric1 = self.metric(
            status="target_not_met",
            recent_measurements=[
                dict(start=self.old_timestamp, end=self.new_timestamp, count=old_count),
                dict(start=self.new_timestamp, end=self.new_timestamp, count=new_count),
            ],
        )
        subject1 = dict(metrics=dict(metric1=red_metric1))
        report1 = dict(
            title="Title",
            report_uuid="report1",
            webhook="webhook",
            subjects=dict(subject1=subject1),
            notification_destinations=dict(uuid1=dict(url=self.report_url, name="destination1")),
        )

        red_metric2 = self.metric(
            name="metric2",
            status="target_met",
            recent_measurements=[
                dict(start=self.old_timestamp, end=self.new_timestamp, count=old_count),
                dict(start=self.new_timestamp, end=self.new_timestamp, count=new_count),
            ],
        )
        subject2 = dict(metrics=dict(metric1=red_metric2))
        report2 = dict(
            title="Title",
            report_uuid="report2",
            webhook="webhook",
            subjects=dict(subject1=subject2),
            notification_destinations=dict(uuid1=dict(url="https://report2", name="destination2")),
        )
        result = []
        reports_json = dict(reports=[report1, report2])
        for notification in self.notification_finder.get_notifications(reports_json, self.most_recent_measurement_seen):
            result.append(notification.metrics)
        self.assertEqual(["metric1", "metric2"], [result[0][0].metric_name, result[1][0].metric_name])

    def test_no_notification_destinations_configured(self):
        """Test that no notification is to be sent if there are no configurations in notification destinations."""
        old_count = dict(status="target_met", value="5")
        new_count = dict(status="target_not_met", value="10")
        red_metric = self.metric(
            name="metric1",
            status="target_not_met",
            recent_measurements=[
                dict(start=self.old_timestamp, end=self.new_timestamp, count=old_count),
                dict(start=self.new_timestamp, end=self.new_timestamp, count=new_count),
            ],
        )
        subject1 = dict(metrics=dict(metric1=red_metric))
        report = dict(
            title="Title",
            report_uuid="report1",
            webhook="webhook",
            subjects=dict(subject1=subject1),
            notification_destinations={},
        )
        report_json = dict(reports=[report])
        self.assertEqual([], self.notification_finder.get_notifications(report_json, self.most_recent_measurement_seen))

    def test_no_notification_destinations_in_json(self):
        """Test that no notification is to be sent if notification destinations do not exist in the data."""
        old_count = dict(status="target_met", value="5")
        new_count = dict(status="target_not_met", value="10")
        red_metric = self.metric(
            name="metric1",
            status="target_not_met",
            recent_measurements=[
                dict(start=self.old_timestamp, end=self.new_timestamp, count=old_count),
                dict(start=self.new_timestamp, end=self.new_timestamp, count=new_count),
            ],
        )
        subject1 = dict(metrics=dict(metric1=red_metric))
        report = dict(title="Title", report_uuid="report1", webhook="webhook", subjects=dict(subject1=subject1))
        report_json = dict(reports=[report])
        self.assertEqual([], self.notification_finder.get_notifications(report_json, self.most_recent_measurement_seen))


class LongUnchangedTests(Base):
    """Unit tests for the 'status long unchanged' notification strategy."""

    def setUp(self):
        """Override to set up a metric fixture."""
        self.old_timestamp = "2019-02-01T00:00:00+00:00"
        self.new_timestamp = "2020-02-01T00:00:00+00:00"
        self.notification_finder = NotificationFinder(self.data_model)
        self.red_metric = self.metric(
            status="target_not_met",
            recent_measurements=[dict(start=self.old_timestamp, end=self.new_timestamp)],
            status_start=self.old_timestamp,
        )

    def test_long_unchanged_status(self):
        """Test that a metric is notable if its status has been the same for 3 weeks."""
        now = datetime.now()
        self.red_metric["status_start"] = str(now - timedelta(days=21, hours=1))
        self.assertEqual(
            "status_long_unchanged", self.notification_finder.get_notification(self.red_metric, "red_metric", now)
        )

    def test_long_unchanged_status_already_notified(self):
        """Test that a metric is not notable if a notification has already been generated for the long status."""
        now = datetime.now()
        self.red_metric["status_start"] = str(now - timedelta(days=21, hours=1))
        self.notification_finder.already_notified.append("red_metric")
        self.assertEqual(None, self.notification_finder.get_notification(self.red_metric, "red_metric", now))

    def test_too_long_unchanged_status(self):
        """Test that a metric isn't notable if its status has been the same for more than 3 weeks."""
        now = datetime.now()
        self.red_metric["status_start"] = str(now - timedelta(days=100))
        self.assertEqual(None, self.notification_finder.get_notification(self.red_metric, "red_metric", now))

    def test_short_unchanged_status(self):
        """Test that a metric isn't notable if its current status has changed in the last 3 weeks."""
        now = datetime.now()
        self.red_metric["status_start"] = str(now - timedelta(days=20, hours=23))
        self.assertEqual(None, self.notification_finder.get_notification(self.red_metric, "red_metric", now))


class CheckIfMetricIsNotableTestCase(Base):
    """Unit tests for the check_if_metric_is_notable method."""

    def setUp(self):
        """Set variables for the tests."""
        self.old_timestamp = "2019-03-01T00:00:00+00:00"
        self.new_timestamp = "2020-03-01T00:00:00+00:00"
        self.metric_uuid = "metric_uuid"
        self.red_metric = self.metric(
            status="target_not_met",
            recent_measurements=[],
            status_start=str(datetime.fromisoformat(datetime.min.isoformat())),
        )
        self.notification_finder = NotificationFinder(self.data_model)
        self.metric_with_recent_measurements = self.metric(
            recent_measurements=[
                dict(start=self.old_timestamp, end=self.old_timestamp, count=dict(status="target_not_met", value="10")),
                dict(
                    start=self.old_timestamp,
                    end=self.new_timestamp,
                    count=dict(
                        status="target_not_met",
                        value="0",
                        status_start=self.old_timestamp,
                    ),
                ),
            ],
            status_start=self.old_timestamp,
        )

    def test_metric_not_notable_if_no_recent_measurements(self):
        """Test that a metric is not notable if it does not contain any recent measurements."""
        self.assertIsNone(
            self.notification_finder.get_notification(
                self.red_metric, self.metric_uuid, datetime.min.replace(tzinfo=timezone.utc)
            )
        )

    def test_metric_is_notable_because_status_changed(self):
        """Test that a metric is notable because the status changed."""
        metric = self.metric(
            recent_measurements=[
                dict(start=self.old_timestamp, end=self.old_timestamp, count=dict(status="target_not_met", value="10")),
                dict(start=self.old_timestamp, end=self.new_timestamp, count=dict(status="target_met", value="0")),
            ]
        )
        self.assertEqual(
            "status_changed",
            self.notification_finder.get_notification(
                metric, self.metric_uuid, datetime.min.replace(tzinfo=timezone.utc)
            ),
        )

    def test_metric_already_notified_is_removed_because_status_changed(self):
        """Test that the metric is removed from already notified when the status changes."""
        metric = self.metric(
            recent_measurements=[
                dict(start=self.old_timestamp, end=self.old_timestamp, count=dict(status="target_not_met", value="10")),
                dict(start=self.old_timestamp, end=self.new_timestamp, count=dict(status="target_met", value="0")),
            ]
        )
        self.notification_finder.already_notified.append(self.metric_uuid)
        self.notification_finder.get_notification(metric, self.metric_uuid, datetime.min.replace(tzinfo=timezone.utc))
        self.assertEqual(self.notification_finder.already_notified, [])

    def test_metric_is_notable_because_status_unchanged_3weeks(self):
        """Test that a metric is notable for long unchanged status."""
        self.assertEqual(
            "status_long_unchanged",
            self.notification_finder.get_notification(
                self.metric_with_recent_measurements,
                self.metric_uuid,
                datetime.fromisoformat(self.old_timestamp) + timedelta(days=21, hours=12),
            ),
        )

    def test_metric_not_notable_if_already_notified(self):
        """Test that a metric isn't notable for long unchanged status if a notification has already been generated."""
        self.notification_finder.already_notified.append(self.metric_uuid)
        self.assertIsNone(
            self.notification_finder.get_notification(
                self.metric_with_recent_measurements,
                self.metric_uuid,
                datetime.fromisoformat(self.old_timestamp) + timedelta(days=21, hours=12),
            )
        )
