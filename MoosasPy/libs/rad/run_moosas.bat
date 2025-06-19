::以下为隐藏radiance运行的操作
@echo off 
:: if "%1"=="h" goto begin 
::     mshta vbscript:createobject("wscript.shell").run("""%~nx0"" h",0)(window.close)&&exit 
:: :begin 
::以下为正常批处理命令，不可含有pause set/p等交互命令 


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
echo cost:%diffM_%-%diffS_% 

::应该触发运行完毕的消息，配合隐藏窗口使用
