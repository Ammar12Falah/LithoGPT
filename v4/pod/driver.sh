#!/bin/bash
# Runs ON THE POD, detached:  nohup bash pod/driver.sh > logs/driver.out 2>&1 &
# Resumable: every step skips work whose output exists (training resumes from resume.pt,
# generation skips finished wells). Re-running after a crash is always safe.
#
# Order is by importance, so that if the spend cap stops the pod, the primary results exist:
#   0 preflight (tests on the pod, GPU determinism, timing)      stop here if any test fails
#   1 tuning: Arm A seed 20260715, dropout x weight decay grid (6 runs), select the setting
#   2 training: A and B2 seeds 20260715..26 (paired), C seeds 20260715..19
#   3 generation, best checkpoint, confirmatory wells: A, B2, then C
#   4 generation, best checkpoint, pilot wells
#   5 generation, step-3000 checkpoint, confirmatory then pilot (secondary result)
#   6 scoring and the four main comparisons
# Baselines on the confirmatory wells run on the CPU alongside phases 1 to 3.
set -u
V4=/Users/ammar/LithoGPT_archive/LithoGPT-2/paper_atce/v4
cd "$V4"
PY=python
CONF=/workspace/lg/confirm/confirmatory_wells.csv
N_TRAIN=${N_TRAIN:-3}       # training jobs side by side on the GPU
N_GEN=${N_GEN:-4}           # generation jobs side by side on the GPU
THREADS=2                   # CPU threads per GPU job
mkdir -p logs runs gens out
log() { echo "[$(date -u '+%F %T UTC')] $*" | tee -a logs/driver.log; touch logs/HEARTBEAT; }
fail() { log "STOP: $*"; echo "$*" > logs/STOP_REASON.txt; touch logs/DRIVER_FINISHED; exit 1; }

# Progress = the newest file time in logs/ (every job writes its own log as it goes);
# the guard stops the pod if nothing in logs/ changes for 40 minutes.

run_queue() {   # $1 = jobs file, $2 = parallel jobs; each line is one shell command.
  # Run twice: jobs resume or skip finished work, so the second pass only redoes failures.
  xargs -P "$2" -I{} bash -c '{}' < "$1"
  xargs -P "$2" -I{} bash -c '{}' < "$1"
}

[ -f "$CONF" ] || fail "confirmatory wells file missing: $CONF"

# ---------------------------------------------------------------- 0 preflight
if [ ! -f out/PREFLIGHT_OK ]; then
  log "phase 0: tests on the pod (CPU), GPU determinism, timing"
  $PY -B d01_data.py --check > logs/d01_check_pod.log 2>&1 || fail "token sequences differ from the Mac build (logs/d01_check_pod.log)"
  $PY -B x10_tests.py --fast > logs/x10_fast_pod.log 2>&1
  grep -q "NOT OK" logs/x10_fast_pod.log && fail "a fast test is NOT OK on the pod (logs/x10_fast_pod.log)"
  V4_TEST_DEVICE=cuda $PY -B x10_tests.py --only same_seed_same_weights > logs/x10_det_cuda.log 2>&1
  grep -q "=> OK" logs/x10_det_cuda.log || fail "same seed does not give the same weights on the GPU (logs/x10_det_cuda.log)"
  $PY -B x11_timing.py > logs/x11_timing_cuda.log 2>&1 || fail "timing script failed"
  touch out/PREFLIGHT_OK
fi

# ---------------------------------------------------------------- CPU: baselines on the confirmatory wells
if [ ! -f out/BASELINES_CONF_DONE ]; then
  ( $PY -B b04_baselines.py run --csv "$CONF" > logs/b04_conf.log 2>&1 && touch out/BASELINES_CONF_DONE ) &
fi

