@ECHO OFF


echo MOOSAS PARALLEL TEST

set /a startS=%time:~6,2%
set /a startM=%time:~3,2%
echo %time%
@ECHO RADIANCE: generate .oct file 
oconv.exe model.rad > model_moosas.oct
@ECHO RADIANCE: renderding
rtrace.exe  -w -h -I+ -u -aa 0.15 -ab 4 -ad 256 -ar 32 -as 20 -st 1 -lw 0.05 -dc 0 -dj 0.7 -dp 32 -dr 0 -ds 0 model_moosas.oct < grid_parallel.input | rcalc -e "$1=($1*0.265+$2*0.670+$3*0.065)*179" > ill_moosas_parallel.output
@ECHO RADIANCE: done

set /a endS=%time:~6,2%
set /a endM=%time:~3,2%
echo %time%
set /a diffS_=%endS%-%startS%
set /a diffM_=%endM%-%startM%
echo MOOSAS PARALLEL cost time:%diffM_%-%diffS_% 

echo ##################  spilt line ##########################

echo MOOSAS TEST

set /a startS=%time:~6,2%
set /a startM=%time:~3,2%
echo %time%
@ECHO RADIANCE: generate .oct file 
oconv.exe model.rad > model_moosas.oct
@ECHO RADIANCE: renderding
rtrace.exe  -w -h -I+ -u -aa 0.15 -ab 4 -ad 256 -ar 32 -as 20 -st 1 -lw 0.05 -dc 0 -dj 0.7 -dp 32 -dr 0 -ds 0 model_moosas.oct < grid.input | rcalc -e "$1=($1*0.265+$2*0.670+$3*0.065)*179" > ill_moosas.output
@ECHO RADIANCE: done

set /a endS=%time:~6,2%
set /a endM=%time:~3,2%
echo %time%
set /a diffS_=%endS%-%startS%
set /a diffM_=%endM%-%startM%
echo MOOSAS cost time:%diffM_%-%diffS_% 

echo ##################  spilt line ##########################

echo Radiance MEDIUM TEST

set /a startS=%time:~6,2%
set /a startM=%time:~3,2%
echo %time%
@ECHO RADIANCE: generate .oct file 
oconv.exe model.rad > model_moosas.oct
@ECHO RADIANCE: renderding
rtrace.exe  -w -h -I+ -u -aa 0.15 -ab 4 -ad 800 -ar 1904 -as 128 -st 0.1 -lw 0.0001 -dc 0.5 -dj 0.7 -dp 32 -dr 0 -ds 0 -av 0.1 0.1 0.1 model_moosas.oct < grid.input | rcalc -e "$1=($1*0.265+$2*0.670+$3*0.065)*179" > ill_radiance_medium.output
@ECHO RADIANCE: done

set /a endS=%time:~6,2%
set /a endM=%time:~3,2%
echo %time%
set /a diffS_=%endS%-%startS%
set /a diffM_=%endM%-%startM%
echo Radiance MEDIUM cost time:%diffM_%-%diffS_% 

echo ##################  spilt line ##########################

echo Daysim TEST

set /a startS=%time:~6,2%
set /a startM=%time:~3,2%
echo %time%
@ECHO RADIANCE: generate .oct file 
oconv.exe model.rad > model_moosas.oct
@ECHO RADIANCE: renderding
rtrace.exe  -w -h -I+ -u -aa 0.1 -ab 5 -ad 1000 -ar 300 -as 20 -st 0.15 -lw 0.004 -lr 6 -dj 0 -dp 512 -dr 2 -ds 0.2 model_moosas.oct < grid.input | rcalc -e "$1=($1*0.265+$2*0.670+$3*0.065)*179" > ill_daysim.output
@ECHO RADIANCE: done
set /a endS=%time:~6,2%
set /a endM=%time:~3,2%
echo %time%
set /a diffS_=%endS%-%startS%
set /a diffM_=%endM%-%startM%
echo Daysim cost time:%diffM_%-%diffS_% 


echo ##################  spilt line ##########################

echo HIGH ACCURACY TEST
set /a startS=%time:~6,2%
set /a startM=%time:~3,2%
echo %time%
@ECHO RADIANCE: generate .oct file 
oconv.exe model.rad > model_moosas.oct
@ECHO RADIANCE: renderding
rtrace.exe  -w -h -I+ -u -aa 0.15 -ab 6 -ad 1024 -ar 96 -as 2 -st 0.05 -lw 0.000001 -dc 0 -lr 6 -dj 0 -dp 4096 -dr 3 -ds 0.01 -ms 1.1 -ss 32 -dt 0 model_moosas.oct < grid.input | rcalc -e "$1=($1*0.265+$2*0.670+$3*0.065)*179" > ill_high_accuracy.output
@ECHO RADIANCE: done
set /a endS=%time:~6,2%
set /a endM=%time:~3,2%
echo %time%
set /a diffS_=%endS%-%startS%
set /a diffM_=%endM%-%startM%
echo HIGH ACCURACY cost time:%diffM_%-%diffS_% 


echo ##################  spilt line ##########################

echo RADSITE TEST
set /a startS=%time:~6,2%
set /a startM=%time:~3,2%
echo %time%
@ECHO RADIANCE: generate .oct file 
oconv.exe model.rad > model_moosas.oct
@ECHO RADIANCE: renderding
rtrace.exe  -w -h -I+ -u -aa 0.15 -ab 2 -ad 512 -ar 128 -as 256 -st 0.15 -lw 0.002 -dc 0.5 -lr 8 model_moosas.oct < grid.input | rcalc -e "$1=($1*0.265+$2*0.670+$3*0.065)*179" > ill_radsite.output
@ECHO RADIANCE: done
set /a endS=%time:~6,2%
set /a endM=%time:~3,2%
echo %time%
set /a diffS_=%endS%-%startS%
set /a diffM_=%endM%-%startM%
echo RADSITE cost time:%diffM_%-%diffS_% 

