# EU-Comply Guidebook

This guide is written for non-technical users who want to understand what the
platform does and how to use it without reading the codebase.

## What EU-Comply Is

EU-Comply is a workspace for reviewing AI systems against the EU AI Act.

In simple terms, it helps a team answer questions like:

- what is this AI system used for
- is it risky under the EU AI Act
- do we need human review before we can trust the result
- what evidence supports the answer
- what should we do next

It is not just a chatbot. It is closer to a compliance workbench.

## What The Platform Does In Plain English

When you use EU-Comply, the platform helps you do this:

1. create a case for an AI system
2. describe what the system does
3. upload evidence such as notes, policies, specs, or model documents
4. process those files into structured facts
5. run a deterministic assessment
6. route sensitive results through a review workflow
7. record a human approval or request changes
8. export the result as a report or audit bundle

## Who This Is For

This platform is useful for:

- AI governance teams
- compliance analysts
- legal reviewers
- product managers working on AI features
- internal audit teams
- founders or operators who need a structured EU AI Act review trail

## The Main Ideas You Need To Know

### Case

A case is one AI system or one governed AI use case that you want to review.

Example:
- "Candidate Screening Assistant"
- "Customer Support Chatbot"
- "Biometric Access Control Pilot"

### Dossier

The dossier is the structured information you know about the system:

- system name
- actor role
- sector
- intended purpose
- model provider
- model name
- geography
- oversight summary

### Artifact

An artifact is a file you upload to support the case.

Examples:

- product note
- internal AI policy
- model card
- PDF requirements document
- DOCX project brief
- spreadsheet with deployment details

### Assessment

The assessment is the machine-generated determination based on the facts and
rules currently implemented in the platform.

Possible outcomes include:

- `out_of_scope`
- `prohibited`
- `high_risk`
- `transparency_only`
- `gpai_related`
- `minimal_risk`
- `needs_more_information`

### Workflow

The workflow is the governed process that decides whether the assessment can
move forward directly or whether it needs human review.

### Review

A review is a human decision recorded in the platform. This matters because the
tool is decision-support software, not a replacement for human governance.

## Before You Start

Make sure the local stack is running.

Typical local URLs:

- Web app: `http://127.0.0.1:3000`
- API: `http://127.0.0.1:8001`
- API docs: `http://127.0.0.1:8001/docs`

Default sign-in for local development:

- Email: `admin@eucomply.dev`
- Password: `change-me-now`

In the browser, the API Base URL field accepts either:

- `http://127.0.0.1:8001`
- `http://127.0.0.1:8001/api/v1`

The current UI can normalize either format automatically.

## Step-By-Step Walkthrough

## 1. Open The Analyst Console

Go to:

`http://127.0.0.1:3000/cases`

You will see the sign-in form for the analyst console.

## 2. Connect To The Backend

In the `API Base URL` field, enter the backend address.

For local use, the safest value is:

`http://127.0.0.1:8001`

Then enter:

- Email: `admin@eucomply.dev`
- Password: `change-me-now`

Click `Sign in`.

What should happen:

- the connection pill changes from `Disconnected`
- the console loads the live case workspace

## 3. Create A New Case

After signing in, use the case creation section.

Fill in:

- title
- description
- owner team
- policy snapshot
- dossier information

Important fields in the dossier:

- `system_name`
- `actor_role`
- `sector`
- `intended_purpose`
- `uses_generative_ai`
- `affects_natural_persons`
- `geographic_scope`
- `deployment_channels`
- `human_oversight_summary`

Example:

- Title: `Hiring Screening Assistant`
- Actor role: `provider`
- Sector: `employment`
- Intended purpose: "Assist recruiters with candidate triage before human review."
- Uses generative AI: `Yes`
- Affects natural persons: `Yes`

Click `Create Case`.

## 4. Upload Evidence

Once a case is selected, go to the `Evidence` section and upload one or more
files.

Good first examples:

- a product brief
- a model card
- a requirements note
- a policy document

After upload, the artifact appears in the case workspace.

## 5. Process The Artifact

Click `Process` for the uploaded artifact.

What the platform does:

- parses the file
- extracts text
- splits it into chunks
- creates extracted-fact candidates
- attaches those facts back to the case

If the document contains conflicting signals, the platform can mark those
instead of pretending the facts are certain.

## 6. Run Assessment

Click `Run Assessment`.

This creates a deterministic assessment run for the selected case.

You will then see:

- the primary outcome
- a summary
- any conflict fields
- triggered obligations

Think of this as the machine’s current answer based on the current rules and
facts.

## 7. Run Workflow

Click `Run Workflow`.

This is different from just running the assessment.

The workflow decides whether the case can move forward or whether it needs human
review because the result is sensitive.

