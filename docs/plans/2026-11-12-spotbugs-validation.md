# SpotBugs documentation verification implementation plan

**Goal:** Verify the documented GitHub workflow against JUnit and retain reproducible evidence.

**Architecture:** Run a Maven baseline using the guide commands, then adapt compilation to the existing Gradle multi-project build. Run SpotBugs 4.10.2 over production bytecode, verify SARIF, archive reports, and use the documented uploader through a temporary private-action checkout.

**Tech Stack:** GitHub Actions, Java 25, Gradle wrapper, SpotBugs 4.10.2, upload-sarif-action.

## Approved design

User approved baseline, Gradle adaptation, execution, and reliability report. PRIVATE_ACTIONS_READ_TOKEN is temporary until the action becomes public. Existing clean checkout is reused on validation/spotbugs-docs.

## Tasks

1. Run the guide's Maven compile/scan commands in a baseline job; preserve logs and conclusion.
2. Compile production modules with the existing Gradle wrapper; export class directories and dependency classpath without altering production build scripts.
3. Invoke the documented SpotBugs core version with SARIF output, validate report structure, and archive evidence even when scan/upload fails.
4. Check out the private upload action using PRIVATE_ACTIONS_READ_TOKEN and invoke it locally with id-token: write.
5. Follow run to completion; diagnose concrete failures; record tested commit, run URLs, report counts, callback outcome, and guide corrections.
