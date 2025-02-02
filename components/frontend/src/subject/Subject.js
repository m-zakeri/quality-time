import React, { useEffect, useState } from 'react';
import { Dropdown, Table } from 'semantic-ui-react';
import { get_subject_measurements } from '../api/subject';
import { TrendTable } from '../trend_table/TrendTable';
import { SubjectDetails } from './SubjectDetails';
import { SubjectFooter } from './SubjectFooter';
import { SubjectTitle } from './SubjectTitle';


function displayedMetrics(allMetrics, hideMetricsNotRequiringAction, tags) {
  const metrics = {}
  Object.entries(allMetrics).forEach(([metric_uuid, metric]) => {
    if (hideMetricsNotRequiringAction && (metric.status === "target_met" || metric.status === "debt_target_met")) { return }
    if (tags.length > 0 && tags.filter(value => metric.tags?.includes(value)).length === 0) { return }
    metrics[metric_uuid] = metric
  })
  return metrics
}


export function Subject(props) {

  const subject = props.report.subjects[props.subject_uuid];
  const metrics = displayedMetrics(subject.metrics, props.hideMetricsNotRequiringAction, props.tags)

  const [measurements, setMeasurements] = useState([]);

  useEffect(() => {
    if (props.subjectTrendTable) {
      get_subject_measurements(props.subject_uuid, props.report_date).then(json => {
        if (json.ok !== false) {
          setMeasurements(json.measurements)
        }
      })
    }
    // eslint-disable-next-line
  }, [props.subjectTrendTable]);

  const hamburgerItems = (
    <>
      <Dropdown.Header>Views</Dropdown.Header>
      <Dropdown.Item onClick={() => props.setSubjectTrendTable(false)} active={!props.subjectTrendTable} >
        Details
      </Dropdown.Item>
      <Dropdown.Item onClick={() => props.setSubjectTrendTable(true)} active={props.subjectTrendTable} >
        Trend table
      </Dropdown.Item>
      <Dropdown.Header>Rows</Dropdown.Header>
      <Dropdown.Item onClick={() => props.setHideMetricsNotRequiringAction(!props.hideMetricsNotRequiringAction)}>
        {props.hideMetricsNotRequiringAction ? 'Show all metrics' : 'Hide metrics not requiring action'}
      </Dropdown.Item>
    </>
  )

  const subjectFooter = (
    <SubjectFooter
      datamodel={props.datamodel}
      subjectUuid={props.subject_uuid}
      subject={props.report.subjects[props.subject_uuid]}
      reload={props.reload}
      reports={props.reports}
      resetSortColumn={() => { }} />
  )

  return (
    <div id={props.subject_uuid}>
      <SubjectTitle subject={subject} {...props} />
      {props.subjectTrendTable ?
        <TrendTable
          datamodel={props.datamodel}
          reportDate={props.report_date}
          metrics={metrics}
          measurements={measurements}
          extraHamburgerItems={hamburgerItems}
          trendTableInterval={props.trendTableInterval}
          setTrendTableInterval={props.setTrendTableInterval}
          trendTableNrDates={props.trendTableNrDates}
          setTrendTableNrDates={props.setTrendTableNrDates}
          tableFooter={subjectFooter}
        />
        :
        <Table sortable>
          <SubjectDetails
            metrics={metrics}
            extraHamburgerItems={hamburgerItems}
            {...props} />
        </Table>
      }
    </div>
  )
}
