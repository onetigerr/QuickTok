## ADDED Requirements
### Requirement: Module execution
The system MUST support execution via the `python -m src.importer` command.

#### Scenario: Running import via module with all arguments
- **GIVEN** the package is installed or `src` is in python path
- **WHEN** user runs `python -m src.importer --channel ccumpot --limit 10`
- **THEN** the import process starts successfully with the channel set to "ccumpot" and limit set to 10
