import {Given} from "cypress-cucumber-preprocessor/steps";

const url = "/example-report-hq";

Given(/^I visit the report and login$/, () => {
    cy.visit(url);
    cy.title().should('eq', 'Quality-time');
    cy.get(".button").contains('Login').click();
    cy.fixture('credentials.json').then((credentials) =>
        cy.get('input[name="username"]')
            .type(credentials.username));
    cy.fixture('credentials.json').then((credentials) =>
        cy.get('input[name="password"]')
            .type(credentials.password));
    cy.get('.button').contains('Submit').click()
});