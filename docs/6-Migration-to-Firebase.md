# Migration from SQL Database to Firebase

## Context and Requirements

* No need to maintain backward compatibility with old IDs.
  * The Firebase database will start empty.
* The data structure can use a nested collection model
  * All admin and player queries will always relate to a specific challenge and a specific round.
  * No cross-round or cross-challenge queries are required.
* All team API keys will be stored in plain text.
  * The risk of API key leakage is considered very low.
  * No additional measures are required to avoid storing API keys in plain text.
  * Task generator secrets will also be stored in plain text.
* The data model should be optimized for the most common queries.


## Data Model

- challenges/{cid}/ — ChallengeDocument
  - rounds/{rid}/ — RoundDocument
    - task-types/{type-code} — TaskTypeDocument
    - tasks/{tid} — TaskDocument
    - submissions/{sid} — SubmissionDocument
    - dashboard/{team-id}/ — TeamDashboardDocument
      - tasks/{type-code} — TeamTaskDashboardDocument
  - teams/{pid}/ — TeamDocument
- keys/{key}/ — APIKeyDocument

### ChallengeDocument

- cid: string
- title: string
- description: str markdown
- teams: {tid: TeamDocument}
- rounds: {rid: RoundDocument}
  
### TeamDocument
 
- tid: string
- challenge_id: int # denormalized
- name: string
- members: string
- captain_contact: string

### APIKeyDocument

- key: string
- challenge_id: int # denormalized
- role: "player" | "admin"
- team_id: string

### RoundDocument

- rid: string
- challenge_id: int # denormalized
- title: string
- description: str markdown
- published: boolean
- claim_by_type: boolean
- start: Date
- end: Date
- task-types: {type-code: TaskTypeDocument}
- tasks: {tid: TaskDocument}
- submissions: {sid: SubmissionDocument}

### TaskTypeDocument

- type-code: string
- challenge_id: int # denormalized
- round_id: int # denormalized
- tasks_count: int
- generator_url: str
- generator_settings: str
- generator_secret: str
- score: int
- time_to_solve: int
 
### TaskDocument

- tid: string
- challenge_id: int # denormalized
- team_id: int # denormalized
- round_id: int # denormalized
- task_type: int
- status: TaskStatus
- statement: str
- input: str
- checker_hint: str
- score: int
- claimed_at: datetime
- solved_at: datetime

#### Indices 

Team:
- (team_id asc, claimed_at desc) — last claimed tasks for a team
- (team_id asc, task_type asc, claimed_at desc) — last claimed tasks by type for a team. Claim task limits check.

Admin:
- (claimed_at desc) — last claimed tasks for an admin

### SubmissionDocument

- sid: string
- challenge_id: int # denormalized
- team_id: int # denormalized
- round_id: int # denormalized
- task_id: int
- status: SubmissionStatus
- submitted_at: datetime
- answer: str
- checker_output: str
- score: int

#### Indices

Team dashboard links:
- (team_id asc, submitted_at desc) — all last submissions for a team
- (team_id asc, task_type asc, submitted_at desc) — last submissions for a particular task_type for a team

Admin dashboard links:
- (submitted_at desc) — last submissions for an admin
- (task_type asc, status asc, submitted_at desc) — monitor specific task problems


### TeamDashboardDocument

- team_id: string
- challenge_id: int # denormalized
- round_id: int # denormalized
- score: int
- task_types: {tid: TeamTaskDashboardDocument} 


### TeamTaskDashboardDocument

- task_type: string
- score: int
- ac: int
- wa: int
- pending: int


## Security Rules

- No need to restrict access to the data. Backend will enforce access control.


## Implementation Details

### Key files to change

back/
* *_service.py
* db_models.py
* database.py — use secrets
* Minor adjustments of api_*.py files to new db models.
* main.py to initialize emulator if local.


### Implementation steps

1. [x] Set up a Firebase emulator, create a test-database and test it in unit tests.
2. [x] Migrate team_service.py to use Firebase, change the necessary models. Check with unit tests with emulators.
3. [x] Migrate challenge_service.py to use Firebase, change the necessary models. Check service with unit tests.
4. [x] Migrate task_service.py to use Firebase, change the necessary models. Check service with unit tests. 
5. [x] Add scripts for backend deployment to Firebase Cloud as a container.
 