# ---------------------------------------------------------------- 1 tuning
log "phase 1: tuning (6 runs, $N_TRAIN side by side)"
: > logs/jobs_tune.txt
for DO in 0 0.1 0.2; do for WD in 0.01 0.1; do
  echo "$PY -B t02_train.py --arm A --seed 20260715 --dropout $DO --wd $WD --outdir runs --threads $THREADS > logs/train_A_20260715_do${DO}_wd${WD}.log 2>&1" >> logs/jobs_tune.txt
done; done
run_queue logs/jobs_tune.txt "$N_TRAIN"
SETTING=$($PY -B x12_select.py --runs runs) || fail "setting selection failed"
DO=$($PY -c "import json;print(json.load(open('out/selected_setting.json'))['dropout'])")
WD=$($PY -c "import json;print(json.load(open('out/selected_setting.json'))['wd'])")
log "selected setting: $SETTING (dropout $DO, weight decay $WD)"

# ---------------------------------------------------------------- 2 training
log "phase 2: training A and B2 (12 paired seeds) and C (5 seeds)"
: > logs/jobs_train.txt
for S in $(seq 20260715 20260726); do
  for ARM in A B2; do
    echo "$PY -B t02_train.py --arm $ARM --seed $S --dropout $DO --wd $WD --outdir runs --threads $THREADS > logs/train_${ARM}_${S}.log 2>&1" >> logs/jobs_train.txt
  done
done
for S in $(seq 20260715 20260719); do
  echo "$PY -B t02_train.py --arm C --seed $S --dropout $DO --wd $WD --outdir runs --threads $THREADS > logs/train_C_${S}.log 2>&1" >> logs/jobs_train.txt
done
run_queue logs/jobs_train.txt "$N_TRAIN"

gen_jobs() {   # $1 ckpt, $2 wells (csv|pilot), $3 jobs file
  for ARM in A B2; do for S in $(seq 20260715 20260726); do
    R="runs/${ARM}_seed${S}_${SETTING}"
    if [ "$2" = csv ]; then W="--wells csv --csv $CONF"; else W="--wells pilot"; fi
    echo "$PY -B g03_generate.py --run_dir $R --ckpt $1 $W --threads $THREADS > logs/gen_${ARM}_${S}_$1_$2.log 2>&1" >> "$3"
  done; done
  for S in $(seq 20260715 20260719); do
    R="runs/C_seed${S}_${SETTING}"
    if [ "$2" = csv ]; then W="--wells csv --csv $CONF"; else W="--wells pilot"; fi
    echo "$PY -B g03_generate.py --run_dir $R --ckpt $1 $W --threads $THREADS > logs/gen_C_${S}_$1_$2.log 2>&1" >> "$3"
  done
}

# ---------------------------------------------------------------- 3, 4, 5 generation
for PHASE in "best csv" "best pilot" "final csv" "final pilot"; do
  set -- $PHASE
  log "generation: checkpoint $1, wells $2 ($N_GEN side by side)"
  J=logs/jobs_gen_$1_$2.txt; : > "$J"; gen_jobs "$1" "$2" "$J"
  run_queue "$J" "$N_GEN"
done

# ---------------------------------------------------------------- 6 scoring
log "phase 6: waiting for the confirmatory baselines, then scoring"
while [ ! -f out/BASELINES_CONF_DONE ]; do sleep 60; done
$PY -B s05_score.py score --csv "$CONF" $(ls -d gens/*/best/csv gens/*/final/csv gens/baseline_*/seed*/csv) > logs/s05_conf.log 2>&1
$PY -B s05_score.py score $(ls -d gens/*/best/pilot gens/*/final/pilot) > logs/s05_pilot.log 2>&1
for CK in best final; do
  $PY -B s05_score.py compare --wellset csv --setting "$SETTING" --ckpt $CK > logs/compare_csv_$CK.log 2>&1
  $PY -B s05_score.py compare --wellset pilot --setting "$SETTING" --ckpt $CK > logs/compare_pilot_$CK.log 2>&1
done
log "ALL DONE"
touch logs/DRIVER_FINISHED
