# Project Discovery Question Framework

Comprehensive question bank organized by discovery module. Adapt questions based on project context.

## Table of Contents
1. [Scope & Context](#scope--context)
2. [Project Management](#project-management)
3. [Systems Inventory](#systems-inventory)
4. [Integration Architecture](#integration-architecture)
5. [Testing & Signoff](#testing--signoff)
6. [Documentation Requirements](#documentation-requirements)
7. [Marketing Function](#marketing-function)
8. [Sales Function](#sales-function)
9. [Service Function](#service-function)
10. [Operations & Data Management](#operations--data-management)

---

## Scope & Context

### Project Identification
- Project/deal title
- Primary stakeholder/owner
- Sales or account manager

### Project Triggers & Goals

**Open-ended:**
- What is triggering this project? What business problems are you solving?
- What are the overarching business goals this project supports?
- What specific outcomes define project success?

**Structured (select all that apply):**
- [ ] Cost reduction / efficiency
- [ ] Revenue growth
- [ ] Improve usability / adoption
- [ ] Digital transformation / innovation
- [ ] Compliance / regulatory requirement
- [ ] System consolidation
- [ ] Platform end-of-life / forced migration
- [ ] Scalability / performance
- [ ] Better reporting / visibility

### Timeline

| Question | Type |
|----------|------|
| Project start date | Date |
| Desired go-live date | Date |
| What factors drive or constrain these dates? | Open |
| Are there hard deadlines (fiscal year, contracts, events)? | Yes/No + Details |
| Is a phased approach acceptable? | Yes/No |

### Organizational Scope

**Divisions & Business Units:**
- How many distinctive business divisions/units operate differently and are in scope?
- For each: Name, region, key differences in process

**Brand Identities:**
- How many distinctive brand identities are included?
- Link to brand guidelines if available

**Functions in Scope:**
- [ ] Marketing
- [ ] Sales
- [ ] Service/Support
- [ ] Operations
- [ ] Finance
- [ ] Other: ________

### Compliance & Regulatory

- What compliance, regulatory, or data privacy frameworks apply?
  - [ ] GDPR
  - [ ] HIPAA
  - [ ] CCPA
  - [ ] SOC 2
  - [ ] PCI-DSS
  - [ ] Industry-specific: ________
- Are there data residency requirements?
- Security certifications required from vendors?

### Stakeholders

| Role | Name | Involvement Level | Decision Authority |
|------|------|-------------------|-------------------|
| Executive Sponsor | | | |
| Project Manager | | | |
| Technical Lead | | | |
| Business Lead | | | |
| End User Representatives | | | |

- Will you have a central project manager as primary point of contact?
- Language preferences for key project roles?

### Post-Go-Live

- How will ongoing change management be handled?
  - [ ] Internal team
  - [ ] Partner managed services
  - [ ] Hypercare period then internal
- How will solution maintenance and optimization be handled?

### Budget Contingency

- If additional hours are required beyond initial estimates, how would you prefer to handle?
  - [ ] Re-prioritize requirements within agreed budget
  - [ ] Access contingency fund
  - [ ] Approve change orders as needed
  - [ ] Defer to future phase

---

## Project Management

### Meeting Cadence

- Describe project meeting requirements (frequency, format, attendees)
- Standing meeting preferences?
- Time zone considerations?

### Collaboration Tools

| Tool | Purpose | Access Needed? |
|------|---------|---------------------|
| | | |

Examples: Teams, Slack, Jira, Asana, Monday.com, Confluence

### Budget & Reporting

- Standard budget reporting is [frequency]. Do you require more frequent reporting?
- Custom budget reporting requirements?
  - [ ] By phase
  - [ ] By workstream
  - [ ] By resource type
  - [ ] Other: ________

### Governance

- Standard governance includes RACI, stakeholder mapping, weekly risk/issue reporting. Additional requirements?
- Is there a project steering committee?
  - [ ] No
  - [ ] Yes, led by client
  - [ ] Yes, led by partner
  - [ ] Yes, joint leadership
- Steering committee meeting frequency?
  - [ ] Weekly
  - [ ] Bi-weekly
  - [ ] Monthly
  - [ ] Quarterly

---

## Systems Inventory

### Current Platform Assessment

**If already using target platform:**
- Which functions currently use it?
- How many instances/portals?
- Current products/modules in use?
- Total record counts by object type?
- Custom objects in use?
- Approximate active workflow/automation count?
- Current integration count?
- Total user count?
- Overall complexity assessment (Low/Medium/High)?

### Systems Inventory Matrix

For each system relevant to the project:

| System | Category | Purpose | Integration Needed? | Data Migration? | Status |
|--------|----------|---------|---------------------|-----------------|--------|
| | CRM / MAP / ERP / etc. | | Uni/Bi/None | Yes/No | Current/New/Retiring |

Include: CRMs, marketing automation, ERPs, data warehouses, BI tools, communication tools, AI/LLM systems

### Data Migration Requirements

| Data Type | Source System | Volume (Records) | Historical Depth | Priority |
|-----------|---------------|------------------|------------------|----------|
| | | | | |

- Data types: Contacts, Companies, Deals/Opportunities, Activities, Campaigns, Custom objects
- Historical engagement data requirements?
- Data cleansing planned before migration?

### Organizational Policies

- Policies or constraints when proposing new systems?
  - [ ] Preferred vendor list
  - [ ] Security standards
  - [ ] IT signoff required
  - [ ] Procurement process
- Policies for granting partner/contractor system access?

---

## Integration Architecture

### Current Integration Infrastructure

- Do you utilize middleware or iPaaS solutions?
  - [ ] No
  - [ ] Yes → List below

| Tool | Purpose | Maintain or Replace? |
|------|---------|---------------------|
| | | |

Examples: Zapier, Make, Workato, Tray.io, MuleSoft, Dell Boomi, custom middleware

### Integration Preferences

- Should existing tools be leveraged or may new tools be proposed?
- Technology preferences for custom integrations?
  - Languages: ________
  - Platforms: ________
  - Constraints: ________

### Integration Ownership

- Preference for managing custom integrations?
  - [ ] Partner builds and maintains
  - [ ] Partner builds, client maintains
  - [ ] Client builds with partner consulting
  - [ ] Fully internal

- In-house development resources available?
- If yes, preference for custom development approach?

---

## Testing & Signoff

### Sandbox Requirements

Which components require sandbox configuration before production?
- [ ] Data migrations
- [ ] Integrations with external systems
- [ ] Critical workflows/automations
- [ ] Custom objects and data model
- [ ] User permissions
- [ ] Lead scoring / lifecycle stages
- [ ] None required

### User Acceptance Testing (UAT)

- UAT approach preference?
  - [ ] Partner-led structured UAT
  - [ ] Client-led with partner support
  - [ ] Collaborative testing sessions
  - [ ] Automated testing required

- UAT documentation requirements?
- Sign-off process and authority?

---

## Documentation Requirements

### Project Documentation (During Implementation)

Which documentation needed during project for alignment and requirements?
- [ ] Data models / ERDs
- [ ] Property descriptions & mapping
- [ ] Functional & technical specifications
- [ ] Systems & data architecture diagrams
- [ ] Data migration reports
- [ ] Users & permissions matrix
- [ ] Process flow diagrams / BPMN

### Handover Documentation

For each artifact, specify detail level:

| Artifact | Not Needed | Basic | Comprehensive |
|----------|------------|-------|---------------|
| Data Models | | | |
| Property Descriptions & Mapping | | | |
| Functional & Technical Specs | | | |
| Systems Architecture | | | |
| Data Migration Reports | | | |
| Users & Permissions | | | |
| System Configuration Docs | | | |
| Integration Documentation | | | |
| Training Materials | | | |

**Basic**: Configuration overviews, object lists, property dictionaries, basic workflow descriptions

**Comprehensive**: Detailed field mappings, process logic, configuration rationales, custom code specs, permission structures, audit reports, limitations, future considerations

---

## Marketing Function

### Customer Journey

Describe typical customer journeys:
- Key channels used
- Lead qualification process
- Nurturing activities
- Marketing to Sales handoff
- Feedback loop from Sales to Marketing

### Marketing Processes

For each process variation (by division/region/product):

| Process | Description | Automation Level | Tools Used |
|---------|-------------|------------------|------------|
| Lead capture | | | |
| Lead scoring | | | |
| Lead qualification | | | |
| Nurture sequences | | | |
| Campaign management | | | |
| Reporting | | | |

### Marketing Roles & Permissions

| Role | User Count | Key Capabilities Needed | Access Level |
|------|------------|------------------------|--------------|
| | | | |

### Template Requirements

| Template Type | Quantity | Customization Level | Brand Variations |
|---------------|----------|--------------------| ----------------|
| Email | | | |
| Landing Page | | | |
| Form | | | |
| Blog | | | |

### Channels & Assets

| Channel | Current Use | Migration Needed? | Integration Required? |
|---------|-------------|-------------------|----------------------|
| Email | | | |
| Social | | | |
| Paid Media | | | |
| Webinars | | | |
| Events | | | |
| Content/Blog | | | |

### Paid Media Requirements

- Ad platforms in use?
- Audience sync requirements?
- Attribution tracking needs?
- Reporting integration?

### Training Requirements

- Training approach?
  - [ ] Train-the-trainer
  - [ ] All users trained
  - [ ] Self-service with documentation
- Documentation preferences?
  - [ ] Training presentations
  - [ ] SOPs / User manuals / Playbooks
  - [ ] Video tutorials
  - [ ] Quick reference guides

### Custom Requirements

Any additional custom requirements? (Calculators, geo-mapping, multi-language, etc.)

---

## Sales Function

### Buying Process

Describe typical buying processes (lead to customer journey):
- Sales cycle length
- Key stages and milestones
- Decision-making process
- Win/loss factors

### Sales Processes

For each process variation (by division/region/product):

| Process | Description | Automation Level | Tools Used |
|---------|-------------|------------------|------------|
| Lead assignment | | | |
| Opportunity management | | | |
| Pipeline stages | | | |
| Quoting/Proposals | | | |
| Forecasting | | | |
| Reporting | | | |

### Outbound Sales (If Applicable)

- Outbound function structure?
  - [ ] Centralized SDR team
  - [ ] Distributed by region/segment
  - [ ] Blended inbound/outbound reps
  - [ ] No dedicated outbound function

- Additional outbound tools? (Salesloft, Outreach, ZoomInfo, Apollo, dialers)
- Integration requirements with outbound tools?
- Distinct processes/playbooks for outbound vs inbound?
- Account assignment and intent data requirements?

### Sales Roles & Permissions

| Role | User Count | Key Capabilities Needed | Access Level |
|------|------------|------------------------|--------------|
| | | | |

### Sales Use Cases

| Use Case | Priority | Complexity | Integration Needed? |
|----------|----------|------------|---------------------|
| | | | |

### Data Sharing Requirements

- Can all sales team members see all deals?
- Data visibility restrictions needed?
- Legal requirements governing sales data access?

### Product Library (If Applicable)

- Product library requirements?
  - [ ] Not needed
  - [ ] Simple product list
  - [ ] Complex with variants/pricing
  - [ ] Integration with external catalog

- Product count?
- Product-related considerations?
  - [ ] Bundles
  - [ ] Recurring vs one-time
  - [ ] Regional pricing
  - [ ] Multi-currency
  - [ ] Discounting rules

### Training Requirements

Same structure as Marketing section

### Custom Requirements

Any additional custom requirements? (Trial users, revenue sharing, billable hours, etc.)

---

## Service Function

### Service Journey

Describe typical service customer journeys:
- Support channels
- Issue categorization
- Escalation paths
- Resolution processes
- Customer feedback loops

### Service Processes

For each process variation:

| Process | Description | Automation Level | Tools Used |
|---------|-------------|------------------|------------|
| Ticket creation | | | |
| Ticket routing | | | |
| SLA management | | | |
| Escalation | | | |
| Knowledge base | | | |
| Customer feedback | | | |

### Service Roles & Permissions

| Role | User Count | Key Capabilities Needed | Access Level |
|------|------------|------------------------|--------------|
| | | | |

### Service Use Cases

| Use Case | Priority | Complexity | Integration Needed? |
|----------|----------|------------|---------------------|
| | | | |

### Service Channels

| Channel | Current Use | Migration Needed? | Integration Required? |
|---------|-------------|-------------------|----------------------|
| Email | | | |
| Phone | | | |
| Chat | | | |
| Self-service portal | | | |
| Social | | | |

### Data Sharing Requirements

- Can all service team members see all tickets?
- Data visibility restrictions needed?
- Legal requirements governing service data access?

### Training Requirements

Same structure as Marketing section

### Custom Requirements

Any additional custom requirements? (Geo-mapping, multi-language, SLA automation, etc.)

---

## Operations & Data Management

### Strategic Consulting Needs

Which areas require strategic consulting?
- [ ] Data Strategy & Governance - Data quality, structure, security, compliance
- [ ] Front Office Systems Architecture - Tool connections, data flows, platform positioning
- [ ] Change Control & Platform Governance - Long-term management, evolution, scalability

### Administrator Roles

| Role | User Count | Responsibilities | Access Level |
|------|------------|------------------|--------------|
| Super Admin | | | |
| Admin | | | |
| Operations | | | |
| IT/Technical | | | |

### Data Enrichment

- Data enrichment requirements?
  - [ ] Not needed
  - [ ] Company data
  - [ ] Contact data
  - [ ] Intent data
  - [ ] Technographics

- Preferred enrichment providers?

### Data Quality Automation

Which automation should be implemented?
- [ ] Preventing duplicate records
- [ ] Standardizing data formats (country names, phone numbers, capitalization)
- [ ] Flagging incomplete or incorrect records
- [ ] Ongoing cleanup routines (archive stale deals, flag inactive contacts)
- [ ] Automated validation or correction workflows

Describe specific requirements for each selected item.

### Sensitive Data Handling

- Does the platform need to handle sensitive/regulated information?
  - [ ] PII (Personal Identifiable Information)
  - [ ] Financial data
  - [ ] Health records
  - [ ] Other: ________

- Specific handling requirements?

### Data Backup & Recovery

- Data backup requirements?
  - [ ] Native platform backup sufficient
  - [ ] Third-party backup solution needed
  - [ ] Custom backup requirements: ________

### Training Requirements

Same structure as Marketing section

### Custom Requirements

Any additional custom requirements? (Multi-language, geo-mapping, custom automation, etc.)
