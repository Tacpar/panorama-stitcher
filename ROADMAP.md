# Roadmap

> **DRAFT for discussion.** The owner has not made decisions for this project. Nothing here is scheduled, accepted, or tagged. The milestone grouping is a proposal and can be reordered or dropped. Anything not supported by the repository is a proposal or a question, not a requirement.

The README calls this a panorama stitching application with a modular structure for images and video. From the code, the job appears to be: choose a folder of still images or a video file, build one panorama with OpenCV, show it, and save a JPEG. That reading is inferred. The repository does not name a user, a camera, or a definition of a good stitch.

`AGENTS.md` has the working rules for agents, including the version file and the ban on pushing to the default branch.

## Current state

The repository is `stitcher.py`, a one-line `README.md`, `VERSION` (`0.1.0`), `CHANGELOG.md`, `AGENTS.md`, and this draft. There is no package, dependency file, test suite, CI, linter, `.gitignore`, license, or sample media. `stitcher.py` has no `__version__`. No git tag exists. The classes in the one file are the "modular structure" the README names.

`python3 stitcher.py` does not reach `mainloop`. `PanoramaController` builds `UIManager` before it sets `root.controller`, and the Select Input button reads `root.controller` while the button is being created. A check on Python 3.12.3, Tk 8.6, OpenCV 5.1.0, NumPy 2.5.5, and Pillow 13.0.0 exited with status 1 and `AttributeError`. Those versions are the check, not a support matrix. The repository does not pin them. The status labels and the Preview, Stitch, and Save buttons are later in `create_widgets` and were not created.

What the pipeline does once `stitch_images` or the loaders are called directly:

- A folder load is a non-recursive lexicographic sort of `*.jpg` and `*.png`. On Linux, `img1.png`, `img10.png`, `img2.png` loaded in that order. `.jpeg`, `.JPG`, and `.PNG` were not loaded. `start_image` is a 1-based index into that list. `num_images` of `all` in any case keeps the rest.
- A video load keeps 1-based frames at or after `start_image` whose index is divisible by `frame_interval` (default `10`). On a 25-frame file, interval 10 and start 1 kept frames 10 and 20. Start 15 kept frame 20. The folder and the video do not use `start_image` the same way.
- `available_images` is a count of matching stills, or `frame_count // interval` for a video. It is logged and not shown. The video figure ignores `start_image`.
- Every selected frame is held in a list at full size. `load_images` accepts `max_size` and the loaders ignore it. `stitch_images` then resizes so the long side is at most 400 px (`INTER_AREA`). Checked: 1000×800 (width × height) became 400×320.
- The default `projection` is `spherical`, which does not warp in this file. `cylindrical` runs `warp_to_cylindrical` first. That function writes source pixels onto a black image with the tangent map in the source, leaves missed pixels at 0, and can stack two source pixels on one integer coordinate. A 20×30 check with `f = 500` turned 100 painted pixels into 91 nonzero outputs. Focal length is `float(focal_ratio) * 1000` (default 500) and does not look at the images. The function comment calls that a placeholder.
- Before OpenCV stitches, each frame is converted to gray, passed through CLAHE with clip `2.0` and tile grid `(8, 8)`, and expanded back to three channels. `Config.clahe_clip_limit` is `1.0` and is never read, and neither is `clahe_tile_grid_size`. A two-image synthetic stitch with the default `spherical` projection, on OpenCV 5.1.0, came back with three equal channels.
- The stitcher is always `cv2.Stitcher_create(cv2.Stitcher_PANORAMA)`. `Config.mode` (`"PANORAMA"`) and `Config.quality` (`"low (Orb)"`) are never read. `transpose_images` is never read. `is_preview` is accepted and unused, so the preview thread and the stitch thread call the same function. The file does not set a feature finder, a warper, or a confidence on the stitcher.
- A status other than `cv2.Stitcher_OK` returns `None` and logs `Stitching failed with status: {status}`. On OpenCV 5.1.0 an empty list and a single image logged status `1`. The UI failure strings, if the window ran, would be `Preview failed` and `Stitching failed`, without that number.
- Save, if a preview canvas exists, stitches again from the source and writes a JPEG. It ignores the `cv2.imwrite` return value. The save dialog was not opened.
- Preview and stitch are started on daemon threads that call Tk (`update_status`, `display_pano`) from the worker, with no `try` around the body. Those threads were not run, because construction raises first.
- `PanoramaController` builds an `ImageProcessor` it never uses. `close_popup` is never called. `datetime`, `gc`, and `traceback` are imported and unused.
- Importing the module opens `panorama.log` in the working directory. There is no `.gitignore`.

