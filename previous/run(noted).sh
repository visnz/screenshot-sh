for j in `ls -l | grep '/'| grep -v 'done'|awk -F" " '{print $9}'`;
# 遍历当前文件夹下的文件夹，排除掉带"done"的文件夹
	do 
	STEMP=0
	for i in `ls $j -l | grep -v '/'|awk -F" " '{print $9}'`;
		# 遍历其中一个文件夹，即为某一天的截图。
		do echo $i;
		# 输出一下名字
		mv $j/$i $j/screenshot`printf "%05d" $STEMP`.jpg;let "STEMP += 1";
		# 因为截图是按时分秒命名，串联的ffmpeg没办法识别这种格式，要全部重新命名，从0开始遍历命名。
	done
	firstfile=`ls $j -l | grep '^-'|awk -F" " '{print $9}'|grep '[0-9][0-9][0-9][0-9]\.'|head -n 1`
	# 获取第一个文件的名字，用于ffmpeg识别
	index=`echo $j/$firstfile|awk -F"." '{print $1}'|tail -c 5;`
	# 获取第一个文件的名字里的数字编号，用于ffmpeg识别
	encodefile=`echo $j/$firstfile|sed "s/$index\./%04d\./"`
	# 获取第一个文件的名字，把数字去掉，用于ffmpeg识别
	sstemp=`basename $j`
	# 获取文件所在目录
	targetfile=./`echo $firstfile|head -c -10`_$sstemp'.mov'
	# 设置生成目标文件，在外面
	ffmpeg -start_number $index -i $encodefile -vcodec mpeg4 -b 30M $targetfile -y
	# ffmpeg生成
	mv $j `echo done$j`
	# 把文件夹名字添加前缀done，排除后续遍历检查。done文件夹可删。
done
