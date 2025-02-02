import React from 'react';
import { Header } from 'semantic-ui-react';
import { EDIT_REPORT_PERMISSION } from '../context/Permissions';
import { SingleChoiceInput } from '../fields/SingleChoiceInput';
import { Logo } from './Logo';

export function SourceType(props) {
  let options = [];
  props.datamodel.metrics[props.metric_type].sources.forEach(
    (key) => {
      const source_type = props.datamodel.sources[key];
      options.push(
        {
          key: key,
          text: source_type.name,
          value: key,
          content:
            <Header as="h4">
              <Header.Content>
                <Logo logo={key} alt={source_type.name} />{source_type.name}<Header.Subheader>{source_type.description}</Header.Subheader>
              </Header.Content>
            </Header>
        })
    });
  return (
    <SingleChoiceInput
      requiredPermissions={[EDIT_REPORT_PERMISSION]}
      label="Source type"
      options={options}
      set_value={(value) => props.set_source_attribute("type", value)}
      value={props.source_type}
    />
  )
}
