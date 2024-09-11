mkdir /e/Multishot/
while [ 1 ];
do mkdir /e/Multishot/`date +"%m-%d"` ;
ffmpeg -f gdigrab -i desktop -s 2240x720 /e/Multishot/`date +"%m-%d"`/screenshot-`date +"%d %T" | sed -e "s/ /-/g; s/:/-/g"`.jpg;
sleep 5;
done