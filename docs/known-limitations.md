# Known limitations

## MVP scope

- This release focuses on raster image conversion in a single-threaded per-job pipeline.
- Video, audio, and document conversion are out of scope.

## HEIC support

- HEIC decoding depends on `pillow-heif` and the underlying `libheif` availability on the host OS.
- Some devices or OS builds may require additional runtime libraries beyond Python packages.

## Performance

- Large images may take noticeable time per file; the UI should remain responsive, but total runtime depends on disk speed and CPU.

## Color management

- This MVP does not implement a full ICC color-managed pipeline beyond Pillow defaults.
