# DQ Gate 8 — G8 PLOTTING ENVIRONMENT

## a. Working environment before

`audit/env_before.txt` — 11 packages, system Python 3.9.6, no matplotlib (as established in
DQ Gate 3).

## b. Isolated venv

```
python3 -m venv ~/lithogpt_plot   # exit 0
~/lithogpt_plot/bin/pip install --upgrade pip   # 21.2.4 -> 26.0.1 (venv-local only)
~/lithogpt_plot/bin/pip install matplotlib      # exit 0
```
Resolved and pinned versions (`audit/lithogpt_plot_venv_pins.txt`):
```
contourpy==1.3.0
cycler==0.12.1
fonttools==4.60.2
importlib_resources==6.5.2
kiwisolver==1.4.7
matplotlib==3.9.4
numpy==2.0.2
packaging==26.2
pillow==11.3.0
pyparsing==3.3.2
python-dateutil==2.9.0.post0
six==1.17.0
zipp==3.23.1
```
matplotlib 3.9.4 (latest compatible with this Mac's system Python 3.9.6) plus its required
dependency closure only — nothing else installed into the venv.

## c. Working environment after, diffed

```
$ python3 -m pip freeze > audit/env_after.txt
$ diff audit/env_before.txt audit/env_after.txt
$ echo $?
0
```
**Byte-identical. The working environment was not touched.** (The venv's own numpy 2.0.2
happens to match the working environment's numpy 2.0.2 by coincidence of both picking the
latest cp39 wheel — they are still two fully separate installations; nothing was installed,
upgraded, or downgraded outside `~/lithogpt_plot`.)

G8 STATUS: COMPLETE. Continuing to G9.