Right now, the workflow especially escalates cases such as:

- `prohibited`
- `needs_more_information`

## 8. Record A Review

If the workflow or assessment needs a human decision, use the `Reviews And
Reports` panel.

You can:

- approve the result
- request changes
- record a rationale
- set an approved outcome

This creates a human-reviewed governance record.

## 9. Export The Result

The platform currently supports:

- JSON export
- Markdown export
- ZIP audit-pack export

The audit pack is the best option when you want a review bundle containing the
current case evidence and assessment context together.

## Three Simple Examples

## Example 1: Hiring Screening Assistant

Imagine a recruiting team uses AI to help screen candidates.

A likely case setup:

- sector: `employment`
- affects natural persons: `true`
- intended purpose: candidate screening or triage
- evidence: hiring process note, screening policy, model notes

What can happen:

- the platform may classify it as `high_risk`
- the obligations section will surface governance duties such as oversight and logging
- the workflow may still proceed, but the team should review the result carefully

Why:

Employment-related AI decisions are one of the most sensitive categories under
the AI Act.

## Example 2: Customer Support Chatbot

Imagine a company launches a chatbot that talks directly to customers.

A likely case setup:

- conversational AI
- natural-person interaction
- customer support use
- no hiring, finance, or biometric decisioning

What can happen:

- the platform may classify it as `transparency_only`
- the team may need to ensure the user is informed they are interacting with AI

Why:

This is often more about disclosure than about high-risk classification.

## Example 3: Real-Time Remote Biometric Use In Public Space

Imagine a deployment involving real-time remote biometric identification for a
law-enforcement public-space context.

A likely case setup:

- remote biometric identification
- law-enforcement context
- real-time public-space usage

What can happen:

- the platform may classify it as `prohibited`
- the workflow will route it into review-required state
- the case should be escalated immediately rather than treated like routine automation

Why:

This is one of the clearest examples of a sensitive outcome that should never be
handled casually.

## How To Read The Main Statuses

### `minimal_risk`

The current rule set did not match a stronger concern.

This does not mean the system is automatically safe in every legal sense. It
means the current deterministic rules did not find a higher category.

### `transparency_only`

The system likely owes a disclosure-style obligation rather than a high-risk
classification.

### `high_risk`

The system likely falls into a higher-governance category and should be treated
seriously.

### `needs_more_information`

The platform does not think it has enough clean evidence to make a trustworthy
decision.

This is usually a sign to improve the dossier or resolve conflicts.

### `prohibited`

The platform found a rule path that indicates the use is not acceptable under
the currently implemented logic and should be escalated immediately.

## How To Use The Platform Well

Best practice:

- keep one case focused on one AI system or governed use case
- upload a few meaningful artifacts instead of a random file dump
- make the intended purpose very clear
- write a human oversight summary in normal language
- run both the assessment and the workflow
- always record a human review for sensitive outcomes
- export the final bundle for traceability

## Common Mistakes

### Entering a dead API URL

If your local API is on `8001`, do not keep an old `8000` value from a previous
session.

The current UI tries to repair this automatically, but a page refresh may still
help if you have an old browser tab open.

### Uploading files but not processing them

An uploaded artifact does not become usable evidence until you click `Process`.

### Treating the machine output as final

The assessment is a supported machine outcome, not the final human governance
decision.

## Troubleshooting

### The page says `Failed to fetch`

Check:

- is the API container running
- is the API reachable at `http://127.0.0.1:8001/api/v1/health/liveness`
- did you hard refresh the browser after a frontend update

### The page says `Not found`

This usually means the API base URL was wrong or stale.

Try:

- refresh the page
- use `http://127.0.0.1:8001`
- sign in again

### The page loads but no cases appear

That can be normal if the environment is fresh and no cases have been created
yet.

## What EU-Comply Does Not Do

It is important to keep expectations honest.

EU-Comply does not currently:

- replace legal counsel
- replace conformity assessment bodies
- fully codify the entire AI Act article by article
- eliminate the need for human review

What it does do well is provide a structured, repeatable, evidence-backed
workflow for governed assessment.

## Best First Demo Flow

If you want to understand the platform quickly, use this sequence:

1. sign in
2. create a hiring-related case
3. upload a short TXT or DOCX artifact mentioning recruiting and screening
4. process the artifact
5. run assessment
6. run workflow
7. record a review
8. export the Markdown report

That gives you the clearest first end-to-end picture of how the product works.

## Final Note

The platform is already structured like a real governance tool, but it should be
used with the same seriousness as any compliance-support system:

- keep inputs accurate
- review outputs critically
- preserve the audit trail
- treat the exported result as governance documentation, not magic truth
