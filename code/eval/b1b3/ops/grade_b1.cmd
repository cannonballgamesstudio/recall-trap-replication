@echo off
wsl -u root -e sh -c "sync; echo 3 > /proc/sys/vm/drop_caches; echo dropped-pre" >> work/p5/b1b3\grade.out 2>&1
wsl -e bash work/p5/b1b3/grade_b1b3.sh ON_s00 ON_s01 ON_s02 OFF_s00 OFF_s01 OFF_s02 T_s00 T_s01 T_s02
wsl -u root -e sh -c "sync; echo 3 > /proc/sys/vm/drop_caches; echo dropped-post" >> work/p5/b1b3\grade.out 2>&1
