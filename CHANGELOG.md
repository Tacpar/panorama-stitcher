# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.1.0] - 2026-11-20

Baseline name for the program already on `main`. The two commits that added `README.md` and `stitcher.py` are summarized here once. There is no git tag.

### Added

- `stitcher.py`, one file with `Config`, `InputManager`, `ImageProcessor`, `Stitcher`, `UIManager`, and `PanoramaController`. It is a Tkinter window meant to stitch a folder of images or frames from a video through OpenCV, show the panorama, and save a JPEG.
- `README.md`, the title and one sentence: a panorama stitching application with a modular structure for images and video. That structure is the classes in `stitcher.py`. There is no package.
- `VERSION` containing `0.1.0`. `stitcher.py` has no `__version__`.
- `AGENTS.md` and a draft `ROADMAP.md`.
- `python3 stitcher.py` builds a `Tk` root titled "Panorama Stitcher" and constructs `PanoramaController`. Widget construction reads `root.controller` on the Select Input button before `PanoramaController` assigns `root.controller`. On Python 3.12.3 with Tk 8.6 that raised `AttributeError` and the process exited before `mainloop`. The Preview, Stitch, Save, and status widgets are later in `create_widgets` and were not created.
- Still-image loading is a non-recursive lexicographic sort of `*.jpg` and `*.png`. `start_image` is a 1-based index into that list. `num_images` of `all` (any case) means the rest of the list.
- Video loading keeps 1-based frames at or after `start_image` whose index is divisible by `frame_interval` (default `10`).
- `stitch_images` resizes so the long side is at most 400 px, optionally forward-warps when `projection` is `cylindrical`, converts to gray, applies CLAHE with clip `2.0` and tile grid `(8, 8)`, expands back to three channels, and calls `cv2.Stitcher_create(cv2.Stitcher_PANORAMA)`. Any other projection string, including the default `spherical`, skips the pre-warp. A status other than `cv2.Stitcher_OK` is logged and the function returns `None`.
- `mode`, `quality`, `transpose_images`, `clahe_clip_limit`, and `clahe_tile_grid_size` are stored on `Config` and not read. `estimate_focal_length` returns `focal_ratio` times 1000 (default 500) and ignores the images.