Not in the tool: a way to start the window, a dependency pin, a test, a sample, a headless entry point, or a written bar for a successful stitch.

## Proposed milestones

Version numbers follow `AGENTS.md`. `0.1.0` is the untagged baseline above. A tag is created only when the owner asks.

### v0.1.1 — open the window

The baseline exits during widget construction. This patch makes the existing buttons reachable and leaves the picture alone.

- Assign `root.controller` before any button reads it, or resolve the controller inside the callback so creation does not need the attribute yet.
- `python3 stitcher.py` stays in `mainloop` with Select Input, Preview, Stitch, and Save created, and those commands bound to the controller methods.
- `load_images` and `stitch_images` keep today's frame choice, 400 px cap, gray CLAHE (clip `2.0`, tiles `8×8`), projection gate, and `Stitcher_PANORAMA`.
- `CHANGELOG.md` records the fix under `## [Unreleased]`, and `VERSION` becomes `0.1.1` when that patch is the release. Tag `v0.1.1` only when the owner asks.

### v0.2.0 — an install and tests that lock this picture

A second machine cannot install from the repo, and nothing locks the pipeline the 0.1.1 fix must not disturb.

- Record OpenCV, NumPy, and Pillow in a file an install can use, and document the Tk package (`python3-tk` on Debian/Ubuntu). A version pin waits on question 17. Until then, name the modules the file imports and do not claim a supported range.
- Add `tests/` and `python3 -m pytest`. Cover the oracles in `AGENTS.md`: resize, the focal-length placeholder, the cylindrical gate, folder sort and slice, video frame selection, and a non-OK stitch returning `None` with the log line.
- The tests run without `mainloop`. Importing `stitcher.py` currently imports `tkinter`, so either the test job has Tk or the pipeline under test moves to a module that does not import it. The milestone does not otherwise restructure the file.
- Ignore `panorama.log` and `__pycache__/` in a `.gitignore`.
- Extend `README.md` with the run command, the libraries, and the pipeline rules the tests lock (400 px long side, gray CLAHE, spherical meaning no pre-warp in this file).
- Done when `python3 -m pytest` passes on a machine that followed the new install notes, and a one-image failure plus a two-image stitch still follow the 0.1.0 pipeline.

### v0.3.0 — failures the operator can see

The worker calls Tk from a daemon thread, and a stitch failure's status integer stays in the log.

- Run status updates and `display_pano` on the Tk main thread.
- An exception in preview or stitch is written to the log and to the status line. The window stays up.
- When `stitch_images` returns `None`, the status line includes the same status integer the log already records.
- Done when a one-image folder ends in a visible failure that includes that integer, a two-image folder that OpenCV accepts still shows the panorama, and the tests from v0.2.0 still pass.

If the owner drops the window in favor of a headless command, this milestone is that command's error path instead of a Tk thread rule. The integer and the traceback still have to be visible.

### v0.4.0 — settings that are stored and never read

`mode`, `quality`, `transpose_images`, `clahe_clip_limit`, `clahe_tile_grid_size`, `is_preview`, and the loader `max_size` do not affect the picture. The controller's extra `ImageProcessor` and `close_popup` are unused.

- Remove each unread field, or leave it in the window with the behavior it actually has today.
- Do not apply `clahe_clip_limit` of `1.0` in place of the hardcoded clip `2.0`. Do not switch the stitcher to `Stitcher_SCANS`. Do not start honoring `quality` or `transpose_images`. Those are behavior changes and wait on the questions below.
- `is_preview` is removed, or preview and stitch differ only in a way the owner has specified.
- Done when every remaining `Config` field is read by the behavior its name describes, the default spherical path still matches the v0.2.0 tests, and the changelog names any field that was removed.

### v0.5.0 — color, resolution, projection, and save

This milestone applies the owner's answers. It does not start until the questions on color, the 400 px cap, projection, focal length, and save have answers.

- The long-side cap is either the stitch resolution, documented as such, or limited to preview while stitch uses a stated size.
- The color path is either the current gray CLAHE, stated in the README in those words, or a color path the owner asked for, with the CLAHE clip and tile grid taken from the values they choose.
- `spherical` and `cylindrical` each match a warp the owner has described, including what happens to pixels the current cylindrical map leaves at 0. Focal length comes from the source they name. The placeholder `focal_ratio * 1000` remains only if they say it is the rule.
- Save writes the panorama already shown, or it documents a recomputation from the source. A failed `cv2.imwrite` is reported. Formats are the ones the owner names. JPEG is the only filter today.
- Done when each of those matches the answer, tests cover the new rule, and `CHANGELOG.md` describes the change to the picture.

