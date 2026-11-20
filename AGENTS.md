# Agent guide

This file is the working agreement for any coding agent in this repository. Follow it on every change.

**Contents**

| Section | What an agent finds there |
| --- | --- |
| [Run](#run) | The start command, what it did when checked, and the libraries it imports |
| [Branches, commits, and pull requests](#branches-commits-and-pull-requests) | No direct work on the default branch, branch prefixes, commit form, pull request rules |
| [Where the code lives](#where-the-code-lives) | Walk through `stitcher.py`: classes, which settings actually run, and the startup failure |
| [Testing](#testing) | No tests today, the command to use once they exist, and checks already supported by the code |
| [Purpose](#purpose) | What the repository is, and what counts as a change to the picture |
| [Repository](#repository) | Paths at the repo root, and what the tree does not contain |
| [Versioning](#versioning) | `VERSION`, the changelog, semver, and when a tag is allowed |
| [Coding standards](#coding-standards) | Style already in `stitcher.py`, and constraints a change has to keep |
| [Scope](#scope) | What a small fix does not drag in |

> **Agents never commit, push, force-push, or merge to `main`.** The same ban applies to the default branch under any other name, including `master`. All work is done on a branch and lands through a pull request that a human reviews and merges. Open the pull request and stop.

## Run

There is no build, installer, or dependency file.

From the repository root the entry point is:

```bash
python3 stitcher.py
```

The `__main__` block creates a `Tk` root, sets the title to "Panorama Stitcher", constructs `PanoramaController`, and would then call `mainloop`.

Checked on Python 3.12.3 with Tk 8.6, OpenCV 5.1.0, NumPy 2.5.5, and Pillow 13.0.0. Those versions are what that check used. The repository does not pin them. `python3 -m py_compile stitcher.py` succeeded. `python3 stitcher.py` exited with status 1 before `mainloop`:

```text
AttributeError: '_tkinter.tkapp' object has no attribute 'controller'
```

`UIManager.create_widgets` evaluates `self.root.controller.on_select_input` while creating the Select Input button. `PanoramaController.__init__` assigns `root.controller` only after `UIManager` returns. The assignment is never reached. Preview, Stitch, Save, and the status labels sit below that button in `create_widgets` and are not created.

Importing `stitcher.py` runs `logging.basicConfig` and opens `panorama.log` in the current working directory at `DEBUG`. That happened on import during the check. Do not commit the log.

Imports that have to succeed before any of the above: `tkinter` (on Debian/Ubuntu often the `python3-tk` package), `cv2` (OpenCV), `numpy`, and `PIL` (Pillow). The rest of the imports are from the standard library. The file contains no GPU, CUDA, or OpenCL calls. Work that does run is on the CPU. `warp_to_cylindrical` is a Python loop over every pixel.

`cv2.Stitcher_create` is the OpenCV 4/5 constructor. This file does not call the older `cv2.createStitcher`.

## Branches, commits, and pull requests

**Never commit, push, force-push, or merge to `main`.** If the default branch is not named `main`, the same ban applies to that branch, including a branch named `master`. All work happens on a branch and lands through a pull request that a human reviews and merges. Open the pull request and stop. Do not merge it, and do not push the result onto the default branch.

Branch names, lowercase and hyphenated:

- `feature/<short-desc>` — new behavior
- `fix/<short-desc>` — a correction to existing behavior
- `docs/<short-desc>` — documentation only
- `release/vX.Y.Z` — version bump and changelog date for a release the owner asked for

Commit messages follow [Conventional Commits](https://www.conventionalcommits.org/):

```
<type>(<optional-scope>): <imperative summary>

<why, when the subject is not enough>
```

Types: `feat`, `fix`, `docs`, `test`, `refactor`, `perf`, `chore`. The subject is lowercase imperative, with no trailing period. Example: `fix(ui): attach the controller before building buttons`. Commits from before this guide do not use this form. New commits do.

Pull request expectations:

- One concern. Leave unrelated refactors out.
- Say what changed and why. If the frames that are used, the resize, the gray/CLAHE path, the pre-warp, or the OpenCV stitcher mode changed the picture, give the old and new behavior in terms a person can check (which frames, pixel size, channels, mode).
- Add or update tests for any behavior change. A docs-only change needs no test.
- Tests, and any lint or type check the repo actually configures, pass before you request review. None are configured today. Report only commands you ran. Do not add a linter, formatter, or CI workflow inside an unrelated change.
- A human reviews and merges.

## Where the code lives

All of the program is in `stitcher.py`, top to bottom.

1. **Logging.** `logging.basicConfig` writes `panorama.log` in the working directory. The format is `%(asctime)s - %(levelname)s - %(message)s`. Level is `DEBUG`. `datetime`, `gc`, and `traceback` are imported and unused.

2. **`Config`.** Defaults: `input_type` `"video"`, `mode` `"PANORAMA"`, `quality` `"low (Orb)"`, `frame_interval` `"10"`, `projection` `"spherical"`, `focal_ratio` `"0.5"`, `transpose_images` `False`, `clahe_clip_limit` `1.0`, `clahe_tile_grid_size` `8`, `start_image` `"1"`, `num_images` `"All"`, `available_images` `0`, `input_path` `None`. Several numbers are stored as strings and parsed at the point of use. `mode`, `quality`, `transpose_images`, `clahe_clip_limit`, and `clahe_tile_grid_size` are never read.

3. **`InputManager`.** `select_input` opens a directory dialog when `input_type` is `"images"`, and a video file dialog for every other value. The video filter is `*.mp4 *.avi *.mov`. For a folder it counts `*.jpg` plus `*.png` and stores that on `available_images`. For a video it stores `frame_count // interval`, using `10` when `frame_interval` is not all digits, and logs the count with a leading `~`. `available_images` is not shown in the window. The dialogs were not opened in the check, because the process exits before `mainloop`.

   `load_images` accepts `max_size` and passes it to the loaders. Neither loader reads `max_size`.

   `_load_folder_images` sorts the concatenation of `*.jpg` and `*.png` in that directory. The patterns are case-sensitive. `start_image` is a 1-based index into that sorted list (`int(start_image) - 1`). `num_images` equal to `all` in any case takes the tail; any other value is passed to `int`. `cv2.imread` skips a path that returns `None`. Checked on Linux: files named `img1.png`, `img10.png`, and `img2.png` loaded in that order, and `.jpeg`, `.JPG`, and `.PNG` were not loaded.

   `_extract_video_frames` reads with `cv2.VideoCapture` until a read fails. The first decoded frame is index 1. A frame is yielded when its index is at least `start_image` and `frame_idx % interval == 0`. `num_images` caps the number of yields. `frame_interval` is parsed with `int` and has no `isdigit` fallback on this path. Checked on a 25-frame file whose frame `n` was marked with a bar of width `2n`: interval 10 and start 1 kept frames 10 and 20. Start 15 kept frame 20. `num_images` of `1` kept frame 10.

4. **`ImageProcessor`.** `resize_image` leaves the image when the long side is at most `max_size` (default 400). Otherwise it scales the long side to `max_size` with `cv2.INTER_AREA`. Checked: a 1000×800 image (width × height) became 400×320. An image with long side 100 was unchanged.

   `warp_to_cylindrical` builds `np.zeros_like` and, for each source pixel, writes it to an integer destination:

   - `theta = (x - xcenter) / f` with `xcenter = w // 2`
   - `x_new = int(f * tan(theta) + xcenter)`
   - `y_new = int(f * h_prime / sqrt(tan(theta)**2 + 1) + ycenter)` where `h_prime = (y - ycenter) / f`

   `int` truncates toward zero. Destinations outside the image are dropped. Unwritten pixels stay 0. Two source pixels can share one destination; the later write wins. There is no interpolation. Checked on a 20×30 image with a 10×10 block and `f = 500`: 100 painted pixels, 91 nonzero outputs. That check does not say the formula matches a reference cylindrical projection.

   `normalize_image` uses `cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))` when `apply_clahe` is true, which is the default. `equalizeHist` runs only when `apply_clahe` is false. No caller passes false. The `Config` CLAHE fields are not the numbers in this call.

5. **`Stitcher`.** `estimate_focal_length` ignores its images argument and returns `float(focal_ratio) * 1000`. The default is 500. The comment in the function calls this a placeholder. The value is used only when `projection` is `"cylindrical"`.

   `stitch_images` always resizes with the default 400 px cap, warps only for `"cylindrical"`, converts BGR to gray, runs `normalize_image`, and converts gray back to BGR. It then calls `cv2.Stitcher_create(cv2.Stitcher_PANORAMA)` and `stitch`. `is_preview` is accepted and unused. `mode` is unused, so `Stitcher_SCANS` is never selected. The file does not set a feature finder, a warper, or a confidence threshold on the stitcher. Status equal to `cv2.Stitcher_OK` returns the panorama. Any other status is logged as `Stitching failed with status: {status}` and the function returns `None`. The empty-input check is in the controller threads, not in this method.

   Checked on OpenCV 5.1.0: an empty list and a single image each returned `None` and logged status `1` (`Stitcher_ERR_NEED_MORE_IMGS` in that build). Two overlapping synthetic images with the default `spherical` projection returned an array whose three channels were equal. The same pair with `cylindrical` also returned an array. Those images were temporary files, not fixtures in the repo.

6. **`UIManager`.** `create_widgets` builds, in order: an input-type combobox (`images`, `video`) whose `StringVar` is not stored on the instance, the Select Input button, status labels, Preview, Stitch, and Save. The combobox writes `config.input_type` on `<<ComboboxSelected>>`. Construction stops at Select Input, as [Run](#run) describes. `update_status` sets `status_var` and calls `root.update_idletasks`. `display_pano` turns BGR into RGB with PIL, stores the `PhotoImage` on `self.popup_photo`, and puts it on a canvas the size of the image in a `Toplevel` titled "Panorama Preview". `close_popup` destroys that window and sets `popup_window` to `None`. It does not clear `popup_canvas`. Nothing calls `close_popup`.

7. **`PanoramaController`.** Builds `Config`, `InputManager`, an `ImageProcessor` that no method uses, `Stitcher`, then `UIManager`, then sets `root.controller`. Preview and Stitch start daemon threads that call `_preview_thread` and `_stitch_thread`. Those methods load every selected frame into a list, call `stitch_images`, and on success call `display_pano` from the worker thread. Status strings are `Generating preview...`, `No images loaded`, `Preview ready`, `Preview failed`, `Stitching panorama...`, `Stitching completed`, and `Stitching failed`. The failure strings do not include the OpenCV status. There is no `try` around the thread body. The threads were not run in the check, because the controller does not finish constructing.

   `on_save_pano` shows the warning `No panorama to save!` when `popup_canvas` is missing. Otherwise it asks for a JPEG path (`defaultextension` `.jpg`), stitches again from the source, and `cv2.imwrite`s that new array. The `imwrite` return value is ignored. A second failure sets `Save failed`.

8. **Entry point.** `if __name__ == "__main__"` is the only place that sets the root title ("Panorama Stitcher") and the only place that calls `mainloop`. The block does run: it builds the root, sets the title, then constructs `PanoramaController`. The exception in that constructor is why `mainloop` does not run.

## Testing

There is no test suite, no `pytest` configuration, and no CI. There is no test command to run today.

Convention once tests exist (they do not yet): put them in `tests/`, use `pytest`, and run this before requesting review:

```bash
python3 -m pytest
```

`pytest` is a recommendation, not a current dependency. Test the pipeline, not `mainloop`. Importing `stitcher.py` imports `tkinter`, `cv2`, `numpy`, and `PIL`, and it creates `panorama.log`. If you split the pipeline out of the UI, put the tests on the module that does not import `tkinter`.

Oracles already in the code, for when you add tests. Items marked as checked were run while writing this guide, on the versions in [Run](#run).

- Long side above `max_size` scales to that long side with `INTER_AREA`. A smaller image is unchanged. Checked: 1000×800 (width × height) became 400×320.
- `estimate_focal_length` returns `float(focal_ratio) * 1000` and does not read pixels. Default 500.
- `projection == "cylindrical"` applies `warp_to_cylindrical`. Any other string, including `"spherical"`, does not.
- Folder order is lexicographic on `*.jpg` and `*.png` only. `start_image` is 1-based into that list. `num_images` of `all` in any case is the uncapped tail. Checked: `img1.png`, `img10.png`, `img2.png` loaded in that order.
- Video: 1-based index, keep frames at or after `start_image` with `frame_idx % interval == 0`, then apply the `num_images` cap. Checked on a 25-frame file: interval 10 and start 1 kept frames 10 and 20.
- `stitch_images` returns `None` and logs `Stitching failed with status: {status}` when the status is not `cv2.Stitcher_OK`. On OpenCV 5.1.0, an empty list and one image logged status 1.
- The default stitch path grays the frames and expands them back to three equal channels before `stitch`.
- Constructing `PanoramaController` raises `AttributeError`. The Select Input button reads `root.controller` during `UIManager` construction, and `root.controller = self` is the statement after `UIManager` returns.

Recommended later, only if the owner adds them to the repo: [Ruff](https://docs.astral.sh/ruff/) for lint and format, [mypy](https://mypy-lang.org/) for types. They are not configured. Do not add them on the side.

## Purpose

The README describes a panorama stitching application with a modular structure for images and video. The program is one Tkinter script written to load still images or video frames, ask OpenCV to stitch them, show the result, and save a JPEG. The classes in `stitcher.py` are that structure. There is no separate package. [Run](#run) records that constructing the window raises before anything is shown.

The picture is the panorama for a given input: which frames are included, the resize, the gray/CLAHE step, whether `warp_to_cylindrical` runs, and the OpenCV stitcher mode. A change that moves any of those is a change to the picture. Call that out in the pull request and in the changelog.

`ROADMAP.md` is a draft for the owner. It is not a task list.

## Repository

| Path | Role |
| --- | --- |
| `stitcher.py` | The whole program |
| `README.md` | Title and one-sentence description |
| `VERSION` | Semantic version of this tree. Current contents: `0.1.0` |
| `CHANGELOG.md` | [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) record. `0.1.0` is the baseline |
| `AGENTS.md` | This guide |
| `ROADMAP.md` | Draft roadmap for discussion |

There is no package, `pyproject.toml`, dependency file, test suite, linter, type checker, CI workflow, `.gitignore`, license file, or sample image or video. `stitcher.py` does not define `__version__`. `panorama.log` and `__pycache__/` appear when the file is imported or run. They are not part of the tree. Do not add them in a commit.

## Versioning

The version of this tree is the single line in `VERSION` at the repository root. The current line is `0.1.0`. That names the baseline in `CHANGELOG.md`. Nothing has been tagged.

`stitcher.py` has no `__version__`. Do not add one as a side effect of another change. If a later change adds a version constant, set it to the same text as `VERSION` in that same change.

Use [Semantic Versioning](https://semver.org/spec/v2.0.0.html): `MAJOR.MINOR.PATCH`. Pre-release identifiers are fine, for example `0.2.0-rc.1`. Git tags use a leading `v` and the same text: `v0.1.0`, `v0.2.0-rc.1`. Do not create a git tag unless the owner asked for that release.

To bump the version, edit `VERSION` and record the change in `CHANGELOG.md`. Keep the file in Keep a Changelog form (`Added`, `Changed`, `Deprecated`, `Removed`, `Fixed`, `Security`). Every pull request that changes behavior updates `## [Unreleased]`. A release the owner asked for moves those notes under `## [X.Y.Z] - YYYY-MM-DD`. Do not invent entries for the commits that predate the changelog. They are already summarized under `0.1.0`.

Below 1.0.0 the picture may still change in a minor version. From 1.0.0 on, a change to which frames are selected, the resize rule, the gray/CLAHE path, the pre-warp, or the stitcher mode, when that change alters the meaning of the output, is a major bump. A patch does not change those. The startup `AttributeError` is widget construction. A fix that only makes the existing buttons call the controller, and leaves `stitch_images` and the loaders alone, is a patch. Name the bump in the pull request.

## Coding standards

Match the file you are editing.

- The third-party imports are `cv2`, `numpy`, and `PIL`. Do not add another dependency unless the owner has agreed. Record an agreed dependency in a file an install can use, and in the changelog.
- `snake_case` for functions and variables, `PascalCase` for classes. A leading underscore marks a helper (`_load_folder_images`, `_extract_video_frames`, `_preview_thread`, `_stitch_thread`). There are no type annotations and no method docstrings. Class comments are one line above the class. Keep that shape in this file. Do not add a `typing` import as a drive-by.
- No formatter is configured. Keep the 4-space indent and the section comments. Do not reflow the file.
- Log with the `logging` module and f-strings, as `select_input` and `stitch_images` already do. Do not switch the file to `print`.
- Numeric settings next to the existing ones are strings when their neighbors are strings (`frame_interval`, `focal_ratio`, `start_image`, `num_images`). Parse them at the point of use.
- Button `command=` values are evaluated when the button is created. `root.controller` is assigned after `UIManager(...)` returns, so a new widget must not read `root.controller` unless that assignment has already run.
- `load_images` plus `stitch_images` decide the picture. `stitch_images` always resizes to the 400 px long-side cap, always runs the gray CLAHE path, and always uses `Stitcher_PANORAMA`. `is_preview` is unused. Do not make preview and stitch diverge as a side effect of another change.
- `normalize_image` hardcodes CLAHE clip `2.0` and tile grid `(8, 8)`. `Config.clahe_clip_limit` is `1.0` and is not read. Do not pass the `Config` fields into CLAHE unless changing those numbers is the point of the pull request.
- `estimate_focal_length` is a placeholder. Do not describe `focal_ratio * 1000` as a focal length measured from the images.
- `warp_to_cylindrical` leaves missed pixels at 0. Do not describe its result as a dense sample of every output pixel.
- `_preview_thread` and `_stitch_thread` call `update_status` and `display_pano` on the worker. Those methods touch Tk. Do not add another background path that touches widgets off the main thread.
- The worker bodies do not catch exceptions. A `ValueError` from `int` on `start_image`, `num_images`, or `frame_interval` leaves the thread. Do not hide that by catching `Exception` and discarding it.
- Do not commit `panorama.log` or `__pycache__/`.

## Scope

A fix for the startup `AttributeError` does not rename `stitcher.py`, add a package, or split the file. That work waits for a roadmap item the owner has accepted. Read `ROADMAP.md` before proposing one. It is a draft.
