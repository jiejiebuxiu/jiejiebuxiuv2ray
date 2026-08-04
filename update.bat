@echo off
chcp 65001 >nul
title V2Ray节点自动更新系统

echo ===============================
echo      V2Ray 自动更新 V13
echo ===============================
echo.

cd /d "%~dp0"

echo [1/5] 测速节点...
python speed_rank_v9.py

echo.
echo [2/5] 清洗节点...
python clean_filter.py

echo.
echo [3/5] 最终排序...
python final_sort_v7.py

echo.
echo [4/5] 生成订阅...
python make_sub_v11.py

echo.
echo [5/5] 上传GitHub...

git add .
git commit -m "auto update nodes"
git push

echo.
echo ===============================
echo 更新完成！
echo V2RayN订阅会自动刷新
echo ===============================

pause