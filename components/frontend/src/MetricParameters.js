import React from 'react';
import { Table } from 'semantic-ui-react';
import { MetricComment } from './MetricComment';
import { MetricName } from './MetricName';
import { MetricTarget } from './MetricTarget';
import { MetricType } from './MetricType';

function MetricParameters(props) {
    const metric_type = props.datamodel.metrics[props.metric.type];
    const metric_name = props.metric.name || metric_type.name;
    return (
        <Table columns={2} basic='very' size='small'>
            <Table.Body>
                <Table.Row>
                    <Table.Cell>Metric type</Table.Cell>
                    <Table.Cell>
                        <MetricType report_uuid={props.report_uuid} metric_uuid={props.metric_uuid}
                            datamodel={props.datamodel} metric_type={props.metric.type} reload={props.reload} />
                    </Table.Cell>
                </Table.Row>
                <Table.Row>
                    <Table.Cell>Metric name</Table.Cell>
                    <Table.Cell>
                        <MetricName report_uuid={props.report_uuid} metric_uuid={props.metric_uuid}
                            datamodel={props.datamodel} metric_name={metric_name} reload={props.reload} />
                    </Table.Cell>
                </Table.Row>
                <Table.Row>
                    <Table.Cell>Metric target</Table.Cell>
                    <Table.Cell>
                        <MetricTarget report_uuid={props.report_uuid} metric_uuid={props.metric_uuid}
                            unit={metric_type.unit} direction={metric_type.direction} reload={props.reload}
                            target={props.metric.target} />
                    </Table.Cell>
                </Table.Row>
                <Table.Row>
                    <Table.Cell>Comment</Table.Cell>
                    <Table.Cell>
                        <MetricComment report_uuid={props.report_uuid} metric_uuid={props.metric_uuid}
                            comment={props.metric.comment} reload={props.reload} />
                    </Table.Cell>
                </Table.Row>
            </Table.Body>
        </Table>
    )
}

export { MetricParameters };