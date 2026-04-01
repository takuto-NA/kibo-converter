# Manual test checklist

## Environment

- Windows 10 or later
- Python 3.11+
- Dependencies installed from `pyproject.toml`

## HEIC to PNG

- [ ] Copy multiple iPhone `HEIC` files into an input folder
- [ ] Set output format to `PNG`
- [ ] Run conversion and verify outputs exist
- [ ] Open a few outputs in an image viewer and confirm orientation looks correct

## Progress and cancellation

- [ ] Run a folder with 100+ images
- [ ] Confirm progress updates while running
- [ ] Press `Cancel` mid-run and confirm the UI remains responsive
- [ ] Confirm the log output explains skipped files after cancellation

## Collision policies

- [ ] Run twice with `Overwrite existing output` and confirm files update
- [ ] Run with `Keep both` and confirm no silent overwrite when content differs
- [ ] Run with `Keep both` when outputs already match and confirm duplicate skip behavior

## Job file persistence

- [ ] Save a job JSON, restart the app, load the job JSON, and confirm fields restore
- [ ] Manually corrupt the JSON and confirm load fails with a clear error message

## Failure cases

- [ ] Include a corrupted image file and confirm the job continues
- [ ] Point output to a read-only location and confirm a clear preflight failure
