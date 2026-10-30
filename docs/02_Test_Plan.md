# Tasks 9 and 10 - Test plan and manual results sheet

## Criteria and requirements traceability

The **expected** column below is a planned test outcome, not a claim of an actual result. The student should replace `PENDING` with `PASS` or `FAIL` and capture evidence from their computer.

| Test | Requirement | Input or condition | Expected result | Actual result | Status |
|---|---|---|---|---|---|
| M01 | FR01 | Add three sample CSV files | All three appear in dataset list | To record | PENDING |
| M02 | FR02 | Analyze multiple large files | Interface stays responsive | To record | PENDING |
| M03 | FR03 | Analyze `orders_north.csv` | Duplicate and missing-value counts appear | To record | PENDING |
| M04 | FR04 | Inspect `TotalEUR` | Numeric summary is displayed | To record | PENDING |
| M05 | FR05 | Search `Valletta` in preview | Only matching sample records remain | To record | PENDING |
| M06 | FR06 | Finish analysis | Progress reaches total, completion message appears | To record | PENDING |
| M07 | FR07 | Cancel a large batch | Worker stops safely; UI recovers | To record | PENDING |
| M08 | FR08 | Save cleaned `orders_north.csv` | New CSV has fewer duplicate rows; original unchanged | To record | PENDING |
| M09 | FR09 | Export summary | Output CSV with one row per column | To record | PENDING |
| M10 | FR10 | Successful batch with audio on | Short notification is heard | To record | PENDING |
| M11 | FR01 | Add a non-CSV file via the selection dialog | Non-CSV files are not selectable | To record | PENDING |
| M12 | FR06 | Malformed CSV with too many fields | Error shown in Activity log; no application crash | To record | PENDING |
| M13 | FR08 | Choose original file as output | Export refused | To record | PENDING |
| M14 | FR03 | Analyze header-only CSV | Zero data rows; score 0.0 | To record | PENDING |
| M15 | FR07 | Restart after cancelling | New analysis can begin | To record | PENDING |
| M16 | Distribution | Build Windows EXE and reopen | Packaged app starts and analyzes sample CSV | To record | PENDING |

## Automated testing

Command: `python -m unittest discover -s tests -v`

At the time the ZIP was prepared in the authoring environment, **35 automated tests passed**. This is not a replacement for retesting the student's Windows version. Store a screenshot from the student's test run in `evidence/`.

## Evidence suggested for the final report

Screenshot 1: dark dashboard after launch. Screenshot 2: sample datasets imported. Screenshot 3: quality overview with missing/duplicate counts. Screenshot 4: column profile. Screenshot 5: newly exported CSV opened separately. Screenshot 6: automated terminal test results. Screenshot 7: benchmark output. Screenshot 8: Git history/branch graph. Screenshot 9: Windows executable running.

## Debugging record template - Task 12

| ID | Problem observed | Probable cause | Change made | Retest | Evidence |
|---|---|---|---|---|---|
| D01 | Enter an issue actually encountered | Identify the source | Describe real edit and commit | PASS/FAIL after retest | Screenshot/log |

Do not invent bugs, screenshots, pass results or commit history. Document issues that actually occur during your development/testing.
