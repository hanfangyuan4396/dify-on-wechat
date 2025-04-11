ps -ef | grep app.py | grep -v grep | awk '{print $2}' | xargs kill
nohup /opt/miniconda3/envs/cow/bin/python -u app.py >> wechat_robot.log 2>&1 &

