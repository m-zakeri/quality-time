import React from 'react';
import { HeaderWithDetails } from '../widgets/HeaderWithDetails';
import { Grid } from 'semantic-ui-react';
import { ChangeLog } from '../changelog/ChangeLog';
import { StringInput } from '../fields/StringInput';
import { MultipleChoiceInput } from '../fields/MultipleChoiceInput';
import { set_reports_attribute } from '../api/report';
import { EDIT_ENTITY_PERMISSION, EDIT_REPORT_PERMISSION } from '../context/Permissions';

export function ReportsTitle(props) {

    function setPermissions(permission, value){
        const permissions = props.permissions
        permissions[permission] = value
        set_reports_attribute("permissions", permissions, props.reload)
    }

    return (
        <HeaderWithDetails level="h1" header={props.title} subheader={props.subtitle}>
            <Grid stackable>
                <Grid.Row columns={2}>
                    <Grid.Column>
                        <StringInput
                            id="report_overview_title"
                            requiredPermissions={[EDIT_REPORT_PERMISSION]}
                            label="Report overview title"
                            set_value={(value) => set_reports_attribute("title", value, props.reload)}
                            value={props.title}
                        />
                    </Grid.Column>
                    <Grid.Column>
                        <StringInput
                            id="report_overview_subtitle"
                            requiredPermissions={[EDIT_REPORT_PERMISSION]}
                            label="Report overview subtitle"
                            set_value={(value) => set_reports_attribute("subtitle", value, props.reload)}
                            value={props.subtitle}
                        />
                    </Grid.Column>
                </Grid.Row>
                <Grid.Row columns={1}>
                    <Grid.Column>
                        <MultipleChoiceInput
                            id="report_overview_edit_report_permission"
                            requiredPermissions={[EDIT_REPORT_PERMISSION]}
                            allowAdditions
                            label="Users allowed to edit reports (user name or email address)"
                            options={props.permissions[EDIT_REPORT_PERMISSION] || []}
                            placeholder="All authenticated users"
                            set_value={(value) => setPermissions(EDIT_REPORT_PERMISSION, value)}
                            value={props.permissions[EDIT_REPORT_PERMISSION]}
                        />
                    </Grid.Column>
                </Grid.Row>
                <Grid.Row columns={1}>
                    <Grid.Column>
                        <MultipleChoiceInput
                            id="report_overview_edit_entity_permission"
                            requiredPermissions={[EDIT_REPORT_PERMISSION]}
                            allowAdditions
                            label="Users allowed to edit measured entities (user name or email address)"
                            options={props.permissions[EDIT_ENTITY_PERMISSION] || []}
                            placeholder="All authenticated users"
                            set_value={(value) => setPermissions(EDIT_ENTITY_PERMISSION, value)}
                            value={props.permissions[EDIT_ENTITY_PERMISSION]}
                        />
                    </Grid.Column>
                </Grid.Row>
                <Grid.Row>
                    <Grid.Column>
                        <ChangeLog />
                    </Grid.Column>
                </Grid.Row>
            </Grid>
        </HeaderWithDetails>
    )
}
