@echo off
wsl -u root -e sh -c "sync; echo 3 > /proc/sys/vm/drop_caches; echo dropped-pre" >> work/p5/b1b3\grade.out 2>&1
wsl -e bash work/p5/b1b3/grade_b1b3.sh TM_s00 TM_s01 TM_s02
wsl -u root -e sh -c "sync; echo 3 > /proc/sys/vm/drop_caches; echo dropped-post" >> work/p5/b1b3\grade.out 2>&1
