# Negative Space

For every sensitive operation, list the guard you expect and whether it is
present.

| Operation | Expected guard | Present? | Location | Gap | Candidate? |
|---|---|---|---|---|---|
| copy into buffer | `len <= sizeof(dst)`, same domain | | | | |
| index into table | `index < count`, same width | | | | |
| use after delete | cursor not NULL / not freed | | | | |
| append to list | list non-empty / tail non-NULL | | | | |
| reuse connection | all identity fields equal | | | | |
| parse sequence range | start and end within window | | | | |
| privilege drop | drop before parsing | | | | |
| IPC peer auth | peer credentials verified | | | | |
| file open | path resolved, no symlink escape | | | | |
| free | all aliases invalidated | | | | |
| length transform | re-validated after transform | | | | |
| auth branch | every branch verifies | | | | |