### v1.0.0 — the bar the owner sets

v1.0.0 is the first version that can be tagged as usable for the input and hardware the owner names. The success bar is not in the repository, so this milestone does not invent one.

- The owner has written who the tool is for, which inputs it must accept, and what a successful stitch is (questions below).
- A fixture the owner accepts meets that bar, including the failure behavior from v0.3.0.
- `README.md` matches the run command and the picture the tests lock.
- Date the changelog section and tag `v1.0.0` when the owner asks. After that tag, changing the meaning of the output is a major version, as `AGENTS.md` says.

## Open questions for the owner

1. Widget construction raises `AttributeError` before `mainloop`. Should the next change only attach the existing buttons, with `load_images` and `stitch_images` left as they are, or do you want layout changes in that same patch?
2. Is the product a desktop window, a headless command, or both? A headless command drops the Tk thread work in v0.3.0 and changes v1.0.0.
3. Which input is first: a folder of stills, a video, or both equally? What resolution, frame count, and overlap should a milestone be judged on?
4. Is the 400 px long-side cap the stitch resolution for every run? Preview and stitch share it, and `is_preview` is ignored.
5. Should the panorama be color? The stitch path converts each frame to gray, runs CLAHE with clip `2.0` and tile grid `(8, 8)`, and expands that to three channels. `Config.clahe_clip_limit` is `1.0` and is never read. A synthetic stitch on OpenCV 5.1.0 came back with equal channels.
6. What should `projection` mean? `spherical` does not warp in this file. `cylindrical` runs `warp_to_cylindrical`, then the same `Stitcher_PANORAMA` path. `Config.mode` and `Config.quality` (`"low (Orb)"`) are never read, and the file does not choose a feature finder.
7. `estimate_focal_length` returns `focal_ratio` (default `0.5`) times 1000 and ignores the images. The comment calls it a placeholder. What should the source be, and should `warp_to_cylindrical` stay? It writes onto a black image, so missed pixels remain 0. A 20×30 check with `f = 500` kept 91 of 100 painted pixels. That check is not a comparison to a reference cylindrical projection.
8. Folder order is lexicographic on `*.jpg` and `*.png` (`img1`, `img10`, `img2` in a Linux check). `.jpeg`, `.JPG`, and `.PNG` were not loaded. Is that the capture order and the format set you need, or do you need numeric filenames or EXIF time?
9. For video, a frame is kept when its 1-based index is at least `start_image` and divisible by `frame_interval` (default `10`). For a folder, `start_image` is a 1-based index into the sorted list. Should those settings mean the same thing?
10. What machine is the target, and is there a limit on runtime or memory? Selected frames are stored full size, and the cylindrical warp is a Python loop over every pixel. The file contains no GPU calls. No runtime or memory figure was measured.
11. What is a successful stitch, and what should a failure show? On OpenCV 5.1.0, an empty list and a single image returned `None` and logged status `1` (`Stitcher_ERR_NEED_MORE_IMGS` in that build). The UI strings do not include the number. The repo does not pin OpenCV, so that integer was not checked on any other version.
12. Save stitches again from the source, offers JPEG only, and runs only when a preview canvas exists. `cv2.imwrite`'s return value is ignored. Should save write the image already shown, and which formats are required?
13. Which unread settings should become real controls (`mode`, `quality`, `transpose_images`, the two CLAHE fields, frame interval, start, count, focal ratio, projection), and which should be deleted? Wiring the stored CLAHE clip would change it from `2.0` to `1.0`.
14. Should `v0.1.0` be tagged on the current tree, including the startup failure, or should the first tag wait until the window stays up and tests lock the pipeline?
15. Is running `stitcher.py` from a known commit enough, or do you want an installable package and a headless entry point?
16. Who has to review a pull request that changes the panorama for the same input before it can merge?
17. The check used Python 3.12.3, Tk 8.6, OpenCV 5.1.0, NumPy 2.5.5, and Pillow 13.0.0. Which versions should the project support? The file calls `cv2.Stitcher_create` (the OpenCV 4/5 name), not `cv2.createStitcher`.
18. Importing the module writes `panorama.log` at `DEBUG` in the working directory. Should that stay the diagnostic, and should the log stay untracked?
