# Run record, confirmatory test (written 21 November 2026, before any result was opened)

## The run
- Pod: RunPod, 1 x NVIDIA A40, Secure Cloud, EU-SE-1, $0.59 per hour; image runpod/pytorch:1.5.0-cu1281-torch280-ubuntu2404
  (Python 3.12.3, torch 2.8.0+cu128). Network volume az93s017wo mounted at /workspace.
- Launches: launch 1 stopped in phase 0 (a resume bug in t02_train.py, fixed before any training; see DEVIATIONS.md in the
  pipeline repo). Launch 2 was stopped after 3 minutes by a stale marker in the Mac watcher. Launch 3 produced the results.
- Launch 3: driver started 2026-11-19 11:29:25 UTC; ALL DONE 2026-11-20 23:29:43 UTC; pod stopped 23:36 UTC.
- Code that ran: every pipeline file on the volume is byte-identical to pipeline commit
  3899723 (paper_atce repo, branch v4/confirmatory-pipeline), checked file by file. The published pipeline commit is
  f94ef8689b00177e218ad33496ebbc3dae157d8a; between the two, the analysis change is the resume fix in t02_train.py only,
  plus pod scripts (pod.py for the RunPod API v2, push, setup, guard, watcher).
- Selected setting (development loss, phase 1): dropout 0.2, weight decay 0.1.
- Seeds: 20260715 to 20260726 for A and B2, 20260715 to 20260719 for C; every run.json has complete: true.
- Tokenizer: cache/tokenizer_v4.joblib (holds the scaler and the k-means), SHA-256
  bd009abf313fd97c0f51f00ebb7b73e77fca2147fa49ba49bb250d22409c2b36.
- Billed by RunPod for the three launches: $21.31 (billing API, 2026-11-21).

## Copies and hashes
All lists are SHA-256, one line per file, paths relative to the run folder
(paper_atce/v4 on the pod; /workspace/lg/archive/LithoGPT-2/paper_atce/v4 on the network volume).
- Network volume az93s017wo, hashed on 2026-11-21 from a pod mounting it: 4,987 files in the run folder.
- Mac copy (paper_atce/v4/pod_results): 4,987 files. Same names, and all 4,987 hashes equal to the volume's.
  List: run_record/run_folder_2026-11-21.sha256 (SHA-256 of the list file:
  eceb7cfc9c09f00dcf9c6f83d108c1a412a693f1a560e9a4d2f039d057d4d95e).
- The run's inputs on the volume (train.csv, split manifest, trend.py, confirmatory_wells.csv) are identical to
  the Mac originals.
- Second copy off the Mac: iCloud Drive, folder LithoGPT_v4_confirmatory_run_2026-11-21, file run_core.tar
  (2,476,896,768 bytes, SHA-256 725248d249953254fdacd04d9a31254076a2ced24d25e1d39ae4544f380d2f5a). It holds
  3,926 files: everything except the 100-step checkpoints (runs/*/ckpt/) and resume.pt files, which do not fit
  in the free iCloud space. Every member was read back from the tar and its hash equals the list above.
  Member list: run_record/icloud_core_members_2026-11-21.sha256.
- The 100-step checkpoints and resume.pt files are on the Mac and on the network volume (kept).

## What the copied run folder records, and what it does not
- Recorded: torch 2.8.0+cu128 and the device in every runs/*/run.json; GPU type NVIDIA A40 in out/x11_timing_cuda.json;
  the seed of every run in its run.json; the tokenizer file (scaler and k-means) and its SHA-256 in cache/;
  the pinned package versions in pod/requirements_pod.txt; SHA-256 of every pushed input in pod/inputs.sha256.
- Not recorded inside the folder: the code commit (it is identified above by matching file hashes); the installed
  versions of numpy, scipy, pandas, scikit-learn and joblib as observed on the pod (only the pins are recorded; the
  setup output was written to the pod's container disk, which is gone); the Python version (3.12.3 was seen during
  setup but is not saved in the folder).
